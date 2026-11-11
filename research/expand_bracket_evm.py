"""Full-prefix execution for every positive, inventory-closed bracket group.
Results are fixed-call cashflow sensitivities; no claim to residual position value.
"""
import json
from decimal import Decimal as D
from simulate_historical_block import R,header,txcall
from crosscheck_wallet_transaction_nonces import block as fetch_header
from expand_evm_attribution import simulate
from screen_expanded import net_for,WETH
from audit_active_wallet_history import receipt_block
def main():
 groups=[r for r in json.loads((R/'multitx_ring_replay.json').read_text())['rows'] if r['closed_positive_no_recognized_position_events']];p=R/'bracket_EVM_attribution.json';previous=json.loads(p.read_text()) if p.exists() else {'rows':[]};done={(r['group_id'],r['target']):r for r in previous['rows']}
 for g in groups:
  for target in g['targets']:
   key=(g['group_id'],target)
   if key in done and done[key]['status']!='unresolved':continue
   if key in done and 'insufficient funds for gas * price + value' in done[key].get('error',''):continue
   n=g['block'];row={'group_id':g['group_id'],'block':n,'target':target,'accounts':g['accounts'],'leg_hashes':[l['hash'] for l in g['legs']]}
   try:
    b=fetch_header(n);last=max(l['index'] for l in g['legs']);prefix=b['transactions'][:last+1];j=next(i for i,t in enumerate(prefix) if t['hash']==target);original=prefix[j];nonce_dependent=any(t['from']==original['from'] for t in prefix[j+1:]);mode='replace_target_with_nonce_only' if nonce_dependent else 'remove_target';row['intervention']=mode
    assert not original.get('authorizationList') or not nonce_dependent,'Authorization nonce replacement requires separate treatment'
    overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};rs={r['transactionHash']:r for r in receipt_block(n)};scenarios={}
    for name in ['actual',mode]:
     txs=[t for t in prefix if name!='remove_target' or t['hash']!=target];calls=[txcall(t) for t in txs]
     if name=='replace_target_with_nonce_only':
      calls[j]={k:v for k,v in calls[j].items() if k in ['from','nonce','gasPrice','maxFeePerGas','maxPriorityFeePerGas']};calls[j].update(to='0x'+'0'*40,value='0x0',input='0x',gas='0x5208')
     req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':overrides,'calls':calls}],'validation':True,'traceTransfers':True},hex(n-1)]};suffix='actual' if name=='actual' else target[2:]+'_'+mode;path=R/'evm_replay_raw'/f'bracket_{g["group_id"]}_{suffix}.json.gz';res=simulate(req,path)
     if 'error' in res:raise RuntimeError(str(res['error']))
     cs=res['result'][0]['calls'];assert len(cs)==len(txs)
     if name=='actual':
      for t,c in zip(txs,cs):
       r=rs[t['hash']];assert r['status']==c['status'] and r['gasUsed']==c['gasUsed'],'baseline prefix status/gas mismatch';lk=lambda l:(l['address'],l['topics'],l['data']);assert [lk(l) for l in r['logs']]==[lk(l) for l in c['logs'] if l['address']!='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'],'baseline prefix logs mismatch'
     if name=='replace_target_with_nonce_only':assert cs[j]['status']=='0x1' and int(cs[j]['gasUsed'],16)==21000
     total={};gas=0;legs=[]
     for t,c in zip(txs,cs):
      if t['hash'] not in row['leg_hashes']:continue
      net=net_for(c,set(g['accounts']));gg=int(c['gasUsed'],16)*int(t['gasPrice'],16);gas+=gg
      for token,v in net.items():total[token]=total.get(token,0)+int(v)
      legs.append({'hash':t['hash'],'status':c['status'],'error':c.get('error'),'gas_wei':str(gg),'net_raw':net})
     assert len(legs)==len(g['legs']);native=total.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0);weth=total.pop(WETH,0);scenarios[name]={'legs':legs,'net_ETH_after_gas':str(D(native+weth-gas)/10**18),'other_token_residual_raw':{k:str(v) for k,v in total.items() if v}}
    assert D(scenarios['actual']['net_ETH_after_gas'])==D(g['net_ETH_after_gas']);assert not scenarios['actual']['other_token_residual_raw'];row.update(status='verified_fixed_call_cashflow_sensitivity',scenarios=scenarios,cashflow_difference_ETH=str(D(scenarios['actual']['net_ETH_after_gas'])-D(scenarios[mode]['net_ETH_after_gas'])))
   except Exception as e:row.update(status='unresolved',error=str(e))
   done[key]=row;out={'groups_in_scope':len(groups),'target_experiments':sum(len(g['targets']) for g in groups),'method':'All positive inventory-closed bracketing groups, each target intervened separately. Actual full prefix receipts and grouped leg cashflow must match. Omit target unless subsequent sender nonce requires explicitly labeled zero-value nonce-only replacement (same fees, 21000 gas). Remaining calldata and block environment unchanged. Evaluate combined leg cashflows, NOT mark-to-market residual pool positions, beneficial ownership or optimized alternatives. Overlapping interventions cannot be added.','rows':list(done.values())};p.write_text(json.dumps(out,indent=2));print(len(done),g['group_id'],row['status'],row.get('cashflow_difference_ETH',row.get('error')),flush=True)
if __name__=='__main__':main()
