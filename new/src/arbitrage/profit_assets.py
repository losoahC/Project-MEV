"""Recognize closed arbitrage retaining ANY one profit token, not only WETH.
Use one explicit exit mark per unit; missing marks stay null, not zero.
"""
import json
from collections import Counter,defaultdict
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.reconstruct import Reconstruction
from src.decoding.events import WETH
getcontext().prec=90
E=Decimal(10)**18

def run():
    p=ROOT/'data/processed/mev_full_window';rows=json.loads((p/'strategy_accounts.json').read_text());blocks={r['block']:r['timestamp'] for r in json.loads((p/'blocks.json').read_text())};book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('USDC',('2026-10-29','2026-10-30'));replays=json.loads((p/'victim_replays.json').read_text())['rows'];result=[]
    for r in rows:
        profit=None;raw=None;verified=r['status']=='verified_cashflow_and_pool_closed_positive_cycle'
        if verified:profit=WETH;raw=str(int(Decimal(r['pool_WETH_surplus_ETH'])*E))
        else:
            ps=r['pool_inventory_residual_nonWETH_raw'];own=r['other_token_residual_raw'];clean=r['status']!='position_debt_or_NFT_requires_separate_accounting' and not r['errors'] and not r['position_events'] and not any('V4' in k for k in r['protocol_counts']) and not r['unknown_pools'] and len(r['distinct_pool_keys'])>=2
            if clean and r['pool_WETH_surplus_ETH']=='0' and len(ps)==1 and own==ps and Decimal(r['gross_before_gas_direct_fee_recipient_ETH'])==0:
                tok,value=next(iter(ps.items()))
                if int(value)>0:profit=tok;raw=value;verified=True
        rr={**r,'profit_token':profit,'gross_profit_token_raw':raw,'verified_single_profit_asset_cycle':verified,'exit_mark_timestamp':blocks[r['transaction_evidence'][-1]['block']],'reference_after_cost_USD':None,'reference_valuation':None,
            'MEV_criterion':'Bracketing interval structure' if r['kind']=='same_sender_bracketing_interval' else 'Closed multipool cycle plus target-pool association; causal dependence not established','victim_intervention_targets':sorted({x['target'] for x in replays if x['removed_front'] in r['included_transactions'] and x['target'] in r['target_hashes'] and x['status']=='verified_fixed_call_victim_intervention'})}
        if verified:
            ts=rr['exit_mark_timestamp'];eth=book.price('ETH',ts)
            if profit==WETH:
                v=book.value('native:eth',int(Decimal(r['net_joint_boundary_ETH'])*E),ts);rr['reference_after_cost_USD']=v['USD'];rr['reference_valuation']={'net_native_asset':v,'method':'One exit-time prior completed minute mark; native net already includes gas and identified direct fee-recipient transfer once.'}
            else:
                v=book.value(profit,int(raw),ts)
                if v['USD'] is not None and eth:rr['reference_after_cost_USD']=str(Decimal(v['USD'])+Decimal(r['net_joint_boundary_ETH'])*eth[0])
                rr['reference_valuation']={'profit_asset':v,'net_native_ETH':r['net_joint_boundary_ETH'],'native_price':str(eth[0]) if eth else None,'native_price_evidence':eth[1] if eth else None,'method':'Profit token and native cost balance valued at the same unit exit mark; not a realized historical inventory cost basis.'}
        rr['net_reference_positive']=Decimal(rr['reference_after_cost_USD'])>0 if rr['reference_after_cost_USD'] is not None else None
        result.append(rr)
    (p/'strategy_profit_assets.json').write_text(json.dumps(result,indent=2));byasset=defaultdict(lambda:{'units':0,'gross_raw':0,'net_native_ETH':Decimal(0),'priced_units':0,'reference_USD':Decimal(0)})
    for r in result:
        if not r['verified_single_profit_asset_cycle']:continue
        a=byasset[r['profit_token']];a['units']+=1;a['gross_raw']+=int(r['gross_profit_token_raw']);a['net_native_ETH']+=Decimal(r['net_joint_boundary_ETH'])
        if r['reference_after_cost_USD'] is not None:a['priced_units']+=1;a['reference_USD']+=Decimal(r['reference_after_cost_USD'])
    summary={'verified_single_profit_asset_units':sum(v['units'] for v in byasset.values()),'priced_positive_units':sum(r['verified_single_profit_asset_cycle'] and r['net_reference_positive'] is True for r in result),'priced_nonpositive_units':sum(r['verified_single_profit_asset_cycle'] and r['net_reference_positive'] is False for r in result),'unpriced_closed_units':sum(r['verified_single_profit_asset_cycle'] and r['net_reference_positive'] is None for r in result),'by_profit_asset':{t:{**{k:str(v) if isinstance(v,Decimal) or k=='gross_raw' else v for k,v in a.items()},'symbol':book.registry.get(t,{}).get('symbol'),'decimals':book.registry.get(t,{}).get('decimals')} for t,a in byasset.items()},'warning':'Transaction-disjoint bounded closed cycles only. Not whole-event MEV, not ultimate beneficial-owner profit. Public service boundary exclusions retained; exit marks can differ across units; no sum with hacker reference shortfalls.'};(p/'profit_asset_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
