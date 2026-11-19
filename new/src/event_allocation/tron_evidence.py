"""Complete public-node receipts and root-call metadata for the TRON pool census.
Every failed attempt is retained; cached evidence is reused without changing bytes.
"""
import json,time,hashlib,base64,threading
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
from src.event_allocation.config import ROOT,OUT,setup
from src.ingestion.evidence import read_json
from src.arbitrage.tron_more import fetch

class Pace:
    def __init__(self,rate=4):self.lock=threading.Lock();self.next=0;self.interval=1/rate
    def wait(self):
        with self.lock:
            delay=max(0,self.next-time.monotonic());self.next=max(self.next,time.monotonic())+self.interval
        if delay:time.sleep(delay)
    def slow(self):
        with self.lock:self.interval=max(self.interval,1.2)

def census_ids():
    ids=set()
    for f in OUT.glob('tron_events_*.json'):
        for r in json.loads(f.read_text())['rows']:ids.add(r['event']['transaction_id'])
    return sorted(ids)

def receipts():
    setup();ids=census_ids();needed=set(ids);cache={}
    account=json.loads((ROOT/'data/processed/mev_tron/all_named_bot_accounting.json').read_text())['rows']+json.loads((ROOT/'data/processed/mev_tron/target_owner_accounting.json').read_text())
    for r in account:
        if r['tx_hash'] in needed:cache[r['tx_hash']]=r['evidence']['receipt']
    rawdir=ROOT/'data/raw/event_allocation/tron_receipts';rawdir.mkdir(parents=True,exist_ok=True)
    for path in rawdir.glob('*.json'):
        d=json.loads(path.read_text());r=d.get('response',{})
        if d.get('http_status')==200 and r.get('id') in needed:cache[r['id']]=str(path.relative_to(ROOT))
    pace=Pace(4);failures=[];index={}
    def one(h):
        if h in cache:
            d=read_json(ROOT/cache[h]);r=d.get('response',d)
            if r.get('id')==h:return h,cache[h],None
        url='https://tron-rpc.publicnode.com/walletsolidity/gettransactioninfobyid';errors=[]
        for attempt in range(1,6):
            path=rawdir/f'{h}-publicnode-attempt{attempt}.json'
            if path.exists():doc=json.loads(path.read_text())
            else:
                pace.wait();doc={'url':url,'request':{'value':h},'acquired_at_utc':datetime.now(timezone.utc).isoformat()}
                try:
                    response=requests.post(url,json=doc['request'],timeout=25);doc.update(http_status=response.status_code,response_body_base64=base64.b64encode(response.content).decode(),response_body_sha256=hashlib.sha256(response.content).hexdigest(),response=response.json())
                except Exception as ex:doc['error']=str(ex)
                temporary=path.with_suffix('.partial');temporary.write_text(json.dumps(doc,indent=2));temporary.replace(path)
            r=doc.get('response') or {}
            if doc.get('http_status')==200 and r.get('id')==h:return h,str(path.relative_to(ROOT)),None
            errors.append({'evidence':str(path.relative_to(ROOT)),'http_status':doc.get('http_status'),'error':r or doc.get('error')})
            if doc.get('http_status') in [403,429] and doc.get('url')==url:pace.slow()
            time.sleep(min(2**attempt,20))
        return h,None,errors
    print('TRON complete receipts',len(ids),'cached',len(cache),'new',len(ids)-len(cache),flush=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i,(h,path,error) in enumerate(pool.map(one,ids),1):
            if path:index[h]=path
            else:failures.append({'tx_hash':h,'attempts':error})
            if i%100==0 or i==len(ids):
                (OUT/'tron_receipt_index.json').write_text(json.dumps({'requested':len(ids),'completed':len(index),'rows':index,'failures':failures,'finished':i==len(ids)},indent=2));print('TRON receipts',i,'/',len(ids),'verified IDs',len(index),'failures',len(failures),flush=True)

def transactions():
    setup();ids=census_ids();rows={};failures=[];dest=OUT/'tron_root_transactions.json';old=json.loads(dest.read_text()) if dest.exists() else {};rows.update(old.get('rows',{}));todo=[h for h in ids if h not in rows]
    for start in range(0,len(todo),35):
        hs=todo[start:start+35];req=[{'jsonrpc':'2.0','id':'event-scope:'+h,'method':'eth_getTransactionByHash','params':['0x'+h]} for h in hs];doc,path=fetch('https://api.trongrid.io/jsonrpc',req);res=doc.get('response');by={r.get('id'):r for r in res} if isinstance(res,list) else {}
        for i,h in enumerate(hs):
            r=by.get('event-scope:'+h,{}).get('result')
            if r and r.get('hash','').removeprefix('0x')==h:rows[h]={'transaction':r,'evidence':path,'batch_id':'event-scope:'+h}
            else:failures.append({'tx_hash':h,'evidence':path,'response':by.get('event-scope:'+h,res)})
        dest.write_text(json.dumps({'requested':len(ids),'completed':len(rows),'rows':rows,'failures':failures,'all_requested_complete':len(rows)==len(ids),'meaning':'RPC root-call metadata keyed by canonical TRON txID. Energy gasPrice is not used to infer paid fees; actual fee comes from native TRON receipts.'},indent=2))
        if start%350==0:print('TRON root metadata',len(rows),'/',len(ids),'failures',len(failures),flush=True)
    print('TRON root metadata done',len(rows),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['receipts','transactions']);a=p.parse_args();receipts() if a.kind=='receipts' else transactions()
