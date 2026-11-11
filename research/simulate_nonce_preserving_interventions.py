"""Separate sensitivity: replace target by a zero-value nonce-consuming transaction.
This is NOT target omission and must never be pooled silently with that experiment.
"""
import json,subprocess
from decimal import Decimal as D
from simulate_historical_block import R,header,txcall
from expand_evm_attribution import simulate
from screen_expanded import net_for,WETH
from audit_active_wallet_history import receipt_block
def main():
 ledger={r['hash']:r for r in json.loads((R/'standalone_ring_raw_replay.json').read_text())['rows']};ex=json.loads((R/'expanded_EVM_attribution.json').read_text())['excluded'];rows=[]
 for item in ex:
  if item['reason']!='subsequent_target_sender_nonce':continue
  h=item['hash'];target=item['removed_target'];r=ledger[h];n=r['block'];row={'hash':h,'target':target,'block':n,'accounts':r['accounts']}
  try:
   b=header(n);i=next(i for i,t in enumerate(b['transactions']) if t['hash']==h);prefix=b['transactions'][:i+1];j=next(i for i,t in enumerate(prefix) if t['hash']==target);original=prefix[j];assert not original.get('authorizationList')
   overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={};rs={x['transactionHash']:x for x in receipt_block(n)}
   for name in ['actual','replace_target_with_nonce_only']:
    calls=[txcall(t) for t in prefix]
    if name!='actual':
     calls[j]={k:v for k,v in calls[j].items() if k in ['from','nonce','gasPrice','maxFeePerGas','maxPriorityFeePerGas']};calls[j].update(to='0x0000000000000000000000000000000000000000',value='0x0',input='0x',gas='0x5208');row['replacement_call']=calls[j]
    req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':overrides,'calls':calls}],'validation':True,'traceTransfers':True},hex(n-1)]};path=R/'evm_replay_raw'/f'{n}_{h[2:]}_nonce_{name}.json.gz';res=simulate(req,path)
    if 'error' in res:raise RuntimeError(str(res['error']))
    cs=res['result'][0]['calls'];assert len(cs)==len(prefix)
    if name=='actual':
     for t,c in zip(prefix,cs):
      a=rs[t['hash']];assert c['status']==a['status'] and c['gasUsed']==a['gasUsed'],'baseline prefix receipt mismatch'
      key=lambda l:(l['address'],l['topics'],l['data']);assert [key(l) for l in c['logs'] if l['address']!='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee']==[key(l) for l in a['logs']]
    else:assert cs[j]['status']=='0x1' and int(cs[j]['gasUsed'],16)==21000,'nonce-only replacement did not execute as expected'
    c=cs[-1];net={k:int(v) for k,v in net_for(c,set(r['accounts'])).items()};cash=net.pop(WETH,0)+net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0)-int(c['gasUsed'],16)*int(prefix[-1]['gasPrice'],16)
    scenarios[name]={'status':c['status'],'error':c.get('error'),'net_ETH_after_gas':str(D(cash)/10**18),'other_token_residual_raw':{k:str(v) for k,v in net.items()}}
   assert D(scenarios['actual']['net_ETH_after_gas'])==D(r['net_ETH_after_gas']);assert not scenarios['actual']['other_token_residual_raw']
   row.update(status='verified_nonce_preserving_sensitivity',scenarios=scenarios,cashflow_difference_ETH=str(D(scenarios['actual']['net_ETH_after_gas'])-D(scenarios['replace_target_with_nonce_only']['net_ETH_after_gas'])))
  except Exception as e:row.update(status='unresolved',error=str(e))
  rows.append(row);out={'method':'Separate sensitivity for cases where outright target omission invalidates later sender nonces. Replace target by zero-value empty-calldata transfer to zero address, same sender/nonce/fee settings, 21000 gas, no authorization list. Preserve all other original calls and historical block environment, validation=true. Changes target fee burden and balances; not equivalent to omission, optimal response, or global causal MEV. Baseline every prefix receipt status/gas/log verified; original actor ledger cashflow verified.','rows':rows};(R/'nonce_preserving_EVM_sensitivity.json').write_text(json.dumps(out,indent=2));print(n,row['status'],row.get('cashflow_difference_ETH',row.get('error')),flush=True)
if __name__=='__main__':main()
