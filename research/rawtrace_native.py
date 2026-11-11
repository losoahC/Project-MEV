"""Public explorer raw traces, with reverted ancestors and root value handled."""
import argparse,json,gzip,subprocess,time,threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
R=Path(__file__).resolve().parent;C=R/'rawtrace_raw';C.mkdir(exist_ok=True)
lock=threading.Lock();last=0
def parse(h,d):
 if not isinstance(d,list) or not d or sum(r.get('traceAddress')==[] for r in d)!=1:raise ValueError('missing or ambiguous root')
 paths=[tuple(r['traceAddress']) for r in d]
 if len(paths)!=len(set(paths)):raise ValueError('duplicate trace path')
 pathset=set(paths);children=defaultdict(int)
 for path in paths:
  if path:
   if path[:-1] not in pathset:raise ValueError('missing parent trace')
   children[path[:-1]]+=1
 if any(children[tuple(r['traceAddress'])]!=r['subtraces'] for r in d):raise ValueError('incomplete child traces')
 bad={tuple(r['traceAddress']) for r in d if r.get('error')};net=defaultdict(int)
 for r in d:
  path=tuple(r['traceAddress'])
  if any(path[:i] in bad for i in range(len(path)+1)):continue
  a=r['action'];typ=r['type']
  if typ=='call':
   if a.get('callType')!='call':continue
   source=a['from'];dest=a['to'];v=int(a['value'],16)
  elif typ=='create':source=a['from'];dest=r.get('result',{}).get('address');v=int(a['value'],16)
  elif typ in ('suicide','selfdestruct'):source=a['address'];dest=a['refundAddress'];v=int(a['balance'],16)
  else:continue
  if not v:continue
  if not dest:raise ValueError('missing recipient')
  net[source.lower()]-=v;net[dest.lower()]+=v
 root=next(r for r in d if r['traceAddress']==[])
 return {'hash':h,'source':'https://eth.blockscout.com/api/v2/transactions/'+h+'/raw-trace','includes_top_level_value':True,'native_net_wei':{a:str(v) for a,v in net.items() if v},'trace_count':len(d),'reverted_paths':len(bad),'root_from':root['action'].get('from'),'root_to':root['action'].get('to'),'root_value':root['action'].get('value'),'root_error':root.get('error')}
def fetch(h):
 global last
 p=C/(h+'.json.gz')
 if p.exists():return parse(h,json.loads(gzip.decompress(p.read_bytes())))
 for attempt in range(3):
  with lock:
   time.sleep(max(0,.4-(time.monotonic()-last)));last=time.monotonic()
  z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35','https://eth.blockscout.com/api/v2/transactions/'+h+'/raw-trace'],capture_output=True)
  if not z.returncode:break
  if attempt==2:raise ValueError(z.stderr.decode()[:160])
  with lock:last=max(last,time.monotonic()+(40 if b'429' in z.stderr else 5))
 d=json.loads(z.stdout);r=parse(h,d);p.write_bytes(gzip.compress(z.stdout));return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--scope',choices=['extension','candidates','missing'],default='extension');a=p.parse_args()
 if a.scope=='extension':hashes={r['hash'] for r in json.loads((R/'extension_ledger.json').read_text())['rows'] if any(int(v)<0 for v in r['net_token_raw'].values())}
 elif a.scope=='missing':hashes={r['hash'] for r in json.loads((R/'all_candidate_accounting.json').read_text())['rows'] if r['native_ETH'] is None}
 else:hashes={r['hash'] for r in json.loads((R/'full_candidates.json').read_text())['rows']}
 rows=[];errors=[];out=R/(('candidates' if a.scope=='missing' else a.scope)+'_rawtrace_native.json')
 previous={r['hash']:r for r in json.loads(out.read_text())['rows']} if out.exists() and a.scope=='missing' else {}
 def save(completed):
  merged={**previous,**{r['hash']:r for r in rows}}
  temp=out.with_suffix('.tmp');temp.write_text(json.dumps({'rows':list(merged.values()),'errors':errors,'requested':len(hashes),'completed':completed},indent=2));temp.replace(out)
 with ThreadPoolExecutor(max_workers=12) as ex:
  fs={ex.submit(fetch,h):h for h in sorted(hashes)}
  for i,f in enumerate(as_completed(fs),1):
   try:rows.append(f.result())
   except Exception as e:errors.append({'hash':fs[f],'error':str(e)})
   if i%50==0:
    save(i);print(i,len(hashes),'errors',len(errors),flush=True)
 save(len(hashes));print('DONE',len(rows),len(errors),flush=True)
if __name__=='__main__':main()
