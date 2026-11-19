"""Exhaustive same-block/pool candidate enumeration within the available wallet sample.

No positive balance is silently promoted to arbitrage; token residuals, boundaries,
external payouts and association limits are retained. Cache-only, no fixture selection.
"""
import json,argparse
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
import pandas as pd
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow,token_net,native_flows
from src.decoding.events import swap,transfer,integer,WETH
ROOT=Path(__file__).resolve().parents[2]
getcontext().prec=90
E=Decimal(10)**18

def events(r):
    return [e for l in r['logs'] if (e:=swap(l))]

def route_evidence(r,ev):
    pools={x['pool'] for x in ev};legs={p:{'incoming':defaultdict(int),'outgoing':defaultdict(int),'transfers':[]} for p in pools}
    for l in r['logs']:
        f=transfer(l)
        if not f:continue
        for field,side in [('recipient','incoming'),('sender','outgoing')]:
            if f[field] in pools:
                p=f[field];legs[p][side][f['token']]+=int(f['amount_raw']);legs[p]['transfers'].append(f)
    return [{'pool':p,'swap_events_in_log_order':sorted([e for e in ev if e['pool']==p],key=lambda e:e['log_index']),
             'incoming_raw':{t:str(v) for t,v in l['incoming'].items()},'outgoing_raw':{t:str(v) for t,v in l['outgoing'].items()},
             'transfer_events':l['transfers'],'ordering_note':'Event order is observable; pool aggregation does not imply a single sequential path.'} for p,l in sorted(legs.items(),key=lambda x:min(e['log_index'] for e in ev if e['pool']==x[0]))]

