"""Price complete same-sender episodes, not only their target-associated legs."""
import json
from collections import Counter,defaultdict
from decimal import Decimal,getcontext
from src.arbitrage.value_candidates import book_from_archive,mark,ROOT,E
getcontext().prec=90

def run():
    out=ROOT/'data/processed/mev_discovery';cs=json.loads((out/'candidates.json').read_text());times={c['block']:c['timestamp'] for c in cs};eps=json.loads((out/'episodes.json').read_text());b=book_from_archive();rows=[];members=Counter((e['block'],t['tx_hash']) for e in eps for t in e['transactions'])
    for e in eps:
        vals=[];eth=b.price('ETH',times[e['block']])
        for t in e['transactions']:
            raw=dict(t['token_net_raw']);raw['native:eth']=t['native_net_wei'];v=mark(b,raw,times[e['block']]);gasusd=Decimal(t['gas_wei'])/E*eth[0] if eth else None
            v.update(tx_hash=t['tx_hash'],gas_USD=str(gasusd) if gasusd is not None else None,marked_after_gas_USD=str(Decimal(v['marked_net_USD'])-gasusd) if gasusd is not None and v['marked_net_USD'] is not None else None);vals.append(v)
        complete=not e['errors'] and all(v['marked_after_gas_USD'] is not None for v in vals)
        duplicate=any(members[(e['block'],v['tx_hash'])]>1 for v in vals)
        rows.append({'episode_id':e['episode_id'],'block':e['block'],'timestamp':times[e['block']],'sender':e['sender'],'executor':e['executor'],'transaction_count':len(vals),'target_hashes':e['target_transactions'],
                     'shared_entrypoint_in_block':e['shared_entrypoint_in_block'],'overlaps_other_operational_boundary':duplicate,
                     'valuation_complete':complete,'marked_after_gas_USD':str(sum((Decimal(v['marked_after_gas_USD']) for v in vals),Decimal(0))) if complete else None,
                     'transactions':vals,'boundary_verified':False,'causal_hacker_loss_USD':None,'meaning':'Complete same-sender same-block transaction set marked at each block time; not actual inventory cost-basis PnL, not a causal MEV total.'})
    (out/'episode_valuations.json').write_text(json.dumps(rows,indent=2));actors=defaultdict(list)
    for r in rows:actors[(r['sender'],r['executor'])].append(r)
    ranks=[]
    for (s,e),a in actors.items():
        ok=[v for v in a if v['valuation_complete'] and not v['overlaps_other_operational_boundary'] and not v['shared_entrypoint_in_block']]
        ranks.append({'sender':s,'executor':e,'episodes_total':len(a),'usable_nonoverlapping_nonshared_complete_episodes':len(ok),'excluded_episodes':len(a)-len(ok),'marked_cashflow_USD':str(sum((Decimal(v['marked_after_gas_USD']) for v in ok),Decimal(0))),'episode_ids':[v['episode_id'] for v in ok],'status':'reference-marked operational cashflow; identity, cross-block inventory basis and missing episodes unresolved'})
    ranks.sort(key=lambda x:Decimal(x['marked_cashflow_USD']),reverse=True);(out/'marked_episode_actor_candidates.json').write_text(json.dumps(ranks,indent=2))
    print(json.dumps({'episodes':len(rows),'complete':sum(x['valuation_complete'] for x in rows),'overlapping':sum(x['overlaps_other_operational_boundary'] for x in rows),'shared':sum(x['shared_entrypoint_in_block'] for x in rows),'all_event_profit_established':False},indent=2))
if __name__=='__main__':run()
