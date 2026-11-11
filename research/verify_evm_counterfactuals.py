"""Offline checks of cached EVM responses, independent of report summaries."""
import json
from decimal import Decimal as D
from simulate_historical_block import R,read,header
from screen_expanded import net_for,WETH
def main():
 checks=[]
 for n in [26301609,26302300,26302437]:
  b=header(n);raw=read(R/'evm_replay_raw'/f'{n}_baseline.json.gz');calls=raw['response']['result'][0]['calls'];rs=read(R/('window_raw' if n<=26301940 else 'extension_raw')/f'{n}.json.gz');rs={r['transactionHash']:r for r in rs}
  assert len(calls)==len(b['transactions'])
  for t,c in zip(b['transactions'],calls):
   r=rs[t['hash']];assert r['status']==c['status'] and r['gasUsed']==c['gasUsed']
   assert [(l['address'],l['topics'],l['data']) for l in r['logs']]==[(l['address'],l['topics'],l['data']) for l in c['logs']]
  checks.append({'check':f'block_{n}_all_receipts','transactions':len(calls),'passed':True})
 strong=json.loads((R/'strong_case_full_EVM_counterfactual.json').read_text());two=json.loads((R/'two_pool_full_EVM_counterfactuals.json').read_text())['rows']
 for row,tag in [(strong,'strong')]+[(r,'two_pool') for r in two]:
  n=row['block'];target=row.get('target',row.get('removed_target'));actual=read(R/'evm_replay_raw'/f'{n}_{tag}_actual.json.gz');cf=read(R/'evm_replay_raw'/f'{n}_{tag}_remove_target.json.gz')
  txs=header(n)['transactions'];j=next(i for i,t in enumerate(txs) if t['hash']==target)
  ac=actual['request']['params'][0]['blockStateCalls'][0]['calls'];cc=cf['request']['params'][0]['blockStateCalls'][0]['calls'];assert cc==ac[:j]+ac[j+1:]
  assert actual['request']['params'][0]['validation'] is True and cf['request']['params'][0]['validation'] is True
  for name,raw in [('actual',actual),('remove_target',cf)]:
   ts=[t for t in txs[:len(ac)] if name=='actual' or t['hash']!=target];cs=raw['response']['result'][0]['calls'];assert len(ts)==len(cs)
   selected={l['hash'] for l in row['scenarios'][name]['legs']} if tag=='strong' else {row['hash']};total=0;other={}
   for t,c in zip(ts,cs):
    if t['hash'] not in selected:continue
    net={k:int(v) for k,v in net_for(c,set(row['accounts'])).items()};total+=net.pop(WETH,0)+net.pop('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',0)-int(c['gasUsed'],16)*int(t['gasPrice'],16)
    for k,v in net.items():other[k]=other.get(k,0)+v
   assert D(total)/10**18==D(row['scenarios'][name]['net_ETH_after_gas']);assert {k:str(v) for k,v in other.items() if v}==row['scenarios'][name]['other_token_residual_raw']
  checks.append({'check':f'block_{n}_unchanged_parameters_and_cashflow','passed':True})
 out={'checks':checks,'all_passed':True,'baseline_transactions':sum(x.get('transactions',0) for x in checks)};(R/'evm_counterfactual_validation.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
