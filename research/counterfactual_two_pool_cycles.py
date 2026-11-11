"""Target-removal feasibility audit of two-pool cycles; reject infeasible frozen intervening flow."""
import json
from pathlib import Path
from decimal import Decimal as D
from classify_incremental_candidates import receipts
R=Path(__file__).resolve().parent;W='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2';SWAP='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822';SYNC='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'
load=lambda n:json.loads((R/n).read_text())
def event_rows(rs,pools):
 events=[];other=[]
 for r in rs:
  last={}
  for l in r['logs']:
   p=l['address']
   if p not in pools:continue
   t=l['topics'][0];w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)]
   if t==SYNC:last[p]=w
   elif t==SWAP:
    j=0 if w[0] and not w[1] and not w[2] else 1 if w[1] and not w[0] and not w[3] else None
    if j is None or p not in last:other.append({'hash':r['transactionHash'],'reason':'nonstandard_swap'});continue
    after=last[p];before=[after[k]-w[k]+w[k+2] for k in [0,1]];events.append({'hash':r['transactionHash'],'pool':p,'index':int(r['transactionIndex'],16),'log_index':int(l['logIndex'],16),'side':j,'input':w[j],'output':w[3-j],'before':before,'after':after})
   elif t not in ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef','0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925']:other.append({'hash':r['transactionHash'],'index':int(r['transactionIndex'],16),'topic':t})
 return events,other
def main():
 data=load('two_pool_counterfactual_metadata.json');meta=data['pools'];cs={r['hash']:r for r in load('full_candidates.json')['rows']};cls={r['hash']:r for r in load('candidate_classification.json')['rows']};out=[]
 for c in data['candidates']:
  h=c['hash'];pools={p[3:] for p in c['pools']};rs=receipts(c['block']);events,other=event_rows(rs,pools);actor=[e for e in events if e['hash']==h];assert len(actor)==2
  # Arrange the economic WETH -> token -> WETH cycle, even when calls use flash-swap order.
  route=sorted(actor,key=lambda e:meta[e['pool']]['token'+str(e['side'])]!=W);assert meta[route[0]['pool']]['token'+str(route[0]['side'])]==W
  assert route[0]['output']==route[1]['input']
  for e in route:assert e['input']*997*e['before'][1-e['side']]//(1000*e['before'][e['side']]+997*e['input'])==e['output']
  targets={p['target'] for p in cs[h]['prior_targets'] if p['block_distance']==0 and p.get('opposite_amount0')};scenarios=[]
  for target in targets:
   te=[e for e in events if e['hash']==target];affected={e['pool'] for e in te};states={};violations=[];intermediate=[]
   for pool in affected:
    seq=[e for e in events if e['pool']==pool];first=next(i for i,e in enumerate(seq) if e['hash']==target);seq=seq[first:];reserve=seq[0]['before'].copy()
    stop=next(e['log_index'] for e in actor if e['pool']==pool)
    for e in seq:
     if e['log_index']>=stop:break
     if e['hash']==target:continue
     j=e['side'];maxout=e['input']*997*reserve[1-j]//(1000*reserve[j]+997*e['input'])
     if e['output']>maxout:violations.append({'hash':e['hash'],'pool':pool,'reason':'observed_intervening_output_exceeds_counterfactual_max','excess_raw':str(e['output']-maxout)})
     reserve[j]+=e['input'];reserve[1-j]-=e['output'];intermediate.append(e['hash'])
    states[pool]=reserve
   for e in other:
    if e.get('index',0)>=min(t['index'] for t in te) and e.get('index',0)<=actor[0]['index']:violations.append({'reason':'non_swap_state_change','event':e})
   outputs=[];inp=route[0]['input']
   if not violations:
    for e in route:
     b=states.get(e['pool'],e['before']);j=e['side'];inp=inp*997*b[1-j]//(1000*b[j]+997*inp);outputs.append(str(inp))
    actual_gross=D(route[1]['output']-route[0]['input'])/D(10**18);costs=actual_gross-D(cls[h]['operational_cashflow_ETH']);cf=D(inp-route[0]['input'])/D(10**18)-costs
   scenarios.append({'removed_target':target,'intervening_swap_count':len(intermediate),'feasible_under_frozen_intervening_flows':not violations,'violations':violations,'counterfactual_route_outputs':outputs,'counterfactual_net_ETH':str(cf) if not violations else None,'actual_minus_counterfactual_ETH':str(D(cls[h]['operational_cashflow_ETH'])-cf) if not violations else None})
  out.append({'hash':h,'block':c['block'],'actual_net_ETH':cls[h]['operational_cashflow_ETH'],'actual_route':route,'scenarios':scenarios})
 result={'method':'Conditional two-pool fixed-investment policy. Remove target pool effects; freeze intervening observed inputs AND outputs, require AMM feasibility; simulate actor maximizing output on its two-pool route. Fixed gas/direct costs. Flash-swap execution order, slippage and other-pool responses not reexecuted. Not whole-EVM causal profit. Infeasible scenarios return null.','rows':out};(R/'two_pool_cycle_counterfactuals.json').write_text(json.dumps(result,indent=2));print([(r['hash'],[(s['feasible_under_frozen_intervening_flows'],s['actual_minus_counterfactual_ETH'],len(s['violations'])) for s in r['scenarios']]) for r in out])
if __name__=='__main__':main()
