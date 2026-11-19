"""Fetch actual failed receipts while the full operator census is progressing."""
import json,time,requests,hashlib,base64
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from src.event_allocation.config import ROOT,OUT,setup
from src.event_allocation.tron_evidence import Pace

def run():
    setup();directory=ROOT/'data/raw/event_allocation/tron_failed_receipts';directory.mkdir(parents=True,exist_ok=True);indexpath=OUT/'tron_failed_receipt_index.json';old=json.loads(indexpath.read_text()) if indexpath.exists() else {};rows=old.get('rows',{});pace=Pace(4);knownfiles=set();known={};errors={};endpoint='https://tron-rpc.publicnode.com/walletsolidity/gettransactioninfobyid';cache={};attemptmax={}
    for path in directory.glob('*.json'):
        h=path.name[:64]
        if '-publicnode-' in path.stem:attemptmax[h]=max(attemptmax.get(h,0),int(path.stem.rsplit('-',1)[1]))
        d=json.loads(path.read_text());r=d.get('response') or {}
        if d.get('http_status')==200 and r.get('id')==h:cache[h]=(str(path.relative_to(ROOT)),int(r.get('fee',0)))
    def one(item):
        h,record=item;failures=[]
        if h in cache:
            path,fee=cache[h];expected=record['fee_raw'];assert expected is None or fee==int(expected)
            return h,{'evidence':path,'history_evidence':record['evidence'],'history_fee_matches_actual':expected is not None,'fee_raw':str(fee)},None
        first=attemptmax.get(h,0)+1
        for attempt in range(first,first+6):
            path=directory/f'{h}-publicnode-{attempt}.json'
            if path.exists():doc=json.loads(path.read_text())
            else:
                pace.wait();doc={'url':endpoint,'request':{'value':h},'acquired_at_utc':datetime.now(timezone.utc).isoformat()}
                try:
                    r=requests.post(endpoint,json=doc['request'],timeout=25);doc.update(http_status=r.status_code,response=r.json(),response_body_sha256=hashlib.sha256(r.content).hexdigest(),response_body_base64=base64.b64encode(r.content).decode())
                except Exception as ex:doc['error']=str(ex)
                path.write_text(json.dumps(doc,indent=2))
            r=doc.get('response') or {}
            if doc.get('http_status')==200 and r.get('id')==h:
                fee=int(r.get('fee',0));expected=record['fee_raw'];assert expected is None or fee==int(expected),(h,fee,expected);return h,{'evidence':str(path.relative_to(ROOT)),'history_evidence':record['evidence'],'history_fee_matches_actual':expected is not None,'fee_raw':str(fee)},None
            failures.append({'evidence':str(path.relative_to(ROOT)),'status':doc.get('http_status')})
            if doc.get('http_status') in [429,403]:pace.slow()
            time.sleep(min(2**attempt,20))
        return h,None,failures
    while True:
        for f in (OUT/'tron_operator_history').glob('*.json'):
            # Incomplete histories may be replaced by a resumed collector.
            if f in knownfiles:continue
            try:d=json.loads(f.read_text())
            except ValueError:continue
            if d['complete']:knownfiles.add(f)
            for h,r in d['rows'].items():
                if r['failed']:known[h]=r
        jobs=[(h,r) for h,r in known.items() if h not in rows and h not in errors]
        with ThreadPoolExecutor(max_workers=6) as pool:
            for i,(h,r,error) in enumerate(pool.map(one,jobs),1):
                if error:errors[h]=error
                else:rows[h]=r
                if i%100==0:print('TRON failed receipt proofs',len(rows),'known',len(known),'errors',len(errors),flush=True)
        p=OUT/'tron_operator_history_summary.json';s=json.loads(p.read_text()) if p.exists() else {};history_done=s.get('finished') is True and s.get('operators_completed')==s.get('operators_requested');expected_failed=sum(r['failed_transactions'] for r in s.get('rows',[])) if history_done else None;discovery_done=history_done and len(known)==expected_failed;doc={'history_collection_finished':history_done,'expected_failed_transactions_from_complete_history':expected_failed,'failed_transactions_discovered':len(known),'verified_receipts':len(rows),'rows':rows,'failures':errors,'all_fees_crosschecked_against_actual_receipts':all(r['history_fee_matches_actual'] for r in rows.values()),'finished':discovery_done and len(rows)==len(known) and not errors};tmp=indexpath.with_suffix('.partial');tmp.write_text(json.dumps(doc,indent=2));tmp.replace(indexpath)
        if discovery_done:print(json.dumps({k:v for k,v in doc.items() if k not in ['rows','failures']},indent=2));return
        time.sleep(20)
if __name__=='__main__':run()
