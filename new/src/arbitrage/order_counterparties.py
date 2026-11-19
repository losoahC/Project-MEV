"""Nine order fills: signed per-address asset redistribution at one reference price.
Pool reserve changes are custodial balance changes, not identified LP wallet profit.
"""
import json,csv
from decimal import Decimal
from collections import defaultdict
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,native_flows
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.decoding.events import transfer,integer,WETH
from src.decoding.extended_events import extended_swap

def run():
    p=ROOT/'data/processed/mev_full_window';orders=json.loads((p/'order_filler_equity.json').read_text());comet=json.loads((p/'comet_resolver_equity.json').read_text());engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('USDC',('2026-10-29','2026-10-30'));rows=[];summaries=[]
    for order in orders['rows']:
        h,rs,tr,paths=engine.block(order['block']);tx=order['tx_hash'];rc=rs[tx];flows=native_flows(tr[tx]);addresses={f[k] for f in flows for k in ['sender','recipient']}|{f[k] for l in rc['logs'] if (f:=transfer(l)) for k in ['sender','recipient']}|{rc['from'].lower(),h['miner'].lower()};addresses.discard(WETH);pools={e['pool'] for l in rc['logs'] if (e:=extended_swap(l))};makers={r['address'] for r in order['target_reference_shortfalls']};assert len(makers)==1;maker=next(iter(makers));gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);burn=integer(rc['gasUsed'])*integer(h['baseFeePerGas']);priority=gas-burn;per={};tokencheck=defaultdict(int);local=[]
        for a in sorted(addresses):
            assets=token_net(rc,{a});native=sum(int(f['amount_raw'])*((f['recipient']==a)-(f['sender']==a)) for f in flows)-(gas if a==rc['from'].lower() else 0)+(priority if a==h['miner'].lower() else 0);assets['native:eth']=assets.get('native:eth',0)+native;adjust={}
            if tx==comet['tx_hash'] and a in [comet['position_owner'],comet['comet']]:
                sign=1 if a==comet['position_owner'] else -1
                for t,v in comet['position_equity_change_raw'].items():assets[t]=assets.get(t,0)+sign*int(v);adjust[t]=str(sign*int(v))
            assets={t:v for t,v in assets.items() if v};per[a]=assets
            for t,v in assets.items():tokencheck['native:eth_or_WETH' if t in [WETH,'native:eth'] else t]+=v
            marks=[book.value(t,v,integer(h['timestamp'])) for t,v in assets.items()];known=sum((Decimal(x['USD']) for x in marks if x['USD'] is not None),Decimal(0));missing=[x['address'] for x in marks if x['USD'] is None]
            role='token issuance/burn accounting sink, not a recipient or beneficial owner' if a=='0x'+'0'*40 else 'target maker' if a==maker else 'block fee-recipient address, not firm-wide builder profit' if a==h['miner'].lower() else 'DEX pool or manager custodial reserve; LP beneficiaries unallocated' if a in pools else 'stated resolver operational boundary' if a in order['boundary'] else 'Compound collateral custody/debt receivable, adjusted' if a==comet['comet'] else 'unidentified actual address'
            r={'tx_hash':tx,'block':order['block'],'address':a,'role':role,'asset_change_after_gas_and_position_principal_raw':{t:str(v) for t,v in assets.items()},'position_principal_adjustment_raw':adjust,'known_asset_reference_USD':str(known),'missing_price_assets':missing,'all_assets_priced':not missing,'valuations':marks,'evidence':paths,'not_final_beneficial_owner_profit':True};rows.append(r);local.append(r)
        tokencheck['native:eth_or_WETH']+=burn;assert all(v==0 for v in tokencheck.values()),tokencheck
        burnUSD=book.value('native:eth',burn,integer(h['timestamp']));assert burnUSD['USD'] is not None;burnUSD=Decimal(burnUSD['USD']);netknown=sum((Decimal(r['known_asset_reference_USD']) for r in local),Decimal(0))+burnUSD;assert netknown==0
        target=next(r for r in local if r['address']==maker);others=sum((Decimal(r['known_asset_reference_USD']) for r in local if r['address']!=maker),Decimal(0))+burnUSD;assert others==-Decimal(target['known_asset_reference_USD']);summary={'tx_hash':tx,'block':order['block'],'maker':maker,'maker_reference_shortfall_USD':str(others),'all_other_addresses_signed_known_asset_change_plus_burn_USD':str(others),'base_fee_burn_USD':str(burnUSD),'all_tokens_conserve_with_wrapping_liability_normalized':True,'known_price_asset_partition_reconciles_exactly':True,'all_address_assets_priced':all(r['all_assets_priced'] for r in local),'unpriced_address_rows':sum(not r['all_assets_priced'] for r in local),'pool_custody_signed_reference_change_USD':str(sum((Decimal(r['known_asset_reference_USD']) for r in local if r['address'] in pools),Decimal(0))),'beneficial_owner_or_MEV_causation_established':False};summaries.append(summary);engine.cache.clear()
    doc={'summary_by_order':summaries,'rows':rows,'method':'Per-address signed asset deltas, actual gas burn/priority, canonical WETH reserve excluded to avoid counting both wrapper backing and claims; observed Comet position changes and counterpart liabilities added symmetrically. One transaction reference price, not realized historical PnL. Do not sum only positive recipients or equate pool custody changes to individual LP wealth.'};(p/'order_counterparty_redistribution.json').write_text(json.dumps(doc,indent=2))
    with (ROOT/'reports/mev_expansion/九笔订单逐地址分配.csv').open('w') as f:
        flat=[{k:(json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v) for k,v in r.items() if k!='valuations'} for r in rows];w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('Order counterparties',len(rows),'orders',len(summaries),'all-asset priced',sum(s['all_address_assets_priced'] for s in summaries));print([(s['block'],s['maker_reference_shortfall_USD'],s['pool_custody_signed_reference_change_USD']) for s in summaries])
if __name__=='__main__':run()
