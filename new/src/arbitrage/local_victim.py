"""Recompute conditional single-pool victim output effects from raw Swap/Sync.
No previous derivative counterfactual report is consumed. Not a full EVM result.
"""
import json
from collections import defaultdict,Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import SYNC,v2_quote
from src.decoding.events import swap,integer
from src.arbitrage.value_candidates import book_from_archive

def run():
    p=ROOT/'data/processed/mev_full_window';cs=json.loads((p/'candidates.json').read_text());targets={t['tx_hash']:t for t in json.loads((p/'targets.json').read_text())};metas={r['pool']:r for r in json.loads((ROOT/'data/processed/mev_discovery/pool_metadata.json').read_text())};pairs=defaultdict(lambda:{'front':set(),'back':set(),'executors':set()})
    for f in (ROOT/'data/processed/mev_discovery/pool_metadata').glob('0x*.json'):
        m=json.loads(f.read_text());metas[m['pool']]=m
    for c in cs:
        for a in c['associations']:
            if a['block_distance']!=0 or ':' in a['pool_key']:continue
            key=(c['block'],c['sender'],a['target'],a['pool_key']);v=pairs[key];v['executors'].add(c['executor'])
            if a['relative_order']=='before' and not a['opposite_direction']:v['front'].add(c['tx_hash'])
            if a['relative_order']=='after' and a['opposite_direction']:v['back'].add(c['tx_hash'])
    wanted=defaultdict(list)
    for key,v in pairs.items():
        if v['front'] and v['back']:wanted[key[0]].append((key,v))
    engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();rows=[]
    for n,groups in sorted(wanted.items()):
        head,rs,_,paths=engine.block(n)
        for (n,sender,target,pool),v in groups:
            m=metas.get(pool,{});base={'block':n,'sender':sender,'executors':sorted(v['executors']),'target':target,'pool':pool,'back_transactions':sorted(v['back']),'evidence':paths}
            if m.get('dex_name')!='Uniswap V2' or not m.get('factory_lookup_matches_pool'):rows.append({**base,'status':'pool_identity_not_yet_verified_UniswapV2'});continue
            tr=rs[target];te=[s for l in tr['logs'] if l['address'].lower()==pool and (s:=swap(l))]
            if len(te)!=1 or not te[0]['protocol'].startswith('V2'):rows.append({**base,'status':'target_not_single_standard_v2_swap'});continue
            logs=sorted([l for r in rs.values() for l in r['logs'] if l['address'].lower()==pool],key=lambda l:integer(l['logIndex']));tpos=next(i for i,l in enumerate(logs) if integer(l['logIndex'])==te[0]['log_index']);previous=[l for l in logs[:tpos] if swap(l)]
            if not previous:continue
            frontlog=previous[-1];front=frontlog['transactionHash'].lower()
            if front not in v['front']:rows.append({**base,'status':'immediate_predecessor_not_same_actor_front'});continue
            fr=rs[front];fe=[s for l in fr['logs'] if l['address'].lower()==pool and (s:=swap(l))]
            if len(fe)!=1:rows.append({**base,'front':front,'status':'front_multiple_swaps'});continue
            fpos=logs.index(frontlog);between=logs[fpos+1:tpos]
            if len(between)!=1 or between[0]['topics'][0].lower()!=SYNC:rows.append({**base,'front':front,'status':'intervening_pool_state_events'});continue
            def state(ev,pos):
                assert pos>0 and logs[pos-1]['topics'][0].lower()==SYNC
                dat=logs[pos-1]['data'];after=[int(dat[i:i+64],16) for i in [2,66]];before=[after[i]-int(ev[f'amount{i}_raw']) for i in [0,1]]
                ins=[i for i in [0,1] if int(ev[f'amount{i}_raw'])>0];outs=[i for i in [0,1] if int(ev[f'amount{i}_raw'])<0];assert len(ins)==len(outs)==1
                side=ins[0];inp=int(ev[f'amount{side}_raw']);actual=-int(ev[f'amount{1-side}_raw']);assert v2_quote(inp,before[side],before[1-side])==actual
                return before,after,side,inp,actual
            try:
                fb,fa,fs,fi,fo=state(fe[0],fpos);tb,ta,side,inp,actual=state(te[0],tpos);assert tb==fa and fs==side
                hypothetical=v2_quote(inp,fb[side],fb[1-side]);delta=hypothetical-actual;token=m[f'token{1-side}'];val=book.value(token,delta,integer(head['timestamp']))
                rows.append({**base,'front':front,'status':'verified_conditional_local_v2_quote','front_before':list(map(str,fb)),'front_after':list(map(str,fa)),'target_before':list(map(str,tb)),'target_after':list(map(str,ta)),'input_side':side,'target_input_raw':str(inp),'actual_output_raw':str(actual),'without_front_fixed_input_output_raw':str(hypothetical),'output_reduction_raw':str(delta),'output_token':token,'valuation':val,'factory_evidence':m['sources'],'victim_addresses':[w['address'] for w in targets[target]['wallets']],
                             'limit':'Local fixed-input 997/1000 pool quote only. Original signed multi-hop execution/minimum output may change or revert without the front. No full EVM victim-loss claim; operator control and alternative equilibrium remain unresolved.'})
            except Exception as ex:rows.append({**base,'front':front,'status':'actual_formula_or_state_validation_failed','error':str(ex)})
        engine.cache.clear()
    summary={'candidate_groups':len(rows),'statuses':dict(Counter(x['status'] for x in rows)),'verified_local_quotes':sum(r['status']=='verified_conditional_local_v2_quote' for r in rows),'full_EVM_victim_interventions':0,'all_event_MEV_loss_proven':False}
    (p/'local_victim_effects.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
