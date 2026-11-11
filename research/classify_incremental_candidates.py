"""Apply the same conservative economic filters to newly found candidates."""
import json,gzip
from collections import defaultdict,Counter
from pathlib import Path
from decimal import Decimal as D,getcontext
from rawtrace_native import parse
from screen_expanded import net_for,V2,V4
from identify_mev import TRANSFER,SWAP_V3,WETH,DEPOSIT,WITHDRAWAL
from complete_late_candidates import events
from classify_candidates import cycle
import value_inventory_ledger as val
getcontext().prec=70
R=Path(__file__).resolve().parent;E=D(10)**18;PCAKE='0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83'
load=lambda n:json.loads((R/n).read_text())
def receipts(n):
 if n>26303950:return json.loads(gzip.decompress((R/'scope_detail_raw'/f'{n}_receipts.json.gz').read_bytes()))['result']
 folder='window_raw' if n<=26301940 else 'extension_raw'
 return json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))
def traces(n):
 p=R/'scope_detail_raw'/f'{n}_trace.json.gz' if n>26303950 else R/'drpc_trace_raw'/f'{n}.json.gz'
 return json.loads(gzip.decompress(p.read_bytes()))['result']
def main():
 sig=load('classification_event_signatures.json');lp={v:k for k,v in sig.items() if k.startswith(('Mint(','Burn(','Collect(','ModifyLiquidity('))};debt={v:k for k,v in sig.items() if k.startswith(('Borrow(','Repay(','Supply(','Withdraw(','LiquidationCall('))};flashes={v for k,v in sig.items() if k.startswith(('Flash(','FlashLoan('))};nfts={v for k,v in sig.items() if k.startswith(('TransferSingle(','TransferBatch('))};known={TRANSFER,SWAP_V3,V2,V4,PCAKE,DEPOSIT,WITHDRAWAL,sig['Approval(address,address,uint256)'],'0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'}|set(lp)|set(debt)|flashes
 old={r['hash'] for r in load('full_candidates.json')['rows']};cs=[r for r in load('pancake_coverage_completion.json')['candidates'] if r['hash'] not in old]+load('late_candidate_completion.json')['rows'];byblock=defaultdict(list)
 for c in cs:byblock[c['block']].append(c)
 for p in load('scope_market_prices.json')['rows']:val.PRICES.setdefault(p['symbol'],{}).update({t:b for t,b in p['bars'].items() if int(t)>1793343767})
 result=[]
 for bi,(n,subset) in enumerate(sorted(byblock.items()),1):
  recs={r['transactionHash']:r for r in receipts(n)};ts=defaultdict(list);wanted={c['hash'] for c in subset}
  for t in traces(n):
   if t.get('transactionHash') in wanted:ts[t['transactionHash']].append(t)
  if n>26303950:b=json.loads(gzip.decompress((R/'scope_detail_raw'/f'{n}_block.json.gz').read_bytes()))['result'];val.HEAD[n]={'timestamp':int(b['timestamp'],16)}
  for c in subset:
   h=c['hash'];r=recs[h];tr=ts[h];es=events(r);tokens={l['address'] for l in r['logs'] if len(l['topics'])==3 and l['topics'][0]==TRANSFER};pools={e['pool'].split(':')[1] for e in es};lps=[];debts=[];unknown=[];nft=False;flash=False
   for l in r['logs']:
    if not l['topics']:continue
    t=l['topics'][0]
    if t in lp:lps.append({'emitter':l['address'],'event':lp[t],'topics':l['topics'],'data':l['data']})
    if t in debt:debts.append({'emitter':l['address'],'event':debt[t]})
    nft|=(t==TRANSFER and len(l['topics'])==4) or t in nfts;flash|=t in flashes
    if t not in known and t not in nfts:unknown.append({'emitter':l['address'],'topic':t})
   protocol=pools|tokens|{x['emitter'] for x in lps+debts};group={r['from'],r['to']}-{None};bad={tuple(t['traceAddress']) for t in tr if t.get('error')};calls=[]
   for t in tr:
    path=tuple(t['traceAddress'])
    if any(path[:i] in bad for i in range(len(path)+1)):continue
    if t['type']=='call' and t['action'].get('callType')=='call':calls.append(t['action'])
   for _ in range(12):
    add={x['to'].lower() for x in calls if x['from'].lower() in group and x['to'].lower() not in protocol and x.get('input','0x')!='0x'}
    if add<=group:break
    group.update(add)
   net=net_for(r,group);others={a:v for a,v in net.items() if a!=WETH and int(v)};nr=parse(h,tr);gas=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/E;cash=sum((D(v)/E for a,v in nr['native_net_wei'].items() if a in group),D(0))+D(net.get(WETH,'0'))/E-gas;outside=set();poolnet=defaultdict(lambda:defaultdict(int))
   for l in r['logs']:
    tt=l['topics']
    if len(tt)!=3 or tt[0]!=TRANSFER:continue
    src='0x'+tt[1][-40:];dst='0x'+tt[2][-40:];v=int(l['data'],16);token=l['address']
    if dst in group and src not in group|pools and v:outside.add(src)
    if dst in pools:poolnet[dst][token]+=v
    if src in pools:poolnet[src][token]-=v
   for x in calls:
    if int(x.get('value','0x0'),16)>0 and x['to'].lower() in group and x['from'].lower() not in group|pools|{WETH}:outside.add(x['from'].lower())
   edges=[]
   for p,amounts in poolnet.items():
    ins=[a for a,v in amounts.items() if v>0];outs=[a for a,v in amounts.items() if v<0]
    if len(ins)==len(outs)==1 and p!='0x000000000004444c5dc75cb358380d2e3de08a90':edges.append({'pool':p,'input_token':ins[0],'output_token':outs[0],'input_raw':str(amounts[ins[0]]),'output_raw':str(-amounts[outs[0]])})
   route=cycle(edges)
   if lps:category='liquidity_position_operation'
   elif debts:category='lending_or_liquidation_operation'
   elif nft:category='nonfungible_position_operation'
   elif others:category='other_token_inventory_open'
   elif outside or unknown:category='external_funding_or_unresolved_protocol'
   elif route and cash>0:category='strong_closed_cycle_evidence'
   elif route:category='closed_cycle_nonpositive_cashflow'
   elif len({e['pool'] for e in es})>=2 and cash>0:category='multipool_positive_unproven_cycle'
   else:category='insufficient_cycle_evidence'
   result.append({'hash':h,'block':n,'index':int(r['transactionIndex'],16),'category':category,'operational_boundary':sorted(group),'operational_cashflow_ETH':str(cash),'other_token_net_raw':others,'liquidity_events':lps,'debt_events':debts,'nft_event_present':nft,'flash_event_present':flash,'unresolved_events':unknown,'external_funding_addresses':sorted(outside),'token_cycle':route,'pool_flow_edges':edges,'gas_ETH':str(gas),'strict':val.portfolio(str(cash),others,n,0),'five_minute':val.portfolio(str(cash),others,n,5)})
  if bi%150==0:print('incremental classified',bi,len(byblock),'rows',len(result),flush=True)
 assert len(result)==2868 and len({r['hash'] for r in result})==2868 and not {r['hash'] for r in result}&old
 summary={k:{'count':sum(r['category']==k for r in result),'operational_cashflow_ETH':str(sum((D(r['operational_cashflow_ETH']) for r in result if r['category']==k),D(0)))} for k in sorted({r['category'] for r in result})}
 (R/'incremental_candidate_classification.json').write_text(json.dumps({'method':'Same conservative event/funding/inventory/cycle filters as original classifier, including Pancake event signature. Structural evidence, not complete economic profit or causal MEV. Operational helpers not proven common owner.','summary':summary,'rows':result},indent=2));print(summary,flush=True)
if __name__=='__main__':main()
