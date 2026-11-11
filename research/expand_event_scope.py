import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'scope_log_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
A=sorted({x['address'].lower() for x in json.loads((R/'address_leads.json').read_text())['wallets']});T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def fetch(task):
 global last
 lo,hi,direction=task;p=C/f'{direction}_{lo}_{hi}.json.gz'
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))['result']
 topics=[T,['0x'+a[2:].zfill(64) for a in A]] if direction=='out' else [T,None,['0x'+a[2:].zfill(64) for a in A]]
 q={'jsonrpc':'2.0','id':1,'method':'eth_getLogs','params':[{'fromBlock':hex(lo),'toBlock':hex(hi),'topics':topics}]}
 for attempt in range(3):
  with lock:time.sleep(max(0,.25-(time.monotonic()-last)));last=time.monotonic()
  z=subprocess.run(['curl','--silent','--show-error','--max-time','35','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True)
  try:
   d=json.loads(z.stdout);assert isinstance(d.get('result'),list),str(d)[:200];p.write_bytes(gzip.compress(json.dumps(d).encode()));return d['result']
  except Exception as e:
   if attempt==2:raise ValueError(str(e)+' '+z.stderr.decode()[:100])
   time.sleep(1)
def main():
 cutoff=json.loads((R/'scope_latest_cutoff.json').read_text())['result'];endblock=int(cutoff['number'],16)
 tasks=[(n,min(n+99,end),d) for start,end in [(26293000,26300639),(26303951,endblock)] for n in range(start,end+1,100) for d in ['in','out']];logs={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(fetch,t):t for t in tasks}
  for i,f in enumerate(as_completed(fs),1):
   try:
    for l in f.result():logs[(l['transactionHash'],l['logIndex'])]=l
   except Exception as e:errors.append({'task':fs[f],'error':str(e)})
   if i%100==0:print('scope queries',i,len(tasks),'logs',len(logs),'errors',len(errors),flush=True)
 rows=sorted(logs.values(),key=lambda l:(int(l['blockNumber'],16),int(l['logIndex'],16)))
 (R/'expanded_scope_logs.json').write_text(json.dumps({'scope':'55 tracker lead addresses only, both directions ERC20 Transfer logs, pre/post original window. Token spam/unverified assets must be excluded; native-only and other addresses are not covered.','ranges':[[26293000,26300639],[26303951,endblock]],'cutoff_timestamp':int(cutoff['timestamp'],16),'queries':len(tasks),'errors':errors,'rows':rows},indent=2));print('DONE',len(rows),'unique tx',len({l['transactionHash'] for l in rows}),'errors',len(errors),flush=True)
if __name__=='__main__':main()
