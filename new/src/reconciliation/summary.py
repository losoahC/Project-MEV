"""Fixed-mark snapshot ledger and explicitly incomplete economic attribution; no fabricated global total."""
from collections import Counter
from decimal import Decimal,getcontext
import json
import pandas as pd
from src.visualization.common import ROOT
from src.reconciliation.pricebook import PriceBook
from src.anomaly.screen import value_net

getcontext().prec=90

def read(path):return json.loads((ROOT/path).read_text())
def save(path,obj):(ROOT/path).write_text(json.dumps(obj,indent=2))

def run():
    balance=read('data/processed/balance_reconciliation.json');rows=balance['rows']
    totals={k:Decimal(0) for k in ['opening','external_inflow','external_outflow','gas','wrapper_net','closing','frozen_closing','nonblacklisted_closing','unexplained_change']}
    assetrows=[]
    for token in sorted({r['token'] for r in rows}):
        selected=[r for r in rows if r['token']==token];first=selected[0];price=Decimal(first['fixed_reference']['reference_USD']);scale=Decimal(10)**first['decimals']
        agg={k:sum(Decimal(r[k+'_raw']) for r in selected)/scale for k in ['opening','external_inflow','external_outflow','gas','unexplained_change']}
        agg['closing']=sum(Decimal(r['observed_closing_raw']) for r in selected)/scale
        agg['wrapper_net']=sum(Decimal(r['wrapper_mint_raw'])-Decimal(r['wrapper_burn_raw']) for r in selected)/scale
        agg['frozen_closing']=sum(Decimal(r['observed_closing_raw']) for r in selected if r['blacklist_status']['blacklisted'])/scale
        agg['nonblacklisted_closing']=agg['closing']-agg['frozen_closing']
        marked={k:str(v*price) for k,v in agg.items()}
        for k in totals:totals[k]+=Decimal(marked[k])
        assetrows.append({'token':token,'symbol':first['symbol'],'units':{k:str(v) for k,v in agg.items()},'reference_USD':str(price),'marked_USD':marked,'price_evidence':first['fixed_reference']['price_evidence']})
    assert totals['opening']+totals['external_inflow']-totals['external_outflow']-totals['gas']+totals['wrapper_net']+totals['unexplained_change']==totals['closing']
    assert totals['frozen_closing']+totals['nonblacklisted_closing']==totals['closing']
    # Contract-aware same-mark economic sensitivity uses the audited M4 registry and bars.
    history=read('data/processed/historical_pricebook.json');book=PriceBook.__new__(PriceBook)
    book.registry=history['registry'];book.loaded={v['symbol'] for v in book.registry.values()};book.bars={};book.conflicts=[]
    for bar in history['rows']:book.bars[(bar['venue'],bar['symbol'],bar['bar_start'])]=bar
    ts=int(pd.Timestamp(balance['valuation_timestamp_utc']).timestamp())
    valuations=read('data/processed/wallet_swap_valuations.json');economic=[]
    counts=Counter(r['tx_hash'] for r in valuations)
    for r in valuations:
        if counts[r['tx_hash']]!=1 or r['position_or_debt_events'] or r['internal_wallet_transfer']:continue
        v=value_net(book,{k:int(a) for k,a in r['net_asset_raw'].items()},ts)
        if v['input_reference_USD'] is None:continue
        inp=Decimal(v['input_reference_USD']);out=Decimal(v['output_reference_USD'])
        if inp<=0 or out<=0:continue
        economic.append({'wallet':r['wallet'],'tx_hash':r['tx_hash'],'input_fixed_reference_USD':str(inp),'output_fixed_reference_USD':str(out),'signed_shortfall_fixed_USD':str(inp-out),'trade_time_shortfall_USD':r.get('loss_USD'),'fixed_reference_timestamp_utc':balance['valuation_timestamp_utc'],'assets':v['assets']})
    primary=[r for r in valuations if counts[r['tx_hash']]==1 and r.get('valuation_complete') and not r['position_or_debt_events'] and not r['internal_wallet_transfer']]
    def econ_stats(selected,field):
        values=[Decimal(r[field]) for r in selected if r[field] is not None]
        return {'rows':len(values),'signed_net_shortfall_USD':str(sum(values,Decimal(0))),'adverse_only_USD':str(sum((v for v in values if v>0),Decimal(0))),'favorable_only_USD':str(sum((-v for v in values if v<0),Decimal(0)))}
    identities=read('data/processed/wallet_registry.json')
    corroborated={w['number'] for w in identities if w['identity_confidence']=='independently_corroborated'}
    ownership=[]
    for label,allowed in [('all_16_teacher_leads',set(range(1,17))),('exclude_unverified_wallet13',corroborated),('exclude_wallet13_and_crosschain_only9',corroborated-{9})]:
        ownership.append({'scenario':label,'wallet_numbers':sorted(allowed),'primary_trade_time':econ_stats([r for r in primary if r['wallet'] in allowed],'loss_USD'),'fixed_mark':econ_stats([r for r in economic if r['wallet'] in allowed],'signed_shortfall_fixed_USD'),'snapshot_closing_USD':str(sum((Decimal(r['observed_closing_raw'])/Decimal(10)**r['decimals']*Decimal(r['fixed_reference']['reference_USD']) for r in rows if r['wallet'] in allowed),Decimal(0))),'ownership_meaning':'Each address is its own boundary; recipient common control is never assumed. Excluding an address tests the lead set, not proof of innocence.'})
    arb=read('data/processed/arbitrage_cases.json');outcomes=read('data/processed/auction_outcomes.json');subs=read('data/processed/auction_submissions.json')
    auction=[]
    relays=sorted({s['relay'] for s in subs}|{r for a in outcomes for r in a['relays']})
    for remove in [None]+relays:
        retained=[s for s in subs if s['relay']!=remove]
        auction.append({'removed_relay':remove,'submission_observations':len(retained),'selected_delivered_outcomes_with_retained_relay_support':sum(any(r!=remove for r in a['relays']) for a in outcomes),'selected_onchain_proposer_payment_matches':sum(a['proposer_payment_exact_match'] for a in outcomes),'meaning':'Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed.'})
    arbtotal={key:str(sum(Decimal(a[key]) for a in arb)) for key in ['gross_after_pool_fees_before_gas_and_builder_ETH','net_after_gas_and_builder_ETH']}
    arbtotal['gas_ETH']=str(sum(Decimal(a['gas_wei']) for a in arb)/10**18)
    arbtotal['direct_builder_ETH']=str(sum(Decimal(a['identified_builder_payment_wei']) for a in arb)/10**18)
    assert Decimal(arbtotal['gross_after_pool_fees_before_gas_and_builder_ETH'])==Decimal(arbtotal['net_after_gas_and_builder_ETH'])+Decimal(arbtotal['gas_ETH'])+Decimal(arbtotal['direct_builder_ETH'])
    paired=[r for r in economic if r['trade_time_shortfall_USD'] is not None]
    result={'paired_price_timing_sensitivity':{'same_transactions':len(paired),'trade_time':econ_stats(paired,'trade_time_shortfall_USD'),'fixed_closing_mark':econ_stats(paired,'signed_shortfall_fixed_USD'),'interpretation':'Same-transaction comparison. Full 621-row and 315-row sample totals have different coverage and cannot be compared as pure price sensitivity.'},'asset_scope':balance['scope'],'valuation_timestamp_utc':balance['valuation_timestamp_utc'],'fixed_mark_assets':assetrows,'asset_ledger_USD':{k:str(v) for k,v in totals.items()},'snapshot_balanced_rows':balance['balanced_rows'],'snapshot_total_rows':balance['total_rows'],'economic_trade_time_sample':econ_stats(primary,'loss_USD'),'economic_fixed_mark_sample':econ_stats(economic,'signed_shortfall_fixed_USD'),'trade_time_vs_fixed_definition':'Trade-time uses prior completed minute per execution; fixed-mark uses a single closing-block prior-minute mark. Fixed-mark differences include subsequent market movement and are a robustness check, not pure execution loss. Both samples require complete known contracts/prices, unique tx and no internal/position/debt mixing.','selected_3_arbitrage_ETH':arbtotal,'whole_incident_initial_stolen_USD':None,'whole_incident_unrecovered_USD':None,'whole_incident_MEV_loss_USD':None,'whole_incident_seized_or_recovered_USD':None,'causal_mev_share_of_execution_loss':None,'teacher_2B_assessment':'Teacher PDF p8 says approximately USD2B frozen stablecoins; our specific historical contract blacklist/balance snapshot can corroborate order of magnitude within Ethereum scope. It does not establish USD2B unrecoverable economic loss or a whole-incident recovery account.','ownership_sensitivity':ownership,'missing_relay_sensitivity':auction,'nonadditivity':['Frozen is a subset of closing holdings.','External transfer inflows include swaps and wrapper redemption; they are not initial stolen assets and must not be summed as theft.','Execution shortfall is not mechanically equal to searcher profit.','Selected arbitrage gross already includes embedded pool fees; gas and builder transfers partition it, not extra losses.','Whole-block proposer payments can include unrelated transactions and are not added to selected arbitrage cost.','November THOR conversions are separate and not added to October Ethereum MEV.'],'unresolved':['Full stolen asset inventory across chains and tokens, legal recovery/seizure and ultimate control remain unverified.','No full no-MEV counterfactual or loss decomposition for all routes.','189 original two-sided rows lack complete trade-time prices; fixed-mark coverage differs.','Historical relay submissions are incomplete, possibly revisions/late bids; no exact auction competition total.']}
    save('data/processed/loss_reconciliation.json',result);save('data/processed/economic_fixed_mark_rows.json',economic)
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in assetrows]).to_parquet(ROOT/'reports/tables/fig08_asset_ledger.parquet',index=False)
    print('Asset snapshot closing USD',totals['closing'],'blacklisted subset USD',totals['frozen_closing'])
    print('Economic complete trade-time sample',len(primary),'fixed-mark sample',len(economic))

if __name__=='__main__':run()
