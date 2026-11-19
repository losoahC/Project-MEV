"""Disjoint candidate-linked strategy intervals; include all same-sender intervening txs.
Public services never become an assumed part of a bot's balance boundary.
"""
import json,bisect
from collections import defaultdict,Counter
from src.arbitrage.discover import ROOT

# Explicitly named routers are exclusions, never ownership labels.
ROUTERS={'0x7a250d5630b4cf539739df2c5dacb4c659f2488d','0xe592427a0aece92de3edee1f18e0157c05861564','0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45','0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f','0x9008d19f58aabd9ed0d60971565aa8510560ab41'}

def run():
    p=ROOT/'data/processed/mev_full_window';cs=json.loads((p/'candidates.json').read_text());cby={c['tx_hash']:c for c in cs};pairs=defaultdict(lambda:{'front':[],'back':[]})
    for c in cs:
        pos=c['block']*10000+c['index']
        for a in c['associations']:
            v=pairs[(c['sender'],a['target'],a['pool_key'])]
            if a['relative_order']=='before' and not a['opposite_direction']:v['front'].append(pos)
            if a['relative_order']=='after' and a['opposite_direction']:v['back'].append(pos)
    intervals=defaultdict(list)
    for (sender,target,pool),v in pairs.items():
        if v['front'] and v['back']:intervals[sender].append((min(v['front']),max(v['back']),target,pool))
    merged={}
    for sender,rs in intervals.items():
        groups=[]
        for lo,hi,t,pool in sorted(rs):
            if groups and lo<=groups[-1]['hi']:
                g=groups[-1];g['hi']=max(g['hi'],hi);g['targets'].add(t);g['pools'].add(pool)
            else:groups.append({'lo':lo,'hi':hi,'targets':{t},'pools':{pool}})
        merged[sender]=groups
    public=set(ROUTERS);public.update(json.loads((ROOT/'data/processed/historical_pricebook.json').read_text())['registry'])
    with (p/'pool_census.jsonl').open() as f:
        for line in f:
            for e in json.loads(line)['events']:public.add(e['pool'])
    units={};assigned={};context=0
    starts={s:[g['lo'] for g in gs] for s,gs in merged.items()}
    with (p/'all_sender_accounting.jsonl').open() as f:
        for line in f:
            row=json.loads(line);h=row['tx_hash'];s=row['sender'];pos=row['block']*10000+row['index'];group=None
            if s in merged:
                i=bisect.bisect_right(starts[s],pos)-1
                if i>=0 and pos<=merged[s][i]['hi']:group=merged[s][i]
            if group:
                uid=f"interval:{s}:{group['lo']}:{group['hi']}";kind='same_sender_bracketing_interval';targets=group['targets']
            elif h in cby:uid='single:'+h;kind='standalone_candidate';targets={a['target'] for a in cby[h]['associations']}
            else:context+=1;continue
            if uid not in units:units[uid]={'unit_id':uid,'kind':kind,'sender':s,'txs':[],'candidate_hashes':[],'target_hashes':set(),'boundary':{s},'excluded_public_entrypoints':set(),'positions':[],'nft_transfers':0}
            u=units[uid];assert h not in assigned;assigned[h]=uid;u['txs'].append({'tx_hash':h,'block':row['block'],'index':row['index'],'entrypoint':row['executor']});u['target_hashes'].update(targets)
            if h in cby:u['candidate_hashes'].append(h)
            if row['executor'] and row['executor'] not in public:u['boundary'].add(row['executor'])
            elif row['executor']:u['excluded_public_entrypoints'].add(row['executor'])
            u['positions'].extend({'tx_hash':h,**e} for e in row.get('position_or_debt_events',[]));u['nft_transfers']+=row.get('recognized_erc721_transfer_events',0)
    assert {h for h in assigned if h in cby}==set(cby)
    for u in units.values():
        for key in ['target_hashes','boundary','excluded_public_entrypoints']:u[key]=sorted(u[key])
        u['txs'].sort(key=lambda r:(r['block'],r['index']));u['ownership_verified']=False;u['grouping_note']='Same-sender overlapping bracketing intervals are merged, with every intervening sender transaction. May combine strategies; no shared-router ownership inferred. Other sender activity remains separately retained.'
    rows=list(units.values());rows.sort(key=lambda u:(u['txs'][0]['block'],u['txs'][0]['index'],u['unit_id']));(p/'strategy_units.json').write_text(json.dumps(rows,indent=2));(p/'public_boundary_exclusions.json').write_text(json.dumps({'addresses':sorted(public),'basis':'Observed Swap emitters, contract-mapped token registry and explicit router/settlement exclusions. Exclusion is not a beneficiary attribution.'},indent=2))
    summary={'units':len(rows),'kinds':dict(Counter(u['kind'] for u in rows)),'candidate_transactions_covered_once':len(cby),'included_transactions_unique':len(assigned),'additional_interval_transactions':len(assigned)-len(cby),'other_sender_transactions_retained_as_context':context,'units_containing_public_entrypoint_exclusions':sum(bool(u['excluded_public_entrypoints']) for u in rows),'profit_total_established':False};(p/'strategy_unit_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
