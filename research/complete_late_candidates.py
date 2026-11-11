"""Extend the same explicit candidate rule to later known-address exchange events."""
import json,gzip
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal as D,getcontext
from fetch_expanded_scope_details import call,R,PCAKE
from screen_expanded import swaps,net_for
from rawtrace_native import parse
import value_inventory_ledger as val
load=lambda n:json.loads((R/n).read_text())
def events(r):
 out=swaps(r)
 for l in r['logs']:
  if l['topics'] and l['topics'][0]==PCAKE:
   w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)]
   if len(w)==7:out.append({'pool':'PancakeV3:'+l['address'],'amount0':str(w[0] if w[0]<2**255 else w[0]-2**256),'amount1':str(w[1] if w[1]<2**255 else w[1]-2**256),'log_index':int(l['logIndex'],16)})
 return out
def detail(n,items):
 getcontext().prec=70
 b=call(n,'block');rs=call(n,'receipts');tr=call(n,'trace')
 assert set(b['transactions'])=={r['transactionHash'] for r in rs}
 assert all(r['blockHash']==b['hash'] for r in rs)
 assert set(b['transactions'])=={t['transactionHash'] for t in tr if t.get('transactionHash') and t['traceAddress']==[]}
 td=defaultdict(list);wanted={c['hash'] for c,r in items};val.HEAD[n]={'timestamp':int(b['timestamp'],16)}
 for t in tr:
  if t.get('transactionHash') in wanted:td[t['transactionHash']].append(t)
 for c,r in items:
  nr=parse(c['hash'],td[c['hash']]);group={r['from'],r['to']}-{None};net=net_for(r,group);cash=(sum((D(v) for a,v in nr['native_net_wei'].items() if a in group),D(0))-D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16)))/D(10**18)
  c.update(timestamp=int(b['timestamp'],16),root_boundary=sorted(group),native_after_gas_ETH=str(cash),net_token_raw=net,strict=val.portfolio(str(cash),net,n,0),five_minute=val.portfolio(str(cash),net,n,5),trace_complete=True)
 return [c for c,r in items]
def main():
 targets={r['hash']:r for r in load('expanded_scope_details.json')['rows'] if r['category']=='pool_swap_compatible'}
 ns=sorted({n for r in targets.values() for n in range(r['block'],r['block']+6)});receipts={};errors=[]
 for p in load('scope_market_prices.json')['rows']:val.PRICES.setdefault(p['symbol'],{}).update(p['bars'])
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(call,n,'receipts'):n for n in ns}
  for i,f in enumerate(as_completed(fs),1):
   try:receipts[fs[f]]=f.result()
   except Exception as e:errors.append({'stage':'receipts','block':fs[f],'error':str(e)})
   if i%100==0:print('late receipt blocks',i,len(ns),'errors',len(errors),flush=True)
 pools={e['pool'] for n,rs in receipts.items() for r in rs if r['transactionHash'] in targets for e in events(r)}
 last={};byblock=defaultdict(list);activity=[]
 for n in sorted(receipts):
  for r in sorted(receipts[n],key=lambda r:int(r['transactionIndex'],16)):
   es=[e for e in events(r) if e['pool'] in pools]
   if not es:continue
   h=r['transactionHash'];links=[]
   for e in es:
    p=last.get(e['pool'])
    if p and 0<=n-p['block']<=5 and p['hash']!=h:links.append({**p,'pool':e['pool'],'block_distance':n-p['block'],'opposite_amount0':int(e['amount0'])*int(p['amount0'])<0})
   if h in targets:
    for e in es:last[e['pool']]={'hash':h,'block':n,'amount0':e['amount0']}
   elif links:byblock[n].append(({'hash':h,'block':n,'index':int(r['transactionIndex'],16),'from':r['from'],'to':r['to'],'prior_targets':links,'pool_events':es},r))
   activity.append({'hash':h,'block':n,'target':h in targets,'pool_events':es})
 rows=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(detail,n,items):n for n,items in byblock.items()}
  for i,f in enumerate(as_completed(fs),1):
   try:rows+=f.result()
   except Exception as e:errors.append({'stage':'detail','block':fs[f],'error':str(e)})
   if i%50==0:print('late trace blocks',i,len(fs),'rows',len(rows),'errors',len(errors),flush=True)
 old={r['hash'] for r in load('full_candidates.json')['rows']}|{r['hash'] for r in load('pancake_coverage_completion.json')['candidates']};new={r['hash'] for r in rows}
 out={'method':'Same/next-five-block affected pool overlap, extended to 180 later known-address compatible swaps. Candidate, not causal arbitrage proof. Native traces complete per fetched candidate block, header/receipt/root hashes checked. Root sender+entry boundary remains provisional and may include shared routers. No claim all later blockchain activity or beneficial-owner profits.','summary':{'targets':len(targets),'requested_receipt_blocks':len(ns),'fetched_receipt_blocks':len(receipts),'affected_pools':len(pools),'candidate_transactions':len(rows),'incremental_candidate_transactions':len(new-old),'union_candidate_transactions':len(old|new),'candidate_blocks':len(byblock),'errors':len(errors)},'errors':errors,'rows':sorted(rows,key=lambda r:(r['block'],r['index'])),'pool_activity':activity}
 (R/'late_candidate_completion.json').write_text(json.dumps(out,indent=2));print('DONE',out['summary'],flush=True)
if __name__=='__main__':main()
