"""Complete bounded event window headers and traces; reuse verified caches."""
import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from drpc_candidate_traces import fetch
R=Path(__file__).resolve().parent;H=R/'full_headers_raw';H.mkdir(exist_ok=True)
lock=threading.Lock();last=0
def header(n):
 global last
 old=R/'window_raw'/f'{n}_block.json.gz';p=H/f'{n}.json.gz'
 if old.exists():return json.loads(gzip.decompress(old.read_bytes()))
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 for attempt in range(4):
  with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
  z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps({'jsonrpc':'2.0','id':n,'method':'eth_getBlockByNumber','params':[hex(n),False]}),'https://eth.drpc.org'],capture_output=True)
  try:
   d=json.loads(z.stdout)['result'];assert int(d['number'],16)==n
   p.write_bytes(gzip.compress(json.dumps(d).encode()));return d
  except Exception:
   if attempt==3:raise
   time.sleep(2*(attempt+1))
def one(n):
 b=header(n);_,coverage=fetch(n,[])
 assert coverage['block_hash']==b['hash']
 return {'block':n,'hash':b['hash'],'timestamp':int(b['timestamp'],16),'miner':b['miner'],'base_fee_wei':str(int(b['baseFeePerGas'],16)),'transactions':coverage['receipt_count'],'trace_count':coverage['trace_count']}
def main():
 rows=[];errors=[];p=R/'full_window_evidence.json'
 with ThreadPoolExecutor(max_workers=6) as ex:
  fs={ex.submit(one,n):n for n in range(26300640,26303951)}
  for i,f in enumerate(as_completed(fs),1):
   try:rows.append(f.result())
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%100==0:
    p.write_text(json.dumps({'rows':rows,'errors':errors},indent=2));print('full window',i,3311,'errors',len(errors),flush=True)
 p.write_text(json.dumps({'rows':sorted(rows,key=lambda r:r['block']),'errors':errors},indent=2));print('DONE',len(rows),len(errors),flush=True)
if __name__=='__main__':main()
