"""Trade-time marked cashflow for closed cycles AND inventory-selling candidates.
Not all-in economic profit: prior inventory basis, hedges, loans and boundaries remain open.
"""
import json
from decimal import Decimal,getcontext
from collections import Counter,defaultdict
from src.arbitrage.discover import ROOT
from src.reconciliation.pricebook import PriceBook
getcontext().prec=90
E=Decimal(10)**18

def book_from_archive():
    h=json.loads((ROOT/'data/processed/historical_pricebook.json').read_text());b=PriceBook.__new__(PriceBook);b.registry=h['registry'];b.loaded={x['symbol'] for x in b.registry.values()};b.conflicts=h['conflicts'];b.bars={(x['venue'],x['symbol'],x['bar_start']):x for x in h['rows']};return b

def mark(b,raw,ts):
    values=[b.value(t,v,ts) for t,v in raw.items() if int(v)]
    missing=[a['address'] for a in values if a['USD'] is None]
    return {'assets':values,'missing_assets':missing,'marked_net_USD':None if missing else str(sum((Decimal(a['USD']) for a in values),Decimal(0)))}

def run():
    out=ROOT/'data/processed/mev_discovery';cs=json.loads((out/'candidates.json').read_text());b=book_from_archive();rows=[]
    for c in cs:
        if 'native_net_wei' not in c:continue
        raw=dict(c['token_net_raw']);raw['native:eth']=c['native_net_wei'];v=mark(b,raw,c['timestamp']);eth=b.price('ETH',c['timestamp']);gas=Decimal(c['gas_wei'])/E;builder=Decimal(c['identified_builder_payment_wei'])/E
        gasusd=str(gas*eth[0]) if eth else None;builderusd=str(builder*eth[0]) if eth else None
        net=str(Decimal(v['marked_net_USD'])-Decimal(gasusd)) if v['marked_net_USD'] is not None and gasusd is not None else None
        poolraw=c['pool_net_to_trader_raw'];pv=mark(b,poolraw,c['timestamp'])
        rows.append({'tx_hash':c['tx_hash'],'block':c['block'],'timestamp':c['timestamp'],'sender':c['sender'],'executor':c['executor'],
                     'boundary':c['accounting_boundary'],'boundary_status':c['boundary_status'],'marked_boundary':v,'gas_USD':gasusd,'direct_builder_USD':builderusd,'marked_cashflow_after_gas_USD':net,
                     'pool_marked_surplus_before_operating_costs':pv,'pool_leg_count':len(c['pool_legs']),
                     'meaning':'Marked cashflow relative to independent same-prior-minute price. NOT realized all-in profit; no earlier inventory basis, offchain hedges, debt or control assumption. Direct builder payment is already in boundary cashflow and not subtracted twice.',
                     'target_hashes':sorted({a['target'] for a in c['associations']}),'causal_victim_loss_USD':None})
    (out/'candidate_valuations.json').write_text(json.dumps(rows,indent=2))
    # Aggregate only transaction-unique mechanically defined pairs; never publish a global profit sum.
    stats=defaultdict(lambda:{'complete_transactions':0,'incomplete_transactions':0,'marked_cashflow_USD':Decimal(0),'gas_USD':Decimal(0),'direct_builder_USD':Decimal(0),'tx_hashes':[]})
    for r in rows:
        a=stats[(r['sender'],r['executor'])];a['tx_hashes'].append(r['tx_hash'])
        if r['marked_cashflow_after_gas_USD'] is None:a['incomplete_transactions']+=1;continue
        a['complete_transactions']+=1
        a['marked_cashflow_USD']+=Decimal(r['marked_cashflow_after_gas_USD']);a['gas_USD']+=Decimal(r['gas_USD']);a['direct_builder_USD']+=Decimal(r['direct_builder_USD'])
    rank=[{'sender':s,'executor':e,**{k:str(v) if isinstance(v,Decimal) else v for k,v in a.items()},'status':'candidate reference-mark ledger; includes only associated transactions, not a complete strategy PnL'} for (s,e),a in stats.items()]
    rank.sort(key=lambda x:Decimal(x['marked_cashflow_USD']),reverse=True);(out/'marked_actor_candidates.json').write_text(json.dumps(rank,indent=2))
    summary={'rows':len(rows),'complete_marked_rows':sum(r['marked_cashflow_after_gas_USD'] is not None for r in rows),'incomplete_marked_rows':sum(r['marked_cashflow_after_gas_USD'] is None for r in rows),'missing_asset_frequency':dict(Counter(t for r in rows for t in r['marked_boundary']['missing_assets'])),'global_profit_total':None}
    (out/'valuation_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='missing_asset_frequency'},indent=2))
if __name__=='__main__':run()
