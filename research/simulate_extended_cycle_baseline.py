"""Test multiblock EVM baseline for the independently verified six-block cycle."""
import json,argparse
from simulate_historical_block import R,header,txcall
from expand_evm_attribution import simulate
from audit_active_wallet_history import receipt_block
from crosscheck_wallet_transaction_nonces import block as fetch_header
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--last-block',type=int,default=26302735);parser.add_argument('--withdrawals',action='store_true');parser.add_argument('--historical-hashes',action='store_true');args=parser.parse_args()
 sell='0xc1f4442a5de3c70625a46ba4d0b6b1576b4305b047e32c0f9a83dac9d23a4803';start=26302728;end=args.last_block;blocks=[];txlists=[]
 for n in range(start,end+1):
  b=fetch_header(n);ts=b['transactions'];ts=ts[:next(i for i,t in enumerate(ts) if t['hash']==sell)+1] if n==26302735 else ts
  overrides={k:b[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()}
  if args.withdrawals:overrides['withdrawals']=b['withdrawals']
  if args.historical_hashes:overrides['blockHash']={str(k):header(k)['hash'] for k in range(start,n)}
  blocks.append({'blockOverrides':overrides,'calls':[txcall(t) for t in ts]});txlists.append(ts)
 suffix='' if end==26302735 else '_to_'+str(end)
 if args.withdrawals:suffix+='_with_withdrawals'
 if args.historical_hashes:suffix+='_historical_hashes'
 req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':[{'blockStateCalls':blocks,'validation':True,'traceTransfers':False},hex(start-1)]};res=simulate(req,R/'evm_replay_raw'/f'extended_cycle_multiblock_baseline{suffix}.json.gz');out={'first_block':start,'last_block':end,'transactions':sum(map(len,txlists)),'method':'Consecutive simulated blocks from historical parent state; actual block overrides. Final exit block stops at exit leg. Checks receipts, not consensus state root.','error':res.get('error'),'mismatches':[]}
 if 'result' in res:
  assert len(res['result'])==len(blocks)
  for n,ts,sim in zip(range(start,end+1),txlists,res['result']):
   rs={r['transactionHash']:r for r in receipt_block(n)};assert len(sim['calls'])==len(ts)
   for t,c in zip(ts,sim['calls']):
    r=rs[t['hash']];key=lambda l:(l['address'],l['topics'],l['data']);checks={'status':c['status']==r['status'],'gas':c['gasUsed']==r['gasUsed'],'logs':[key(l) for l in c['logs']]==[key(l) for l in r['logs']]}
    if not all(checks.values()):out['mismatches'].append({'block':n,'hash':t['hash'],'checks':checks,'actual_gas':r['gasUsed'],'simulated_gas':c['gasUsed']})
 out['all_receipts_match']='result' in res and not out['mismatches'];(R/f'extended_cycle_multiblock_EVM_baseline{suffix}.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
