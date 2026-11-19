"""Outgoing operator history, including paid failed attempts absent from Swap logs."""
import json,time,hashlib,base64,requests
from datetime import datetime,timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from src.event_allocation.config import ROOT,OUT,START,END,setup
from src.event_allocation.tron_evidence import Pace
from src.arbitrage.tron_collect import encode_addr,decode_addr
from src.ingestion.public_evidence import PublicEvidence

def run():
    setup();metadata=json.loads((OUT/'tron_root_transactions.json').read_text());assert metadata['all_requested_complete'];owners=sorted({encode_addr(r['transaction']['from'][2:]) for r in metadata['rows'].values()});pairs={(encode_addr(r['transaction']['from'][2:]),encode_addr(r['transaction']['to'][2:])) for r in metadata['rows'].values()};api=PublicEvidence(ROOT,True);pace=Pace(.8);directory=OUT/'tron_operator_history';directory.mkdir(exist_ok=True);attempts=ROOT/'data/raw/event_allocation/tron_history';attempts.mkdir(parents=True,exist_ok=True)
    def page(url):
        cache=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if cache.exists():
            d=json.loads(cache.read_text())
            if d.get('http_status')==200 and (d.get('response') or {}).get('success'):return d,str(cache.relative_to(ROOT))
        key=hashlib.sha256(url.encode()).hexdigest();previous=list(attempts.glob(key+'-*.json'))
        for path in previous:
            d=json.loads(path.read_text())
            if d.get('http_status')==200 and (d.get('response') or {}).get('success'):return d,str(path.relative_to(ROOT))
        first=max([int(p.stem.rsplit('-',1)[1]) for p in previous],default=0)+1
        for attempt in range(first,first+6):
            path=attempts/(key+f'-{attempt}.json')
            if path.exists():d=json.loads(path.read_text())
            else:
                pace.wait();d={'url':url,'acquired_at_utc':datetime.now(timezone.utc).isoformat()}
                try:
                    response=requests.get(url,timeout=25);d.update(http_status=response.status_code,response_body_base64=base64.b64encode(response.content).decode(),response_body_sha256=hashlib.sha256(response.content).hexdigest(),response=response.json())
                except Exception as ex:d['error']=str(ex)
                path.write_text(json.dumps(d,indent=2))
            if d.get('http_status')==200 and (d.get('response') or {}).get('success'):return d,str(path.relative_to(ROOT))
            if d.get('http_status')==429:time.sleep(6)
        return d,str(path.relative_to(ROOT))
    def one(owner):
        dest=directory/(owner+'.json')
        if dest.exists():
            old=json.loads(dest.read_text())
            if old['complete']:return old
        url=f'https://api.trongrid.io/v1/accounts/{owner}/transactions?only_confirmed=true&only_from=true&limit=200&min_timestamp={START*1000}&max_timestamp={END*1000-1}&order_by=block_timestamp,asc';seen=set();pages=[];rows={};error=None
        while url:
            assert urlparse(url).netloc=='api.trongrid.io' and url not in seen;seen.add(url);cache=ROOT/'data/raw/public_http'/(hashlib.sha256(url.encode()).hexdigest()+'.json')
            d,path=page(url);j=d.get('response') or {}
            if d.get('http_status')!=200 or j.get('success') is not True:error={'evidence':path,'http_status':d.get('http_status'),'response':j};break
            pages.append(path)
            for t in j.get('data',[]):
                assert t['txID'] not in rows;contracts=t['raw_data']['contract'];owner_hex=decode_addr(owner);assert any(c['parameter']['value'].get('owner_address')==owner_hex for c in contracts);ret=t.get('ret',[]);fee_known=bool(ret) and all('fee' in r for r in ret);entry=next((encode_addr(c['parameter']['value']['contract_address']) for c in contracts if c['type']=='TriggerSmartContract'),None);rows[t['txID']]={'transaction':t,'evidence':path,'failed':any(r.get('contractRet')!='SUCCESS' for r in ret),'fee_raw':str(sum(int(r['fee']) for r in ret)) if fee_known else None,'same_operator_entrypoint_as_pool_trade':(owner,entry) in pairs}
            if len(pages)%5==0:
                tmp=dest.with_suffix('.partial');tmp.write_text(json.dumps({'owner':owner,'complete':False,'pages':pages,'transactions':len(rows),'failed_transactions':sum(r['failed'] for r in rows.values()),'error':None,'rows':rows}));tmp.replace(dest)
            if len(pages)%20==0:print('TRON history paginating',owner,'pages',len(pages),'transactions',len(rows),flush=True)
            url=j.get('meta',{}).get('links',{}).get('next')
        record={'owner':owner,'complete':url is None and error is None,'pages':pages,'transactions':len(rows),'failed_transactions':sum(r['failed'] for r in rows.values()),'error':error,'rows':rows};dest.write_text(json.dumps(record,indent=2));return record
    summaries=[]
    print('TRON outgoing-history operators',len(owners),flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for i,r in enumerate(pool.map(one,owners),1):
            summaries.append({k:v for k,v in r.items() if k!='rows'})
            if i%25==0 or i==len(owners):(OUT/'tron_operator_history_summary.json').write_text(json.dumps({'operators_requested':len(owners),'operators_completed':sum(r['complete'] for r in summaries),'rows':summaries,'finished':i==len(owners)},indent=2));print('TRON operator histories',i,'/',len(owners),'complete',sum(r['complete'] for r in summaries),flush=True)
if __name__=='__main__':run()
