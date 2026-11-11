import json,gzip,subprocess
from decimal import Decimal as D
from simulate_historical_block import R,read,header,txcall
from screen_expanded import net_for,WETH
def main():
 ledger={r['hash']:r for r in json.loads((R/'standalone_ring_raw_replay.json').read_text())['rows']};rows=[]
 for case in json.loads((R/'two_pool_cycle_counterfactuals.json').read_text())['rows']:
  n=case['block'];h=case['hash'];target=case['scenarios'][0]['removed_target'];r=ledger[h];b=header(n)
  assert json.loads((R/f'evm_baseline_{n}.json').read_text())['all_receipts_match']
  i=next(i for i,t in enumerate(b['transactions']) if t['hash']==h);j=next(i for i,t in enumerate(b['transactions']) if t['hash']==target);prefix=b['transactions'][:i+1]
  assert not any(t['from']==prefix[j]['from'] for t in prefix[j+1:])
  overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={}
  for name in ['actual','remove_target']:
   ts=[t for t in prefix if name=='actual' or t['hash']!=target]
   req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':overrides,'calls':[txcall(t) for t in ts]}],'validation':True,'traceTransfers':True},hex(n-1)]}
   path=R/'evm_replay_raw'/f'{n}_two_pool_{name}.json.gz'
   if path.exists():res=read(path)['response']
   else:
    p=subprocess.run(['curl','--silent','--show-error','--max-time','55','-H','Content-Type: application/json','--data-binary','@-','https://eth.drpc.org'],input=json.dumps(req),capture_output=True,text=True,check=True);res=json.loads(p.stdout);path.write_bytes(gzip.compress(json.dumps({'request':req,'response':res}).encode()))
   if 'error' in res:raise RuntimeError(res)
   calls=res['result'][0]['calls'];assert len(calls)==len(ts);c=calls[-1];t=ts[-1];assert t['hash']==h
   net={k:int(v) for k,v in net_for(c,set(r['accounts'])).items()};native=net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0);weth=net.pop(WETH,0);gas=int(c['gasUsed'],16)*int(t['gasPrice'],16)
   scenarios[name]={'status':c['status'],'error':c.get('error'),'gas_wei':str(gas),'net_ETH_after_gas':str(D(native+weth-gas)/10**18),'other_token_residual_raw':{k:str(v) for k,v in net.items()},'failed_transactions':[t['hash'] for t,c in zip(ts,calls) if c['status']=='0x0']}
  assert D(scenarios['actual']['net_ETH_after_gas'])==D(r['net_ETH_after_gas']);assert not scenarios['actual']['other_token_residual_raw']
  rows.append({'block':n,'hash':h,'removed_target':target,'accounts':r['accounts'],'baseline_all_receipts_match':True,'actual_cashflow_matches_raw_trace_ledger':True,'scenarios':scenarios,'fixed_transaction_cashflow_difference_ETH':str(D(scenarios['actual']['net_ETH_after_gas'])-D(scenarios['remove_target']['net_ETH_after_gas']))})
 out={'method':'Historical full-prefix EVM execution with validation=true, exact original call parameters and block environment. Remove one target; no subsequent nonce from its sender before evaluated actor. All intervening contracts execute normally, including reverts. Gas repriced using unchanged effective gas price. Difference measures a fixed-transaction intervention, not optimal alternative policy or event-wide attributable profit.','rows':rows};(R/'two_pool_full_EVM_counterfactuals.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
