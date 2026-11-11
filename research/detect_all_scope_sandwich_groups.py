"""Conservative same-sender, immediate-pool-neighbor sandwich structures."""
import json,gzip
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D,getcontext
from screen_expanded import net_for
from complete_late_candidates import events as swaps
from classify_incremental_candidates import receipts as read_receipts, traces as read_traces
from rawtrace_native import parse
from identify_mev import WETH,TRANSFER
getcontext().prec=70
R=Path(__file__).resolve().parent;E=D(10)**18
def load(n):return json.loads((R/n).read_text())
def main():
 targets=load('all_scope_swaps.json')['rows'];events=load('all_scope_pool_events.json');classed={r['hash']:r for r in load('candidate_classification.json')['rows']+load('incremental_candidate_classification.json')['rows']};sig=load('classification_event_signatures.json');risk_topics={v for k,v in sig.items() if k.startswith(('Mint(','Burn(','Collect(','ModifyLiquidity(','Borrow(','Repay(','Supply(','Withdraw(','LiquidationCall(','TransferSingle(','TransferBatch('))}
 poolrows=defaultdict(dict);byhash={}
 for r in events:
  byhash[r['hash']]=r
  for p in {x['pool'] for x in r['pool_events']}:poolrows[p][r['hash']]=r
 lists={p:sorted(x.values(),key=lambda r:(r['block'],r['index'])) for p,x in poolrows.items()};positions={p:{r['hash']:i for i,r in enumerate(rs)} for p,rs in lists.items()}
 rec_cache={};trace_cache={}
 def receipts(n):
  if n not in rec_cache:
   rec_cache[n]={r['transactionHash']:r for r in read_receipts(n)}
  return rec_cache[n]
 pairs={}
 for t in targets:
  for p in {e['pool'] for e in t['pool_events']}:
   i=positions[p][t['hash']];rs=lists[p]
   if i==0 or i+1==len(rs):continue
   front,back=rs[i-1],rs[i+1]
   if front['block']!=t['block'] or back['block']!=t['block']:continue
   recs=receipts(t['block']);f,b=recs[front['hash']],recs[back['hash']]
   if f['from']!=b['from'] or f['from']==recs[t['hash']]['from']:continue
   amount=lambda rr:sum(int(e['amount0']) for e in rr['pool_events'] if e['pool']==p)
   fa,ta,ba=amount(front),amount(t),amount(back)
   if fa*ta<=0 or ba*ta>=0:continue
   key=(front['hash'],back['hash']);item=pairs.setdefault(key,{'front':key[0],'back':key[1],'block':t['block'],'sender':f['from'],'links':[]});item['links'].append({'target':t['hash'],'pool':p,'front_index':front['index'],'target_index':t['index'],'back_index':back['index']})
 # Shared-leg pairs form one episode, avoiding double-counting transaction costs.
 parents={}
 def find(h):
  parents.setdefault(h,h)
  if parents[h]!=h:parents[h]=find(parents[h])
  return parents[h]
 for f,b in pairs:parents[find(b)]=find(f)
 groups=defaultdict(list)
 for item in pairs.values():groups[find(item['front'])].append(item)
 out=[]
 for items in groups.values():
  n=items[0]['block'];recs=receipts(n);legs=sorted({x[k] for x in items for k in ['front','back']},key=lambda h:int(recs[h]['transactionIndex'],16));accounts={x['sender'] for x in items};pools=set();tokens=set();traces=defaultdict(list)
  for t in read_traces(n):
   if t.get('transactionHash') in legs:traces[t['transactionHash']].append(t)
  for h in legs:
   accounts.add(recs[h]['to']);pools.update(e['pool'].split(':')[1] for e in swaps(recs[h]));tokens.update(l['address'] for l in recs[h]['logs'] if len(l['topics'])==3 and l['topics'][0]==TRANSFER)
  for _ in range(12):
   extra=set()
   for h in legs:
    bad={tuple(t['traceAddress']) for t in traces[h] if t.get('error')}
    for t in traces[h]:
     path=tuple(t['traceAddress']);a=t['action']
     if any(path[:i] in bad for i in range(len(path)+1)):continue
     if t['type']=='call' and a.get('callType')=='call' and a['from'] in accounts and a['to'] not in pools|tokens and a.get('input','0x')!='0x':extra.add(a['to'])
   if extra<=accounts:break
   accounts.update(extra)
  net=defaultdict(int);eth=D(0);gas=D(0);risks=[];legrows=[]
  for h in legs:
   r=recs[h];tr=parse(h,traces[h]);en=sum((D(v)/E for a,v in tr['native_net_wei'].items() if a in accounts),D(0));tn=net_for(r,accounts);fee=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/E
   for token,value in tn.items():net[token]+=int(value)
   eth+=en;gas+=fee
   for l in r['logs']:
    if l['topics'] and (l['topics'][0] in risk_topics or l['topics'][0]==TRANSFER and len(l['topics'])==4):risks.append({'hash':h,'emitter':l['address'],'topic':l['topics'][0]})
   legrows.append({'hash':h,'index':int(r['transactionIndex'],16),'cashflow_ETH':str(en+D(tn.get(WETH,'0'))/E-fee),'gas_ETH':str(fee),'single_tx_category':classed.get(h,{}).get('category','not_in_post_target_candidate_set')})
  other={a:str(v) for a,v in net.items() if a!=WETH and v};cash=eth+D(net[WETH])/E-gas
  out.append({'block':n,'senders':sorted({x['sender'] for x in items}),'legs':legrows,'targets':sorted({z['target'] for x in items for z in x['links']}),'links':[z for x in items for z in x['links']],'operational_boundary':sorted(accounts),'other_token_net_raw':other,'position_or_debt_events':risks,'closed_without_recognized_position_events':not other and not risks,'net_cashflow_ETH':str(cash),'gas_ETH':str(gas),'interpretation':'Same-sender bracketing and direction evidence; operational addresses are not verified beneficial owners; hidden liabilities and external positions remain possible.'})
 summary={'pair_count':len(pairs),'episode_count':len(out),'unique_leg_count':len({r['hash'] for g in out for r in g['legs']}),'target_count':len({h for g in out for h in g['targets']}),'closed_without_position_events':sum(g['closed_without_recognized_position_events'] for g in out),'positive_closed_episodes':sum(g['closed_without_recognized_position_events'] and D(g['net_cashflow_ETH'])>0 for g in out),'closed_net_cashflow_ETH':str(sum((D(g['net_cashflow_ETH']) for g in out if g['closed_without_recognized_position_events']),D(0)))}
 (R/'all_scope_sandwich_groups.json').write_text(json.dumps({'method':'Same-block immediate preceding/following observed swap on affected pool; same sender; front follows target net direction and back reverses it. Shared legs merged. Not full event counterfactual.','summary':summary,'groups':out},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
