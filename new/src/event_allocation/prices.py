"""One frozen quote schedule, contract identities and provenance for the full frame.
Quotes are shared by all entries of the same transaction, including negative entries.
"""
import json,time,gzip,base64,hashlib
import requests
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from urllib.parse import urlencode
from decimal import Decimal
from eth_abi import encode,decode
from src.event_allocation.config import ROOT,OUT,START,END,setup
from src.event_allocation.ethereum_journal import AAVE
from src.event_allocation.tron_evidence import Pace
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.enrich import PacedEvidence
from src.ingestion.public_evidence import PublicEvidence
from src.reconciliation.inventory import MULTICALL,selector
from src.decoding.events import USDT,USDC,WETH

def load_book():
    from src.arbitrage.full_valuations import FullWindowBook
    b=book_from_archive();b.__class__=FullWindowBook;b.engine=Reconstruction(ROOT.parent/'research',False);b.binance_spot('USDC',('2026-10-29','2026-10-30'));b.binance_spot('TRX',('2026-10-29','2026-10-30'));b.loaded.add('TRX');return b

def fetch_primary():
    setup();b=load_book();assets=json.loads((OUT/'ethereum_journal_summary.json').read_text())['asset_frequency'];symbols=sorted({b.registry[a]['symbol'] for a in assets if a in b.registry});api=PublicEvidence(ROOT,True);pace=Pace(4);jobs=[]
    for symbol in symbols:
        missing=[ts for ts in range(START-60,END,60) if ('Coinbase',symbol,ts) not in b.bars]
        buckets=defaultdict(list)
        for ts in missing:buckets[ts//14400].append(ts)
        for times in buckets.values():
            begin=min(times);end=max(times)+60;fmt=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ');url='https://api.exchange.coinbase.com/products/'+symbol+'-USD/candles?'+urlencode({'granularity':60,'start':fmt(begin),'end':fmt(end)});jobs.append((symbol,url))
    dest=OUT/'primary_price_sources.json';old=json.loads(dest.read_text()) if dest.exists() else [];results={r['url']:r for r in old}
    def one(job):
        symbol,url=job;cache=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if not cache.exists():pace.wait()
        doc,path=api.get(url);raw=doc.get('response');ok=doc.get('http_status')==200 and isinstance(raw,list) and all(isinstance(r,list) and len(r)==6 for r in raw)
        if doc.get('http_status')==429:pace.slow()
        return {'symbol':symbol,'url':url,'evidence':path,'usable':ok,'candles':len(raw) if ok else 0,'http_status':doc.get('http_status')}
    print('Full-frame Coinbase quote queries',len(jobs),'verified currency IDs',len(symbols),flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(one,jobs),1):
            results[r['url']]=r
            if i%25==0 or i==len(jobs):dest.write_text(json.dumps(list(results.values()),indent=2));print('Primary quote pages',i,'/',len(jobs),flush=True)
    dest.write_text(json.dumps(list(results.values()),indent=2))

def expanded_book():
    b=load_book();path=OUT/'primary_price_sources.json'
    if path.exists():
        for r in json.loads(path.read_text()):
            if not r['usable']:continue
            doc=json.loads((ROOT/r['evidence']).read_text())
            for c in doc['response']:b.add_bar(r['symbol'],c[0],c[4],c[1],c[2],r['evidence'])
    bp=OUT/'binance_price_sources.json'
    if bp.exists():
        for symbol in sorted({r['symbol'] for r in json.loads(bp.read_text()) if r['usable']}):b.binance_spot(symbol,('2026-10-29','2026-10-30'))
    ip=OUT/'supplemental_market_identities.json'
    if ip.exists():
        for a,m in json.loads(ip.read_text()).items():
            assert m['http_status']==200 and m['identity_contract_present_in_source'];b.registry[a]=m;b.binance_spot(m['symbol'],('2026-10-29','2026-10-30'))
    return b

def fetch_binance():
    b=expanded_book();symbols=sorted({m['symbol'] for m in b.registry.values() if not all(any(('Coinbase',m['symbol'],ts-off*60) in b.bars for off in range(6)) for ts in range(START-60,END,60))});api=PublicEvidence(ROOT,True);pace=Pace(3);jobs=[(s,day) for s in symbols for day in ['2026-10-29','2026-10-30']];rows=[]
    def one(job):
        symbol,day=job;url=f'https://data.binance.vision/data/spot/daily/klines/{symbol}USDT/1m/{symbol}USDT-1m-{day}.zip';path=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if not path.exists():pace.wait()
        doc,source=api.get(url)
        return {'symbol':symbol,'day':day,'usable':doc.get('http_status')==200,'evidence':source,'http_status':doc.get('http_status')}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(one,jobs),1):
            rows.append(r)
            if i%50==0 or i==len(jobs):(OUT/'binance_price_sources.json').write_text(json.dumps(rows,indent=2));print('Verified-contract Binance quote files',i,'/',len(jobs),flush=True)

