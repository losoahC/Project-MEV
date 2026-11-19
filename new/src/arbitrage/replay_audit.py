"""Independently audit archived RPC EVM executions; do not import prior numeric reports."""
import json
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,cashflow
from src.ingestion.evidence import read_json
from src.decoding.events import integer,WETH
getcontext().prec=90
NATIVE='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'

def txcall(t):
    keys=['from','to','gas','value','input','nonce','accessList','authorizationList','maxFeePerBlobGas','blobVersionedHashes']
    keys+=['maxFeePerGas','maxPriorityFeePerGas'] if 'maxFeePerGas' in t else ['gasPrice']
    return {k:t[k] for k in keys if k in t}

def run():
    out=ROOT/'data/processed/mev_full_window';engine=Reconstruction(ROOT.parent/'research',False);spec=read_json(ROOT/'data/fixtures/arbitrage_cases.json');selected=[spec['sandwich']]+spec['cases'][1:];rows=[];baseline_count=0
    for c in selected:
        n=c['block'];head,rs,tr,paths=engine.block(n);transactions=head['transactions'];assert all(isinstance(t,dict) for t in transactions)
        def source(suffix):
            p=engine.legacy/'evm_replay_raw'/f'{n}_{suffix}.json.gz';ref=engine.store.archive(p,'Archived public Ethereum simulation RPC; original acquisition date not certified','eth_simulateV1');return read_json(ROOT/ref),ref
        raw,bsource=source('baseline');calls=raw['response']['result'][0]['calls'];assert len(calls)==len(transactions)
        def norm(logs):return [(l['address'].lower(),[t.lower() for t in l['topics']],l['data'].lower()) for l in logs if l['address'].lower()!=NATIVE]
        for tx,sc in zip(transactions,calls):
            rc=rs[tx['hash']];assert integer(rc['status'])==integer(sc['status']) and integer(rc['gasUsed'])==integer(sc['gasUsed']) and norm(rc['logs'])==norm(sc['logs'])
        baseline_count+=len(calls)
        legs={c['front'],c['back']} if c['case_id']=='S1' else {c['tx_hash']};accounts=set(c['accounts']);tag='strong' if c['case_id']=='S1' else 'two_pool';result={'case_id':c['case_id'],'block':n,'target':c['target'],'accounts':sorted(accounts),'baseline_transactions_reproduced':len(calls),'evidence':{**paths,'baseline_simulation':bsource},'scenarios':{}}
        last=max(integer(rs[h]['transactionIndex']) for h in legs);prefix=transactions[:last+1];targetindex=next(i for i,t in enumerate(prefix) if t['hash']==c['target'])
        for scenario in ['actual','remove_target']:
            raw,src=source(tag+'_'+scenario);req=raw['request'];opt=req['params'][0];assert req['method']=='eth_simulateV1' and opt['validation'] is True and opt['traceTransfers'] is True and req['params'][1]==hex(n-1)
            assert len(opt['blockStateCalls'])==1;block=opt['blockStateCalls'][0];assert not block.get('stateOverrides')
            expected={'number':head['number'],'time':head['timestamp'],'gasLimit':head['gasLimit'],'feeRecipient':head['miner'],'prevRandao':head['mixHash'],'baseFeePerGas':head['baseFeePerGas']}
            assert block['blockOverrides']==expected
            txs=prefix if scenario=='actual' else prefix[:targetindex]+prefix[targetindex+1:];assert block['calls']==[txcall(t) for t in txs]
            sims=raw['response']['result'][0]['calls'];assert len(sims)==len(txs);net=0;other={};details=[]
            for tx,sc in zip(txs,sims):
                if scenario=='actual':
                    rc=rs[tx['hash']];assert integer(rc['status'])==integer(sc['status']) and integer(rc['gasUsed'])==integer(sc['gasUsed']) and norm(rc['logs'])==norm(sc['logs'])
                if tx['hash'] not in legs:continue
                balance=token_net(sc,accounts);gas=integer(sc['gasUsed'])*integer(rs[tx['hash']]['effectiveGasPrice']);net+=balance.pop(WETH,0)+balance.pop(NATIVE,0)-gas
                for t,v in balance.items():other[t]=other.get(t,0)+v
                details.append({'tx_hash':tx['hash'],'status':integer(sc['status']),'gas_wei':str(gas),'error':sc.get('error')})
            actualtrace=sum((Decimal(cashflow(rs[h],tr[h],accounts,head['miner'])['net_after_gas_and_builder_ETH']) for h in legs),Decimal(0)) if scenario=='actual' else None
            value=Decimal(net)/Decimal(10)**18
            if actualtrace is not None:assert value==actualtrace
            result['scenarios'][scenario]={'net_cashflow_ETH':str(value),'other_token_residual_raw':{t:str(v) for t,v in other.items() if v},'legs':details};result['evidence'][scenario+'_simulation']=src
        result['actual_minus_removed_target_cashflow_ETH']=str(Decimal(result['scenarios']['actual']['net_cashflow_ETH'])-Decimal(result['scenarios']['remove_target']['net_cashflow_ETH']))
        result['interpretation']='Fixed-original-call target-removal sensitivity, not victim loss or optimal alternative profit. A reverted exit can leave economically valuable untracked/non-boundary inventory; negative cashflow is not all-in wealth loss. RPC simulation response audited offline, not a fresh local EVM execution or consensus proof.'
        rows.append(result);engine.cache.clear()
    engine.store.save();summary={'cases':len(rows),'baseline_transactions_status_gas_logs_reproduced':baseline_count,'rows':rows,'hacker_incremental_loss_proven':False,'not_additive':True,'simulation_documentation':'https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-eth'}
    (out/'replay_audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2));print([(x['case_id'],x['actual_minus_removed_target_cashflow_ETH']) for x in rows])
if __name__=='__main__':run()
