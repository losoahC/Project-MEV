import json
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 single=load('standalone_ring_raw_replay.json')['rows'];multi=load('multitx_ring_replay.json')['rows'];positive=[g for g in multi if g['closed_positive_no_recognized_position_events']];evm=load('expanded_EVM_attribution.json');nonce=load('nonce_preserving_EVM_sensitivity.json');brackets=load('bracket_EVM_attribution.json');validation=load('bracket_EVM_validation.json');assert validation['all_completed_claims_verified'] and validation['unique_groups_verified']==111 and validation['counts']['verified_experiments']==117
 sh={r['hash'] for r in single};mh={l['hash'] for g in positive for l in g['legs']};assert not sh&mh
 linked={r['hash'] for r in single if r['same_block_opposite_link']};covered={r['hash'] for r in evm['rows']}|{r['hash'] for r in nonce['rows']};assert linked==covered
 grouped=defaultdict(list)
 for r in brackets['rows']:grouped[r['group_id']].append(r)
 both_success=[];failed=set()
 for g in positive:
  for r in grouped[g['group_id']]:
   cf=r['scenarios'][r['intervention']]
   if all(l['status']=='0x1' for l in cf['legs']) and not cf['other_token_residual_raw']:
    both_success.append({'group_id':g['group_id'],'block':g['block'],'target':r['target'],'actual_net_ETH':g['net_ETH_after_gas'],'counterfactual_net_ETH':cf['net_ETH_after_gas'],'fixed_call_cashflow_difference_ETH':r['cashflow_difference_ETH'],'scope':'Both legs execute and endpoint non-WETH inventory closes; operational boundary, not final owner or unobserved position valuation.'})
   else:failed.add(g['group_id'])
 out={'all_linked_standalone_actors_have_intervention_evidence':True,'linked_standalone_actors':len(linked),'standalone_closed_positive_cashflow_ETH':str(sum((D(r['net_ETH_after_gas']) for r in single),D(0))),'positive_bracket_groups':len(positive),'positive_bracket_cashflow_ETH':str(sum((D(g['net_ETH_after_gas']) for g in positive),D(0))),'standalone_and_bracket_transaction_hashes_disjoint':True,'bracket_groups_with_counterfactual_failed_leg':len(failed),'bracket_both_scenarios_execute_and_endpoint_close':both_success,'interpretation':'Actual cashflow totals describe selected positive closed groups and are not event-wide causal MEV. Standalone 344 linked actors are a subset of 1063. Bracket 117 target experiments cover 111 groups, so never sum intervention differences. Failed counterfactual exits leave economic positions unvalued even if endpoint token transfers net to zero.'};(R/'execution_evidence_summary.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
