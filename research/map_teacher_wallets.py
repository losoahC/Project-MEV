import json
from pathlib import Path
from collections import defaultdict
from classify_incremental_candidates import receipts
from screen_expanded import net_for
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
wallets=load('exploiter_1_16_and_bot_audit.json')['wallets'];targets=load('全部兑换时间线.json')['rows'];groups=load('all_scope_sandwich_groups.json')['groups'];rings=load('mev_ring_audit.json')['rows'];byblock=defaultdict(list)
for t in targets:byblock[t['block']].append(t)
gmap=defaultdict(set);rmap=defaultdict(set)
for i,g in enumerate(groups):
 for h in g['targets']:gmap[h].add(i)
for r in rings:
 if r['graph_balanced_positive_closed_candidate']:
  for p in r['target_links']:rmap[p['target']].add(r['hash'])
rows=[]
for n,ts in sorted(byblock.items()):
 rs={r['transactionHash']:r for r in receipts(n)}
 for t in ts:
  for w in wallets:
   net={a:str(v) for a,v in net_for(rs[t['hash']],{w['address']}).items() if int(v)}
   if any(int(v)<0 for v in net.values()):rows.append({'wallet_number':w['number'],'address':w['address'],'target':t['hash'],'block':n,'wallet_token_net_raw':net,'sandwich_group_ids':sorted(gmap[t['hash']]),'associated_closed_rings':sorted(rmap[t['hash']])})
summary=[]
for w in wallets:
 rr=[r for r in rows if r['wallet_number']==w['number']];summary.append({**w,'token_net_out_target_count':len(rr),'sandwich_groups':len({g for r in rr for g in r['sandwich_group_ids']}),'associated_closed_rings':len({h for r in rr for h in r['associated_closed_rings']})})
out={'method':'Per-wallet ERC20/WETH net-out within existing 1352 target universe; not complete transaction history or native-only attribution. Group and ring links are associations. Do not sum wallet counts without transaction deduplication. No allocation of aggregate shortfall to individual wallets.','wallets':summary,'rows':rows};(R/'teacher_wallet_target_matrix.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
