"""Include every same-sender transaction in each associated block, including losses.

Operational two-address boundaries remain tentative; shared entrypoints are flagged.
This stage cannot claim beneficial owners or causal victim losses.
"""
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
import json
from src.arbitrage.discover import ROOT,route_evidence,events
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow,token_net,native_flows
from src.decoding.events import integer,WETH
getcontext().prec=90
E=Decimal(10)**18

def run():
    out=ROOT/'data/processed/mev_discovery';cs=json.loads((out/'candidates.json').read_text());groups=defaultdict(list)
    for c in cs:groups[c['block']].append(c)
    engine=Reconstruction(ROOT.parent/'research',False);episodes=[];negative_corrections=[]
    for i,(n,cands) in enumerate(sorted(groups.items()),1):
        head,rs,ts,paths=engine.block(n);by_sender=defaultdict(list);callers=defaultdict(set)
        for h,r in rs.items():
            by_sender[r['from'].lower()].append(h)
            if r.get('to'):callers[r['to'].lower()].add(r['from'].lower())
        for sender,executor in sorted({(c['sender'],c['executor']) for c in cands}):
            boundary={sender,executor}-{''};allhash=by_sender[sender];matching=[c for c in cands if c['sender']==sender and c['executor']==executor]
            net=defaultdict(int);poolnet=defaultdict(int);gross=Decimal(0);retained=Decimal(0);gas=0;builder=0;rows=[];errors=[]
            for h in sorted(allhash,key=lambda h:integer(rs[h]['transactionIndex'])):
                r=rs[h]
                try:
                    f=cashflow(r,ts[h],boundary,head['miner']);gross+=Decimal(f['gross_after_pool_fees_before_gas_and_builder_ETH']);retained+=Decimal(f['net_after_gas_and_builder_ETH']);gas+=int(f['gas_wei']);builder+=int(f['identified_builder_payment_wei'])
                    for t,v in f['token_net_raw'].items():net[t]+=int(v)
                    legs=route_evidence(r,events(r)) if integer(r['status'])==1 else []
                    for l in legs:
                        for t,v in l['incoming_raw'].items():poolnet[t]-=int(v)
                        for t,v in l['outgoing_raw'].items():poolnet[t]+=int(v)
                    rows.append({'tx_hash':h,'index':integer(r['transactionIndex']),'status':integer(r['status']),**f,'pool_legs':legs,'native_flows':native_flows(ts[h])})
                except Exception as ex:errors.append({'tx_hash':h,'error':str(ex)})
            other={t:str(v) for t,v in net.items() if t!=WETH and v};poolother={t:str(v) for t,v in poolnet.items() if t!=WETH and v}
            shared=len(callers[executor])>1
            candidate_subtotal=sum((Decimal(c.get('net_after_gas_and_builder_ETH','0')) for c in matching if c['classification']=='inventory_closed_positive_cashflow_candidate'),Decimal(0))
            result={'episode_id':f'{n}:{sender}:{executor}','block':n,'sender':sender,'executor':executor,'boundary':sorted(boundary),'entrypoint_senders_in_block':sorted(callers[executor]),'shared_entrypoint_in_block':shared,
                'included_all_sender_transactions_in_block':True,'transaction_count':len(rows),'associated_candidate_transactions':[c['tx_hash'] for c in matching],'target_transactions':sorted({a['target'] for c in matching for a in c['associations']}),
                'inventory_residual_non_WETH_raw':other,'pool_residual_non_WETH_raw':poolother,'pool_surplus_WETH_wei':str(poolnet.get(WETH,0)),
                'gross_ETH':str(gross),'gas_ETH':str(Decimal(gas)/E),'direct_builder_ETH':str(Decimal(builder)/E),'net_ETH':str(retained),'positive_single_leg_candidate_subtotal_ETH':str(candidate_subtotal),
                'candidate_subtotal_minus_episode_ETH':str(candidate_subtotal-retained),'transactions':rows,'errors':errors,'evidence':paths,'causal_hacker_loss_USD':None}
            closed=not errors and not other and not poolother and poolnet.get(WETH,0)>0 and retained>0
            result['classification']='closed_positive_episode_requires_boundary_verification' if closed else 'inventory_open_or_nonpositive_or_incomplete_episode'
            result['net_aggregation_allowed']=False
            result['limit']='Same-sender whole-block grouping can mix strategies; shared entrypoint balances can belong to other users. No beneficial ownership or causal loss inferred. Cross-block funding and all external payouts still require investigation.'
            episodes.append(result)
            if candidate_subtotal>0 and (candidate_subtotal-retained)>Decimal('1'):negative_corrections.append({k:v for k,v in result.items() if k not in ['transactions','evidence']})
        engine.cache.clear()
        if i%100==0:print('episode blocks',i,'episodes',len(episodes),flush=True)
    (out/'episodes.json').write_text(json.dumps(episodes,indent=2));negative_corrections.sort(key=lambda r:Decimal(r['candidate_subtotal_minus_episode_ETH']),reverse=True);(out/'negative_leg_corrections.json').write_text(json.dumps(negative_corrections,indent=2))
    summary={'blocks':len(groups),'episodes':len(episodes),'classification':dict(Counter(e['classification'] for e in episodes)),'shared_entrypoint_episodes':sum(e['shared_entrypoint_in_block'] for e in episodes),'large_positive_leg_overstatements_corrected':len(negative_corrections),'total_profit_established':False}
    (out/'episode_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
