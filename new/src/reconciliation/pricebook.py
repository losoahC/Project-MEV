"""Contract-aware historical prices with raw-file provenance and explicit missing observations."""
import base64
import csv
from decimal import Decimal
import io
import json
from pathlib import Path
import re
import zipfile

from src.decoding.events import WETH,USDT,USDC
from src.ingestion.evidence import read_json


class PriceBook:
    def __init__(self,engine):
        self.engine=engine
        self.registry={}
        self.bars={}
        self.conflicts=[]
        self.loaded=set()
        currency_path=engine.source('coinbase_currency_contracts.json')
        tokens_path=engine.source('coingecko_eth_tokenlist.json')
        if not currency_path or not tokens_path:
            raise FileNotFoundError('Currency contract catalog and chain-specific decimal registry required')
        self.currency_source=self.archive(currency_path,'https://api.exchange.coinbase.com/currencies','Coinbase supported network contracts; legacy snapshot')
        self.token_source=self.archive(tokens_path,'https://tokens.coingecko.com/ethereum/all.json','Ethereum token registry; decimals are metadata until RPC crosscheck')
        tokens={t['address'].lower():t for t in read_json(tokens_path)['tokens'] if t['chainId']==1}
        for currency in read_json(currency_path):
            for network in currency.get('supported_networks',[]):
                address=(network.get('contract_address') or '').lower()
                if network.get('id')=='ethereum' and re.fullmatch(r'0x[0-9a-f]{40}',address) and address in tokens:
                    self.registry[address]={'symbol':currency['id'].upper(),'decimals':tokens[address]['decimals'],'identity_basis':self.currency_source,'decimal_basis':self.token_source}
        self.registry[WETH]={'symbol':'ETH','decimals':18,'identity_basis':'WETH contract redemption parity with native ETH; explicit wrapper assumption','decimal_basis':'ERC20 WETH canonical constant'}
        self.registry['native:eth']={'symbol':'ETH','decimals':18,'identity_basis':'Ethereum native ETH','decimal_basis':'Ethereum wei denomination'}

    def archive(self,path,provider,method):
        path=Path(path)
        if path.is_relative_to(self.engine.legacy):
            return self.engine.store.archive(path,provider,method)
        return str(path.relative_to(self.engine.store.root))

    def add_bar(self,symbol,timestamp,close,low,high,source,venue='Coinbase',quote='USD'):
        t=int(timestamp);values=tuple(Decimal(str(v)) for v in (close,low,high))
        if any(v<=0 for v in values):
            return
        key=(venue,symbol,t)
        if key in self.bars:
            prior=self.bars[key]
            if tuple(Decimal(prior[k]) for k in ('close','low','high'))!=values:
                self.conflicts.append({'venue':venue,'symbol':symbol,'bar_start':t,'first':prior,'other_source':source,'other_values':list(map(str,values))})
                prior['conflicting']=True
            prior['sources']=sorted(set(prior['sources'])|{source})
        else:
            self.bars[key]={'close':str(values[0]),'low':str(values[1]),'high':str(values[2]),'quote':quote,'sources':[source],'conflicting':False}

    def load(self,symbol):
        symbol=symbol.upper()
        if symbol in self.loaded:
            return
        self.loaded.add(symbol)
        candidates=[]
        for directory in ('prices_raw','extension_prices_raw'):
            actual=self.engine.legacy/directory
            paths=list(actual.glob('*.json')) if actual.exists() else [p for origin,p in self.engine.archive_by_origin.items() if origin.startswith(directory+'/')]
            for p in paths:
                origin=str(p.relative_to(self.engine.legacy)) if p.is_relative_to(self.engine.legacy) else next(o for o,v in self.engine.archive_by_origin.items() if v==p)
                name=Path(origin).stem
                if name.upper()==symbol or re.fullmatch(re.escape(symbol)+r'_\d+',name,re.I):
                    candidates.append(p)
        directory=self.engine.legacy/'inventory_price_raw'
        paths=list(directory.glob('coinbase_*.json')) if directory.exists() else [p for o,p in self.engine.archive_by_origin.items() if o.startswith('inventory_price_raw/coinbase_')]
        for p in paths:
            origin=str(p.relative_to(self.engine.legacy)) if p.is_relative_to(self.engine.legacy) else next(o for o,v in self.engine.archive_by_origin.items() if v==p)
            if re.fullmatch('coinbase_'+re.escape(symbol)+r'_\d+\.json',Path(origin).name,re.I):
                candidates.append(p)
        for path in sorted(set(candidates)):
            data=read_json(path)
            if not isinstance(data,list):
                continue
            source=self.archive(path,'https://api.exchange.coinbase.com',f'Historical {symbol}-USD candles; granularity=60; legacy cached bytes')
            for row in data:
                if isinstance(row,list) and len(row)==6:
                    self.add_bar(symbol,row[0],row[4],row[1],row[2],source)

        fresh_index=self.engine.store.root/'data/processed/fresh_price_sources.json'
        if fresh_index.exists():
            for item in read_json(fresh_index):
                if item['symbol']!=symbol or not item.get('usable'):
                    continue
                doc=read_json(self.engine.store.root/item['evidence_path'])
                if doc.get('http_status')!=200 or not isinstance(doc.get('response'),list):
                    continue
                for row in doc['response']:
                    if isinstance(row,list) and len(row)==6 and Decimal(str(row[5]))>0:
                        self.add_bar(symbol,row[0],row[4],row[1],row[2],item['evidence_path'])

    def binance_eth(self,online=False):
        self.binance_spot('ETH',('2026-10-29','2026-10-30'))

    def binance_spot(self,symbol,days):
        for day in days:
            url=f'https://data.binance.vision/data/spot/daily/klines/{symbol}USDT/1m/{symbol}USDT-1m-{day}.zip'
            doc,source=self.engine.public.get(url)
            if doc.get('http_status')!=200:
                continue
            with zipfile.ZipFile(io.BytesIO(base64.b64decode(doc['response_body_base64']))) as z:
                for name in z.namelist():
                    if not name.endswith('.csv'):
                        continue
                    for row in csv.reader(io.TextIOWrapper(z.open(name))):
                        if not row or not row[0].isdigit() or Decimal(row[5])<=0:
                            continue
                        t=int(row[0]);t=t//1_000_000 if t>=100_000_000_000_000 else t//1000
                        self.add_bar(symbol,t,row[4],row[3],row[2],source,venue='Binance',quote='USDT')

    def price(self,symbol,timestamp,stale=0,lookback=1,venue='Coinbase',field='close'):
        self.load(symbol)
        target=int(timestamp)//60*60-60*lookback
        for offset in range(stale+1):
            t=target-offset*60
            bar=self.bars.get((venue,symbol.upper(),t))
            if not bar or bar['conflicting']:
                continue
            value=Decimal(bar[field]);evidence={'venue':venue,'symbol':symbol,'quote':bar['quote'],'bar_start':t,'stale_minutes':offset,'lookback_minutes':lookback,'field':field,'sources':bar['sources']}
            if bar['quote']=='USDT':
                mark=self.price('USDT',timestamp,stale,lookback,'Coinbase',field)
                if mark is None:
                    return None
                value*=mark[0];evidence['USDT_USD_conversion']=mark[1]
            return value,evidence
        return None

    def value(self,address,raw,timestamp,stale=0,lookback=1,eth_venue='Coinbase',field='close'):
        meta=self.registry.get(address)
        if not meta:
            return {'address':address,'raw':str(raw),'USD':None,'reason':'unverified_contract_to_market_mapping'}
        p=self.price(meta['symbol'],timestamp,stale,lookback,eth_venue if meta['symbol']=='ETH' else 'Coinbase',field)
        if p is None:
            return {'address':address,'raw':str(raw),**meta,'USD':None,'reason':'no_nonconflicting_completed_minute_price'}
        amount=Decimal(raw)/Decimal(10)**meta['decimals']
        return {'address':address,'raw':str(raw),**meta,'quantity':str(amount),'reference_USD':str(p[0]),'USD':str(amount*p[0]),'price_evidence':p[1],'confidence':'reference_price_estimate_from_contract_matched_market'}

    def dump(self,path):
        rows=[{'venue':v,'symbol':s,'bar_start':t,**b} for (v,s,t),b in sorted(self.bars.items())]
        path.write_text(json.dumps({'rows':rows,'conflicts':self.conflicts,'registry':self.registry},indent=2))
