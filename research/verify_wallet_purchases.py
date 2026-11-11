import json
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from classify_incremental_candidates import receipts,traces
from rawtrace_native import parse
from screen_expanded import net_for
import value_inventory_ledger as v
R=Path(__file__).resolve().parent;E=D(10)**18
load=lambda n:json.loads((R/n).read_text())
def main():
 for p in load('scope_market_prices.json')['rows']:v.PRICES.setdefault(p['symbol'],{}).update({t:b for t,b in p['bars'].items() if int(t)>1793343767})
 for r in load('expanded_scope_details.json')['rows']:v.HEAD[r['block']]={'timestamp':r['timestamp']}
 wallets=load('exploiter_1_16_and_bot_audit.json')['wallets'];leads={w['address'].lower() for w in load('address_leads.json')['wallets']};bb=defaultdict(list)
 for t in load('全部兑换时间线.json')['rows']:bb[t['block']].append(t)
 rows=[];errors=[]
 for n,ts in sorted(bb.items()):
  rr={r['transactionHash']:r for r in receipts(n)};tt=defaultdict(list);wanted={t['hash'] for t in ts}
  for t in traces(n):
   if t.get('transactionHash') in wanted:tt[t['transactionHash']].append(t)
  for t in ts:
   h=t['hash'];rec=rr[h]
   try:native=parse(h,tt[h])['native_net_wei']
   except Exception as ex:errors.append({'hash':h,'error':str(ex)});continue
   for w in wallets:
    net=net_for(rec,{w['address']});eth=D(native.get(w['address'],'0'))/E+D(net.get(v.WETH,'0'))/E
    if eth<=0 or not any(int(x)<0 for a,x in net.items() if a!=v.WETH):continue
    # Strict simple purchases only: all non-ETH assets must be paid, not received.
    complex_flow=any(int(x)>0 for a,x in net.items() if a!=v.WETH)
    internal=False
    for log in rec['logs']:
     topics=log['topics']
     if len(topics)==3 and topics[0]=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
      a,b='0x'+topics[1][-40:],'0x'+topics[2][-40:]
      if a!=b and w['address'] in {a,b} and a in leads and b in leads:internal=True
    for trace in tt[h]:
     a=trace.get('action',{})
     if a.get('from') in leads and a.get('to') in leads and w['address'] in {a.get('from'),a.get('to')} and int(a.get('value','0x0'),16)>0:internal=True
    complex_flow=complex_flow or internal
    vals=[v.token_value(a,x,v.HEAD[n]['timestamp'],0) for a,x in net.items() if a!=v.WETH];price=v.price('ETH',v.HEAD[n]['timestamp'],0);complete=price is not None and all(x['USD'] is not None for x in vals)
    cost=-sum((D(x['USD']) for x in vals),D(0)) if complete else None
    gas=D(int(rec['gasUsed'],16)*int(rec['effectiveGasPrice'],16))/E if rec['from']==w['address'] else D(0)
    rows.append({'wallet':w['number'],'address':w['address'],'hash':h,'block':n,'ETH_WETH_net_received':str(eth),'wallet_paid_gas_ETH':str(gas),'other_token_net_raw':net,'internal_lead_transfer_present':internal,'simple_ETH_purchase':not complex_flow,'strict_price_complete':complete,'payment_value_USD':str(cost) if complete else None,'effective_USD_per_ETH':str(cost/eth) if complete and not complex_flow else None,'reference_ETH_USD':str(price[0]) if price else None,'overpayment_USD_excluding_gas':str(cost-eth*price[0]) if complete and not complex_flow else None,'asset_price_evidence':vals,'ETH_price_evidence':price[1] if price else None})
 summary=[]
 for w in wallets:
  rs=[r for r in rows if r['wallet']==w['number']];good=[r for r in rs if r['overpayment_USD_excluding_gas'] is not None]
  summary.append({'wallet':w['number'],'purchase_candidates':len(rs),'strict_simple_purchases':len(good),'ETH_received_priced_subset':str(sum((D(r['ETH_WETH_net_received']) for r in good),D(0))),'overpayment_USD_excluding_gas':str(sum((D(r['overpayment_USD_excluding_gas']) for r in good),D(0)))})
 out={'scope':'Existing 1352 exchange targets only; not full wallet history. Per-wallet native trace and ERC20 net; ETH/WETH combined. Simple purchase excludes simultaneous other-token receipts. Strict previous completed minute; shortfall not causal MEV. No allocation of other wallets flows.','errors':errors,'summary':summary,'rows':rows};(R/'wallet_ETH_purchase_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary));assert not errors
if __name__=='__main__':main()