def fetch_supplemental():
    a='0x6c5ba91642f10282b576d91922ae6448c9d52f4e';url='https://docs.phala.com/network/overview/get-pha-and-transfer';doc,path=PublicEvidence(ROOT,True).get(url);body=base64.b64decode(doc['response_body_base64']).decode().lower();assert doc['http_status']==200 and a in body and 'binance.com' in body;dec=json.loads((OUT/'contract_decimals.json').read_text())[a];assert dec['decimals']==18
    identity={a:{'symbol':'PHA','decimals':18,'official_identity_URL':url,'identity_basis':path,'decimal_basis':dec,'identity_contract_present_in_source':True,'http_status':200}};(OUT/'supplemental_market_identities.json').write_text(json.dumps(identity,indent=2));b=load_book();b.engine=Reconstruction(ROOT.parent/'research',True);b.binance_spot('PHA',('2026-10-29','2026-10-30'))

def fetch_hyperliquid():
    request={'type':'candleSnapshot','req':{'coin':'TRX','interval':'15m','startTime':(START-900)*1000,'endTime':END*1000}};key=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest();path=ROOT/'data/raw/public_http'/('hyperliquid-'+key+'.json')
    if path.exists():doc=json.loads(path.read_text())
    else:
        response=requests.post('https://api.hyperliquid.xyz/info',json=request,timeout=25);doc={'endpoint':'https://api.hyperliquid.xyz/info','request':request,'http_status':response.status_code,'acquired_at_utc':datetime.now(timezone.utc).isoformat(),'response':response.json(),'response_body_base64':base64.b64encode(response.content).decode(),'response_body_sha256':hashlib.sha256(response.content).hexdigest()};path.write_text(json.dumps(doc,indent=2))
    assert doc['http_status']==200 and isinstance(doc['response'],list) and doc['response'];(OUT/'hyperliquid_TRX_15m_source.json').write_text(json.dumps({'evidence':str(path.relative_to(ROOT)),'available_bars':len(doc['response']),'not_exact_same_minute_replication':True},indent=2))

