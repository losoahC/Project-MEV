"""Fixed signed-call parameters, omit victim, execute unchanged prefix through back leg."""
import json,gzip,subprocess
from decimal import Decimal
from simulate_historical_block import R,read,header,txcall
from screen_expanded import net_for,WETH
def main():
 n=26301609;assert json.loads((R/f'evm_baseline_{n}.json').read_text())['all_receipts_match']
 group=next(r for r in json.loads((R/'multitx_ring_replay.json').read_text())['rows'] if r['group_id']==80)
 b=header(n);target=group['targets'][0];prefix=b['transactions'][:12];removed=next(t for t in prefix if t['hash']==target)
 assert not any(t['from']==removed['from'] for t in prefix[11:]),'Removal leaves a nonce gap'
 overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()}
 scenarios={}
 for name in ['actual','remove_target']:
  ts=[t for t in prefix if name=='actual' or t['hash']!=target]
  req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':overrides,'calls':[txcall(t) for t in ts]}],'validation':True,'traceTransfers':True},hex(n-1)]}
  path=R/'evm_replay_raw'/f'{n}_strong_{name}.json.gz'
  if path.exists():res=read(path)['response']
  else:
   p=subprocess.run(['curl','--silent','--show-error','--max-time','55','-H','Content-Type: application/json','--data-binary','@-','https://eth.drpc.org'],input=json.dumps(req),text=True,capture_output=True,check=True);res=json.loads(p.stdout);path.write_bytes(gzip.compress(json.dumps({'request':req,'response':res}).encode()))
  if 'error' in res:raise RuntimeError(res)
  calls=res['result'][0]['calls'];assert len(calls)==len(ts);legs=[];total={};gas=0
  for t,c in zip(ts,calls):
   if t['hash'] not in [l['hash'] for l in group['legs']]:continue
   net=net_for(c,set(group['accounts']));g=int(c['gasUsed'],16)*int(t['gasPrice'],16);gas+=g
   for token,v in net.items():total[token]=total.get(token,0)+int(v)
   legs.append({'hash':t['hash'],'status':c['status'],'gas_wei':str(g),'net_raw':net,'error':c.get('error')})
  total={k:v for k,v in total.items() if v};native=total.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0);weth=total.pop(WETH,0)
  scenarios[name]={'legs':legs,'net_ETH_after_gas':str(Decimal(native+weth-gas)/10**18),'other_token_residual_raw':{k:str(v) for k,v in total.items()},'all_remaining_statuses':[c['status'] for c in calls]}
 assert scenarios['actual']['net_ETH_after_gas']==group['net_ETH_after_gas'];assert not scenarios['actual']['other_token_residual_raw']
 out={'block':n,'target':target,'accounts':group['accounts'],'baseline_all_146_receipts_match':True,'actual_cashflow_matches_raw_trace_ledger':True,'scenarios':scenarios,'method':'Replay full prefix through back leg from previous-block state, historical block environment, validation=true. Counterfactual removes target only; all remaining calldata, sender, value, nonce, access list and fees unchanged. No subsequent transaction from removed sender in prefix. Synthetic native-transfer logs plus ERC20/WETH logs, less actual simulated gas. This is a fixed-transaction intervention, not optimized strategy or market equilibrium.'}
 (R/'strong_case_full_EVM_counterfactual.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
