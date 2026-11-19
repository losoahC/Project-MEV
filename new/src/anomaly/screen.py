import argparse
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal,getcontext
import json

import pandas as pd
from web3 import Web3

from src.arbitrage.reconstruct import Reconstruction,ROOT,save
from src.arbitrage.accounting import token_net,native_flows,cashflow,SYNC,v2_execution_decomposition
from src.decoding.events import integer,swap,transfer,WETH,SWAP_V2,SWAP_V3
from src.decoding.router import inspect_router
from src.ingestion.evidence import read_json
from src.reconciliation.pricebook import PriceBook

getcontext().prec=90
SWAPS={SWAP_V2,SWAP_V3,'0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f','0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83'}
POSITION_EVENTS=['Mint(address,address,int24,int24,uint128,uint256,uint256)','Burn(address,int24,int24,uint128,uint256,uint256)','Collect(address,address,int24,int24,uint128,uint128)','Mint(address,uint256,uint256)','Burn(address,uint256,uint256,address)','ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)','Borrow(address,address,address,uint256,uint8,uint256,uint16)','Repay(address,address,address,uint256,bool)','Supply(address,address,address,uint256,uint16)','Withdraw(address,address,address,uint256)','LiquidationCall(address,address,address,uint256,uint256,address,bool)']
POSITION_TOPICS={'0x'+Web3.keccak(text=s).hex().removeprefix('0x'):s for s in POSITION_EVENTS}


def pool_events(receipt):
    out=[]
    for log in receipt['logs']:
        topics=log.get('topics',[])
        if topics and topics[0].lower() in SWAPS:
            key=log['address'].lower()+(':'+topics[1].lower() if topics[0].lower().startswith('0x40e9') else '')
            out.append({'pool_key':key,'pool':log['address'].lower(),'log_index':integer(log['logIndex']),'topic':topics[0].lower()})
    return out


def classify_loss(input_usd,output_usd,position_events=False,internal_wallet_transfer=False):
    if input_usd is None or output_usd is None:
        return {'loss_USD':None,'loss_rate':None,'qualifies':False,'reason':'incomplete_valuation'}
    inp,out=Decimal(input_usd),Decimal(output_usd)
    if inp<=0 or out<=0:
        return {'loss_USD':None,'loss_rate':None,'qualifies':False,'reason':'not_a_two_sided_observable_net_exchange'}
    loss=inp-out;rate=1-out/inp
    eligible=not position_events and not internal_wallet_transfer
    return {'loss_USD':str(loss),'loss_rate':str(rate),'qualifies':eligible and inp>100000 and rate>Decimal('.05'),'reason':'reference_shortfall_screen_only' if eligible else 'mixed_positions_or_internal_wallet_flows','valuation_complete':True}


def value_net(book,nets,ts,stale=0,lookback=1,eth_venue='Coinbase'):
    assets=[book.value(t,raw,ts,stale,lookback,eth_venue) for t,raw in sorted(nets.items()) if raw]
    missing=[v for v in assets if v['USD'] is None]
    inp=sum((-Decimal(v['USD']) for v in assets if v['USD'] is not None and int(v['raw'])<0),Decimal(0))
    out=sum((Decimal(v['USD']) for v in assets if v['USD'] is not None and int(v['raw'])>0),Decimal(0))
    return {'input_reference_USD':str(inp) if not missing else None,'output_reference_USD':str(out) if not missing else None,'assets':assets,'missing_assets':missing}


