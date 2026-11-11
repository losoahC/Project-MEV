"""Check whether a documented client-specific blockHash override is honored."""
import json
from simulate_historical_block import R,header
from expand_evm_attribution import simulate
def main():
 n=26302728;expected=header(n)['hash'];probe='0x'+format(0xabcdef1234,'040x');code='0x63'+format(n,'08x')+'4060005260206000f3';rows=[]
 for mode in ['default','override_map']:
  override={'number':hex(n+1)}
  if mode=='override_map':override['blockHash']={str(n):expected}
  req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':[{'calls':[]},{'blockOverrides':override,'stateOverrides':{probe:{'code':code}},'calls':[{'to':probe,'gas':'0x186a0'}]}],'validation':False},hex(n-1)]};res=simulate(req,R/'evm_replay_raw'/f'blockhash_probe_v2_{mode}.json.gz');row={'mode':mode,'actual_historical_hash':expected,'error':res.get('error')}
  if 'result' in res:
   returned=res['result'][1]['calls'][0]['returnData'];row.update(generated_prior_hash=res['result'][0]['hash'],queried_BLOCKHASH=returned,returned_historical_hash=returned==expected)
  rows.append(row)
 out={'method':'Read-only injected probe contract executes PUSH4 historical_block_number, BLOCKHASH, MSTORE, RETURN in second simulated block. Tests whether client honors blockHash map override; does not alter real chain.','source':'https://reth.rs/docs/reth/rpc/types/struct.BlockOverrides.html','rows':rows};(R/'simulated_blockhash_capability.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
