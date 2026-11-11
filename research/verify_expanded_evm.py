import json
from decimal import Decimal as D
from collections import Counter
from simulate_historical_block import R,read,header,txcall
from screen_expanded import net_for,WETH
from audit_active_wallet_history import receipt_block
def main():
 data=json.loads((R/'expanded_EVM_attribution.json').read_text());counts=Counter();errors=[];checked=0;blocks=set();actual_hashes=set()
 for row in data['rows']:
  if row['status']!='verified_fixed_transaction_intervention':counts['unresolved']+=1;continue
  try:
   n=row['block'];h=row['hash'];target=row['removed_target'];ts=header(n)['transactions'];i=next(i for i,t in enumerate(ts) if t['hash']==h);prefix=ts[:i+1];rs={r['transactionHash']:r for r in receipt_block(n)}
   baseline=json.loads((R/f'evm_baseline_{n}.json').read_text());assert len(baseline['rows'])>=len(prefix) and all(all(x[k] for k in ['status_match','gas_match','logs_match']) for x in baseline['rows'][:i+1]);blocks.add(n)
   for name in ['actual','remove_target']:
    suffix='actual' if name=='actual' else target[2:];raw=read(R/'evm_replay_raw'/f'{n}_{h[2:]}_{suffix}.json.gz');params=raw['request']['params'];assert params[0]['validation'] is True and params[1]==hex(n-1)
    chosen=[t for t in prefix if name=='actual' or t['hash']!=target];assert params[0]['blockStateCalls'][0]['calls']==[txcall(t) for t in chosen];cs=raw['response']['result'][0]['calls'];assert len(cs)==len(chosen)
    if name=='actual':
     for t,c in zip(chosen,cs):
      r=rs[t['hash']];assert r['status']==c['status'] and r['gasUsed']==c['gasUsed'];actual_hashes.add(t['hash'])
      key=lambda l:(l['address'],l['topics'],l['data'])
      assert [key(l) for l in r['logs']]==[key(l) for l in c['logs'] if l['address']!='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee']
    c=cs[-1];t=chosen[-1];net={k:int(v) for k,v in net_for(c,set(row['accounts'])).items()};cash=net.pop(WETH,0)+net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0)-int(c['gasUsed'],16)*int(t['gasPrice'],16)
    assert D(cash)/10**18==D(row['scenarios'][name]['net_ETH_after_gas']);assert {k:str(v) for k,v in net.items()}==row['scenarios'][name]['other_token_residual_raw']
   diff=D(row['scenarios']['actual']['net_ETH_after_gas'])-D(row['scenarios']['remove_target']['net_ETH_after_gas']);assert diff==D(row['cashflow_difference_ETH'])
   counts['positive_difference' if diff>0 else 'negative_difference' if diff<0 else 'zero_difference']+=1;counts['counterfactual_revert' if row['scenarios']['remove_target']['status']=='0x0' else 'counterfactual_success']+=1;checked+=1
  except Exception as e:errors.append({'hash':row['hash'],'target':row['removed_target'],'error':repr(e)})
 out={'eligible_experiments':data['eligible_experiments'],'completed_rows':len(data['rows']),'verified_experiments':checked,'verified_blocks':len(blocks),'unique_actual_prefix_transactions_checked':len(actual_hashes),'counts':dict(counts),'errors':errors,'all_completed_claims_verified':not errors,'warning':'Interventions can share transactions/targets and are not additive event-wide profit.'};(R/'expanded_EVM_validation.json').write_text(json.dumps(out,indent=2));print(out);assert not errors
if __name__=='__main__':main()
