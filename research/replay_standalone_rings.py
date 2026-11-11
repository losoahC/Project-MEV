import json
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from classify_incremental_candidates import receipts,traces
from rawtrace_native import parse
from screen_expanded import net_for
from identify_mev import WETH
R=Path(__file__).resolve().parent;E=D(10)**18
rings=json.loads((R/'mev_ring_audit.json').read_text())['rows'];bb=defaultdict(list)
for r in rings:
 if r['graph_balanced_positive_closed_candidate'] and not r['sandwich_group_ids']:bb[r['block']].append(r)
rows=[]
for n,rs in sorted(bb.items()):
 recs={r['transactionHash']:r for r in receipts(n)};tt=defaultdict(list);wanted={r['hash'] for r in rs}
 for t in traces(n):
  if t.get('transactionHash') in wanted:tt[t['transactionHash']].append(t)
 for r in rs:
  h=r['hash'];rec=recs[h];a=set(r['operational_boundary']);native=parse(h,tt[h]);net=net_for(rec,a);gas=D(int(rec['gasUsed'],16)*int(rec['effectiveGasPrice'],16))/E;cash=sum((D(v)/E for k,v in native['native_net_wei'].items() if k in a),D(0))+D(net.get(WETH,'0'))/E-gas;other={k:v for k,v in net.items() if k!=WETH and int(v)}
  rows.append({'hash':h,'block':n,'accounts':sorted(a),'net_ETH_after_gas':str(cash),'other_token_net_raw':other,'gas_ETH':str(gas),'native_net_wei':native['native_net_wei'],'trace_tree_validated':True,'cashflow_matches':cash==D(r['operational_net_ETH_after_gas']),'same_block_opposite_link':r['same_block_opposite_link'],'target_links':r['target_links']})
summary={'count':len(rows),'mismatches':sum(not r['cashflow_matches'] for r in rows),'open_token_inventory':sum(bool(r['other_token_net_raw']) for r in rows),'net_ETH':str(sum((D(r['net_ETH_after_gas']) for r in rows),D(0))),'same_block_opposite_count':sum(r['same_block_opposite_link'] for r in rows),'same_block_opposite_net_ETH':str(sum((D(r['net_ETH_after_gas']) for r in rows if r['same_block_opposite_link']),D(0)))}
(R/'standalone_ring_raw_replay.json').write_text(json.dumps({'method':'Independent receipt and full native trace replay; operational boundary, not beneficial ownership. Same-block opposite association is not causal profit attribution. Excludes all known sandwich legs.','summary':summary,'rows':rows},indent=2));print(summary);assert not summary['mismatches'] and not summary['open_token_inventory']
