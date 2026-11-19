"""Deep-dive the five largest qualifying losses without inferring intent or causal MEV."""
import argparse
from collections import defaultdict
from decimal import Decimal
import json

import pandas as pd

from src.anomaly.screen import pool_events
from src.arbitrage.reconstruct import Reconstruction,ROOT,save
from src.arbitrage.accounting import cashflow,SYNC,v2_execution_decomposition
from src.decoding.events import swap,integer,WETH,successful_trace
from src.decoding.router import inspect_router
from src.ingestion.evidence import read_json
from src.reconciliation.pricebook import PriceBook


def investigate(online=False,legacy=None):
    engine=Reconstruction(legacy or ROOT.parent/'research',online)
    rows=read_json(ROOT/'data/processed/wallet_swap_valuations.json')
    qualifying=sorted([r for r in rows if r['qualifies']],key=lambda r:Decimal(r['loss_USD']),reverse=True)
    known_arbitrages=read_json(ROOT/'data/processed/arbitrage_cases.json')
    edges=pd.read_parquet(ROOT/'data/processed/wallet_edges.parquet')
    book=PriceBook(engine)
    reports=[]
    for rank,row in enumerate(qualifying[:5],1):
        header,receipts,traces,paths=engine.block(row['block']);receipt=receipts[row['tx_hash']]
        transaction=next((t for t in header['transactions'] if isinstance(t,dict) and t['hash'].lower()==row['tx_hash']),None)
        if transaction is None:
            transaction,txsource=engine.public.rpc('eth_getTransactionByHash',[row['tx_hash']])
        else:
            txsource=paths['header']
        live,livesource=engine.public.rpc('eth_getTransactionReceipt',[row['tx_hash']])
        assert live['blockHash']==receipt['blockHash'] and live['logs']==receipt['logs'],'Fresh receipt disagrees with archived log authority'
        router=inspect_router(transaction['input'])
        failed=[t['traceAddress'] for t in traces[row['tx_hash']] if t.get('error')]
        router_calls=[]
        for tr in traces[row['tx_hash']]:
            action=tr.get('action',{})
            if tr.get('type')=='call' and successful_trace(tr,failed) and action.get('input','')[:10].lower() in ('0x3593564c','0x24856bc3'):
                router_calls.append({'trace_address':tr['traceAddress'],'call_type':action.get('callType'),'caller':action.get('from'),'callee':action.get('to'),'inspection':inspect_router(action['input'])})
        decoded_limits=[{**bound,'trace_address':call['trace_address']} for call in router_calls for bound in call['inspection'].get('limits',[])]
        candidates=[];targetpools=set(row['swap_pool_keys'])
        for h,r in receipts.items():
            if h==row['tx_hash'] or integer(r['status'])!=1:
                continue
            overlap=targetpools & {e['pool_key'] for e in pool_events(r)}
            if not overlap:
                continue
            idx=integer(r['transactionIndex']);info={'tx_hash':h,'transaction_index':idx,'relative_index':idx-row['transaction_index'],'shared_pools':sorted(overlap),'sender':r['from'],'executor':r.get('to'),'provisional_native_WETH_net_after_gas_ETH':None,'other_token_residual_raw':None}
            if traces[h] and r.get('to'):
                c=cashflow(r,traces[h],{r['from'].lower(),r['to'].lower()},header['miner'])
                info['provisional_native_WETH_net_after_gas_ETH']=c['net_after_gas_and_builder_ETH'];info['other_token_residual_raw']=c['other_token_residual_raw']
                info['boundary_limit']='Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link.'
            candidates.append(info)
        candidates.sort(key=lambda r:r['transaction_index'])
        mechanical=[];syncs={}
        for log in sorted(receipt['logs'],key=lambda l:integer(l['logIndex'])):
            if log.get('topics') and log['topics'][0].lower()==SYNC:
                syncs[log['address'].lower()]=[int(log['data'][i:i+64],16) for i in (2,66)]
            event=swap(log)
            if not event or not event['protocol'].startswith('V2'):
                continue
            after=syncs.get(event['pool'])
            if not after:
                continue
            amounts=[int(event['amount0_raw']),int(event['amount1_raw'])]
            if amounts[0]*amounts[1]>=0:
                continue
            before=[after[j]-amounts[j] for j in (0,1)];side=0 if amounts[0]>0 else 1
            d=v2_execution_decomposition(amounts[side],-amounts[1-side],before[side],before[1-side])
            mechanical.append({'pool':event['pool'],'log_index':event['log_index'],'before_reserves_raw':list(map(str,before)),'after_reserves_raw':list(map(str,after)),**d,'limit':'Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV.'})
        # Current route's ETH/USDT V3 price-state movement, without pretending a spot quote is a fixed-size route counterfactual.
        major='0x4e68ccd3e89f51c3074ca5072bbac773960dfa36'
        price_state=[]
        if any(e['pool']==major for e in pool_events(receipt)):
            meta=engine.metadata(major,'V3-compatible (event only)',row['block']-1)
            states=engine.states(row['block'],{major:meta})
            eth_index=0 if meta['token0']==WETH else 1
            stable_index=1-eth_index
            stable_ref=book.price('USDT',row['timestamp'])
            for s in states:
                if s['tx_hash']!=row['tx_hash']:
                    continue
                def spot(state):
                    ratio=(Decimal(state['sqrt_price_x96'])/Decimal(2)**96)**2*Decimal(10)**(meta['decimals0']-meta['decimals1'])
                    return (ratio if eth_index==0 else 1/ratio)*stable_ref[0]
                before,after=spot(s['before']),spot(s['after'])
                qty=[abs(Decimal(s[f'amount{i}_raw']))/Decimal(10)**meta[f'decimals{i}'] for i in (0,1)]
                price_state.append({'pool':major,'log_index':s['log_index'],'before_spot_USD_per_ETH':str(before),'after_spot_USD_per_ETH':str(after),'actual_leg_average_USD_per_ETH':str(qty[stable_index]*stable_ref[0]/qty[eth_index]),'before_active_liquidity':s['before']['active_liquidity'],'after_active_liquidity':s['after']['active_liquidity'],'before_state':s['before'],'after_state':s['after'],'metadata':meta,'limit':'Observed marginal pool-state movement and trade-size average. Does not quantify no-fee full-route impact, tick-level opportunity or causal MEV.'})
        incoming=edges[(edges.recipient==row['address']) & (edges.timestamp>=row['timestamp']) & (edges.timestamp<=row['timestamp']+600) & (edges.tx_hash!=row['tx_hash'])]
        compensations=incoming[['tx_hash','sender','token','amount_raw','timestamp_utc','evidence_path']].to_dict('records')
        verified=[a for a in known_arbitrages if a['target']==row['tx_hash']]
        minbounds=[b for b in decoded_limits if b['bound_kind'] in ('minimum_output','unwrap_minimum','sweep_minimum')]
        zero_bounds=[b for b in minbounds if int(b['bound_raw'])==0]
        report={**row,'case_id':f'N{rank}','transaction_input_evidence':txsource,'fresh_receipt_evidence':livesource,'router_limit_inspection':router,'successful_router_call_inspections':router_calls,'observed_nonzero_minimum_bounds':[b for b in minbounds if int(b['bound_raw'])>0],'observed_zero_minimum_bound_count':len(zero_bounds),'same_block_pool_neighbors':candidates,'observed_profitable_inventory_closed_neighbor_candidates':sum(c['provisional_native_WETH_net_after_gas_ETH'] is not None and Decimal(c['provisional_native_WETH_net_after_gas_ETH'])>0 and not c['other_token_residual_raw'] for c in candidates),'verified_arbitrage_cases_linked':[a['case_id'] for a in verified],'v2_mechanical_leg_checks':mechanical,'major_ETH_USDT_pool_price_states':price_state,'other_incoming_transfers_next_10min':compensations,'repeated_qualifying_swaps_by_same_wallet':sum(r['address']==row['address'] for r in qualifying),
            'compensating_profit_established':False,'counterfactual_incremental_MEV_loss_USD':None,'intentional_self_loss_established':False,'final_classification':'insufficient_evidence','classification_detail':'Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.',
            'confidence':{'asset_flows':'observed receipts and complete successful call trees','reference_loss':'estimated prior completed minute close','slippage_fields':'ABI-compatible numeric inspection; exact deployed command semantics unresolved','same_block_associations':'observed, causal assignment unresolved','intent':'unresolved'}}
        reports.append(report);save(ROOT/f'reports/case_studies/N{rank}_abnormal_swap.json',report)
        print(f'N{rank}: reference loss ${Decimal(row["loss_USD"]):,.2f}; {len(candidates)} same-block pool neighbours; {len(zero_bounds)} decoded zero minimum guards',flush=True)
    save(ROOT/'data/processed/anomaly_case_studies.json',reports)
    engine.store.save();engine.public.write_index()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--legacy');a=p.parse_args();investigate(a.online,a.legacy)
