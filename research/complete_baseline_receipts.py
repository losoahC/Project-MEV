import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'baseline_raw';lock=threading.Lock();last=0
def one(b):
 global last
 n=b['block'];p=C/f'{n}_receipts.json.gz'
 if p.exists():rs=json.loads(gzip.decompress(p.read_bytes()))
 else:
  for attempt in range(3):
   with lock:time.sleep(max(0,.25-(time.monotonic()-last)));last=time.monotonic()
   q={'jsonrpc':'2.0','id':1,'method':'eth_getBlockReceipts','params':[hex(n)]};z=subprocess.run(['curl','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True)
   try:
    d=json.loads(z.stdout);rs=d['result'];assert isinstance(rs,list);break
   except Exception:
    if attempt==2:raise ValueError(z.stdout.decode()[:150]+z.stderr.decode()[:100])
    time.sleep(1)
  p.write_bytes(gzip.compress(json.dumps(rs).encode()))
 header=json.loads(gzip.decompress((C/f'{n}_block.json.gz').read_bytes()));assert {r['transactionHash'] for r in rs}==set(header['transactions']);assert all(r['blockHash']==header['hash'] for r in rs)
 base=int(b['base_fee_wei']);gas=sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in rs);burn=sum(int(r['gasUsed'],16)*base for r in rs);failed=[r for r in rs if int(r['status'],16)==0]
 assert sum(int(r['gasUsed'],16) for r in rs)==b['gas_used']
 return {**b,'gas_fee_wei':str(gas),'priority_fee_wei':str(gas-burn),'failed_count':len(failed),'failed_gas_fee_wei':str(sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in failed))}
def main():
 old=json.loads((R/'baseline_block_costs.json').read_text());rows=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(one,b):b['block'] for b in old['rows']}
  for i,f in enumerate(as_completed(fs),1):
   try:rows.append(f.result())
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%100==0:print('baseline receipts',i,len(fs),'errors',len(errors),flush=True)
 out={'note':'Preceding calendar day at same UTC hours as ORIGINAL first window (not whole extended window). Full receipts now independently matched to block header. Descriptive comparator, not causal identification.','first_block':old['first_block'],'last_block':old['last_block'],'errors':errors,'rows':sorted(rows,key=lambda x:x['block'])};(R/'baseline_complete_costs.json').write_text(json.dumps(out,indent=2));print('DONE',len(rows),len(errors),flush=True)
if __name__=='__main__':main()
