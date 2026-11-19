"""Archive and rescan all 3311 original-window blocks, including orders and V4.
Original reports are leads only; every result is recomputed from raw receipts/traces.
"""
import json,bisect
from collections import defaultdict,Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,native_flows,cashflow
from src.decoding.events import transfer,integer
from src.decoding.extended_events import extended_swap,order_event

FIRST,LAST=26300640,26303950
FOCUS='0x0cdd9cbb825212c6cc5b0b36239e94218ee661d8'

def run():
    out=ROOT/'data/processed/mev_full_window';out.mkdir(exist_ok=True);engine=Reconstruction(ROOT.parent/'research',False)
    registry=json.loads((ROOT/'data/processed/wallet_registry.json').read_text());leads={r['address'] for r in registry};branch='0x9749292d74fd460982d0912ea9515ea24736c762';monitored=leads|{branch}
    scope={'original_leads':sorted(leads),'additional_order_swapper':branch,'additional_address_basis':'Observed 500M USDT payment from original wallet 2, transaction 0x68d7d69deaeb9750c38020b4f8d3728146ca8d2267eba1e38cf9b56722ad659a; receiving funds proves association, not control. Full-window transactions re-evaluated independently.'}
    (out/'address_scope.json').write_text(json.dumps(scope,indent=2))
    targets=[];events=[];orders=[];focus=[];failures=[];totals=Counter();blocks=[]
    for n in range(FIRST,LAST+1):
        try:head,rs,ts,paths=engine.block(n)
        except Exception as ex:failures.append({'block':n,'error':str(ex)});continue
        totals['blocks']+=1;totals['receipts']+=len(rs);totals['failed_receipts']+=sum(integer(r['status'])==0 for r in rs.values());blocks.append({'block':n,'block_hash':head['hash'],'timestamp':integer(head['timestamp']),'receipts':len(rs),'evidence':paths})
        for h,r in sorted(rs.items(),key=lambda x:integer(x[1]['transactionIndex'])):
            if integer(r['status'])!=1:continue
            ev=[];oe=[];touch=set();focus_touch=r['from'].lower()==FOCUS or (r.get('to') or '').lower()==FOCUS
            for l in r['logs']:
                s=extended_swap(l)
                if s:ev.append(s)
                o=order_event(l)
                if o:oe.append(o)
                t=transfer(l)
                if t:
                    touch.update({t['sender'],t['recipient']}&monitored)
                    focus_touch|=FOCUS in (t['sender'],t['recipient'])
            debit={a:token_net(r,{a}) for a in touch};debit={a:v for a,v in debit.items() if any(vv<0 for vv in v.values())}
            # An order without a pool swap still counts when the payer's debit is observed.
            target=bool(debit and (ev or oe))
            if ev:events.append({'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'sender':r['from'].lower(),'executor':(r.get('to') or '').lower(),'events':ev,'is_target':target})
            if target or focus_touch:
                try:flows=native_flows(ts[h])
                except Exception as ex:flows=None;failures.append({'block':n,'tx_hash':h,'error':'native flow '+str(ex)})
                if target:
                    wallets=[]
                    for a,net in debit.items():
                        native=sum(int(f['amount_raw'])*((f['recipient']==a)-(f['sender']==a)) for f in flows) if flows is not None else None
                        wallets.append({'address':a,'source_category':'original_lead' if a in leads else 'direct_funding_association','token_net_raw':{t:str(v) for t,v in net.items()},'native_net_wei':str(native) if native is not None else None})
                    targets.append({'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'timestamp':integer(head['timestamp']),'wallets':wallets,'pool_events':ev,'order_events':oe,'evidence':paths})
                    for o in oe:orders.append({'tx_hash':h,'block':n,'timestamp':integer(head['timestamp']),'root_sender':r['from'],'root_executor':r['to'],**o,'evidence':paths})
                if focus_touch:
                    net=token_net(r,{FOCUS});native=sum(int(f['amount_raw'])*((f['recipient']==FOCUS)-(f['sender']==FOCUS)) for f in flows) if flows is not None else None
                    gas=integer(r['gasUsed'])*integer(r['effectiveGasPrice']) if r['from'].lower()==FOCUS else 0
                    focus.append({'address':FOCUS,'tx_hash':h,'block':n,'timestamp':integer(head['timestamp']),'token_net_raw':{t:str(v) for t,v in net.items()},'native_net_wei':str(native) if native is not None else None,'gas_wei':str(gas),'pool_events':ev,'evidence':paths})
        engine.cache.clear()
        if totals['blocks']%200==0:print('full window',totals['blocks'],'targets',len(targets),'pool tx',len(events),'focus tx',len(focus),flush=True)
    engine.store.save()
    targethashes={x['tx_hash'] for x in targets};index=defaultdict(list)
    for t in targets:
        for ev in t['pool_events']:index[ev['pool_key']].append((t['block']*10000+t['index'],t,ev))
    for p in index:index[p].sort(key=lambda x:x[0])
    keys={p:[x[0] for x in vv] for p,vv in index.items()};candidates=[]
    for r in events:
        if r['tx_hash'] in targethashes:continue
        links=[]
        for ev in r['events']:
            p=ev['pool_key']
            if p not in index:continue
            lo=bisect.bisect_left(keys[p],max(FIRST,r['block']-5)*10000);hi=bisect.bisect_left(keys[p],(min(LAST,r['block']+5)+1)*10000)
            for _,t,te in index[p][lo:hi]:
                links.append({'target':t['tx_hash'],'target_block':t['block'],'target_index':t['index'],'pool_key':p,'actor_log_index':ev['log_index'],'target_log_index':te['log_index'],'block_distance':r['block']-t['block'],'relative_order':'after' if (r['block'],r['index'])>(t['block'],t['index']) else 'before','opposite_direction':int(ev['amount0_raw'])*int(te['amount0_raw'])<0})
        if links:candidates.append({**r,'associations':links,'classification':'same_pool_within_5_blocks_candidate_not_confirmed_MEV'})
    for name,rows in [('blocks',blocks),('targets',targets),('orders',orders),('focus_address_ledger',focus),('candidates',candidates),('failures',failures)]:
        (out/(name+'.json')).write_text(json.dumps(rows,indent=2))
    # Keep complete pool census compact and independent of the targeted candidate selection.
    with (out/'pool_census.jsonl').open('w') as f:
        for row in events:f.write(json.dumps(row,separators=(',',':'))+'\n')
    summary={**totals,'first_block':FIRST,'last_block':LAST,'targets':len(targets),'target_original_lead_only':sum(any(w['source_category']=='original_lead' for w in t['wallets']) for t in targets),'targets_without_pool_events':sum(not t['pool_events'] for t in targets),'target_order_events':len(orders),'pool_transactions':len(events),'candidate_transactions_symmetric_5_blocks':len(candidates),'candidate_unique_hashes':len({x['tx_hash'] for x in candidates}),'candidate_protocols':dict(Counter(e['protocol'] for c in candidates for e in c['events'])),'bitquery_focus_address_transactions':len(focus),'failures':len(failures),'complete_window_raw_read':totals['blocks']==LAST-FIRST+1 and not failures,'counterfactual_or_profit_total_established':False}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