def fetch_secondary():
    setup();b=expanded_book();frequency=json.loads((OUT/'ethereum_journal_summary.json').read_text())['asset_frequency'];addresses=sorted(a for a in frequency if a.startswith('0x') and len(a)==42);api=PacedEvidence(ROOT,True);metadata={};state_block=max(r['block'] for r in json.loads((ROOT/'data/processed/mev_full_window/blocks.json').read_text()) if r['timestamp']<END)
    for start in range(0,len(addresses),120):
        aa=addresses[start:start+120];inp='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(a,True,selector('decimals()')) for a in aa]])).hex();raw,path=api.rpc('eth_call',[{'to':MULTICALL,'data':inp},hex(state_block)]);ret=decode(['(bool,bytes)[]'],bytes.fromhex(raw[2:]))[0]
        for i,(a,(ok,v)) in enumerate(zip(aa,ret)):metadata[a]={'decimals':int.from_bytes(v,'big') if ok and len(v)==32 and int.from_bytes(v,'big')<=255 else None,'evidence':path,'batch_index':i,'block':state_block}
    (OUT/'contract_decimals.json').write_text(json.dumps(metadata,indent=2));http=PublicEvidence(ROOT,True);pace=Pace(3);needed=[]
    reserve_candidates=set()
    with gzip.open(OUT/'ethereum_journal.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line)
            for e in row['position_events']:
                if e.get('emitter') in AAVE:
                    for field in ['asset','collateral_asset','debt_asset']:
                        if e.get(field):reserve_candidates.add((e['emitter'],e[field]))
    # Ask the authenticated lending pool for its registered reserve tokens.
    # Probing arbitrary token fallback functions can consume the full RPC gas cap.
    receipt_tokens={};rc=sorted(reserve_candidates)
    for start in range(0,len(rc),50):
        aa=rc[start:start+50];inp='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(pool,True,selector('getReserveData(address)')+encode(['address'],[asset])) for pool,asset in aa]])).hex();raw,path=api.rpc('eth_call',[{'to':MULTICALL,'data':inp},hex(state_block)]);ret=decode(['(bool,bytes)[]'],bytes.fromhex(raw[2:]))[0]
        for i,((pool,asset),(ok,v)) in enumerate(zip(aa,ret)):
            if not ok or len(v)<352:continue
            words=[v[n:n+32] for n in range(0,len(v),32)]
            for field,name in [(8,'aToken'),(9,'stableDebtToken'),(10,'variableDebtToken')]:
                token='0x'+words[field][-20:].hex()
                if int(token,16):receipt_tokens[token]={'underlying':asset,'pool':pool,'kind':name,'evidence':path,'batch_index':i,'return_word_index':field,'ABI_source':'https://github.com/aave-dao/aave-v3-origin/blob/main/src/contracts/protocol/libraries/types/DataTypes.sol'}
    (OUT/'position_receipt_tokens.json').write_text(json.dumps(receipt_tokens,indent=2))
    # Only addresses with a genuine primary-price gap require secondary discovery.
    for a in addresses:
        meta=b.registry.get(a);complete=meta and all(any(('Coinbase',meta['symbol'],ts-off*60) in b.bars for off in range(6)) for ts in range(START-60,END,60))
        if not complete and metadata[a]['decimals'] is not None and a not in receipt_tokens:needed.append(a)
    probe=[];anchor=START-60
    for start in range(0,len(needed),65):
        aa=needed[start:start+65];url=f'https://coins.llama.fi/prices/historical/{anchor}/'+','.join('ethereum:'+a for a in aa)+'?searchWidth=5m';pace.wait();d,path=http.get(url);coins=(d.get('response') or {}).get('coins',{});probe.append({'evidence':path,'addresses':aa,'quotes':coins});print('Secondary supported-contract discovery',min(start+65,len(needed)),'/',len(needed),flush=True)
    supported=set()
    for r in probe:
        for key,q in r['quotes'].items():
            a=key.removeprefix('ethereum:')
            if a in metadata and q.get('decimals')==metadata[a]['decimals'] and Decimal(str(q.get('confidence',0)))>=Decimal('.9') and Decimal(str(q.get('price',0)))>0:supported.add(a)
    (OUT/'secondary_discovery.json').write_text(json.dumps({'rows':probe,'supported_addresses':sorted(supported),'unsupported_addresses':sorted(set(needed)-supported)},indent=2))
    # Five-minute sampling; quotes never cross the as-of cutoff. Values carry an
    # explicit age and are absent after the maximum age, rather than interpolated.
    jobs=[];aa=sorted(supported)
    for ts in range(START-300,END,300):
        for start in range(0,len(aa),65):
            chunk=aa[start:start+65];url=f'https://coins.llama.fi/prices/historical/{ts}/'+','.join('ethereum:'+a for a in chunk)+'?searchWidth=5m';jobs.append((ts,chunk,url))
    rows=[]
    def one(job):
        ts,aa,url=job;cache=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if not cache.exists():pace.wait()
        d,path=http.get(url);data=(d.get('response') or {}).get('coins',{});result=[]
        for a in aa:
            q=data.get('ethereum:'+a)
            if q and q.get('decimals')==metadata[a]['decimals'] and Decimal(str(q.get('confidence',0)))>=Decimal('.9') and Decimal(str(q.get('price',0)))>0 and ts-600<=q.get('timestamp',0)<=ts+300:result.append({'address':a,'query_timestamp':ts,'quote':q,'evidence':path})
        return result
    print('Secondary temporal quote queries',len(jobs),'supported assets',len(supported),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i,res in enumerate(pool.map(one,jobs),1):
            rows.extend(res)
            if i%50==0 or i==len(jobs):(OUT/'secondary_quotes.json').write_text(json.dumps(rows,indent=2));print('Secondary temporal pages',i,'/',len(jobs),flush=True)
    (OUT/'secondary_quotes.json').write_text(json.dumps(rows,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['primary','secondary','binance']);a=p.parse_args();{'primary':fetch_primary,'secondary':fetch_secondary,'binance':fetch_binance}[a.kind]()
