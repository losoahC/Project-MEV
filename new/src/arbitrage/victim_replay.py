"""Fresh historical fixed-call interventions removing a front leg BEFORE the victim.
Audit the entire actual prefix first. Never replace failed counterfactuals with quotes.
"""
import json,hashlib,base64,requests,datetime,argparse
from decimal import Decimal
from collections import defaultdict
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net
from src.arbitrage.replay_audit import txcall,NATIVE
from src.decoding.events import integer,WETH
from src.arbitrage.value_candidates import book_from_archive

def request(params):
    req={'jsonrpc':'2.0','id':1,'method':'eth_simulateV1','params':params};key=hashlib.sha256(json.dumps(req,sort_keys=True).encode()).hexdigest();path=ROOT/'data/raw/victim_simulations'/f'{key}.json';path.parent.mkdir(exist_ok=True)
    if path.exists():return json.loads(path.read_text()),str(path.relative_to(ROOT))
    doc={'request':req,'endpoint':'https://eth.drpc.org','acquired_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        r=requests.post(doc['endpoint'],json=req,timeout=55);doc.update(http_status=r.status_code,response_body_base64=base64.b64encode(r.content).decode(),response_body_sha256=hashlib.sha256(r.content).hexdigest());doc['response']=r.json()
    except Exception as ex:doc['transport_error']=str(ex)
    path.write_text(json.dumps(doc,indent=2));return doc,str(path.relative_to(ROOT))

def balance(sim,a):
    d=token_net(sim,{a});d['native:eth']=d.pop(WETH,0)+d.pop(NATIVE,0);return {t:v for t,v in d.items() if v}

def run(limit=3):
    out=ROOT/'data/processed/mev_full_window';raw=json.loads((out/'local_victim_effects.json').read_text());eligible=[r for r in raw['rows'] if r['status']=='verified_conditional_local_v2_quote' and r['valuation']['USD'] is not None];eligible.sort(key=lambda r:Decimal(r['valuation']['USD']),reverse=True);engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();rows=json.loads((out/'victim_replays.json').read_text())['rows'] if (out/'victim_replays.json').exists() else []
    done={(x['target'],x['removed_front']) for x in rows};eligible=[r for r in eligible if (r['target'],r['front']) not in done]
    for lead in eligible[:limit]:
        n=lead['block'];head,rs,_,paths=engine.block(n);target=lead['target'];front=lead['front'];last=integer(rs[target]['transactionIndex']);prefix=head['transactions'][:last+1];findex=integer(rs[front]['transactionIndex']);sender=rs[front]['from'].lower();result={'block':n,'target':target,'removed_front':front,'victim_addresses':lead['victim_addresses'],'local_quote_reduction_raw':lead['output_reduction_raw'],'evidence':paths,'gas_included_in_output_effect':False}
        if any(t['from'].lower()==sender for t in prefix[findex+1:]):result.update(status='nonce_dependency_requires_separate_intervention');rows.append(result);continue
        override={k:head[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};scenarios={};valid=True
        for label,txs in [('actual',prefix),('without_front',[t for t in prefix if t['hash']!=front])]:
            opt={'blockStateCalls':[{'blockOverrides':override,'calls':[txcall(t) for t in txs]}],'validation':True,'traceTransfers':True}
            doc,src=request([opt,hex(n-1)]);result['evidence'][label+'_simulation']=src
            if not doc.get('response',{}).get('result'):result.update(status='simulation_failed',failed_scenario=label,error=doc.get('response',doc.get('transport_error')));valid=False;break
            calls=doc['response']['result'][0]['calls']
            try:
                assert len(calls)==len(txs)
                if label=='actual':
                    def logs(ls):return [(l['address'].lower(),[t.lower() for t in l['topics']],l['data'].lower()) for l in ls if l['address'].lower()!=NATIVE]
                    for tx,sim in zip(txs,calls):
                        rc=rs[tx['hash']];assert integer(rc['status'])==integer(sim['status']) and integer(rc['gasUsed'])==integer(sim['gasUsed']) and logs(rc['logs'])==logs(sim['logs'])
                sim=calls[-1];assert txs[-1]['hash']==target
                scenarios[label]={'target_status':integer(sim['status']),'target_gas_used':integer(sim['gasUsed']),'error':sim.get('error'),'victim_net_raw':{a:{t:str(v) for t,v in balance(sim,a).items()} for a in lead['victim_addresses']}}
            except Exception as ex:result.update(status='baseline_or_prefix_validation_failed',failed_scenario=label,error=repr(ex));valid=False;break
        result['scenarios']=scenarios
        if valid:
            result['actual_prefix_transactions_reproduced']=len(prefix)
            if all(s['target_status']==1 for s in scenarios.values()):
                effects=[]
                for a in lead['victim_addresses']:
                    ac={t:int(v) for t,v in scenarios['actual']['victim_net_raw'][a].items()};cf={t:int(v) for t,v in scenarios['without_front']['victim_net_raw'][a].items()};delta={t:cf.get(t,0)-ac.get(t,0) for t in set(ac)|set(cf)};delta={t:v for t,v in delta.items() if v};unchanged=all(cf.get(t,0)==v for t,v in ac.items() if v<0) and all(ac.get(t,0)==v for t,v in cf.items() if v<0)
                    marks=[book.value(t,v,integer(head['timestamp'])) for t,v in delta.items()];usd=str(sum((Decimal(v['USD']) for v in marks),Decimal(0))) if all(v['USD'] is not None for v in marks) else None
                    effects.append({'address':a,'inputs_unchanged':unchanged,'without_front_minus_actual_asset_raw':{t:str(v) for t,v in delta.items()},'marked_output_improvement_USD':usd,'valuation':marks})
                result.update(status='verified_fixed_call_victim_intervention',victim_effects=effects)
            else:result['status']='verified_prefix_counterfactual_target_reverted'
        result['limit']='Conditional historical fixed-call execution, removing only one front transaction. Other calls, quotes, signatures and policy are not reoptimized. Not whole-event MEV, not equilibrium loss, not directly equal to bot profit.'
        rows.append(result);engine.cache.clear();print(n,result['status'],flush=True)
    (out/'victim_replays.json').write_text(json.dumps({'rows':rows,'whole_event_loss_established':False,'method':'Fresh archived eth_simulateV1 historical prefix; actual status/gas/logs must reproduce before target effect accepted.'},indent=2));print('Completed attempts',len(rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=3);a=p.parse_args();run(a.limit)
