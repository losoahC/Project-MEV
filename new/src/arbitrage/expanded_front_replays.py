"""Fresh same-block front-removal experiments across V2/V3/V4 candidates.
Every actual prefix must reproduce before reporting a victim effect.
"""
import json,time,argparse
from collections import defaultdict,Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.replay_audit import txcall,NATIVE
from src.arbitrage.victim_replay import request,balance
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.decoding.events import integer

def run(limit=0):
    p=ROOT/'data/processed/mev_full_window';cs=json.loads((p/'candidates.json').read_text());targets={t['tx_hash']:t for t in json.loads((p/'targets.json').read_text())};pairs=defaultdict(lambda:{'front':set(),'back':set(),'pools':set()})
    for c in cs:
        for a in c['associations']:
            if a['block_distance']!=0:continue
            z=pairs[(c['sender'],a['target'],a['pool_key'])]
            if a['relative_order']=='before' and not a['opposite_direction']:z['front'].add((c['index'],c['tx_hash']))
            if a['relative_order']=='after' and a['opposite_direction']:z['back'].add((c['index'],c['tx_hash']))
    queue={}
    for (sender,target,pool),z in pairs.items():
        if not z['front'] or not z['back']:continue
        g=queue.setdefault((sender,target),{'sender':sender,'target':target,'block':targets[target]['block'],'fronts':set(),'backs':set(),'pools':set()});g['fronts'].update(h for _,h in z['front']);g['backs'].update(h for _,h in z['back']);g['pools'].add(pool)
    dest=p/'expanded_front_replays.json';rows=json.loads(dest.read_text())['rows'] if dest.exists() else [];done={(r['sender'],r['target']) for r in rows};todo=[q for key,q in sorted(queue.items(),key=lambda x:(x[1]['block'],x[0])) if key not in done];todo=todo[:limit] if limit else todo;engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('USDC',('2026-10-29','2026-10-30'));next_request=0
    def flush():
        doc={'queued_experiments':len(queue),'completed':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),'rows':rows,'all_incident_equilibrium_loss_established':False,'method':'Remove all matched same-sender same-block front calls before target; fixed remaining to/input/value/gas/fee. Remaining sender nonces automatically assigned only if necessary and no CREATE dependency. No arbitrary state overrides. Actual status/gas/logs validated first.'};dest.write_text(json.dumps(doc,indent=2));return doc
    print('front-removal queue',len(queue),'remaining',len(todo),flush=True)
    for q in todo:
        n=q['block'];head,rs,tr,paths=engine.block(n);target=q['target'];fronts=q['fronts'];idx=integer(rs[target]['transactionIndex']);prefix=head['transactions'][:idx+1];sender=q['sender'];nonce_dependent=[t for t in prefix if t['hash'] not in fronts and t['from'].lower()==sender];row={**q,'fronts':sorted(fronts),'backs':sorted(q['backs']),'pools':sorted(q['pools']),'victim_addresses':[w['address'] for w in targets[target]['wallets']],'evidence':paths,'nonce_reassigned_after_front_removal':bool(nonce_dependent)}
        if sender==rs[target]['from'].lower():row['status']='same_actor_target_excluded';rows.append(row);flush();continue
        if any(not t.get('to') for t in nonce_dependent):row['status']='top_level_CREATE_nonce_dependency';rows.append(row);flush();continue
        override={k:head[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={};valid=True
        for label,txs in [('actual',prefix),('without_fronts',[t for t in prefix if t['hash'] not in fronts])]:
            calls=[txcall(t) for t in txs]
            if label!='actual':
                for t,c in zip(txs,calls):
                    if t['from'].lower()==sender:c.pop('nonce',None)
            params=[{'blockStateCalls':[{'blockOverrides':override,'calls':calls}],'validation':True,'traceTransfers':True},hex(n-1)];time.sleep(max(0,next_request-time.monotonic()));doc,src=request(params);next_request=time.monotonic()+1.15;row['evidence'][label+'_simulation']=src
            sims=doc.get('response',{}).get('result')
            if not sims:row.update(status='RPC_execution_response_error',failed_scenario=label,error=doc.get('response',doc.get('transport_error')));valid=False;break
            sims=sims[0]['calls']
            try:
                assert len(sims)==len(txs)
                if label=='actual':
                    def norm(ls):return [(l['address'].lower(),[t.lower() for t in l['topics']],l['data'].lower()) for l in ls if l['address'].lower()!=NATIVE]
                    for tx,sim in zip(txs,sims):
                        real=rs[tx['hash']];assert integer(real['status'])==integer(sim['status']) and integer(real['gasUsed'])==integer(sim['gasUsed']) and norm(real['logs'])==norm(sim['logs'])
                sim=sims[-1];assert txs[-1]['hash']==target;scenarios[label]={'status':integer(sim['status']),'target_gas_used':integer(sim['gasUsed']),'victim_asset_net_raw':{a:{t:str(v) for t,v in balance(sim,a).items()} for a in row['victim_addresses']},'error':sim.get('error')}
            except Exception as ex:row.update(status='actual_prefix_or_sequence_mismatch',failed_scenario=label,error=repr(ex));valid=False;break
        row['scenarios']=scenarios
        if valid:
            row['actual_prefix_transactions_reproduced']=len(prefix)
            if any(s['status']!=1 for s in scenarios.values()):row['status']='verified_actual_prefix_target_reverts_under_intervention'
            else:
                effects=[]
                for a in row['victim_addresses']:
                    ac={t:int(v) for t,v in scenarios['actual']['victim_asset_net_raw'][a].items()};cf={t:int(v) for t,v in scenarios['without_fronts']['victim_asset_net_raw'][a].items()};delta={t:cf.get(t,0)-ac.get(t,0) for t in set(ac)|set(cf)};delta={t:v for t,v in delta.items() if v};marks=[book.value(t,v,integer(head['timestamp'])) for t,v in delta.items()];usd=str(sum((Decimal(m['USD']) for m in marks),Decimal(0))) if all(m['USD'] is not None for m in marks) else None;inputs_same=all(cf.get(t,0)==v for t,v in ac.items() if v<0) and all(ac.get(t,0)==v for t,v in cf.items() if v<0);effects.append({'address':a,'inputs_unchanged':inputs_same,'without_front_minus_actual_raw':{t:str(v) for t,v in delta.items()},'weakly_dominates_actual':all(v>=0 for v in delta.values()),'reference_asset_improvement_USD':usd,'valuations':marks})
                row.update(status='verified_conditional_front_removal',victim_effects=effects)
        rows.append(row);flush();engine.cache.clear();print(n,len(rows),'/',len(queue),row['status'],flush=True)
    result=flush();print('finished',result['completed'],result['statuses'],flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);a=parser.parse_args();run(a.limit)
