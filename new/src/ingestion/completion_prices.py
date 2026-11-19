"""Fetch exact-contract historical secondary quotes for genuinely missing marks.
Primary CEX marks stay unchanged. Reported future timestamps/low confidence are rejected.
"""
import json,time,hashlib
from collections import defaultdict
from decimal import Decimal
from eth_abi import encode,decode
from src.arbitrage.discover import ROOT
from src.arbitrage.enrich import PacedEvidence
from src.ingestion.public_evidence import PublicEvidence
from src.reconciliation.inventory import MULTICALL,selector
from src.decoding.events import USDT

def run():
    p=ROOT/'data/processed/mev_full_window';needed=defaultdict(set);blocks={r['block']:r['timestamp'] for r in json.loads((p/'blocks.json').read_text())}
    for r in json.loads((p/'terminal_cycle_profits.json').read_text()):
        for a in r['missing_price_assets']:needed[r['reference_exit_timestamp']//60*60-60].add(a)
    for r in json.loads((p/'order_counterparty_redistribution.json').read_text())['rows']:
        for a in r['missing_price_assets']:needed[blocks[r['block']]//60*60-60].add(a)
    targets=json.loads((ROOT/'data/processed/mev_tron/target_owner_accounting.json').read_text())
    for r in targets:
        if r['swap_events'] and Decimal(r['USDT_net'])<0 and r['reference_shortfall_excluding_gas_USD'] is None:needed[r['timestamp']//60*60-60].add(USDT)
    tokens=sorted({a for aa in needed.values() for a in aa});api=PacedEvidence(ROOT,True);calls=[(a,True,selector('decimals()')) for a in tokens];inp='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[calls])).hex();raw,src=api.rpc('eth_call',[{'to':MULTICALL,'data':inp},hex(26303950)]);ret=decode(['(bool,bytes)[]'],bytes.fromhex(raw[2:]))[0];meta={}
    for i,(a,(ok,data)) in enumerate(zip(tokens,ret)):
        meta[a]={'decimals':int.from_bytes(data,'big') if ok and len(data)==32 else None,'evidence':src,'batch_index':i,'block':26303950}
    rows=[];http=PublicEvidence(ROOT,True)
    for i,(ts,aa) in enumerate(sorted(needed.items()),1):
        coins=','.join('ethereum:'+a for a in sorted(aa));url=f'https://coins.llama.fi/prices/historical/{ts}/{coins}?searchWidth=5m';cached=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json');time.sleep(0 if cached.exists() else 1.1);doc,path=http.get(url);data=doc.get('response',{}).get('coins',{}) if isinstance(doc.get('response'),dict) else {}
        for a in sorted(aa):
            quote=data.get('ethereum:'+a);r={'address':a,'requested_timestamp':ts,'evidence':path,'token_metadata':meta[a],'accepted':False,'provider':'DefiLlama historical exact-contract price; secondary, not the primary Coinbase convention'}
            if quote:
                r['quote']=quote;valid='timestamp' in quote and 0<quote['timestamp']<ts+60 and ts-quote['timestamp']<=300 and Decimal(str(quote.get('price',0)))>0 and Decimal(str(quote.get('confidence',1)))>=Decimal('.9') and quote.get('decimals')==meta[a]['decimals'];r['accepted']=bool(valid)
                if not valid:r['reason']='Quote freshness/confidence/positive-price/onchain-decimal check did not pass'
            else:r['reason']='Exact contract not returned by historical provider'
            rows.append(r)
        if i%10==0:print('secondary quote groups',i,'/',len(needed),flush=True)
    for r in rows:
        if r['accepted'] or not r.get('quote') or r['quote'].get('timestamp',0)<r['requested_timestamp']+60:continue
        a=r['address'];ts=r['requested_timestamp'];u=f'https://coins.llama.fi/prices/historical/{ts-300}/ethereum:{a}?searchWidth=5m';cached=ROOT/'data/raw/public_http'/(hashlib.sha256(u.encode()).hexdigest()+'.json');time.sleep(0 if cached.exists() else 1.1);d,source=http.get(u);q=(d.get('response') or {}).get('coins',{}).get('ethereum:'+a)
        if q and 'timestamp' in q and ts-600<=q['timestamp']<ts+60 and Decimal(str(q.get('price',0)))>0 and Decimal(str(q.get('confidence',0)))>=Decimal('.9') and q.get('decimals')==r['token_metadata']['decimals']:
            r['rejected_future_quote']=r['quote'];r['rejected_future_evidence']=r['evidence'];r.update(quote=q,evidence=source,accepted=True,retry_query_timestamp=ts-300);r.pop('reason',None)
    dest=ROOT/'data/processed/completion_secondary_prices.json'
    previous=json.loads(dest.read_text())['rows'] if dest.exists() else []
    merged={(r['address'],r['requested_timestamp']):r for r in previous}
    for r in rows:
        key=(r['address'],r['requested_timestamp'])
        if r['accepted'] or key not in merged or not merged[key]['accepted']:merged[key]=r
    rows=list(merged.values())
    dest.write_text(json.dumps({'rows':rows,'primary_prices_unchanged':True,'no_constant_stablecoin_peg_assumed':True},indent=2));print('secondary rows',len(rows),'accepted',sum(r['accepted'] for r in rows),'missing',[(r['address'],r['reason']) for r in rows if not r['accepted']])
if __name__=='__main__':run()
