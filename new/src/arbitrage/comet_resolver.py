"""Transaction-specific Comet equity audit, verified with historical prefix executions.
Diagnostic views are appended after actual transactions; their gas is NOT trade cost.
"""
import json
from decimal import Decimal
from eth_abi import encode,decode
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.replay_audit import txcall,NATIVE
from src.arbitrage.victim_replay import request
from src.arbitrage.accounting import cashflow
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.value_candidates import book_from_archive
from src.decoding.events import integer,WETH,USDT
from src.reconciliation.inventory import MULTICALL

BLOCK=26300895
TX='0x3fd5ec345eaf60faca94c652f5ac5c0dca77b4ef3c355fb12cb8f5108464a0b6'
COMET='0xa17581a9e3356d9a858b789d68b4d866e593ae94'
RESOLVER='0x9b1303ebf09bc51b7fac376c9e421e8daae63b82'

def selector(sig):return Web3.keccak(text=sig)[:4]

def run():
    engine=Reconstruction(ROOT.parent/'research',False);h,rs,tr,paths=engine.block(BLOCK);rc=rs[TX];idx=integer(rc['transactionIndex']);boundary={RESOLVER,rc['from'].lower()}
    jobs=[('base_token','baseToken()',[],[]),('supply_raw','balanceOf(address)',['address'],[RESOLVER]),('borrow_raw','borrowBalanceOf(address)',['address'],[RESOLVER]),('USDT_collateral_raw','collateralBalanceOf(address,address)',['address','address'],[RESOLVER,USDT])]
    calldata='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(COMET,False,selector(sig)+encode(types,args)) for _,sig,types,args in jobs]])).hex()
    # Use a funded, externally owned account already present in the block. No overrides.
    diagnostic={'from':rc['from'],'to':MULTICALL,'gas':'0x1e8480','gasPrice':h['baseFeePerGas'],'value':'0x0','input':calldata}
    override={k:h[v] for k,v in {'number':'number','time':'timestamp','gasLimit':'gasLimit','feeRecipient':'miner','prevRandao':'mixHash','baseFeePerGas':'baseFeePerGas'}.items()};states={};sources={};reproduced=0
    def norm(logs):return [(l['address'].lower(),[t.lower() for t in l['topics']],l['data'].lower()) for l in logs if l['address'].lower()!=NATIVE]
    for label,end in [('before',idx),('after',idx+1)]:
        prefix=h['transactions'][:end];params=[{'blockStateCalls':[{'blockOverrides':override,'calls':[txcall(t) for t in prefix]+[diagnostic]}],'validation':True,'traceTransfers':True},hex(BLOCK-1)]
        doc,source=request(params);sources[label]=source
        if not doc.get('response',{}).get('result'):raise RuntimeError((label,doc.get('response',doc.get('transport_error'))))
        sims=doc['response']['result'][0]['calls'];assert len(sims)==len(prefix)+1
        for tx,sim in zip(prefix,sims):
            actual=rs[tx['hash']];assert integer(actual['status'])==integer(sim['status']) and integer(actual['gasUsed'])==integer(sim['gasUsed']) and norm(actual['logs'])==norm(sim['logs'])
        reproduced+=len(prefix);diagnosis=sims[-1];assert integer(diagnosis['status'])==1
        values=decode(['(bool,bytes)[]'],bytes.fromhex(diagnosis['returnData'][2:]))[0];assert len(values)==len(jobs);state={}
        for (name,_,_,_),(ok,data) in zip(jobs,values):
            assert ok and len(data)==32;state[name]='0x'+data[-20:].hex() if name=='base_token' else str(int.from_bytes(data,'big'))
        assert state['base_token']==WETH;states[label]=state
    cf=cashflow(rc,tr[TX],boundary,h['miner']);liquid={t:int(v) for t,v in cf['token_net_raw'].items() if t!=COMET};liquid['native:eth']=int(cf['native_net_wei'])-int(cf['gas_wei']);positions={WETH:(int(states['after']['supply_raw'])-int(states['before']['supply_raw']))-(int(states['after']['borrow_raw'])-int(states['before']['borrow_raw'])),USDT:int(states['after']['USDT_collateral_raw'])-int(states['before']['USDT_collateral_raw'])};equity={t:liquid.get(t,0)+positions.get(t,0) for t in set(liquid)|set(positions)};equity={t:v for t,v in equity.items() if v}
    book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('USDC',('2026-10-29','2026-10-30'));marks=[book.value(t,v,integer(h['timestamp'])) for t,v in equity.items()];net=str(sum((Decimal(v['USD']) for v in marks),Decimal(0))) if all(v['USD'] is not None for v in marks) else None
    result={'tx_hash':TX,'block':BLOCK,'boundary':sorted(boundary),'common_beneficial_ownership_proven':False,'comet':COMET,'position_owner':RESOLVER,'states':states,'actual_cashflow':cf,'liquid_change_after_actual_gas_raw':{t:str(v) for t,v in liquid.items() if v},'position_equity_change_raw':{t:str(v) for t,v in positions.items() if v},'combined_equity_change_raw':{t:str(v) for t,v in equity.items()},'reference_valuations':marks,'reference_equity_gain_after_gas_USD':net,'actual_prefix_transaction_comparisons':reproduced,'evidence':{**paths,'prefix_state_diagnostics':sources},'mechanism':'Order resolver uses received USDT as collateral and borrows WETH from Compound to fulfil the order. Equity accounting adds collateral and subtracts debt; borrowed cash is not profit.','MEV_classification':'Order-filling execution spread; transaction ordering causation not established. Not classified as MEV from gas or Compound borrowing.','limits':['Prefix RPC reproduces actual statuses/gas/logs; not a consensus state-root proof.','Diagnostic view-call gas is excluded; only actual transaction gas is deducted.','Marked position equity at transaction time, not liquidation proceeds, ultimate owner PnL or eventual debt repayment.','External payments remain outside the stated boundary; no common ownership inferred.'],'protocol_interface_source':'https://raw.githubusercontent.com/compound-finance/comet/main/contracts/CometMainInterface.sol'}
    (ROOT/'data/processed/mev_full_window/comet_resolver_equity.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['states','combined_equity_change_raw','reference_equity_gain_after_gas_USD']},indent=2))
if __name__=='__main__':run()
