import json
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from classify_incremental_candidates import receipts,traces
from rawtrace_native import parse
from screen_expanded import net_for
from identify_mev import WETH
R=Path(__file__).resolve().parent;E=D(10)**18
load=lambda n:json.loads((R/n).read_text())
def main():
 groups=load('all_scope_sandwich_groups.json')['groups'];bb=defaultdict(list)
 for i,g in enumerate(groups):bb[g['block']].append((i,g))
 rows=[]
 for n,gs in sorted(bb.items()):
  recs={r['transactionHash']:r for r in receipts(n)};tt=defaultdict(list)
  for t in traces(n):
   if t.get('transactionHash'):tt[t['transactionHash']].append(t)
  for i,g in gs:
   accounts=set(g['operational_boundary']);tokens=defaultdict(int);cash=D(0);legs=[]
   for leg in sorted(g['legs'],key=lambda x:x['index']):
    h=leg['hash'];r=recs[h];nr=parse(h,tt[h]);net=net_for(r,accounts);native=sum((D(x)/E for a,x in nr['native_net_wei'].items() if a in accounts),D(0));gas=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/E
    for a,x in net.items():tokens[a]+=int(x)
    cash+=native+D(net.get(WETH,'0'))/E-gas
    legs.append({'hash':h,'index':int(r['transactionIndex'],16),'native_ETH':str(native),'token_net_raw':net,'gas_ETH':str(gas),'trace_tree_validated':True})
   others={a:str(x) for a,x in tokens.items() if a!=WETH and x};match=abs(cash-D(g['net_cashflow_ETH']))<D('1e-18')
   rows.append({'group_id':i,'block':n,'targets':g['targets'],'accounts':sorted(accounts),'legs':legs,'nonWETH_residual_raw':others,'net_ETH_after_gas':str(cash),'matches_previous_ledger':match,'closed_positive_no_recognized_position_events':not others and cash>0 and not g['position_or_debt_events'],'limitation':'Validates combined endpoint cashflow, not exclusive capital continuity or ownership; transfers between legs and positions outside boundary may matter.'})
 out={'scope':'All existing same-block sandwich structural groups. Fresh receipt and full native call-tree replay. Does not discover arbitrary cross-block strategies or prove causal profit.','groups':len(rows),'cashflow_mismatches':sum(not r['matches_previous_ledger'] for r in rows),'closed_positive_groups':sum(r['closed_positive_no_recognized_position_events'] for r in rows),'rows':rows};(R/'multitx_ring_replay.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
if __name__=='__main__':main()
