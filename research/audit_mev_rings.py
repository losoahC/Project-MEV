"""Audit complete token flow graphs, not merely one cycle returned by DFS."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal as D
R=Path(__file__).resolve().parent
W='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
def load(n):return json.loads((R/n).read_text())
def main():
 candidates={}
 for f,k in [('full_candidates.json','rows'),('pancake_coverage_completion.json','candidates'),('late_candidate_completion.json','rows')]:
  for c in load(f)[k]:
   if c['hash'] not in candidates:candidates[c['hash']]=dict(c)
   else:candidates[c['hash']]['prior_targets']=candidates[c['hash']].get('prior_targets',[])+c.get('prior_targets',[])
 groups=load('all_scope_sandwich_groups.json')['groups'];members=defaultdict(list)
 for i,g in enumerate(groups):
  for l in g['legs']:members[l['hash']].append(i)
 rows=[]
 for f in ['candidate_classification.json','incremental_candidate_classification.json']:
  for r in load(f)['rows']:
   edges=r.get('pool_flow_edges',[])
   if not edges:continue
   adj=defaultdict(set);balance=defaultdict(int)
   for e in edges:
    a,b=e['input_token'],e['output_token'];adj[a].add(b);balance[a]-=int(e['input_raw']);balance[b]+=int(e['output_raw'])
   def reaches(a,b):
    seen=set();stack=[a]
    while stack:
     x=stack.pop()
     if x==b:return True
     if x not in seen:seen.add(x);stack.extend(adj[x]-seen)
    return False
   cyc=[e for e in edges if reaches(e['output_token'],e['input_token'])]
   if not cyc:continue
   c=candidates[r['hash']];c['prior_targets']=[dict(p,target=p.get('target',p.get('hash'))) for p in c.get('prior_targets',[])];links=list({(p['target'],p['pool'],p['block_distance'],p.get('opposite_amount0')):p for p in c.get('prior_targets',[])}.values())
   residual={a:str(n) for a,n in balance.items() if a!=W and n}
   strong=r['category']=='strong_closed_cycle_evidence'
   rows.append({'hash':r['hash'],'block':r['block'],'sender':c.get('from'),'execution_contract':c.get('to'),'category':r['category'],'operational_boundary':r['operational_boundary'],'all_pool_flow_edges':edges,'cycle_edge_count':len(cyc),'edge_count':len(edges),'all_edges_in_directed_cycles':len(cyc)==len(edges),'non_WETH_pool_flow_residual_raw':residual,'pool_flow_WETH_surplus_raw':str(balance[W]),'operational_net_ETH_after_gas':r['operational_cashflow_ETH'],'gas_ETH':r['gas_ETH'],'target_links':links,'same_block_opposite_link':any(p['block_distance']==0 and p.get('opposite_amount0') is True for p in links),'sandwich_group_ids':members[r['hash']],'graph_balanced_positive_closed_candidate':strong and not residual and len(cyc)==len(edges) and balance[W]>0,'flash_event_present':r.get('flash_event_present',False),'caveat':'Pool edges are aggregate transfer evidence, not chronological allocation of capital. Operational address boundary is not ownership. Target links are association, not proof of causal profit.'})
 accepted=[r for r in rows if r['graph_balanced_positive_closed_candidate']];disjoint=[r for r in accepted if not r['sandwich_group_ids']]
 bots=defaultdict(lambda:{'count':0,'net_ETH':D(0)})
 for r in disjoint:bots[r['sender']]['count']+=1;bots[r['sender']]['net_ETH']+=D(r['operational_net_ETH_after_gas'])
 stats={'transactions_with_graph_cycle':len(rows),'previous_strong_class_in_cycle_rows':sum(r['category']=='strong_closed_cycle_evidence' for r in rows),'all_edges_cyclic_nonWETH_balanced_positive':len(accepted),'accepted_with_same_block_opposite_target':sum(r['same_block_opposite_link'] for r in accepted),'accepted_overlapping_sandwich_legs':len(accepted)-len(disjoint),'accepted_outside_sandwich_legs':len(disjoint),'outside_sandwich_operational_net_ETH':str(sum((D(r['operational_net_ETH_after_gas']) for r in disjoint),D(0))),'flash_event_cycle_rows':sum(r['flash_event_present'] for r in rows)}
 out={'method':'Independent whole graph cycle-membership and per-token raw amount conservation audit. No global MEV claim. Non-WETH residual exclusion is conservative; fees/rebases/transfers can explain residuals. Excludes all sandwich legs from standalone sum to prevent double counting.','summary':stats,'bots_outside_sandwich':[{'sender':a,'count':v['count'],'net_ETH':str(v['net_ETH'])} for a,v in sorted(bots.items(),key=lambda x:x[1]['net_ETH'],reverse=True)],'rows':rows}
 assert len({r['hash'] for r in rows})==len(rows)
 assert all(not r['sandwich_group_ids'] for r in disjoint)
 (R/'mev_ring_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 lines=['# MEV 交易环第一轮核查','', '本轮从全部候选重查完整兑换图，而不是只取 DFS 找到的第一条环。金额以既有操作地址边界净现金流为准，已扣 gas；未证明最终所有权或因果收益。','',*['- '+k+': '+str(v) for k,v in stats.items()],'','## 非夹击腿的高收益闭环候选','']
 for r in sorted(disjoint,key=lambda r:D(r['operational_net_ETH_after_gas']),reverse=True)[:20]:
  lines += [f"### {r['hash']}",f"- 区块：{r['block']}；发送者：{r['sender']}；执行合约：{r['execution_contract']}",f"- 操作边界净收益：{r['operational_net_ETH_after_gas']} ETH；gas：{r['gas_ETH']} ETH",f"- 同区块反向目标关联：{r['same_block_opposite_link']}；目标："+', '.join(sorted({p['target'] for p in r['target_links']})), '- 全部兑换边：']
  lines += [f"  - {e['input_token']} ({e['input_raw']} raw) → {e['output_token']} ({e['output_raw']} raw)，池 {e['pool']}" for e in r['all_pool_flow_edges']]
 lines+=['','## 后续必须核查','- 根据原始日志顺序和内部调用核验每条兑换边，验证协议身份及转账税等特殊行为。','- 跨交易环不能仅凭同一发送者合并；需资金连续性和库存追踪。','- 图闭合且资金为正是套利结构证据。黑客交易造成了多少收益仍需要反事实或更强的状态证据。','- 图残差不能直接认定无套利，需区分手续费、库存和未识别路径。']
 (R/'MEV交易环核查.md').write_text('\n'.join(lines)+'\n');print(json.dumps(stats))
if __name__=='__main__':main()
