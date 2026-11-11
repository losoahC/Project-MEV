"""Conditional one-pool fixed-input replay, with bot's second-leg input tied to first-leg output."""
import json
from pathlib import Path
from decimal import Decimal as D
from classify_incremental_candidates import receipts
R=Path(__file__).resolve().parent
SWAP='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822';SYNC='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'
g=json.loads((R/'extended_cycle_interval_verification.json').read_text())['rows'][0];pool='0x25647e01bd0967c1b9599fa3521939871d1d0888';meta=json.loads((R/'all_scope_v2_pool_metadata.json').read_text())['pools'][pool];assert meta['verified_uniswap_v2']
cs=json.loads((R/'full_candidates.json').read_text())['rows'];targets={p['target'] for c in cs if c['hash'] in g['legs'] for p in c['prior_targets'] if p['pool']=='V2:'+pool};events=[];issues=[]
for n in range(g['start_block']-1,g['end_block']+1):
 for r in receipts(n):
  if n==g['end_block'] and int(r['transactionIndex'],16)>g['end_index']:continue
  logs=[l for l in r['logs'] if l['address']==pool];sync=None
  for l in logs:
   t=l['topics'][0];w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)]
   if t==SYNC:sync=w
   elif t==SWAP:
    j=0 if w[0]>0 and w[1]==0 and w[2]==0 else 1 if w[1]>0 and w[0]==0 and w[3]==0 else None
    if j is None or sync is None:issues.append('nonstandard swap');continue
    before=[sync[k]-w[k]+w[k+2] for k in [0,1]];pred=w[j]*997*before[1-j]//(1000*before[j]+997*w[j])
    events.append({'hash':r['transactionHash'],'block':n,'index':int(r['transactionIndex'],16),'log_index':int(l['logIndex'],16),'predicted_output':pred,'side':j,'input':w[j],'output':w[3-j],'before':before,'after':sync.copy()})
   else:issues.append({'hash':r['transactionHash'],'non_swap_pool_event':t})
start=next(i for i,e in enumerate(events) if e['hash'] in targets);events=events[start:]
failures=[]
for e in events:
 if e['predicted_output']!=e['output']:
  j=e['side'];minimum_input=e['before'][j]*e['output']*1000//((e['before'][1-j]-e['output'])*997)+1
  failures.append({'hash':e['hash'],'block':e['block'],'log_index':e['log_index'],'output_gap_raw':str(e['predicted_output']-e['output']),'exact_output_inverse_matches':minimum_input==e['input'],'minimum_input_raw':str(minimum_input),'observed_input_raw':str(e['input'])})
continuous=all(a['after']==b['before'] for a,b in zip(events,events[1:]))
if failures or issues or not continuous:
 out={'status':'not_admitted_to_strict_fixed_input_counterfactual','actual_net_ETH':g['wallet_only_net_ETH'],'pool':pool,'targets':sorted(targets),'actual_swaps':events,'fixed_input_mismatches':failures,'non_swap_events':issues,'reserve_continuity':continuous,'reason':'Actual fixed-input maximum-output model fails on intervening swaps. Must inspect exact-output/multihop call semantics before causal replay. No counterfactual profit reported.'}
 (R/'extended_cycle_counterfactual.json').write_text(json.dumps(out,indent=2));print('Rejected strict replay:',len(failures),'mismatches; inverse exact-output matches',sum(f['exact_output_inverse_matches'] for f in failures));raise SystemExit(0)
actuallegs=[e for e in events if e['hash'] in g['legs']];assert len(actuallegs)==2 and actuallegs[0]['side']==0 and actuallegs[1]['side']==1;assert actuallegs[0]['output']==actuallegs[1]['input'];gas=sum(D(a['gas_ETH']) for a in g['wallet_interval_activities']);scenarios=[]
for removed in [{t} for t in sorted(targets)]+[targets]:
 reserves=events[0]['before'].copy();bought=None;sold=None;replayed=[]
 for e in events:
  if e['hash'] in removed:continue
  j=e['side'];inp=bought if e['hash']==g['legs'][1] else e['input'];assert inp is not None
  output=inp*997*reserves[1-j]//(1000*reserves[j]+997*inp);reserves[j]+=inp;reserves[1-j]-=output
  if e['hash']==g['legs'][0]:bought=output
  if e['hash']==g['legs'][1]:sold=output
  replayed.append({'hash':e['hash'],'input':str(inp),'output':str(output)})
 net=D(sold-actuallegs[0]['input'])/D(10**18)-gas;scenarios.append({'removed_targets':sorted(removed),'counterfactual_net_ETH':str(net),'actual_minus_counterfactual_ETH':str(D(g['wallet_only_net_ETH'])-net),'bot_token_acquired':str(bought),'bot_WETH_recovered':str(sold),'replayed_swaps':replayed})
out={'method':'Verified Uniswap V2 one-pool integer replay. Actual outputs and all consecutive reserves reproduced. Remove specified target swaps; hold all other swap inputs fixed except bot sale uses all tokens acquired by its simulated purchase. Gas fixed; ignores slippage/reverts, other pools and behavioral responses. Conditional sensitivity, not whole-EVM or global causal MEV.','pool':pool,'actual_net_ETH':g['wallet_only_net_ETH'],'actual_swaps':events,'scenarios':scenarios,'non_swap_events':issues}
(R/'extended_cycle_counterfactual.json').write_text(json.dumps(out,indent=2));print('swaps',len(events));print([{k:v for k,v in s.items() if k!='replayed_swaps'} for s in scenarios])
