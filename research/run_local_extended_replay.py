"""Run retained read-only simulation against a loopback-only historical Anvil fork."""
import json,gzip,urllib.request,time
from simulate_historical_block import R,read,header
from audit_active_wallet_history import receipt_block
def main():
 req=read(R/'evm_replay_raw/extended_cycle_multiblock_baseline_with_withdrawals_historical_hashes.json.gz')['request']
 for b in req['params'][0]['blockStateCalls']:
  override=b['blockOverrides'];override.pop('withdrawals',None);n=int(override['number'],16);prices={r['blobGasPrice'] for r in receipt_block(n) if 'blobGasPrice' in r}
  if not prices:
   assert n==26302734 and header(n)['excessBlobGas']==header(n+1)['excessBlobGas'];prices={r['blobGasPrice'] for r in receipt_block(n+1) if 'blobGasPrice' in r}
  assert len(prices)==1;override['blobBaseFee']=next(iter(prices))
 endpoint='http://127.0.0.1:18545';started=time.time();out={'endpoint':endpoint,'anvil_version':'1.9.0','request':req,'adapter_limitation':'Anvil block overrides do not include withdrawals; omit them and validate actual receipts before inference. Historical blobBaseFee comes from actual blob receipts; block 26302734 shares excessBlobGas with 26302735. Consensus balances are not claimed reproduced.'}
 print('Starting loopback historical simulation; no real-chain transactions are submitted.',flush=True)
 try:
  q=urllib.request.Request(endpoint,data=json.dumps(req).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(q,timeout=1800) as response:out['response']=json.load(response)
 except Exception as e:out['transport_error']=str(e)
 out['elapsed_seconds']=time.time()-started;path=R/'evm_replay_raw/extended_cycle_local_anvil_v190_baseline.json.gz'
 if path.exists():path.rename(path.with_name(path.name+'.previous_'+str(time.time_ns())))
 path.write_bytes(gzip.compress(json.dumps(out).encode()));res=out.get('response',{});summary={'error':res.get('error'),'transport_error':out.get('transport_error'),'elapsed_seconds':out['elapsed_seconds'],'adapter_limitation':out['adapter_limitation'],'mismatches':[],'compared_transactions':0}
 if 'result' in res:
  assert len(res['result'])==len(req['params'][0]['blockStateCalls'])
  for block,sim in zip(req['params'][0]['blockStateCalls'],res['result']):
   n=int(block['blockOverrides']['number'],16);ts=header(n)['transactions'][:len(block['calls'])];rs={r['transactionHash']:r for r in receipt_block(n)};assert len(sim['calls'])==len(ts)
   for t,c in zip(ts,sim['calls']):
    r=rs[t['hash']];key=lambda l:(l['address'],l['topics'],l['data']);checks={'status':c['status']==r['status'],'gas':c['gasUsed']==r['gasUsed'],'logs':[key(l) for l in c['logs']]==[key(l) for l in r['logs']]};summary['compared_transactions']+=1
    if not all(checks.values()):summary['mismatches'].append({'block':n,'hash':t['hash'],'checks':checks,'actual_gas':r['gasUsed'],'simulated_gas':c['gasUsed']})
 summary['all_receipts_match']=summary['compared_transactions']==1851 and not summary['mismatches'];(R/'extended_cycle_local_EVM_baseline.json').write_text(json.dumps(summary,indent=2));print({k:v for k,v in summary.items() if k!='mismatches'},'mismatches',len(summary['mismatches']),flush=True)
if __name__=='__main__':main()
