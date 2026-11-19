"""Follow the other named TRON traders, preserving API pagination and receipt failures."""
import json,time,threading,requests,hashlib,datetime,base64
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_collect import decode_addr
BOTS=['TVFxAQUx3xrrGrwEwCVFMNkPd2z5zTwAoc','TDR4JCtV4TEWAueKhAKkS3bZ8PPvPmGsui','TActorJXZ3oqWCRH9f5LfpLAtsStWuXdK4']
LOCK=threading.Lock();NEXT=[0.0]

def fetch(url,body=None):
    key=hashlib.sha256((url+json.dumps(body,sort_keys=True)).encode()).hexdigest();p=ROOT/'data/raw/tron_expansion'/(key+'.json')
    if p.exists():return json.loads(p.read_text()),str(p.relative_to(ROOT))
    with LOCK:
        time.sleep(max(0,NEXT[0]-time.monotonic()));NEXT[0]=time.monotonic()+1.15
    doc={'url':url,'request':body,'acquired_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r=requests.get(url,timeout=30) if body is None else requests.post(url,json=body,timeout=30)
        doc.update(http_status=r.status_code,response_body_base64=base64.b64encode(r.content).decode(),response_body_sha256=hashlib.sha256(r.content).hexdigest());doc['response']=r.json()
    except Exception as ex:doc['error']=str(ex)
    p.write_text(json.dumps(doc,indent=2));return doc,str(p.relative_to(ROOT))

def one(bot):
    dest=ROOT/'data/processed/mev_tron'/bot;dest.mkdir(exist_ok=True);url=f'https://api.trongrid.io/v1/accounts/{bot}/transactions?only_confirmed=true&only_from=true&limit=200&min_timestamp=1793305800000&max_timestamp=1793343600000';seen=set();transactions={};pages=[];failures=[];complete=False
    while url:
        assert urlparse(url).netloc=='api.trongrid.io' and url not in seen;seen.add(url);doc,path=fetch(url);data=doc.get('response',{})
        if doc.get('http_status')!=200 or data.get('success') is not True:failures.append({'kind':'history','evidence':path,'error':data or doc.get('error')});break
        pages.append(path)
        for t in data['data']:transactions[t['txID']]={'transaction':t,'transaction_evidence':path}
        url=data.get('meta',{}).get('links',{}).get('next')
        if not url:complete=True
    (dest/'history.json').write_text(json.dumps({'bot':bot,'pages':pages,'no_next_page_returned':complete,'rows':list(transactions.values())},indent=2));print(bot,'history',len(transactions),'pages',len(pages),'complete',complete,flush=True)
    rows=[];bh=decode_addr(bot)
    for i,(h,tx) in enumerate(sorted(transactions.items()),1):
        t=tx['transaction'];owned=[c for c in t['raw_data']['contract'] if c['parameter']['value'].get('owner_address')==bh]
        if not owned:continue
        doc,path=fetch('https://api.trongrid.io/walletsolidity/gettransactioninfobyid',{'value':h});info=doc.get('response',{})
        if doc.get('http_status')!=200 or info.get('id')!=h:failures.append({'kind':'receipt','tx_hash':h,'evidence':path,'error':info or doc.get('error')});continue
        rows.append({'tx_hash':h,'bot':bot,'bot_hex':bh,'transaction':t,'receipt':info,'receipt_evidence':path,'transaction_evidence':tx['transaction_evidence']})
        if i%50==0:print(bot,'receipts',i,'/',len(transactions),'failures',len(failures),flush=True)
    (dest/'receipts.json').write_text(json.dumps(rows,indent=2));summary={'bot':bot,'history_transactions':len(transactions),'history_no_next_page_returned':complete,'history_pages':len(pages),'receipt_rows':len(rows),'failures':failures,'coverage_note':'Confirmed indexed outgoing address history; not cryptographic full-chain completeness or all related actors.'};(dest/'collection_summary.json').write_text(json.dumps(summary,indent=2));print(bot,'DONE',len(rows),'failures',len(failures),flush=True);return summary

def run():
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,BOTS))
    (ROOT/'data/processed/mev_tron/other_named_collection_summary.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':run()
