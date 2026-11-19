"""Frozen, auditable marks. No future quote or ticker-only token matching."""
import json,bisect
from decimal import Decimal,getcontext
from src.event_allocation.config import ROOT,OUT,END
from src.event_allocation.prices import expanded_book
from src.decoding.events import USDT,USDC,WETH
from src.arbitrage.tron_accounting import U,W,ZERO
getcontext().prec=90

class Quotes:
    def __init__(self,mode='primary'):
        assert mode in ['primary','stable1'];self.mode=mode;self.book=expanded_book();self.cache={};self.records={};self.secondary={};self.secondary_conflicts=[];conflicting=set()
        self.decimals=json.loads((OUT/'contract_decimals.json').read_text());self.receipts=json.loads((OUT/'position_receipt_tokens.json').read_text())
        for r in json.loads((OUT/'secondary_quotes.json').read_text()):
            a=r['address'];ts=int(r['quote']['timestamp']);key=(a,ts);by=self.secondary.setdefault(a,{})
            if key in conflicting:continue
            if ts in by and Decimal(str(by[ts]['quote']['price']))!=Decimal(str(r['quote']['price'])):
                self.secondary_conflicts.append({'address':a,'timestamp':ts,'first':by[ts],'other':r});by.pop(ts);conflicting.add(key)
            else:by[ts]=r
        self.secondary={a:sorted(d.items()) for a,d in self.secondary.items()}
        self.stables={USDT,USDC,'0x6b175474e89094c44da98b954eedeac495271d0f'}
        self.tron_metadata={r['token_hex']:r for r in json.loads((ROOT/'data/processed/mev_tron/token_metadata_current.json').read_text())}

    def spot(self,symbol,minute,venue='Coinbase'):
        result=self.book.price(symbol,minute,stale=5,venue=venue)
        if result and self.mode=='stable1' and result[1]['quote']=='USDT':
            ev=dict(result[1]);ev.pop('USDT_USD_conversion',None);ev['USDT_USD_assumption']='1, explicit stablecoin sensitivity';bar=self.book.bars[venue,symbol,ev['bar_start']];result=(Decimal(bar['close']),ev)
        return result

    def quote(self,asset,timestamp):
        minute=int(timestamp)//60*60;key=(asset,minute)
        if key in self.cache:return self.cache[key]
        q={'asset':asset,'asof_minute':minute,'price_USD':None,'decimals':None,'reason':None,'mode':self.mode};mapped=asset
        if asset in [U]:mapped=USDT;q['chain_price_mapping']='Canonical TRON USDT uses same-issuer Ethereum USDT USD quote; cross-chain premium excluded.';q['decimals']=6
        if asset in [W,ZERO,'native:trx']:
            q['decimals']=6;result=self.spot('TRX',minute,venue='Binance')
            if result:q.update(price_USD=str(result[0]),evidence=result[1],quality='independent_spot_USDT_converted')
        else:
            meta=self.book.registry.get(mapped);onchain=self.decimals.get(mapped,{})
            if meta:q['identity_evidence']=meta.get('identity_basis');q['denomination_evidence']=onchain.get('evidence',meta.get('decimal_basis'))
            if asset=='native:eth':q['decimals']=18
            elif q['decimals'] is None:q['decimals']=onchain.get('decimals',self.tron_metadata.get(asset,{}).get('decimals'))
            if self.mode=='stable1' and mapped in self.stables:
                q.update(price_USD='1',quality='explicit_stablecoin_parity_sensitivity',evidence={'assumption':'USDT, USDC, DAI at USD1; not an observed market price'})
            elif mapped in self.receipts:q['reason']='Lending receipt/debt share: underlying principal recorded separately; no double valuation.'
            elif meta and (mapped=='native:eth' or onchain.get('decimals')==meta['decimals'] or asset==U):
                q['decimals']=q['decimals'] if asset==U else meta['decimals'];result=self.spot(meta['symbol'],minute)
                if result:q.update(price_USD=str(result[0]),evidence=result[1],quality='independent_Coinbase_contract_matched')
                else:
                    result=self.spot(meta['symbol'],minute,venue='Binance')
                    if result:q.update(price_USD=str(result[0]),evidence=result[1],quality='independent_Binance_contract_matched_USDT_converted')
            if q['price_USD'] is None and mapped not in self.receipts and mapped in self.secondary:
                values=self.secondary[mapped];idx=bisect.bisect_left([t for t,_ in values],minute)-1
                if idx>=0:
                    ts,r=values[idx]
                    if minute-ts<=600:q.update(price_USD=str(r['quote']['price']),decimals=6 if asset==U else self.decimals[mapped]['decimals'],evidence={'source':r['evidence'],'quote_timestamp':ts,'age_seconds':minute-ts,'confidence':r['quote']['confidence']},quality='exact_contract_DefiLlama_secondary_possible_pool_endogeneity')
        if q['price_USD'] is not None and 'DefiLlama' in json.dumps(q.get('evidence',{})):q['quality']='exact_contract_DefiLlama_secondary_or_USDT_conversion_possible_pool_endogeneity'
        if q['price_USD'] is None and q['reason'] is None:q['reason']='No accepted nonfuture contract-matched quote within staleness limit.'
        if q['decimals'] is None:q['price_USD']=None;q['reason']='No verified denomination.'
        self.cache[key]=q;self.records[f'{asset}@{minute}']=q;return q

    def value(self,asset,raw,timestamp):
        q=self.quote(asset,timestamp)
        return Decimal(raw)*Decimal(q['price_USD'])/Decimal(10)**q['decimals'] if q['price_USD'] is not None else None

    def vector(self,vector,timestamp):
        total=Decimal(0);missing={};secondary=False
        for a,raw in vector.items():
            if not int(raw):continue
            v=self.value(a,raw,timestamp);q=self.quote(a,timestamp)
            if v is None:missing[a]=str(raw)
            else:total+=v;secondary|=q['quality'].startswith('exact_contract_DefiLlama')
        return {'priced_component_USD':str(total),'unpriced_raw':missing,'fully_priced':not missing,'uses_secondary_pool_dependent_price':secondary}

    def dump(self):
        path=OUT/f'quote_schedule_{self.mode}.json';path.write_text(json.dumps({'policy':{'asof':'strictly before transaction minute; prior completed close','primary_max_stale_minutes':5,'secondary_max_age_seconds':600,'secondary_endogeneity':'Exact contract and decimals do not establish independent fair price. Secondary quotes are flagged. Conflicting prices at one address/timestamp are excluded.','terminal_price_asof_timestamp':END},'secondary_price_conflicts_excluded':self.secondary_conflicts,'rows':list(self.records.values())},indent=2));return path
