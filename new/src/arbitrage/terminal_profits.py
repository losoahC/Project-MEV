"""Verify closed-capital DEX cycles retaining one OR several surplus assets.
Every surplus must bridge to the constant boundary; no negative terminal pool asset.
"""
import json
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction
getcontext().prec=90
E=Decimal(10)**18

def run():
    p=ROOT/'data/processed/mev_full_window';rows=json.loads((p/'strategy_accounts_v4.json').read_text());blocks={r['block']:r['timestamp'] for r in json.loads((p/'blocks.json').read_text())};book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('USDC',('2026-10-29','2026-10-30'));results=[]
    for r in rows:
        clean=not r['errors'] and not r['position_events'] and r['status']!='position_debt_or_NFT_requires_separate_accounting' and not r['unknown_pools'] and r.get('v4_keys_resolved',False) and not r.get('v4_nonzero_hooks') and len(r['distinct_pool_keys'])>=2
        poolnative=Decimal(r['pool_WETH_surplus_ETH']) if r['pool_WETH_surplus_ETH'] is not None else None;poolother=r['pool_inventory_residual_nonWETH_raw'];positive=poolnative is not None and poolnative>=0 and all(int(v)>0 for v in poolother.values()) and (poolnative>0 or bool(poolother));bridge=poolnative is not None and poolnative==Decimal(r['gross_before_gas_direct_fee_recipient_ETH']) and poolother==r['other_token_residual_raw']
        if not(clean and positive and bridge):continue
        ts=blocks[r['transaction_evidence'][-1]['block']];native=book.value('native:eth',int(Decimal(r['net_joint_boundary_ETH'])*E),ts);values=[native]+[book.value(t,int(v),ts) for t,v in poolother.items()];missing=[v['address'] for v in values if v['USD'] is None];usd=str(sum((Decimal(v['USD']) for v in values),Decimal(0))) if not missing else None;surplus={**poolother}
        if poolnative>0:surplus['native:eth_or_WETH']=str(int(poolnative*E))
        results.append({**r,'terminal_pool_surplus_raw':surplus,'retained_profit_asset_count':len(surplus),'reference_exit_timestamp':ts,'reference_valuations':values,'net_reference_USD':usd,'net_reference_positive':Decimal(usd)>0 if usd is not None else None,'missing_price_assets':missing,'verified_operational_cycle':True,'MEV_causally_attributed':False,'valuation_note':'All terminal assets and gas/native costs marked at the same unit-exit prior completed minute. Reference accounting, not firm-wide realized PnL or optimal equilibrium loss.'})
    (p/'terminal_cycle_profits.json').write_text(json.dumps(results,indent=2));assets=defaultdict(int)
    for r in results:
        for t,v in r['terminal_pool_surplus_raw'].items():assets[t]+=int(v)
    summary={'verified_disjoint_cycle_units':len(results),'single_surplus_asset_units':sum(r['retained_profit_asset_count']==1 for r in results),'multiple_surplus_asset_units':sum(r['retained_profit_asset_count']>1 for r in results),'fully_priced_units':sum(r['net_reference_USD'] is not None for r in results),'positive_after_cost_units':sum(r['net_reference_positive'] is True for r in results),'nonpositive_after_cost_units':sum(r['net_reference_positive'] is False for r in results),'priced_reference_net_USD':str(sum((Decimal(r['net_reference_USD']) for r in results if r['net_reference_USD'] is not None),Decimal(0))),'gross_surplus_asset_raw':{t:str(v) for t,v in assets.items()},'gas_ETH':str(sum((Decimal(r['gas_ETH']) for r in results),Decimal(0))),'direct_fee_recipient_ETH':str(sum((Decimal(r['direct_fee_recipient_ETH']) for r in results),Decimal(0))),'warning':'Bounded covered cycles, transaction disjoint and full interval costs included. This does not include open-inventory sellers, fees outside identified boundaries, incomplete metadata, or all incident chains. Not whole-event MEV or ultimate-owner profit.'};(p/'terminal_cycle_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
