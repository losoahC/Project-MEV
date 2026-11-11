"""Resumable fixed-transaction interventions; preserve failures and exclusions."""
import argparse,json,gzip,subprocess,time
from decimal import Decimal as D
from simulate_historical_block import R,read,header,txcall
from screen_expanded import net_for,WETH
def simulate(req,path):
 if path.exists():
  artifact=read(path)
  assert artifact['request']==req,'Cached request differs from requested experiment'
  cached=artifact['response']
  if 'result' in cached:return cached
  backup=path.with_name(path.name+'.error_'+str(time.time_ns()))
  path.rename(backup)
 time.sleep(.2)
 p=subprocess.run(['curl','--silent','--show-error','--max-time','55','-H','Content-Type: application/json','--data-binary','@-','https://eth.drpc.org'],input=json.dumps(req),text=True,capture_output=True,check=True)
 res=json.loads(p.stdout);path.write_bytes(gzip.compress(json.dumps({'request':req,'response':res}).encode()));return res
def main():
 p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=20);args=p.parse_args();outpath=R/'expanded_EVM_attribution.json';previous=json.loads(outpath.read_text()) if outpath.exists() else {'rows':[]};done={(r['hash'],r['removed_target']):r for r in previous['rows']};excluded=[];cases=[]
 for r in json.loads((R/'standalone_ring_raw_replay.json').read_text())['rows']:
  if not r['same_block_opposite_link']:continue
  try:b=header(r['block'])
  except FileNotFoundError:excluded.append({'hash':r['hash'],'block':r['block'],'reason':'missing_full_header'});continue
  ts=b['transactions'];idx={t['hash']:i for i,t in enumerate(ts)};i=idx[r['hash']]
  for h in sorted({l['target'] for l in r['target_links'] if l['block_distance']==0 and l['opposite_amount0']}):
   j=idx.get(h)
   reason='target_not_preceding' if j is None or j>=i else 'subsequent_target_sender_nonce' if any(t['from']==ts[j]['from'] for t in ts[j+1:i+1]) else None
   if reason:excluded.append({'hash':r['hash'],'removed_target':h,'reason':reason});continue
   cases.append((r,h))
 processed=0
 def save():
  out={'method':'Each same-block opposite-pool linked target is removed separately from full prefix with all other call parameters unchanged, validation=true and historical block overrides. Baseline status/gas/logs through evaluated actor must match; later block mismatches are explicitly outside the evaluated prefix. Original actor cashflow must independently match raw-trace ledger. Separate interventions overlap and must not be summed as event-wide causal profit. No optimization or attribution to beneficial owners.','eligible_experiments':len(cases),'excluded':excluded,'rows':list(done.values())};outpath.write_text(json.dumps(out,indent=2))
 for r,h in cases:
  key=(r['hash'],h)
  if key in done and done[key]['status']!='unresolved':continue
  if key in done and 'insufficient funds for gas * price + value' in done[key].get('error',''):continue
  if processed>=args.limit:break
  n=r['block'];row={'block':n,'hash':r['hash'],'removed_target':h,'accounts':r['accounts']}
  try:
   baseline=R/f'evm_baseline_{n}.json'
   if not baseline.exists():
    result=subprocess.run(['python3',str(R/'simulate_historical_block.py'),'--block',str(n)],capture_output=True,text=True,timeout=65)
    if result.returncode or not baseline.exists():raise RuntimeError('baseline failed: '+result.stdout[-500:]+result.stderr[-500:])
   b=header(n);i=next(i for i,t in enumerate(b['transactions']) if t['hash']==r['hash']);prefix=b['transactions'][:i+1]
   validation=json.loads(baseline.read_text());assert len(validation['rows'])>=len(prefix) and all(all(x[k] for k in ['status_match','gas_match','logs_match']) for x in validation['rows'][:i+1]),'baseline receipt mismatch within evaluated prefix'
   row['baseline_scope']='whole_block' if validation['all_receipts_match'] else 'prefix_through_actor_only'
   overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={}
   for name in ['actual','remove_target']:
    ts=[t for t in prefix if name=='actual' or t['hash']!=h]
    req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'blockOverrides':overrides,'calls':[txcall(t) for t in ts]}],'validation':True,'traceTransfers':True},hex(n-1)]}
    suffix='actual' if name=='actual' else h[2:];path=R/'evm_replay_raw'/f'{n}_{r["hash"][2:]}_{suffix}.json.gz';res=simulate(req,path)
    if 'error' in res:raise RuntimeError(str(res['error']))
    cs=res['result'][0]['calls'];assert len(cs)==len(ts);c=cs[-1];t=ts[-1];net={k:int(v) for k,v in net_for(c,set(r['accounts'])).items()};native=net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0);weth=net.pop(WETH,0);gas=int(c['gasUsed'],16)*int(t['gasPrice'],16)
    scenarios[name]={'status':c['status'],'error':c.get('error'),'net_ETH_after_gas':str(D(native+weth-gas)/10**18),'gas_wei':str(gas),'other_token_residual_raw':{k:str(v) for k,v in net.items()},'failed_hashes':[t['hash'] for t,c in zip(ts,cs) if c['status']=='0x0']}
   assert D(scenarios['actual']['net_ETH_after_gas'])==D(r['net_ETH_after_gas']),'actual native cashflow mismatch';assert not scenarios['actual']['other_token_residual_raw'],'actual inventory mismatch'
   row.update(status='verified_fixed_transaction_intervention',scenarios=scenarios,cashflow_difference_ETH=str(D(scenarios['actual']['net_ETH_after_gas'])-D(scenarios['remove_target']['net_ETH_after_gas'])),counterfactual_inventory_closed=not scenarios['remove_target']['other_token_residual_raw'])
  except Exception as e:row.update(status='unresolved',error=str(e))
  done[key]=row;processed+=1;save();print(processed,n,row['status'],row.get('cashflow_difference_ETH',row.get('error')),flush=True)
 save()
if __name__=='__main__':main()
