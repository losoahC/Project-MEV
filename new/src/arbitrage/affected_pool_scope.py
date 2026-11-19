"""Whole-window affected-pool census, without a +/-5-block discovery cutoff."""
import json,bisect
from collections import defaultdict,Counter
from src.arbitrage.discover import ROOT

def run():
    p=ROOT/'data/processed/mev_full_window';ts=json.loads((p/'targets.json').read_text());index=defaultdict(list)
    for t in ts:
        for e in t['pool_events']:index[e['pool_key']].append((t['block']*10000+t['index'],t['tx_hash']))
    for pool,rs in index.items():index[pool]=sorted(set(rs))
    keys={k:[r[0] for r in rs] for k,rs in index.items()};targethash={t['tx_hash'] for t in ts};counts=Counter();senders=set();dest=p/'affected_pool_scope.jsonl'
    with (p/'pool_census.jsonl').open() as f,dest.open('w') as output:
        for line in f:
            r=json.loads(line);shared={e['pool_key'] for e in r['events']}&set(index)
            if not shared:continue
            pos=r['block']*10000+r['index'];prior=[]
            for pool in shared:
                i=bisect.bisect_left(keys[pool],pos)-1
                if i>=0:at,h=index[pool][i];prior.append({'pool_key':pool,'last_prior_target':h,'block_distance':r['block']-at//10000})
            category='target' if r['tx_hash'] in targethash else 'after_prior_target' if prior else 'before_first_target_control';r.update(scope_category=category,affected_pool_keys=sorted(shared),last_prior_targets=prior,attribution='Whole-window pool association; not all trades are MEV or incident-caused.')
            output.write(json.dumps(r,separators=(',',':'))+'\n');counts[category]+=1;senders.add(r['sender'])
    summary={'affected_pool_keys':len(index),'scope_transactions':sum(counts.values()),'categories':dict(counts),'distinct_senders':len(senders),'discovery_cutoff_blocks':None,'whole_event_profit_established':False};(p/'affected_pool_scope_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
