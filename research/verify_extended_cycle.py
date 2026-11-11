import json
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from classify_incremental_candidates import receipts,traces
from rawtrace_native import parse
from screen_expanded import net_for
from identify_mev import WETH
R=Path(__file__).resolve().parent;E=D(10)**18
out=[]
for g in json.loads((R/'cross_block_cycles_50000_10000.json').read_text())['groups']:
 accounts=set(g['accounts']);legset=set(g['legs']);activities=[];wallet=None
 for n in range(g['start_block'],g['end_block']+1):
  rs=receipts(n);tt=defaultdict(list)
  for t in traces(n):
   if t.get('transactionHash'):tt[t['transactionHash']].append(t)
  for r in rs:
   idx=int(r['transactionIndex'],16)
   if n==g['start_block'] and idx<g['start_index'] or n==g['end_block'] and idx>g['end_index']:continue
   h=r['transactionHash']
   if h==g['legs'][0]:wallet=r['from']
   # Sender is explicitly derived from first leg; public router is never a wallet identity.
   if wallet is None:continue
   net=net_for(r,{wallet});hit=r['from']==wallet or bool(net)
   if not hit:
    hit=any(wallet in {t.get('action',{}).get(k) for k in ['from','to','address','refundAddress']} for t in tt[h])
   if not hit:continue
   nr=parse(h,tt[h]);native=D(nr['native_net_wei'].get(wallet,'0'))/E;gas=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/E if r['from']==wallet else D(0)
   if not net and not native and not gas:continue
   activities.append({'hash':h,'block':n,'index':idx,'is_candidate_leg':h in legset,'wallet':wallet,'native_ETH':str(native),'token_net_raw':net,'gas_ETH':str(gas),'cashflow_ETH_WETH':str(native+D(net.get(WETH,'0'))/E-gas)})
 net=defaultdict(int)
 for a in activities:
  for t,x in a['token_net_raw'].items():net[t]+=int(x)
 other={t:str(x) for t,x in net.items() if t!=WETH and x};cash=sum((D(a['cashflow_ETH_WETH']) for a in activities),D(0));intervening=[a for a in activities if not a['is_candidate_leg']]
 out.append({**g,'wallet_only_accounts':[wallet],'wallet_interval_activities':activities,'intervening_economic_transactions':len(intervening),'wallet_only_other_token_residual':other,'wallet_only_net_ETH':str(cash),'verified_wallet_endpoint_closure':not other and cash>0 and not intervening,'causal_MEV_proven':False,'limits':'Full wallet flow scan inside observed interval; does not prove zero starting inventory or causal dependence on hacker target. Public router excluded from wallet balance.'})
(R/'extended_cycle_interval_verification.json').write_text(json.dumps({'rows':out},indent=2));print([(r['wallet_only_net_ETH'],r['wallet_only_other_token_residual'],r['intervening_economic_transactions'],r['verified_wallet_endpoint_closure']) for r in out])
