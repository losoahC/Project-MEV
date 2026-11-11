import json,gzip
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from rawtrace_native import parse
from screen_expanded import net_for
from value_inventory_ledger import portfolio
from audit_target_v2_fees import call
R=Path(__file__).resolve().parent;SIG='0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83';FACT='0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865'
load=lambda n:json.loads((R/n).read_text())
def main():
 identified=load('order_protocol_identification.json')['pancake_events'];ps={e['pool']:e['block'] for e in identified};meta={}
 for p,n in ps.items():
  m={k:call('pancake_'+p+'_'+k,p,s,n) for k,s in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155'),('fee','0xddca3f43')]};m={k:('0x'+v[-40:] if k!='fee' else int(v,16)) for k,v in m.items()};assert m['factory']==FACT
  raw=call('pancake_'+p+'_factory_getPool',FACT,'0x1698ee82'+m['token0'][2:].zfill(64)+m['token1'][2:].zfill(64)+hex(m['fee'])[2:].zfill(64),n);assert '0x'+raw[-40:]==p;m['factory_verified']=True;meta[p]=m
 targets={r['hash'] for r in load('unified_target_valuation.json')['rows'] if r['eligible_exchange_candidate']};oldtargets={r['hash'] for r in load('full_swaps.json')['rows']};oldcandidates={r['hash'] for r in load('full_candidates.json')['rows']};events=[];last={};candidates=[];target_events=[]
 for n in range(26300640,26303951):
  folder='window_raw' if n<=26301940 else 'extension_raw';rs=json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()));wanted=[]
  for r in rs:
   es=[]
   for l in r['logs']:
    if l['address'] in meta and l['topics'] and l['topics'][0]==SIG:
     w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];assert len(w)==7
     es.append({'pool':l['address'],'amount0':str(w[0] if w[0]<2**255 else w[0]-2**256),'amount1':str(w[1] if w[1]<2**255 else w[1]-2**256),'protocol_fee0_raw':str(w[5]),'protocol_fee1_raw':str(w[6]),'log_index':int(l['logIndex'],16)})
   if not es:continue
   h=r['transactionHash'];links=[]
   for e in es:
    prior=last.get(e['pool'])
    if prior and 0<=n-prior['block']<=5 and prior['hash']!=h:links.append({**prior,'pool':e['pool'],'block_distance':n-prior['block']})
   if h in targets:
    target_events.append({'hash':h,'block':n,'events':es})
    for e in es:last[e['pool']]={'hash':h,'block':n}
   elif links:
    c={'hash':h,'block':n,'from':r['from'],'to':r['to'],'prior_targets':links,'events':es,'already_in_old_candidate_set':h in oldcandidates};candidates.append(c)
    if h not in oldcandidates:wanted.append((c,r))
   events.append({'hash':h,'block':n,'events':es})
  if wanted:
   traces=defaultdict(list);hs={c['hash'] for c,r in wanted}
   for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result']:
    if t.get('transactionHash') in hs:traces[t['transactionHash']].append(t)
   for c,r in wanted:
    nr=parse(c['hash'],traces[c['hash']]);group={r['from'],r['to']};cash=sum((D(v)/10**18 for a,v in nr['native_net_wei'].items() if a in group),D(0))-D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/10**18;net=net_for(r,group);c.update(root_boundary=sorted(group),native_after_gas_ETH=str(cash),net_token_raw=net,strict=portfolio(str(cash),net,n,0),five_minute=portfolio(str(cash),net,n,5))
 out={'method':'Previously omitted Pancake V3 event format. All three affected pools verified against official factory getPool. Same/next-five-block overlap remains only a candidate rule. Incremental accounting uses root sender+entry boundary, not beneficial-owner or complete strategy profit. Existing candidate hashes are not added twice.','pools':meta,'summary':{'target_transactions':len(target_events),'new_target_transactions':len({x['hash'] for x in target_events}-oldtargets),'pancake_candidate_transactions':len(candidates),'new_candidate_transactions':sum(not x['already_in_old_candidate_set'] for x in candidates),'union_candidate_transactions':len(oldcandidates|{x['hash'] for x in candidates})},'target_events':target_events,'candidates':candidates,'pool_activity':events};(R/'pancake_coverage_completion.json').write_text(json.dumps(out,indent=2));print(out['summary'],flush=True)
if __name__=='__main__':main()
