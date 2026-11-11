"""Public trace_block download; match complete transaction roots to receipts."""
import json,gzip,subprocess,time,threading
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from rawtrace_native import parse
R=Path(__file__).resolve().parent;C=R/'drpc_trace_raw';C.mkdir(exist_ok=True)
URL='https://eth.drpc.org';lock=threading.Lock();last=0
def fetch(n,candidates):
 global last
 path=C/f'{n}.json.gz'
 if path.exists():d=json.loads(gzip.decompress(path.read_bytes()))
 else:
  request=json.dumps({'jsonrpc':'2.0','id':n,'method':'trace_block','params':[hex(n)]})
  for attempt in range(4):
   with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
   z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',request,URL],capture_output=True)
   try:
    if z.returncode:raise ValueError(z.stderr.decode()[:200])
    d=json.loads(z.stdout)
    if not isinstance(d.get('result'),list):raise ValueError(str(d)[:250])
    break
   except Exception as e:
    if attempt==3:raise
    with lock:last=max(last,time.monotonic()+(20 if '429' in str(e) else 2*(attempt+1)))
  path.write_bytes(gzip.compress(z.stdout))
 traces=d['result'];folder='window_raw' if n<=26301940 else 'extension_raw'
 receipts={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))};groups=defaultdict(list)
 for t in traces:
  if not t.get('transactionHash'):continue
  h=t['transactionHash']
  if h not in receipts or t['blockNumber']!=n or t['blockHash']!=receipts[h]['blockHash']:raise ValueError('trace block/hash/transaction mismatch')
  if t['transactionPosition']!=int(receipts[h]['transactionIndex'],16):raise ValueError('trace transaction index mismatch')
  groups[h].append(t)
 if set(groups)!=set(receipts):raise ValueError('incomplete block transaction coverage')
 if any(sum(t['traceAddress']==[] for t in ts)!=1 for ts in groups.values()):raise ValueError('missing/duplicate transaction roots')
 out=[]
 for c in candidates:
  h=c['hash'];r=parse(h,groups[h]);rec=receipts[h]
  if r['root_from'].lower()!=rec['from'] or (r['root_to'] or '').lower()!=(rec['to'] or ''):raise ValueError('root identity mismatch')
  if bool(r['root_error'])!=(int(rec['status'],16)==0):raise ValueError('root status mismatch')
  r.update(source=URL,rpc_method='trace_block',block=n,block_hash=rec['blockHash'],raw_file=str(path.relative_to(R)))
  out.append(r)
 return out,{'block':n,'block_hash':next(iter(receipts.values()))['blockHash'],'receipt_count':len(receipts),'trace_count':len(traces),'candidate_count':len(out)}
def main():
 blocks=defaultdict(list)
 for c in json.loads((R/'full_candidates.json').read_text())['rows']:blocks[c['block']].append(c)
 rows=[];coverage=[];errors=[];dest=R/'drpc_candidate_native.json'
 def save():
  tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps({'source':URL,'method':'trace_block; complete root transaction coverage checked against independently cached receipts; candidate call trees checked for complete parent/child structure','rows':rows,'coverage':coverage,'errors':errors,'requested_blocks':len(blocks)},indent=2));tmp.replace(dest)
 with ThreadPoolExecutor(max_workers=6) as ex:
  fs={ex.submit(fetch,n,cs):n for n,cs in sorted(blocks.items())}
  for i,f in enumerate(as_completed(fs),1):
   try:
    rs,c=f.result();rows.extend(rs);coverage.append(c)
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%25==0:save();print('blocks',i,len(blocks),'candidate traces',len(rows),'errors',len(errors),flush=True)
 save();print('DONE',len(coverage),len(rows),len(errors),flush=True)
if __name__=='__main__':main()
