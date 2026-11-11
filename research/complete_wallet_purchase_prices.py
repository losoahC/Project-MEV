"""Resolve each price exclusion without silently changing benchmark semantics."""
import json
from pathlib import Path
from decimal import Decimal as D
import value_inventory_ledger as v
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 for p in load('scope_market_prices.json')['rows']:v.PRICES.setdefault(p['symbol'],{}).update({t:b for t,b in p['bars'].items() if int(t)>1793343767})
 for r in load('expanded_scope_details.json')['rows']:v.HEAD[r['block']]={'timestamp':r['timestamp']}
 oracle={r['id']:r for r in load('oracle_assisted_scenarios.json')['rows'] if r['kind']=='target'};rows=[]
 for r in load('wallet_ETH_purchase_audit.json')['rows']:
  ts=v.HEAD[r['block']]['timestamp'];scenarios={}
  for label,stale in [('strict',0),('five_minute',5),('fifteen_minute',15)]:
   assets=[v.token_value(a,raw,ts,stale) for a,raw in r['other_token_net_raw'].items() if a!=v.WETH];ep=v.price('ETH',ts,stale);missing=[a['address'] for a in assets if a['USD'] is None]
   diff=-sum((D(a['USD']) for a in assets),D(0))-D(r['ETH_WETH_net_received'])*ep[0] if ep and not missing else None
   scenarios[label]={'overpayment_USD':str(diff) if diff is not None else None,'assets':assets,'missing':missing,'ETH_price':str(ep[0]) if ep else None,'ETH_price_evidence':ep[1] if ep else None}
  base=scenarios['five_minute'];assets=[dict(a) for a in base['assets']];used=[]
  oa={a['address']:a for a in oracle.get(r['hash'],{}).get('assets',[]) if a.get('oracle_price_USD')}
  for a in assets:
   if a['USD'] is None and a['address'] in oa:
    q=oa[a['address']];t=v.TOK[a['address']];a['USD']=str(D(a['raw'])/(D(10)**t['decimals'])*D(q['oracle_price_USD']));a['oracle_price_USD']=q['oracle_price_USD'];a['oracle_block']=q['oracle_block'];used.append(a['address'])
  missing=[a['address'] for a in assets if a['USD'] is None];diff=-sum((D(a['USD']) for a in assets),D(0))-D(r['ETH_WETH_net_received'])*D(base['ETH_price']) if base['ETH_price'] and not missing else None
  scenarios['mixed_five_minute_oracle']={'overpayment_USD':str(diff) if diff is not None else None,'assets':assets,'oracle_assets':used,'missing':missing}
  rows.append({'hash':r['hash'],'block':r['block'],'wallet':r['wallet'],'simple_purchase':r['simple_ETH_purchase'],'ETH_received':r['ETH_WETH_net_received'],'scenarios':scenarios})
 summary={}
 for mode in rows[0]['scenarios']:
  rs=[r for r in rows if r['simple_purchase'] and r['scenarios'][mode]['overpayment_USD'] is not None];summary[mode]={'count':len(rs),'overpayment_USD':str(sum((D(r['scenarios'][mode]['overpayment_USD']) for r in rs),D(0)))}
 unresolved=[r for r in rows if all(s['overpayment_USD'] is None for s in r['scenarios'].values())]
 out={'method':'Separate nested stale-price scenarios; mixed uses previous-block Aave prices already cached. Oracle is not executable market price and feed timestamps remain unaudited. No par assumption or DAR-to-D price substitution. Gas excluded; shortfall not causal MEV.','summary':summary,'unresolved_hashes':[r['hash'] for r in unresolved],'rows':rows}
 (R/'wallet_purchase_price_completion.json').write_text(json.dumps(out,indent=2));print(summary);print('unresolved',out['unresolved_hashes'])
 for r in rows:
  if r['scenarios']['strict']['overpayment_USD'] is not None:
   old=next(x for x in load('wallet_ETH_purchase_audit.json')['rows'] if x['hash']==r['hash'] and x['wallet']==r['wallet']);assert D(old['overpayment_USD_excluding_gas'])==D(r['scenarios']['strict']['overpayment_USD'])
if __name__=='__main__':main()
