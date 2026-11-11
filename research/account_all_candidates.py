"""Every screened candidate gets a row; unavailable native flows remain null."""
import json,csv
from decimal import Decimal,getcontext
from pathlib import Path
getcontext().prec=70
R=Path(__file__).resolve().parent;D=Decimal;E=D(10)**18;WETH='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
def main():
 bulk=json.loads((R/'bulk_native.json').read_text());coverage=bulk['coverage'];nets=bulk['internal_net_wei']
 old={r['hash']:r for r in json.loads((R/'native_evidence.json').read_text())['rows']};raw={}
 for p in [R/'rawtrace_crosscheck.json',R/'candidates_rawtrace_native.json',R/'drpc_candidate_native.json']:
  if p.exists():raw.update({r['hash']:r for r in json.loads(p.read_text())['rows']})
 rows=[]
 for c in json.loads((R/'full_candidates.json').read_text())['rows']:
  h=c['hash'];accounts={a for a in [c['from'],c['to']] if a};eth=None;source=None
  if h in raw:
   assert raw[h]['root_from'].lower()==c['from'].lower(),h+' root sender mismatch'
   assert (raw[h]['root_to'] or '').lower()==(c['to'] or '').lower(),h+' root recipient mismatch'
   assert bool(raw[h].get('root_error'))==(c['status']==0),h+' root status mismatch'
   assert sum(map(int,raw[h]['native_net_wei'].values()))==0,h+' native imbalance'
   eth=sum((D(v)/E for a,v in raw[h]['native_net_wei'].items() if a in accounts),D(0));source=raw[h]['source']+(' trace_block' if raw[h].get('rpc_method')=='trace_block' else '')
  elif h in old:
   eth=sum((D(v) for a,v in old[h]['native_internal_net_eth'].items() if a in accounts),D(0));source=old[h]['source']
  elif any(r['first']<=c['block']<=r['last'] for r in coverage):
   assert c['from'] and c['to'],'Root value cancellation requires both endpoints'
   eth=sum((D(v)/E for a,v in nets.get(h,{}).items() if a in accounts),D(0));source='Blockscout fully paginated block-range internal transfers'
  net=c['sender_and_to_token_net_raw'];weth=D(net.get(WETH,'0'))/E;other={t:v for t,v in net.items() if t!=WETH and int(v)};gas=D(c['gas_fee_wei'])/E
  rows.append({'hash':h,'block':c['block'],'index':c['index'],'from':c['from'],'to':c['to'],'native_source':source,'native_ETH':str(eth) if eth is not None else None,'WETH_delta':str(weth),'gas_ETH':str(gas),'other_token_net_raw':other,'other_token_inventory_closed':not bool(other),'net_ETH_WETH_after_gas':str(eth+weth-gas) if eth is not None else None,'same_block_as_target':any(x['block_distance']==0 for x in c['prior_targets']),'opposite_amount0':any(x['opposite_amount0'] for x in c['prior_targets'])})
 closed=[r for r in rows if r['native_ETH'] is not None and r['other_token_inventory_closed']]
 summary={'candidates':len(rows),'native_available':sum(r['native_ETH'] is not None for r in rows),'native_missing':sum(r['native_ETH'] is None for r in rows),'other_token_inventory_closed':sum(r['other_token_inventory_closed'] for r in rows),'native_available_and_other_inventory_closed':len(closed),'closed_group_cashflow_ETH':str(sum((D(r['net_ETH_WETH_after_gas']) for r in closed),D(0))),'candidate_gas_ETH':str(sum((D(r['gas_ETH']) for r in rows),D(0)))}
 (R/'all_candidate_accounting.json').write_text(json.dumps({'method':'Sender+recipient account-boundary cashflows; root value cancels within this group; gas charged once. Not ownership or event-causal profit. Nonzero other-token inventory is not marked-to-market. Public trace availability selects the observed subset; do not extrapolate.','summary':summary,'rows':rows},indent=2))
 with (R/'全部候选核算.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({**r,'other_token_net_raw':json.dumps(r['other_token_net_raw'])})
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