def run(online=False,legacy=None):
    engine=Reconstruction(legacy or ROOT.parent/'research',online)
    book=PriceBook(engine)
    book.binance_eth()
    registry=read_json(ROOT/'data/processed/wallet_registry.json');wallets={w['address']:w for w in registry}
    txs=pd.read_parquet(ROOT/'data/processed/transactions.parquet')
    wanted=txs.groupby('block_number').tx_hash.apply(set)
    rows=[];raw_records=[];excluded=[];first_seen={}
    for i,(number,hashes) in enumerate(wanted.items(),1):
        header,receipts,traces,paths=engine.block(int(number));ts=integer(header['timestamp'])
        for h in sorted(hashes):
            receipt=receipts[h]
            events=pool_events(receipt)
            if integer(receipt['status'])!=1 or not events:
                continue
            if not traces[h]:
                excluded.append({'tx_hash':h,'reason':'missing_native_call_tree'});continue
            flows=native_flows(traces[h])
            position=[{'emitter':l['address'],'event':POSITION_TOPICS[l['topics'][0].lower()]} for l in receipt['logs'] if l.get('topics') and l['topics'][0].lower() in POSITION_TOPICS]
            internal=any(f['sender'] in wallets and f['recipient'] in wallets and f['sender']!=f['recipient'] for f in flows)
            internal|=any(t and t['sender'] in wallets and t['recipient'] in wallets and t['sender']!=t['recipient'] and int(t['amount_raw'])>0 for t in (transfer(l) for l in receipt['logs']))
            for address,w in wallets.items():
                net=token_net(receipt,{address})
                native=sum(int(f['amount_raw'])*((f['recipient']==address)-(f['sender']==address)) for f in flows)
                eth=net.pop(WETH,0)+native
                if eth:
                    net['native:eth']=eth
                if not any(v<0 for v in net.values()) or not any(v>0 for v in net.values()):
                    continue
                for token in net:
                    if token in book.registry and token!='native:eth':
                        first_seen.setdefault(token,int(number))
                raw_records.append({'wallet':w['number'],'address':address,'identity_confidence':w['identity_confidence'],'tx_hash':h,'block':int(number),'transaction_index':integer(receipt['transactionIndex']),'timestamp':ts,'timestamp_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat(),'net_asset_raw':{t:str(v) for t,v in net.items()},'position_or_debt_events':position,'internal_wallet_transfer':bool(internal),'swap_event_count':len(events),'swap_pool_keys':sorted({e['pool_key'] for e in events}),
                    'gas_paid_by_wallet_wei':str(integer(receipt['gasUsed'])*integer(receipt['effectiveGasPrice'])) if receipt['from'].lower()==address else '0','receipt_evidence':paths['receipts'],'trace_evidence':paths['traces'],'header_evidence':paths['header']})
        engine.cache.clear()
        if i%200==0:
            print(f'Anomaly reconstruction: {i}/{len(wanted)} blocks; {len(raw_records)} two-sided wallet exchanges',flush=True)
    # Historical decimals checks use the first observed swap block per contract.
    print(f'Checking historical decimals for {len(first_seen)} contract-matched assets',flush=True)
    def decimals(task):
        token,number=task
        try:
            response,source=engine.public.call(token,'decimals()',number-1)
            return token,integer(response),source,None
        except (RuntimeError,FileNotFoundError,ValueError) as exc:
            return token,None,None,str(exc)
    decimal_audit=[]
    with ThreadPoolExecutor(max_workers=5) as executor:
        for token,value,source,error in executor.map(decimals,sorted(first_seen.items())):
            old=book.registry[token]['decimals']
            decimal_audit.append({'token':token,'metadata_decimals':old,'historical_rpc_decimals':value,'source':source,'error':error,'snapshot_block':first_seen[token]-1})
            if value is None or value!=old:
                book.registry.pop(token,None)
            else:
                book.registry[token]['decimal_basis']=source
    for raw in raw_records:
        net={t:int(v) for t,v in raw['net_asset_raw'].items()};valuation=value_net(book,net,raw['timestamp'])
        classification=classify_loss(valuation['input_reference_USD'],valuation['output_reference_USD'],bool(raw['position_or_debt_events']),raw['internal_wallet_transfer'])
        scenarios={}
        for label,stale,lookback,venue in [('stale_5min',5,1,'Coinbase'),('lookback_5min',0,5,'Coinbase'),('lookback_15min',0,15,'Coinbase'),('binance_ETH_same_minute',0,1,'Binance')]:
            v=value_net(book,net,raw['timestamp'],stale,lookback,venue)
            scenarios[label]={**classify_loss(v['input_reference_USD'],v['output_reference_USD'],bool(raw['position_or_debt_events']),raw['internal_wallet_transfer']),'input_reference_USD':v['input_reference_USD'],'output_reference_USD':v['output_reference_USD'],'missing_contracts':[a['address'] for a in v['missing_assets']]}
        rows.append({**raw,**valuation,**classification,'sensitivity':scenarios,'classification':'insufficient_evidence' if classification['qualifies'] else 'not_flagged_or_not_identified','intent':'unresolved; no intent inferred from economic loss','priority_million_plus':classification['loss_USD'] is not None and Decimal(classification['loss_USD'])>1000000,'five_million_focus':classification['loss_USD'] is not None and Decimal(classification['loss_USD'])>=5000000})
    qualifying=sorted([r for r in rows if r['qualifies']],key=lambda r:Decimal(r['loss_USD']),reverse=True)
    repeat=Counter(r['address'] for r in qualifying)
    for rank,row in enumerate(qualifying,1):
        row['rank']=rank;row['wallet_qualifying_swap_count']=repeat[row['address']]
    save(ROOT/'data/processed/wallet_swap_valuations.json',rows)
    save(ROOT/'data/processed/anomaly_decimal_audit.json',decimal_audit)
    save(ROOT/'data/processed/anomaly_excluded.json',excluded)
    def flat(row):
        return {k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()}
    pd.DataFrame([flat(r) for r in rows]).to_parquet(ROOT/'data/processed/wallet_swap_valuations.parquet',index=False)
    pd.DataFrame([flat(r) for r in qualifying]).to_parquet(ROOT/'data/processed/suspicious_transactions.parquet',index=False)
    book.dump(ROOT/'data/processed/historical_pricebook.json')
    save(ROOT/'data/processed/anomaly_coverage.json',{'wallets':16,'transactions_in_m1':len(txs),'two_sided_swap_wallet_rows':len(rows),'fully_valued_rows':sum(r['input_reference_USD'] is not None for r in rows),'qualified_rows':len(qualifying),'million_plus_qualified':sum(r['priority_million_plus'] for r in qualifying),'five_million_plus_qualified':sum(r['five_million_focus'] for r in qualifying),'price_conflicts':len(book.conflicts),'excluded_missing_native_traces':len(excluded),'sum_signed_reference_shortfall_priced_rows_USD':str(sum((Decimal(r['loss_USD']) for r in rows if r['loss_USD'] is not None),Decimal(0))),'limits':['Wallet rows can share a transaction. This sum is not a deduplicated event loss reconciliation.','Reference-value shortfall is estimated, not intentional loss or MEV profit.','Position/debt and inter-wallet mixed transfers do not qualify as simple execution losses.','Unknown contract identity and missing/conflicting prices remain null.','Only the existing M1 event window and 16 wallet leads are screened.']})
    engine.store.save();engine.public.write_index()
    print(f'Screened {len(rows)} two-sided swap rows, {len(qualifying)} qualify; {sum(r["five_million_focus"] for r in qualifying)} exceed $5M reference shortfall')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--legacy');a=p.parse_args();run(a.online,a.legacy)
