"""Validate sequential EVM execution against every actual receipt before inference."""
import argparse, gzip, json, subprocess, time
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):
 d=json.loads(gzip.decompress(p.read_bytes()));return d.get('result',d) if isinstance(d,dict) else d
def header(n):
 for p in [R/'window_raw'/f'{n}_block.json.gz',R/'full_headers_raw'/f'{n}.json.gz',R/'wallet_header_raw'/f'{n}.json.gz']:
  if p.exists():
   b=read(p)
   if not b['transactions'] or isinstance(b['transactions'][0],dict):return b
 raise FileNotFoundError(n)
def txcall(t):
 keys=['from','to','gas','value','input','nonce','accessList','authorizationList','maxFeePerBlobGas','blobVersionedHashes']
 keys+=['maxFeePerGas','maxPriorityFeePerGas'] if 'maxFeePerGas' in t else ['gasPrice']
 return {k:t[k] for k in keys if k in t}
def main():
 p=argparse.ArgumentParser();p.add_argument('--block',type=int,default=26301609);a=p.parse_args();n=a.block;b=header(n)
 override={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()}
 req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':override,'calls':[txcall(t) for t in b['transactions']]}],'validation':True,'traceTransfers':False},hex(n-1)]}
 cache=R/'evm_replay_raw';cache.mkdir(exist_ok=True);path=cache/f'{n}_baseline.json.gz'
 if path.exists() and 'error' in read(path)['response']:
  path.rename(path.with_name(path.name+'.error_'+str(time.time_ns())))
 if path.exists():resp=read(path)['response']
 else:
  run=subprocess.run(['curl','--silent','--show-error','--max-time','55','-H','Content-Type: application/json','--data-binary','@-','https://eth.drpc.org'],input=json.dumps(req),text=True,capture_output=True,check=True)
  resp=json.loads(run.stdout);path.write_bytes(gzip.compress(json.dumps({'request':req,'response':resp}).encode()))
 if 'error' in resp:print(resp);return
 from audit_active_wallet_history import receipt_block
 receipts=receipt_block(n);actual={r['transactionHash']:r for r in receipts};calls=resp['result'][0]['calls'];rows=[]
 def logs(ls):return [(l['address'].lower(),l['topics'],l['data']) for l in ls]
 for t,s in zip(b['transactions'],calls):
  r=actual[t['hash']];rows.append({'hash':t['hash'],'status_match':r['status']==s['status'],'gas_match':r['gasUsed']==s['gasUsed'],'logs_match':logs(r['logs'])==logs(s['logs']),'actual_gas':r['gasUsed'],'simulated_gas':s['gasUsed']})
 out={'block':n,'transactions':len(b['transactions']),'simulated_calls':len(calls),'all_receipts_match':len(calls)==len(b['transactions']) and all(all(r[k] for k in ['status_match','gas_match','logs_match']) for r in rows),'rows':rows,'limits':'Receipt reproduction validates transaction status, gas and ordered event logs, not complete state root or consensus-level withdrawal/system transitions.'}
 (R/f'evm_baseline_{n}.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});print('mismatches',[r for r in rows if not all(r[k] for k in ['status_match','gas_match','logs_match'])][:8])
if __name__=='__main__':main()
