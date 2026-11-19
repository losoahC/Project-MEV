"""Nine observed order fills, one transaction each; debt-aware marked boundaries."""
import json
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.value_candidates import book_from_archive
from src.decoding.events import integer,WETH

def run():
    p=ROOT/'data/processed/mev_full_window';targets=[t for t in json.loads((p/'targets.json').read_text()) if t['order_events']];engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('USDC',('2026-10-29','2026-10-30'));comet=json.loads((p/'comet_resolver_equity.json').read_text());public=set(json.loads((p/'public_boundary_exclusions.json').read_text())['addresses']);rows=[];victims=json.loads((p/'target_reference_valuations.json').read_text())
    for t in targets:
        h,rs,tr,paths=engine.block(t['block']);tx=t['tx_hash'];rc=rs[tx];top=h['transactions'][integer(rc['transactionIndex'])];boundary={rc['from'].lower(),top['to'].lower()}|{o['filler'].lower() for o in t['order_events'] if o.get('filler')};boundary-=public;assert rc['from'].lower() in boundary
        cf=cashflow(rc,tr[tx],boundary,h['miner']);comet_calls=[x for x in tr[tx] if x.get('action',{}).get('to','').lower()==comet['comet']];assets={a:int(v) for a,v in cf['token_net_raw'].items()};assets['native:eth']=int(cf['native_net_wei'])-int(cf['gas_wei']);position_adjustment={};qualified=True
        if tx==comet['tx_hash']:
            assert boundary==set(comet['boundary']);assets={a:int(v) for a,v in comet['combined_equity_change_raw'].items()};position_adjustment=comet['position_equity_change_raw']
        elif comet_calls:qualified=False
        marks=[book.value(a,v,integer(h['timestamp'])) for a,v in assets.items() if v];usd=str(sum((Decimal(v['USD']) for v in marks),Decimal(0))) if qualified and all(v['USD'] is not None for v in marks) else None
        rows.append({'tx_hash':tx,'block':t['block'],'order_events':t['order_events'],'boundary':sorted(boundary),'common_beneficial_owner_proven':False,'actual_cashflow':cf,'position_adjustment_raw':position_adjustment,'equity_change_after_gas_raw':{a:str(v) for a,v in assets.items() if v},'valuations':marks,'reference_net_after_gas_USD':usd,'target_reference_shortfalls':[r for r in victims if r['tx_hash']==tx],'MEV_incremental_loss_USD':None,'MEV_criterion':'Order-filling price spread; no ordering-causation proof. Gas/payment alone is not MEV.','limit':'Marked operational-boundary equity for this fill only, not firm-wide cost-basis PnL. External payments are outside boundary. Unrecognized credit/inventory can remain a limitation.','evidence':paths});engine.cache.clear()
    result={'rows':rows,'transactions':len(rows),'priced':sum(r['reference_net_after_gas_USD'] is not None for r in rows),'reference_equity_gain_after_gas_USD':str(sum((Decimal(r['reference_net_after_gas_USD']) for r in rows if r['reference_net_after_gas_USD'] is not None),Decimal(0))),'direct_fee_recipient_ETH':str(sum((Decimal(r['actual_cashflow']['identified_builder_payment_wei'])/10**18 for r in rows),Decimal(0))),'all_incident_fills_complete':False,'not_additive_to_cycle_catalog_without_tx_deduplication':True}
    (p/'order_filler_equity.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2));print([(r['block'],r['reference_net_after_gas_USD']) for r in rows])
if __name__=='__main__':run()
