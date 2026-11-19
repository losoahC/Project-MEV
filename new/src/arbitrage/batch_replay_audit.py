"""Audit all archived target-removal experiments from raw requests/responses.
The old report supplies experiment identifiers/accounts only, never trusted outcomes.
"""
import json
from collections import Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,cashflow
from src.arbitrage.replay_audit import txcall,NATIVE
from src.decoding.events import integer,WETH
from src.ingestion.evidence import read_json
getcontext().prec=90
E=Decimal(10)**18

def run():
    p=ROOT/'data/processed/mev_full_window';index=read_json(ROOT.parent/'research/expanded_EVM_attribution.json')['rows'];public=set(read_json(p/'public_boundary_exclusions.json')['addresses']);targets={r['tx_hash'] for r in read_json(p/'targets.json')};engine=Reconstruction(ROOT.parent/'research',False);results=[];prefixchecked=set()
    for i,item in enumerate(index,1):
        n=item['block'];h=item['hash'];target=item['removed_target'];accounts=set(item['accounts']);r={'block':n,'actor':h,'removed_target':target,'accounts':sorted(accounts),'boundary_includes_public_service':bool(accounts&public),'public_services':sorted(accounts&public),'target_in_current_monitored_scope':target in targets,'MEV_criterion':'Fixed-call target-removal response; not high gas alone','status':'unverified','scenarios':{},'evidence':{}}
        try:
            head,rs,tr,paths=engine.block(n);r['evidence'].update(paths);last=integer(rs[h]['transactionIndex']);prefix=head['transactions'][:last+1];assert all(isinstance(tx,dict) for tx in prefix);assert target in {t['hash'] for t in prefix};assert rs[h]['from'].lower() in accounts
            expected={'number':head['number'],'time':head['timestamp'],'gasLimit':head['gasLimit'],'feeRecipient':head['miner'],'prevRandao':head['mixHash'],'baseFeePerGas':head['baseFeePerGas']}
            allscenarios=True
            for name,suffix in [('actual','actual'),('remove_target',target[2:])]:
                path=engine.legacy/'evm_replay_raw'/f'{n}_{h[2:]}_{suffix}.json.gz';src=engine.store.archive(path,'Archived public simulation RPC response; original acquisition time uncertified','eth_simulateV1');doc=read_json(ROOT/src);req=doc['request'];opts=req['params'][0];r['evidence'][name]=src
                assert req['method']=='eth_simulateV1' and req['params'][1]==hex(n-1) and opts['validation'] is True and opts['traceTransfers'] is True and len(opts['blockStateCalls'])==1
                block=opts['blockStateCalls'][0];assert not block.get('stateOverrides') and block['blockOverrides']==expected
                chosen=prefix if name=='actual' else [t for t in prefix if t['hash']!=target];assert block['calls']==[txcall(t) for t in chosen]
                if not doc.get('response',{}).get('result'):
                    r['scenarios'][name]={'response_error':doc.get('response')};allscenarios=False;continue
                calls=doc['response']['result'][0]['calls'];assert len(calls)==len(chosen)
                def logs(ls):return [(l['address'].lower(),[v.lower() for v in l['topics']],l['data'].lower()) for l in ls if l['address'].lower()!=NATIVE]
                if name=='actual':
                    for tx,sc in zip(chosen,calls):
                        rc=rs[tx['hash']];assert integer(rc['status'])==integer(sc['status']) and integer(rc['gasUsed'])==integer(sc['gasUsed']) and logs(rc['logs'])==logs(sc['logs']);prefixchecked.add(tx['hash'])
                sc=calls[-1];assert chosen[-1]['hash']==h;net=token_net(sc,accounts);amount=net.pop(WETH,0)+net.pop(NATIVE,0)-integer(sc['gasUsed'])*integer(rs[h]['effectiveGasPrice']);value=Decimal(amount)/E
                if name=='actual':assert value==Decimal(cashflow(rs[h],tr[h],accounts,head['miner'])['net_after_gas_and_builder_ETH'])
                r['scenarios'][name]={'status':integer(sc['status']),'gas_used':integer(sc['gasUsed']),'net_joint_ETH':str(value),'other_token_residual_raw':{t:str(v) for t,v in net.items() if v},'error':sc.get('error')}
            r['actual_prefix_transactions_reproduced']=len(prefix)
            if allscenarios:
                delta=Decimal(r['scenarios']['actual']['net_joint_ETH'])-Decimal(r['scenarios']['remove_target']['net_joint_ETH']);r.update(status='verified_archived_fixed_call_intervention',actual_minus_removed_target_ETH=str(delta),positive_dependency=delta>0)
            else:r['status']='actual_prefix_verified_counterfactual_response_error'
        except Exception as ex:r.update(status='audit_failed_or_source_missing',error=repr(ex))
        r['interpretation']='Archived RPC simulation audited from request parameters and reproduced actual prefix. Addresses are a stated operational boundary, not common ownership. Public-service boundaries must not be counted as bot profit. Differences across overlapping interventions cannot be added; failed alternative submission costs are not observed realized profit.';results.append(r);engine.cache.clear()
        if i%50==0:print('batch replay audited',i,'/',len(index),flush=True)
    engine.store.save();summary={'experiments':len(results),'statuses':dict(Counter(r['status'] for r in results)),'unique_actual_prefix_transactions_reproduced':len(prefixchecked),'public_service_boundaries':sum(r['boundary_includes_public_service'] for r in results),'within_current_target_scope':sum(r['target_in_current_monitored_scope'] for r in results),'positive_differences':sum(r.get('positive_dependency') is True for r in results),'nonpositive_differences':sum(r.get('positive_dependency') is False for r in results),'whole_event_causal_total_established':False};(p/'batch_target_removal_audit.json').write_text(json.dumps({'summary':summary,'rows':results},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
