import json,gzip,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import scan_window as sw
R=Path(__file__).resolve().parent;C=R/'baseline_raw';C.mkdir(exist_ok=True);sw.C=C
def header(n):
 p=C/f'{n}_block.json.gz'
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 z=subprocess.check_output(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBlockByNumber','params':[hex(n),False]}),sw.URL]);d=json.loads(z)['result'];p.write_bytes(gzip.compress(json.dumps(d).encode()));return d
def first_at(t,lo,hi):
 while lo<hi:
  m=(lo+hi)//2
  if int(header(m)['timestamp'],16)<t:lo=m+1
  else:hi=m
 return lo
def one(n):
 b=header(n);base=int(b['baseFeePerGas'],16);gas=int(b['gasUsed'],16)
 return {'block':n,'timestamp':int(b['timestamp'],16),'transactions':len(b['transactions']),'gas_used':gas,'base_fee_wei':str(base),'base_burn_wei':str(base*gas),'priority_fee_wei':None,'failed_count':None,'failed_gas_fee_wei':None}
def main():
 event=json.loads((R/'window_block_costs.json').read_text())['rows'];t0=event[0]['timestamp']-86400;t1=event[-1]['timestamp']-86400
 lo=first_at(t0,26293000,26294000);hi=first_at(t1+1,lo,26295500)-1;print('baseline range',lo,hi,flush=True)
 rows=[];errors=[]
 with ThreadPoolExecutor(max_workers=5) as ex:
  fs={ex.submit(one,n):n for n in range(lo,hi+1)}
  for i,f in enumerate(as_completed(fs),1):
   try:rows.append(f.result())
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%100==0:print('baseline',i,len(fs),'errors',len(errors),flush=True)
 rows.sort(key=lambda r:r['block']);out={'note':'One preceding calendar day at same UTC times; descriptive comparator, not causal identification. Header-only: receipts returned null, so priority fees and failed counts are UNKNOWN, not zero.','first_block':lo,'last_block':hi,'errors':errors,'rows':rows}
 (R/'baseline_block_costs.json').write_text(json.dumps(out,indent=2));print('DONE',len(rows),len(errors),flush=True)
if __name__=='__main__':main()
