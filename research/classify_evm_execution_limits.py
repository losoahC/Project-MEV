"""Separate missing evidence from an invalid fixed transaction sequence."""
import json
from collections import Counter
from simulate_historical_block import R,read
from simulate_historical_block import header,txcall
from audit_active_wallet_history import receipt_block
from screen_expanded import net_for,WETH
from decimal import Decimal as D
def main():
 rows=[];ledger={r['hash']:r for r in json.loads((R/'standalone_ring_raw_replay.json').read_text())['rows']}
 for r in json.loads((R/'expanded_EVM_attribution.json').read_text())['rows']:
  if r['status']!='unresolved':continue
  p=R/'evm_replay_raw'/f"{r['block']}_{r['hash'][2:]}_{r['removed_target'][2:]}.json.gz";a=R/'evm_replay_raw'/f"{r['block']}_{r['hash'][2:]}_actual.json.gz"
  cf=read(p)['response'] if p.exists() else {};actual=read(a)['response'] if a.exists() else {};error=cf.get('error',{})
  category='unresolved_execution_or_data_issue'
  if 'result' in actual and error.get('code')==-38014 and 'insufficient funds' in error.get('message',''):
   category='counterfactual_sequence_infeasible_insufficient_balance'
   # Prove the actual prefix and the single omission, not merely RPC success.
   ar=read(a);cr=read(p);ts=header(r['block'])['transactions'];i=next(i for i,t in enumerate(ts) if t['hash']==r['hash']);ts=ts[:i+1];cs=actual['result'][0]['calls'];assert len(cs)==len(ts);rs={x['transactionHash']:x for x in receipt_block(r['block'])}
   assert ar['request']['params'][0]['blockStateCalls'][0]['calls']==[txcall(t) for t in ts]
   assert cr['request']['params'][0]['blockStateCalls'][0]['calls']==[txcall(t) for t in ts if t['hash']!=r['removed_target']]
   for t,c in zip(ts,cs):
    receipt=rs[t['hash']];assert receipt['status']==c['status'] and receipt['gasUsed']==c['gasUsed'];key=lambda l:(l['address'],l['topics'],l['data']);assert [key(l) for l in receipt['logs']]==[key(l) for l in c['logs'] if l['address']!='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee']
   l=ledger[r['hash']];net={k:int(v) for k,v in net_for(cs[-1],set(l['accounts'])).items()};cash=net.pop(WETH,0)+net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0)-int(cs[-1]['gasUsed'],16)*int(ts[-1]['gasPrice'],16);assert not net;assert D(cash)/10**18==D(l['net_ETH_after_gas'])
  elif 'timeout' in r.get('error','').lower() or 'exit status 56' in r.get('error',''):category='transient_public_endpoint_failure'
  elif 'baseline' in r.get('error',''):category='baseline_not_yet_validated'
  rows.append({'block':r['block'],'hash':r['hash'],'removed_target':r['removed_target'],'category':category,'error':r.get('error'),'actual_prefix_has_result':'result' in actual,'actual_receipts_and_cashflow_independently_verified':category=='counterfactual_sequence_infeasible_insufficient_balance','counterfactual_error':error or None,'profit_difference':None})
 out={'method':'Classification of retained raw RPC responses. Insufficient-balance rejection after a successful actual prefix is evidence that the fixed counterfactual sequence cannot be executed under normal validation; no invented funding, zero-profit imputation or numerical causal estimate. A result alone is not independent actual receipt validation; see main verifier for completed cases.','counts':dict(Counter(r['category'] for r in rows)),'rows':rows};(R/'EVM_execution_limit_classification.json').write_text(json.dumps(out,indent=2));print(out['counts'])
if __name__=='__main__':main()
