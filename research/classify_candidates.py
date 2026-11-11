"""Conservative transaction-structure classification; never causal profit proof."""
import json,gzip,csv
from collections import defaultdict,Counter
from pathlib import Path
from decimal import Decimal as D,getcontext
from screen_expanded import net_for,V2,V4
from identify_mev import TRANSFER,SWAP_V3,WETH,DEPOSIT,WITHDRAWAL
getcontext().prec=70
R=Path(__file__).resolve().parent;E=D(10)**18
def load(n):return json.loads((R/n).read_text())
def cycle(edges):
 graph=defaultdict(list)
 for e in edges:graph[e['input_token']].append(e)
 def visit(start,node,path,seen):
  for e in graph[node]:
   if e['pool'] in {x['pool'] for x in path}:continue
   nxt=e['output_token'];p=path+[e]
   if nxt==start and len(p)>=2:return p
   if nxt not in seen and len(p)<12:
    found=visit(start,nxt,p,seen|{nxt})
    if found:return found
  return None
 for token in list(graph):
  found=visit(token,token,[],{token})
  if found:return found
 return []
def main():
 signatures=load('classification_event_signatures.json');lp={v:k for k,v in signatures.items() if k.startswith(('Mint(','Burn(','Collect(','ModifyLiquidity('))};debt={v:k for k,v in signatures.items() if k.startswith(('Borrow(','Repay(','Supply(','Withdraw(','LiquidationCall('))}
 flashes={v for k,v in signatures.items() if k.startswith(('Flash(','FlashLoan('))};nfts={v for k,v in signatures.items() if k.startswith(('TransferSingle(','TransferBatch('))}
 known={TRANSFER,SWAP_V3,V2,V4,DEPOSIT,WITHDRAWAL,signatures['Approval(address,address,uint256)'],'0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'}|set(lp)|set(debt)|flashes
 cs=load('full_candidates.json')['rows'];acc={r['hash']:r for r in load('all_candidate_accounting.json')['rows']};native={r['hash']:r for r in load('drpc_candidate_native.json')['rows']};byblock=defaultdict(list)
 for c in cs:byblock[c['block']].append(c)
 poolorder=defaultdict(dict)
 for r in load('full_pool_events.json'):
  for p in {e['pool'] for e in r['pool_events']}:poolorder[p][r['hash']]=(r['block'],r['index'])
 positions={p:{h:i for i,(h,_) in enumerate(sorted(rows.items(),key=lambda x:x[1]))} for p,rows in poolorder.items()}
 target_amounts={}
 for t in load('full_swaps.json')['rows']:
  amounts=defaultdict(int)
  for e in t['pool_events']:amounts[e['pool']]+=int(e['amount0'])
  target_amounts[t['hash']]=amounts
 result=[]
 for bi,(n,subset) in enumerate(sorted(byblock.items()),1):
  folder='window_raw' if n<=26301940 else 'extension_raw';recs={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))};traces=defaultdict(list)
  for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result']:
   if t.get('transactionHash'):traces[t['transactionHash']].append(t)
  for c in subset:
   h=c['hash'];r=recs[h];a=acc[h];ts=traces[h];tokens={l['address'] for l in r['logs'] if len(l['topics'])==3 and l['topics'][0]==TRANSFER};pools={e['pool'].split(':')[1] for e in c['pool_events']};lp_events=[];debt_events=[];unknown=[];nft=False;flash=False
   for l in r['logs']:
    if not l['topics']:continue
    topic=l['topics'][0]
    if topic in lp:lp_events.append({'emitter':l['address'],'event':lp[topic],'topics':l['topics'],'data':l['data']})
    if topic in debt:debt_events.append({'emitter':l['address'],'event':debt[topic]})
    nft|=(topic==TRANSFER and len(l['topics'])==4) or topic in nfts
    flash|=topic in flashes
    if topic not in known and topic not in nfts:unknown.append({'emitter':l['address'],'topic':topic})
   protocol=pools|tokens|{e['emitter'] for e in lp_events+debt_events}
   group={c['from'],c['to']};bad={tuple(t['traceAddress']) for t in ts if t.get('error')};calls=[]
   for t in ts:
    path=tuple(t['traceAddress'])
    if any(path[:i] in bad for i in range(len(path)+1)):continue
    if t['type']=='call' and t['action'].get('callType')=='call':calls.append(t['action'])
   # Operational boundary, not an assertion of common beneficial ownership.
   for _ in range(12):
    add={x['to'].lower() for x in calls if x['from'].lower() in group and x['to'].lower() not in protocol and x.get('input','0x')!='0x'}
    if add<=group:break
    group.update(add)
   net=net_for(r,group);others={t:v for t,v in net.items() if t!=WETH and int(v)};eth=sum((D(v)/E for x,v in native[h]['native_net_wei'].items() if x in group),D(0));weth=D(net.get(WETH,'0'))/E;cash=eth+weth-D(a['gas_ETH'])
   outside_funding=set();poolnet=defaultdict(lambda:defaultdict(int))
   for l in r['logs']:
    tt=l['topics']
    if len(tt)!=3 or tt[0]!=TRANSFER:continue
    src='0x'+tt[1][-40:];dst='0x'+tt[2][-40:];amount=int(l['data'],16);token=l['address']
    if dst in group and src not in group and src not in pools and amount:outside_funding.add(src)
    if dst in pools:poolnet[dst][token]+=amount
    if src in pools:poolnet[src][token]-=amount
   for x in calls:
    if int(x.get('value','0x0'),16)>0 and x['to'].lower() in group and x['from'].lower() not in group|pools|{WETH}:outside_funding.add(x['from'].lower())
   edges=[]
   for p,amounts in poolnet.items():
    ins=[t for t,v in amounts.items() if v>0];outs=[t for t,v in amounts.items() if v<0]
    if len(ins)==len(outs)==1 and p!='0x000000000004444c5dc75cb358380d2e3de08a90':edges.append({'pool':p,'input_token':ins[0],'output_token':outs[0],'input_raw':str(amounts[ins[0]]),'output_raw':str(-amounts[outs[0]])})
   route=cycle(edges);nearest=[];candidate_amounts=defaultdict(int)
   for e in c['pool_events']:candidate_amounts[e['pool']]+=int(e['amount0'])
   for t in c['prior_targets']:
    pp=positions.get(t['pool'],{});adjacent=h in pp and t['target'] in pp and pp[h]-pp[t['target']]==1
    opposite=candidate_amounts[t['pool']]*target_amounts[t['target']][t['pool']]<0
    if opposite and adjacent:nearest.append({**t,'opposite_amount0':True,'direction_basis':'net amount0 across all same-pool swaps in each transaction','next_observed_swap_on_pool':True})
   association='same_block_next_pool_swap_opposite' if any(x['block_distance']==0 for x in nearest) else ('later_block_next_pool_swap_opposite' if nearest else 'temporal_pool_overlap_only')
   if lp_events:category='liquidity_position_operation'
   elif debt_events:category='lending_or_liquidation_operation'
   elif nft:category='nonfungible_position_operation'
   elif others:category='other_token_inventory_open'
   elif outside_funding or unknown:category='external_funding_or_unresolved_protocol'
   elif route and cash>0:category='strong_closed_cycle_evidence'
   elif route:category='closed_cycle_nonpositive_cashflow'
   elif len({e['pool'] for e in c['pool_events']})>=2 and cash>0:category='multipool_positive_unproven_cycle'
   else:category='insufficient_cycle_evidence'
   result.append({'hash':h,'block':n,'index':c['index'],'category':category,'association':association,'operational_boundary':sorted(group),'boundary_expanded':len(group)>len({c['from'],c['to']}),'root_boundary_cashflow_ETH':a['net_ETH_WETH_after_gas'],'operational_cashflow_ETH':str(cash),'other_token_net_raw':others,'liquidity_events':lp_events,'debt_events':debt_events,'nft_event_present':nft,'flash_event_present':flash,'unresolved_events':unknown,'external_funding_addresses':sorted(outside_funding),'token_cycle':route,'pool_flow_edges':edges,'closest_opposite_links':nearest,'pool_count':len({e['pool'] for e in c['pool_events']}),'gas_ETH':a['gas_ETH']})
  if bi%200==0:print('classified blocks',bi,'rows',len(result),flush=True)
 summary={}
 for k in sorted({r['category'] for r in result}):
  rr=[r for r in result if r['category']==k];summary[k]={'count':len(rr),'operational_cashflow_ETH':str(sum((D(r['operational_cashflow_ETH']) for r in rr),D(0))),'root_cashflow_ETH':str(sum((D(r['root_boundary_cashflow_ETH']) for r in rr),D(0))),'same_block_next_opposite':sum(r['association']=='same_block_next_pool_swap_opposite' for r in rr)}
 out={'method':'Conservative event/asset-flow classification. Compatible event signatures do not certify factory identity. Operational helper expansion is not beneficial-owner proof. Directed pool token-flow cycle plus positive closed ETH/WETH cashflow is structural evidence, not counterfactual MEV. Recognized LP/debt/NFT, unknown events, outside funding and open ERC20 inventory block the strongest class. Other protocols/state liabilities can remain unobserved.','summary':summary,'rows':result}
 (R/'candidate_classification.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
