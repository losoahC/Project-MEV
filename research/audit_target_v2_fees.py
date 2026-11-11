import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal as D
from value_inventory_ledger import token_value,HEAD
R=Path(__file__).resolve().parent;C=R/'v2_fee_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
FACTORY='0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f'
def call(tag,to,data,n):
 global last
 p=C/(tag+'.json')
 if p.exists():return json.loads(p.read_text())['response']['result']
 with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
 req={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},hex(n)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(req),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':req,'response':json.loads(z.stdout)};p.write_text(json.dumps(d));return d['response']['result']
def main():
 targets=json.loads((R/'full_swaps.json').read_text())['rows'];pools={}
 for t in targets:
  for e in t['pool_events']:
   if e['pool'].startswith('V2:'):pools.setdefault(e['pool'][3:],{'block':t['block']})
 tasks=[(p+'_'+f,p,s,v['block']) for p,v in pools.items() for f,s in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155')]]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(call,*t):t[0] for t in tasks}
  for f in as_completed(fs):
   tag=fs[f];pool,field=tag.split('_');raw=f.result();assert len(raw)==66;pools[pool][field]='0x'+raw[-40:]
 for pool,m in pools.items():
  if m['factory']==FACTORY:
   got=call(pool+'_getPair',FACTORY,'0xe6a43905'+m['token0'][2:].zfill(64)+m['token1'][2:].zfill(64),m['block']);m['verified_uniswap_v2']='0x'+got[-40:]==pool
  else:m['verified_uniswap_v2']=False
 rows=[];cache={}
 for t in targets:
  es=[e for e in t['pool_events'] if e['pool'].startswith('V2:')]
  if not es:continue
  n=t['block']
  if n not in cache:
   folder='window_raw' if n<=26301940 else 'extension_raw';cache[n]={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))}
  logs=cache[n][t['hash']]['logs'];byidx={int(l['logIndex'],16):l for l in logs}
  for e in es:
   pool=e['pool'][3:];m=pools[pool];l=byidx[e['log_index']];w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];assert len(w)==4
   row={'hash':t['hash'],'block':n,'pool':pool,'log_index':e['log_index'],'amount0_in':str(w[0]),'amount1_in':str(w[1]),'amount0_out':str(w[2]),'amount1_out':str(w[3]),'verified_uniswap_v2':m['verified_uniswap_v2']}
   if not m['verified_uniswap_v2']:row['status']='unsupported_factory';rows.append(row);continue
   # Sync emitted immediately before standard pair Swap; decode reserves after trade.
   sync=next((z for z in reversed(logs) if int(z['logIndex'],16)<e['log_index'] and z['address']==pool and z['topics'][0]=='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'),None)
   if not sync:row['status']='missing_sync';rows.append(row);continue
   after=[int(sync['data'][i:i+64],16) for i in range(2,len(sync['data']),64)];before=[after[j]-w[j]+w[j+2] for j in [0,1]]
   row['reserves_before']=list(map(str,before));row['reserves_after']=list(map(str,after))
   j=0 if w[0]>0 and w[1]==0 and w[2]==0 else 1 if w[1]>0 and w[0]==0 and w[3]==0 else None
   if j is None:row['status']='complex_two_sided_swap';rows.append(row);continue
   predicted=w[j]*997*before[1-j]//(before[j]*1000+w[j]*997);row['output_formula_match']=predicted==w[3-j]
   # Router can request less than the maximum; only exact matches enter primary fee sample.
   if not row['output_formula_match']:row['status']='nonstandard_output';rows.append(row);continue
   rawfee=D(w[j])*D(3)/1000;row.update(status='verified_standard_swap',fee_asset=token_value(m[f'token{j}'],str(rawfee),HEAD[n]['timestamp'],5),gross_fee_raw=str(rawfee),input_token=m[f'token{j}'])
   rows.append(row)
 good=[r for r in rows if r['status']=='verified_standard_swap'];priced=[r for r in good if r['fee_asset']['USD'] is not None]
 out={'method':'Target-transaction V2 swap gross pool trading fee = input * 3/1000, fractional raw units retained analytically. Only official factory getPair verified and exact integer 997 output reproduction included. Fee accrues inside reserves; it is not an immediate transfer or LP net profit. Protocol fee share/LP ownership and other routes excluded. Target transaction may contain additional routing; not all costs are abnormal MEV.','pools':pools,'rows':rows,'summary':{'target_v2_swaps':len(rows),'verified_standard_swaps':len(good),'priced_fee_swaps':len(priced),'marked_gross_pool_fees_USD':str(sum((D(r['fee_asset']['USD']) for r in priced),D(0)))}}
 (R/'target_v2_fee_accounting.json').write_text(json.dumps(out,indent=2));print(out['summary'],flush=True)
if __name__=='__main__':main()
