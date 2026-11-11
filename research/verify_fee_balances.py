import json,subprocess,random,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;C=R/'fee_balance_raw';C.mkdir(exist_ok=True)
def call(task):
 n,a=task;p=C/f'{n}_{a}.json'
 if p.exists():return int(json.loads(p.read_text())['response']['result'],16)
 req={'jsonrpc':'2.0','id':1,'method':'eth_getBalance','params':[a,hex(n)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(req),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':req,'response':json.loads(z.stdout)};p.write_text(json.dumps(d));return int(d['response']['result'],16)
def main():
 blocks=json.loads((R/'full_fee_distribution.json').read_text())['blocks'];rng=random.Random(565);sample=rng.sample(blocks,12);sample+=[b for b in blocks if b['block'] in [26300663,26300686,26301609]];tasks=set()
 for b in sample:
  for a in {b['fee_recipient'],b.get('proposer_fee_recipient',b['fee_recipient'])}:
   for n in [b['block']-1,b['block']]:tasks.add((n,a))
 tasks=sorted(tasks)
 with ThreadPoolExecutor(max_workers=3) as ex:values=dict(zip(tasks,ex.map(call,tasks)))
 rows=[]
 for b in sample:
  for role,a,field in [('block_fee_recipient',b['fee_recipient'],'fee_recipient_observed_execution_ETH_delta_wei')]+([('proposer',b['proposer_fee_recipient'],'proposer_execution_delta_wei')] if 'proposer_execution_delta_wei' in b else []):
   observed=values[(b['block'],a)]-values[(b['block']-1,a)];computed=int(b[field]);rows.append({'block':b['block'],'role':role,'address':a,'balance_difference_wei':str(observed),'execution_accounting_wei':str(computed),'difference_wei':str(observed-computed),'match':observed==computed})
 (R/'fee_balance_validation.json').write_text(json.dumps({'method':'Independent historical eth_getBalance differences versus full trace plus receipt fee accounting. Any mismatch requires inspecting consensus withdrawals or accounting omissions.','rows':rows},indent=2));print('balance matches',sum(r['match'] for r in rows),'of',len(rows));print([r for r in rows if not r['match']])
if __name__=='__main__':main()
