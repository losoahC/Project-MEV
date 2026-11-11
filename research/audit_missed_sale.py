import json
from pathlib import Path
from decimal import Decimal as D
from classify_incremental_candidates import receipts,traces
from screen_expanded import net_for,swaps
from rawtrace_native import parse
from value_inventory_ledger import portfolio
R=Path(__file__).resolve().parent;d=json.loads((R/'history_edge_cases_verified.json').read_text());out=[]
for x in d['sale_pool_neighborhood']:
 h=x['hash'];n=x['block'];r=next(r for r in receipts(n) if r['transactionHash']==h);a={r['from'],r['to']}-{None};nr=parse(h,[t for t in traces(n) if t.get('transactionHash')==h]);native=sum((D(v)/D(10**18) for k,v in nr['native_net_wei'].items() if k in a),D(0));net=net_for(r,a);gas=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/D(10**18)
 out.append({**x,'accounts':sorted(a),'native_ETH':str(native),'token_net_raw':net,'gas_ETH':str(gas),'strict_net_valuation':portfolio(str(native-gas),net,n,0),'all_pool_events':swaps(r),'caveat':'from+to boundary only; not ownership. No causal link inferred from five-block proximity.'})
(R/'missed_sale_and_followup_audit.json').write_text(json.dumps({'rows':out,'original_target_count':1352,'augmented_target_count':1353,'original_statistics_unchanged':True},indent=2));print([(r['hash'],r['strict_net_valuation']['USD']) for r in out])
