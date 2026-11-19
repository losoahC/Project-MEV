"""Attach explicit mechanism criteria; never label high gas alone as MEV."""
import json
from collections import Counter,defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT

def classify(c):
    links=c['associations'];closed=c.get('pool_inventory_closed_WETH_cycle',False);positive=Decimal(c.get('net_after_gas_and_builder_ETH','0'))>0 and not c.get('other_token_residual_raw',{'unknown':'1'})
    pools=len(c['pool_legs']);arb=closed and positive and pools>=2
    back=any(a['relative_order']=='after' and a['opposite_direction'] for a in links)
    front=any(a['relative_order']=='before' and not a['opposite_direction'] for a in links)
    return {'tx_hash':c['tx_hash'],'block':c['block'],'sender':c['sender'],'executor':c['executor'],
            'mechanism':'multi_pool_inventory_closed_arbitrage_candidate' if arb else 'inventory_or_episode_accounting_required',
            'criteria':{'successful_pool_events':bool(c['swap_event_count']),'distinct_pool_count':pools,'pool_non_WETH_inventory_closed':closed,'positive_operational_cashflow_no_other_tokens':positive,'after_target_same_pool_opposite_direction':back,'before_target_same_pool_same_direction':front},
            'ordering_evidence':'backrun_compatible' if back else 'front_leg_compatible' if front else 'same_pool_association_only',
            'gas_is_MEV_criterion':False,'mev_causally_established':False,'boundary_verified':False,'confirmation_status':'candidate_requires_manual_or_stronger_replay_validation'}

def run():
    out=ROOT/'data/processed/mev_discovery';cs=json.loads((out/'candidates.json').read_text());rows=[classify(c) for c in cs]
    byhash={c['tx_hash']:c for c in cs};ep=json.loads((out/'episodes.json').read_text());patterns=[]
    for e in ep:
        pairs=defaultdict(lambda:{'front':[],'back':[]})
        for h in e['associated_candidate_transactions']:
            for a in byhash[h]['associations']:
                key=(a['target'],a['pool'])
                if a['relative_order']=='before' and not a['opposite_direction']:pairs[key]['front'].append(h)
                if a['relative_order']=='after' and a['opposite_direction']:pairs[key]['back'].append(h)
        for (target,pool),p in pairs.items():
            if p['front'] and p['back']:patterns.append({'episode_id':e['episode_id'],'target':target,'pool':pool,'front':sorted(set(p['front'])),'back':sorted(set(p['back'])),'classification':'sandwich_pattern_candidate','episode_net_ETH':e['net_ETH'],'episode_inventory_residual':e['inventory_residual_non_WETH_raw'],'shared_entrypoint':e['shared_entrypoint_in_block'],'causal_incremental_hacker_loss_USD':None})
    (out/'classification.json').write_text(json.dumps(rows,indent=2));(out/'sandwich_patterns.json').write_text(json.dumps(patterns,indent=2))
    print('mechanisms',dict(Counter(x['mechanism'] for x in rows)),'sandwich-pattern associations',len(patterns))
if __name__=='__main__':run()
