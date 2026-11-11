import json,gzip
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
from value_inventory_ledger import token_value,HEAD
R=Path(__file__).resolve().parent
SWAP='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822';SYNC='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'
def main():
 groups=json.loads((R/'sandwich_structure_groups.json').read_text())['groups'];meta=json.loads((R/'target_v2_fee_accounting.json').read_text())['pools'];cache={};rows=[];seen=set()
 def swap(r,pool):
  ls=[l for l in r['logs'] if l['address']==pool and l['topics'][0]==SWAP]
  if len(ls)!=1:return None
  l=ls[0];w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];ss=[z for z in r['logs'] if z['address']==pool and z['topics'][0]==SYNC and int(z['logIndex'],16)<int(l['logIndex'],16)]
  if not ss:return None
  s=ss[-1];after=[int(s['data'][i:i+64],16) for i in range(2,len(s['data']),64)];before=[after[j]-w[j]+w[j+2] for j in [0,1]];j=0 if w[0]>0 and w[1]==0 and w[2]==0 else 1 if w[1]>0 and w[0]==0 and w[3]==0 else None
  if j is None:return None
  actual=w[3-j];pred=w[j]*997*before[1-j]//(before[j]*1000+w[j]*997)
  if actual!=pred:return None
  return {'input_side':j,'input':w[j],'output':actual,'before':before,'after':after,'log_index':int(l['logIndex'],16)}
 for gi,g in enumerate(groups):
  for link in g['links']:
   if not link['pool'].startswith('V2:'):continue
   key=(link['target'],link['pool'])
   if key in seen:continue
   seen.add(key);pool=link['pool'][3:];n=g['block'];row={'group':gi,'block':n,'target':link['target'],'pool':pool}
   if not meta.get(pool,{}).get('verified_uniswap_v2'):row['status']='unverified_pool';rows.append(row);continue
   if n not in cache:
    folder='window_raw' if n<=26301940 else 'extension_raw';cache[n]=json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))
   rs=cache[n];byindex={int(r['transactionIndex'],16):r for r in rs};front=byindex[link['front_index']];target=byindex[link['target_index']];f=swap(front,pool);t=swap(target,pool)
   if not f or not t:row['status']='multiple_or_nonstandard_swaps';rows.append(row);continue
   if f['input_side']!=t['input_side'] or f['after']!=t['before']:row['status']='intervening_pool_state_change';rows.append(row);continue
   # Any intervening pool event invalidates simple removal even if reserves cancel.
   between=[l for r in rs if link['front_index']<=int(r['transactionIndex'],16)<=link['target_index'] for l in r['logs'] if l['address']==pool and f['log_index']<int(l['logIndex'],16)<t['log_index'] and l['topics'][0]!=SYNC]
   if between:row['status']='intervening_pool_event';rows.append(row);continue
   j=t['input_side'];x=t['input'];cf=x*997*f['before'][1-j]//(f['before'][j]*1000+x*997);delta=cf-t['output'];asset=token_value(meta[pool][f'token{1-j}'],str(delta),HEAD[n]['timestamp'],5)
   row.update(status='verified_local_fixed_input',front=front['transactionHash'],front_swap=f,target_swap=t,without_front_output_raw=str(cf),actual_target_output_raw=str(t['output']),target_output_reduction_raw=str(delta),output_asset_valuation=asset)
   rows.append(row)
 good=[r for r in rows if r['status']=='verified_local_fixed_input'];priced=[r for r in good if r['output_asset_valuation']['USD'] is not None]
 out={'method':'Local V2 fixed-input counterfactual removes immediate preceding same-direction swap only. Official factory and actual integer output reproduced for front and target. Require exact consecutive reserve state and no intervening pool event. Hold target input fixed, so not full multihop/whole-block reexecution, not equilibrium or trader net profit. No sum with cashflow or execution-shortfall totals.','summary':{'links':len(rows),'verified':len(good),'priced':len(priced),'marked_target_output_reduction_USD':str(sum((D(r['output_asset_valuation']['USD']) for r in priced),D(0))),'statuses':dict(Counter(r['status'] for r in rows))},'rows':rows}
 (R/'v2_local_counterfactuals.json').write_text(json.dumps(out,indent=2));print(out['summary'])
if __name__=='__main__':main()
