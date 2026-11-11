import json
from pathlib import Path
from collections import defaultdict
from classify_incremental_candidates import receipts
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 merged={};targets={r['hash'] for r in load('full_swaps.json')['rows']}|{r['hash'] for r in load('pancake_coverage_completion.json')['target_events']}|{r['hash'] for r in load('expanded_scope_details.json')['rows'] if r['category']=='pool_swap_compatible'}
 for source,rows in [('original',load('full_pool_events.json')),('pancake',load('pancake_coverage_completion.json')['pool_activity']),('later',load('late_candidate_completion.json')['pool_activity'])]:
  for r in rows:
   d=merged.setdefault(r['hash'],{'hash':r['hash'],'block':r['block'],'target':r['hash'] in targets,'pool_events':[]})
   if 'index' in r:d['index']=r['index']
   es=r.get('pool_events',r.get('events',[]));seen={(e['pool'],e['log_index']) for e in d['pool_events']}
   for e in es:
    e=dict(e)
    if source=='pancake':e['pool']='PancakeV3:'+e['pool']
    if (e['pool'],e['log_index']) not in seen:d['pool_events'].append(e);seen.add((e['pool'],e['log_index']))
 byblock=defaultdict(list)
 for r in merged.values():
  if 'index' not in r:byblock[r['block']].append(r)
 for n,rs in byblock.items():
  indices={r['transactionHash']:int(r['transactionIndex'],16) for r in receipts(n)}
  for r in rs:r['index']=indices[r['hash']]
 rows=sorted(merged.values(),key=lambda r:(r['block'],r['index']));ts=[r for r in rows if r['target']];assert len(ts)==1348
 (R/'all_scope_pool_events.json').write_text(json.dumps(rows));(R/'all_scope_swaps.json').write_text(json.dumps({'method':'Original V2/V3/V4 plus verified original Pancake V3 and later compatible events, unique transaction hashes. Order-only four targets excluded from pool-neighbor analysis.','rows':ts},indent=2));print('pool targets',len(ts),'pool transactions',len(rows),flush=True)
if __name__=='__main__':main()
