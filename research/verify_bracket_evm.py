"""Independently recheck cached bracket interventions and distinguish unfinished exits."""
import json
from collections import Counter
from decimal import Decimal as D
from simulate_historical_block import R,read,header,txcall
from screen_expanded import net_for,WETH
from audit_active_wallet_history import receipt_block
def main():
 data=json.loads((R/'bracket_EVM_attribution.json').read_text());groups={g['group_id']:g for g in json.loads((R/'multitx_ring_replay.json').read_text())['rows']};errors=[];counts=Counter();rows=[]
 for r in data['rows']:
  if r['status']!='verified_fixed_call_cashflow_sensitivity':counts['unresolved']+=1;continue
  try:
   g=groups[r['group_id']];prefix=header(r['block'])['transactions'][:max(l['index'] for l in g['legs'])+1];j=next(i for i,t in enumerate(prefix) if t['hash']==r['target']);rs={a['transactionHash']:a for a in receipt_block(r['block'])};scenarios={}
   for name in ['actual',r['intervention']]:
    suffix='actual' if name=='actual' else r['target'][2:]+'_'+r['intervention'];raw=read(R/'evm_replay_raw'/f'bracket_{r["group_id"]}_{suffix}.json.gz');cs=raw['response']['result'][0]['calls'];chosen=[t for t in prefix if name!='remove_target' or t['hash']!=r['target']];expected=[txcall(t) for t in chosen]
    if name=='replace_target_with_nonce_only':
     expected[j]={k:v for k,v in expected[j].items() if k in ['from','nonce','gasPrice','maxFeePerGas','maxPriorityFeePerGas']};expected[j].update(to='0x'+'0'*40,value='0x0',input='0x',gas='0x5208');assert cs[j]['status']=='0x1' and int(cs[j]['gasUsed'],16)==21000
    params=raw['request']['params'];assert params[0]['validation'] is True and params[1]==hex(r['block']-1);assert params[0]['blockStateCalls'][0]['calls']==expected;assert len(cs)==len(chosen)
    total={};gas=0;leg_status=[]
    for t,c in zip(chosen,cs):
     if name=='actual':
      receipt=rs[t['hash']];assert receipt['status']==c['status'] and receipt['gasUsed']==c['gasUsed'];lk=lambda l:(l['address'],l['topics'],l['data']);assert [lk(l) for l in receipt['logs']]==[lk(l) for l in c['logs'] if l['address']!='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee']
     if t['hash'] not in r['leg_hashes']:continue
     for token,v in net_for(c,set(r['accounts'])).items():total[token]=total.get(token,0)+int(v)
     gas+=int(c['gasUsed'],16)*int(t['gasPrice'],16);leg_status.append(c['status'])
    cash=total.pop(WETH,0)+total.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0)-gas;residual={k:str(v) for k,v in total.items() if v};assert D(cash)/10**18==D(r['scenarios'][name]['net_ETH_after_gas']);assert residual==r['scenarios'][name]['other_token_residual_raw'];scenarios[name]={'cash_wei':cash,'leg_status':leg_status,'token_residual':residual}
   assert D(scenarios['actual']['cash_wei'])/10**18==D(g['net_ETH_after_gas']);diff=scenarios['actual']['cash_wei']-scenarios[r['intervention']]['cash_wei'];assert D(diff)/10**18==D(r['cashflow_difference_ETH'])
   cf=scenarios[r['intervention']];counts[r['intervention']]+=1;counts['positive_cashflow_difference' if diff>0 else 'negative_cashflow_difference' if diff<0 else 'zero_cashflow_difference']+=1
   incomplete=any(s!='0x1' for s in cf['leg_status']);counts['counterfactual_strategy_has_failed_leg' if incomplete else 'counterfactual_all_legs_success']+=1;counts['verified_experiments']+=1
   rows.append({'group_id':r['group_id'],'target':r['target'],'intervention':r['intervention'],'counterfactual_leg_status':cf['leg_status'],'counterfactual_token_residual':cf['token_residual'],'incomplete_strategy_cashflow_not_realized_profit':incomplete,'original_group_net_ETH':g['net_ETH_after_gas']})
  except Exception as e:errors.append({'group_id':r['group_id'],'target':r['target'],'error':repr(e)})
 out={'expected_groups':data['groups_in_scope'],'expected_target_experiments':data['target_experiments'],'attempted':len(data['rows']),'counts':dict(counts),'unique_groups_verified':len({r['group_id'] for r in rows}),'errors':errors,'rows':rows,'all_completed_claims_verified':not errors,'interpretation':'Failed exit prevents interpreting grouped cashflow difference as realized profit difference. Original actual group cashflow can be shown once per group; target sensitivities overlap.'};(R/'bracket_EVM_validation.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});assert not errors
if __name__=='__main__':main()