def run():
    out=ROOT/'data/processed/mev_discovery';out.mkdir(exist_ok=True)
    engine=Reconstruction(ROOT.parent/'research',False)
    txs=pd.read_parquet(ROOT/'data/processed/transactions.parquet');groups=txs.groupby('block_number').tx_hash.apply(set)
    reg=json.loads((ROOT/'data/processed/wallet_registry.json').read_text());wallets={w['address'] for w in reg}
    targets=[];candidates=[];failures=[];scanned=0;all_receipts=0;target_rejected=Counter()
    for n,hs in groups.items():
        try:header,rs,ts,paths=engine.block(int(n))
        except Exception as ex:failures.append({'block':int(n),'error':str(ex)});continue
        scanned+=1;all_receipts+=len(rs);evs={h:events(r) for h,r in rs.items() if integer(r['status'])==1}
        bypool=defaultdict(list)
        for h,ev in evs.items():
            for e in ev:bypool[e['pool']].append((h,e))
        linked=defaultdict(list)
        for h in sorted(hs):
            r=rs[h];es=evs.get(h,[])
            if not es:target_rejected['no_recognized_successful_pool_event']+=1;continue
            # Require an actual asset debit by an incident lead, not merely incidental contact.
            debited=sorted(a for a in wallets if any(v<0 for v in token_net(r,{a}).values()))
            if not debited:target_rejected['no_lead_token_debit']+=1;continue
            targets.append({'block':int(n),'tx_hash':h,'index':integer(r['transactionIndex']),'wallets_debited':debited,'events':es,'evidence':paths})
            for te in es:
                for ah,ae in bypool[te['pool']]:
                    if ah==h or ah in hs:continue
                    # Signed pool deltas establish opposite/same direction per token slot.
                    opposite=int(ae['amount0_raw'])*int(te['amount0_raw'])<0
                    linked[ah].append({'target':h,'target_index':integer(r['transactionIndex']),'target_wallets':debited,'pool':te['pool'],
                                       'target_log_index':te['log_index'],'actor_log_index':ae['log_index'],'opposite_direction':opposite,
                                       'relative_order':'after' if integer(rs[ah]['transactionIndex'])>integer(r['transactionIndex']) else 'before'})
        for h,links in linked.items():
            r=rs[h];es=evs[h];sender=r['from'].lower();executor=(r.get('to') or '').lower();boundary={sender,executor}-{''};record={'block':int(n),'tx_hash':h,'index':integer(r['transactionIndex']),
                'timestamp':integer(header['timestamp']),'sender':sender,'executor':executor,'accounting_boundary':sorted(boundary),
                'boundary_status':'mechanical sender+entrypoint; private control and shared-router status unverified',
                'fee_recipient':header['miner'].lower(),'associations':links,'pool_legs':route_evidence(r,es),'swap_event_count':len(es),'evidence':paths,
                'causal_hacker_loss_USD':None,'causal_limit':'Same-block/pool association does not prove incremental victim loss. Requires counterfactual replay.'}
            try:
                cf=cashflow(r,ts[h],boundary,header['miner']);record.update(cf)
                flows=native_flows(ts[h]);record['external_native_payouts']=[f for f in flows if f['sender'] in boundary and f['recipient'] not in boundary]
                record['external_token_payouts']=[f for l in r['logs'] if (f:=transfer(l)) and f['sender'] in boundary and f['recipient'] not in boundary]
                # Pool-side closure is an independent check against arbitrary boundary expansion.
                residual=defaultdict(int)
                for leg in record['pool_legs']:
                    for t,v in leg['incoming_raw'].items():residual[t]-=int(v)
                    for t,v in leg['outgoing_raw'].items():residual[t]+=int(v)
                record['pool_net_to_trader_raw']={t:str(v) for t,v in residual.items() if v}
                closed=not any(v for t,v in residual.items() if t!=WETH) and residual.get(WETH,0)>0
                record['pool_inventory_closed_WETH_cycle']=closed
                profitable=Decimal(cf['net_after_gas_and_builder_ETH'])>0 and not cf['other_token_residual_raw']
                record['classification']='inventory_closed_positive_cashflow_candidate' if closed and profitable else 'associated_trade_requires_inventory_or_multi_tx_accounting'
            except Exception as ex:record.update(classification='unpriced_or_trace_incomplete',accounting_error=str(ex))
            candidates.append(record)
        engine.cache.clear()
        if scanned%100==0:print('blocks',scanned,'targets',len(targets),'candidate tx',len(candidates),flush=True)
    hashes=[x['tx_hash'] for x in candidates];assert len(hashes)==len(set(hashes))
    for name,rows in [('targets',targets),('candidates',candidates),('failures',failures)]:
        (out/f'{name}.json').write_text(json.dumps(rows,indent=2))
    selected=[x for x in candidates if x['classification']=='inventory_closed_positive_cashflow_candidate']
    total=sum((Decimal(x['net_after_gas_and_builder_ETH']) for x in selected),Decimal(0))
    leaderboard=defaultdict(lambda:{'transactions':0,'net_ETH':Decimal(0),'gross_ETH':Decimal(0),'gas_ETH':Decimal(0),'direct_builder_ETH':Decimal(0)})
    for x in selected:
        a=leaderboard[(x['sender'],x['executor'])];a['transactions']+=1
        for k,field in [('net_ETH','net_after_gas_and_builder_ETH'),('gross_ETH','gross_after_pool_fees_before_gas_and_builder_ETH')]:a[k]+=Decimal(x[field])
        a['gas_ETH']+=Decimal(x['gas_wei'])/E;a['direct_builder_ETH']+=Decimal(x['identified_builder_payment_wei'])/E
    ranks=[{'sender':s,'executor':e,**{k:str(v) if isinstance(v,Decimal) else v for k,v in a.items()}} for (s,e),a in leaderboard.items()];ranks.sort(key=lambda x:Decimal(x['net_ETH']),reverse=True)
    (out/'leaderboard_candidates.json').write_text(json.dumps(ranks,indent=2))
    summary={'scope':'All transactions in every available block containing an original wallet-sample transaction; successful V2/V3-compatible pool events only. Not whole event/all chains.','blocks_requested':len(groups),'blocks_scanned':scanned,'block_failures':len(failures),'receipts_scanned':all_receipts,'targets_with_pool_events_and_debit':len(targets),'target_rejections':dict(target_rejected),'unique_associated_transactions':len(candidates),'classes':dict(Counter(x['classification'] for x in candidates)),
             'closed_positive_candidate_cashflow_ETH':str(total),'sum_warning':'Candidate accounting boundaries unverified. Not an approved profit total; multi-transaction/sandwich episodes may overlap and must be reconciled before aggregation.',
             'next_required':['Verify private executors vs shared routers and real profit recipients','Reconstruct multi-transaction episodes including negative legs','Enrich token metadata, factory and per-event path branches','Extend neighboring blocks, RFQ fills and TRON','Counterfactual replay before causal victim-loss attribution']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
