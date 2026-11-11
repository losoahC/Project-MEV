"""Conservative contiguous operational-boundary inventory closure search."""
import json,argparse
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--blocks',type=int,default=5);parser.add_argument('--legs',type=int,default=50);args=parser.parse_args()
 rows=load('candidate_classification.json')['rows']+load('incremental_candidate_classification.json')['rows'];by=defaultdict(list)
 used={l['hash'] for g in load('all_scope_sandwich_groups.json')['groups'] for l in g['legs']}|{r['hash'] for r in load('standalone_ring_raw_replay.json')['rows']}
 for r in rows:by[tuple(sorted(r['operational_boundary']))].append(r)
 results=[]
 def eligible(r):return r['hash'] not in used and not any([r['liquidity_events'],r['debt_events'],r['nft_event_present'],r['unresolved_events'],r['external_funding_addresses']])
 for boundary,rs in by.items():
  rs.sort(key=lambda r:(r['block'],r['index']))
  for i,start in enumerate(rs):
   if not eligible(start) or not start['other_token_net_raw']:continue
   net=defaultdict(int);cash=D(0);legs=[]
   for r in rs[i:i+args.legs]:
    if r['block']-start['block']>args.blocks or not eligible(r):break
    legs.append(r['hash']);cash+=D(r['operational_cashflow_ETH'])
    for a,v in r['other_token_net_raw'].items():net[a]+=int(v)
    if len(legs)>1 and not any(net.values()):
     if cash>0 and r['block']>start['block']:
      results.append({'accounts':list(boundary),'start_block':start['block'],'start_index':start['index'],'end_block':r['block'],'end_index':r['index'],'legs':legs.copy(),'net_ETH_after_gas':str(cash),'status':'endpoint_inventory_closure_candidate'});used.update(legs)
     break
 out={'scope':'Search all 16491 classified candidates; identical operational address boundary; consecutive transactions within boundary; maximum blocks and legs recorded in output metadata. Excludes existing sandwich legs and standalone closed cycles. Stops at recognized positions, unresolved events and external funding. Does not infer ownership or causal profit. Complete noncandidate activity within interval must be checked separately.','maximum_blocks':args.blocks,'maximum_legs':args.legs,'groups':results,'count':len(results),'net_ETH':str(sum((D(r['net_ETH_after_gas']) for r in results),D(0)))}
 (R/('cross_block_cycle_candidates.json' if args.blocks==5 and args.legs==50 else f'cross_block_cycles_{args.blocks}_{args.legs}.json')).write_text(json.dumps(out,indent=2));print('groups',out['count'],'netETH',out['net_ETH'])
if __name__=='__main__':main()
