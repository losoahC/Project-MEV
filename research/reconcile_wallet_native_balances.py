"""Indexed root/internal ETH flows reconciled against independent historical balances."""
import json,gzip,subprocess,time,threading
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from audit_active_wallet_history import receipt_block
R=Path(__file__).resolve().parent;C=R/'wallet_balance_raw';C.mkdir(exist_ok=True);cutoff=26349764;lock=threading.Lock();last=0
load=lambda n:json.loads((R/n).read_text())
def balance(a,n):
 global last
 p=C/f'{a}_{n}.json'
 if p.exists():return int(json.loads(p.read_text())['response']['result'],16)
 with lock:time.sleep(max(0,.25-(time.monotonic()-last)));last=time.monotonic()
 q={'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':[a,hex(n)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':q,'response':json.loads(z.stdout)};value=int(d['response']['result'],16);p.write_text(json.dumps(d));return value

def main():
 wallets=load('exploiter_1_16_and_bot_audit.json')['wallets'];allrecords=defaultdict(lambda:defaultdict(dict))
 for scan in load('wallet_history_coverage.json')['rows']:
  for p in scan['pages']:
   for x in json.loads(gzip.decompress((R/p).read_bytes()))['items']:
    n=x.get('block_number')
    if n is None or n>cutoff:continue
    kind=scan['endpoint'];h=x.get('hash') if kind=='transactions' else x['transaction_hash'];key=(h,x.get('index')) if kind=='internal-transactions' else (h,x.get('log_index')) if kind=='token-transfers' else h;allrecords[scan['wallet']][kind][str(key)]=x
 requests=[];starts={}
 for w in wallets:
  nums=[x['block_number'] for kind in allrecords[w['number']].values() for x in kind.values()];start=min(nums)-1 if nums else cutoff;starts[w['number']]=start;requests.extend([(w['address'],start),(w['address'],cutoff)])
 balances={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(balance,*q):q for q in set(requests)}
  for f in as_completed(fs):
   try:balances[fs[f]]=f.result()
   except Exception as e:errors.append({'query':fs[f],'error':str(e)})
 rows=[];rc={}
 for w in wallets:
  a=w['address'];data=allrecords[w['number']];entries=[];root_net=0;internal_net=0;gas=0
  for x in data['transactions'].values():
   h=x['hash'];n=x['block_number'];src=(x.get('from') or {}).get('hash','').lower();dst=(x.get('to') or x.get('created_contract') or {}).get('hash','').lower();v=int(x['value']);success=x['status']=='ok';delta=(int(dst==a)-int(src==a))*v if success else 0;root_net+=delta
   if src==a:
    if n not in rc:rc[n]={r['transactionHash']:r for r in receipt_block(n)}
    r=rc[n][h];fee=int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16);gas+=fee
   else:fee=0
   if delta or fee:entries.append({'hash':h,'block':n,'kind':'root','native_net_wei':str(delta),'gas_wei':str(fee)})
  for x in data['internal-transactions'].values():
   assert x['index']!=0,'root double count risk'
   if not x['success'] or x['error']:continue
   assert x['type']=='call','unsupported indexed internal type'
   src=(x.get('from') or {}).get('hash','').lower();dst=(x.get('to') or x.get('created_contract') or {}).get('hash','').lower();delta=(int(dst==a)-int(src==a))*int(x['value']);internal_net+=delta
   if delta:entries.append({'hash':x['transaction_hash'],'block':x['block_number'],'kind':'internal','index':x['index'],'native_net_wei':str(delta)})
  start=starts[w['number']];before=balances.get((a,start));after=balances.get((a,cutoff));pred=before+root_net+internal_net-gas if before is not None else None;residual=after-pred if after is not None and pred is not None else None
  rows.append({'wallet':w['number'],'address':a,'start_block':start,'cutoff_block':cutoff,'start_balance_wei':str(before) if before is not None else None,'end_balance_wei':str(after) if after is not None else None,'root_net_wei':str(root_net),'internal_net_wei':str(internal_net),'receipt_gas_paid_wei':str(gas),'predicted_end_balance_wei':str(pred) if pred is not None else None,'residual_wei':str(residual) if residual is not None else None,'balance_reconciled':residual==0,'entries':entries})
 out={'method':'Balance at block before first indexed activity plus indexed successful top-level value and successful non-root internal CALL values minus receipt gas equals independent historical cutoff balance. Does not exclude omitted offsetting flows or prove token history. Nonzero residual requires investigation; no automatic fill.','rows':rows,'errors':errors,'all_reconciled':all(r['balance_reconciled'] for r in rows)};(R/'wallet_native_balance_reconciliation.json').write_text(json.dumps(out,indent=2));print([(r['wallet'],r['start_balance_wei'],r['residual_wei']) for r in rows]);print('errors',errors)
if __name__=='__main__':main()
