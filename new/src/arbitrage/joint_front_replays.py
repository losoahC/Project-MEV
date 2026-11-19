"""One joint front-removal intervention per block; target hashes counted once.
Independent block-start states are explicit, not a continuous all-incident scenario.
"""
import json,time
from collections import defaultdict,Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.replay_audit import txcall,NATIVE
from src.arbitrage.victim_replay import request,balance
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.decoding.events import integer
from src.arbitrage.complete_surplus_ledger import claim_event,ZERO

def assets(sim,a):
    result=balance(sim,a)
    for l in sim.get('logs',[]):
        c=claim_event(l)
        if c and a!=ZERO:
            key='claim:'+c['currency'];result[key]=result.get(key,0)+int(c['amount_raw'])*((c['recipient']==a)-(c['sender']==a))
    return {t:v for t,v in result.items() if v}

def run():
    p=ROOT/'data/processed/mev_full_window';source=json.loads((p/'expanded_front_replays.json').read_text());byblock=defaultdict(list)
    for r in source['rows']:byblock[r['block']].append(r)
    dest=p/'joint_front_replays.json';rows=json.loads(dest.read_text())['rows'] if dest.exists() else [];done={r['block'] for r in rows};engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('USDC',('2026-10-29','2026-10-30'));next_request=0
    def flush():
        summary={'blocks':len(rows),'planned_blocks':len(byblock),'statuses':dict(Counter(r['status'] for r in rows)),'unique_target_transactions':len({e['target'] for r in rows for e in r.get('target_effects',[])}),'separate_block_start_states':True,'continuous_event_counterfactual':False}
        doc={'summary':summary,'rows':rows};dest.write_text(json.dumps(doc,indent=2));return summary
    for n,leads in sorted(byblock.items()):
        if n in done:continue
        # Single-target blocks reuse the identical independently validated simulation.
        head,rs,tr,paths=engine.block(n);fronts={h for lead in leads for h in lead['fronts']};senders={r['sender'] for r in leads};targets={r['target']:r['victim_addresses'] for r in leads};last=max(integer(rs[h]['transactionIndex']) for h in targets);prefix=head['transactions'][:last+1];row={'block':n,'removed_fronts':sorted(fronts),'senders':sorted(senders),'targets':sorted(targets),'evidence':paths,'target_effects':[],'nonce_reassignment':'Only remaining transactions of removed senders omit nonce; fixed calldata/value/to/gas/fees. This is a simulated intervention, not a rebroadcast of signed transactions.'}
        if any(t['hash'] not in fronts and t['from'].lower() in senders and (not t.get('to') or any(x['type']=='create' for x in tr[t['hash']])) for t in prefix):
            row['status']='CREATE_nonce_dependency_excluded';rows.append(row);flush();continue
        override={k:head[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={};valid=True
        for label,txs in [('actual',prefix),('without_fronts',[t for t in prefix if t['hash'] not in fronts])]:
            calls=[txcall(t) for t in txs]
            if label!='actual':
                for t,c in zip(txs,calls):
                    if t['from'].lower() in senders:c.pop('nonce',None)
            params=[{'blockStateCalls':[{'blockOverrides':override,'calls':calls}],'validation':True,'traceTransfers':True},hex(n-1)];time.sleep(max(0,next_request-time.monotonic()));doc,src=request(params);next_request=time.monotonic()+1.15;row['evidence'][label+'_simulation']=src;result=doc.get('response',{}).get('result')
            if not result:row.update(status='RPC_execution_response_error',failed_scenario=label,error=doc.get('response',doc.get('transport_error')));valid=False;break
            sims=result[0]['calls']
            try:
                assert len(sims)==len(txs)
                if label=='actual':
                    norm=lambda ls:[(l['address'].lower(),[t.lower() for t in l['topics']],l['data'].lower()) for l in ls if l['address'].lower()!=NATIVE]
                    for tx,sim in zip(txs,sims):
                        rc=rs[tx['hash']];assert integer(rc['status'])==integer(sim['status']) and integer(rc['gasUsed'])==integer(sim['gasUsed']) and norm(rc['logs'])==norm(sim['logs'])
                scenarios[label]={t['hash']:sim for t,sim in zip(txs,sims) if t['hash'] in targets}
            except Exception as ex:row.update(status='baseline_or_sequence_validation_failed',error=repr(ex));valid=False;break
        if valid:
            row['actual_prefix_transactions_reproduced']=len(prefix);row['status']='verified_joint_block_intervention'
            for target,addresses in targets.items():
                actual=scenarios['actual'][target];cf=scenarios['without_fronts'][target];effect={'target':target,'actual_status':integer(actual['status']),'counterfactual_status':integer(cf['status']),'addresses':[]}
                for a in addresses:
                    ac=assets(actual,a);cc=assets(cf,a);delta={t:cc.get(t,0)-ac.get(t,0) for t in set(ac)|set(cc)};delta={t:v for t,v in delta.items() if v};same=all(cc.get(t,0)==v for t,v in ac.items() if v<0) and all(ac.get(t,0)==v for t,v in cc.items() if v<0);marks=[book.value(t,v,integer(head['timestamp'])) for t,v in delta.items()];usd=str(sum((Decimal(m['USD']) for m in marks),Decimal(0))) if all(m['USD'] is not None for m in marks) else None;effect['addresses'].append({'address':a,'actual_net_raw':{t:str(v) for t,v in ac.items()},'counterfactual_net_raw':{t:str(v) for t,v in cc.items()},'difference_raw':{t:str(v) for t,v in delta.items()},'inputs_unchanged':same,'weakly_dominates_actual':all(v>=0 for v in delta.values()),'reference_output_difference_USD':usd,'valuations':marks})
                row['target_effects'].append(effect)
        rows.append(row);flush();engine.cache.clear();print(n,len(rows),'/',len(byblock),row['status'],flush=True)
    print(json.dumps(flush(),indent=2),flush=True)
if __name__=='__main__':run()
