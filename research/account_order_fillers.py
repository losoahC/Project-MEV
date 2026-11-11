import json,gzip
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D
from rawtrace_native import parse
from screen_expanded import net_for,swaps
from identify_mev import TRANSFER,WETH
from value_inventory_ledger import portfolio
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 orders=load('order_protocol_identification.json')['orders'];byhash=defaultdict(list)
 for o in orders:byhash[o['hash']].append(o)
 sig=load('classification_event_signatures.json');debt={v:k for k,v in sig.items() if k.startswith(('Borrow(','Repay(','Supply(','Withdraw(','LiquidationCall('))};leads={x['address'].lower() for x in load('address_leads.json')['wallets']};out=[]
 for h,os in byhash.items():
  n=os[0]['block'];folder='window_raw' if n<=26301940 else 'extension_raw';r=next(x for x in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes())) if x['transactionHash']==h);tr=[x for x in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result'] if x.get('transactionHash')==h];native=parse(h,tr);tokens={l['address'] for l in r['logs'] if l['topics'] and l['topics'][0]==TRANSFER};pools={e['pool'].split(':')[1] for e in swaps(r)};named={o['filler'] for o in os if 'filler' in o};group={r['from'],r['to']}|named;group-=leads
  # Unknown event-emitting contracts are excluded from helper expansion, not silently merged.
  excluded=tokens|pools|leads|{l['address'] for l in r['logs'] if l['address'] not in group};bad={tuple(t['traceAddress']) for t in tr if t.get('error')};calls=[t['action'] for t in tr if t['type']=='call' and t['action'].get('callType')=='call' and not any(tuple(t['traceAddress'])[:i] in bad for i in range(len(t['traceAddress'])+1))]
  for _ in range(12):
   add={a['to'] for a in calls if a['from'] in group and a['to'] not in excluded and a.get('input','0x')!='0x'}
   if add<=group:break
   group|=add
  net=net_for(r,group);cash=sum((D(v)/10**18 for a,v in native['native_net_wei'].items() if a in group),D(0));gas=D(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))/10**18 if r['from'] in group else D(0);cash-=gas
  de=[{'emitter':l['address'],'event':debt[l['topics'][0]]} for l in r['logs'] if l['topics'] and l['topics'][0] in debt]
  # Compound III USDC Comet interactions create/repay implicit debt not represented by transferable debt tokens.
  compound=any(a['to']=='0xa17581a9e3356d9a858b789d68b4d866e593ae94' for a in calls)
  out.append({'hash':h,'block':n,'orders':os,'operational_boundary':sorted(group),'native_after_gas_ETH':str(cash),'net_token_raw':net,'gas_ETH':str(gas),'recognized_debt_events':de,'compound_market_interaction':compound,'strict':portfolio(str(cash),net,n,0),'five_minute':portfolio(str(cash),net,n,5),'profit_interpretation':'Marked transaction asset change only; debt/position state, multi-order allocation, helper ownership and external hedges need independent treatment.'})
 summary={}
 for mode in ['strict','five_minute']:
  rs=[x for x in out if x[mode]['USD'] is not None and not x['recognized_debt_events'] and not x['compound_market_interaction']];summary[mode]={'priced_without_flagged_debt':len(rs),'marked_asset_change_USD':str(sum((D(x[mode]['USD']) for x in rs),D(0)))}
 (R/'order_filler_accounting.json').write_text(json.dumps({'method':'Group orders by transaction to avoid duplicate gas. Official UniswapX Fill identifies filler and swapper. 1inch OrderFilled uses transaction entry as provisional resolver boundary, not proven beneficial owner. Native and all ERC20 net changes minus gas; borrowed cash is not profit. No sum with candidate strategy accounting without transaction deduplication.','summary':summary,'rows':out},indent=2));print(summary)
 for x in out:print(x['hash'][:12],x['strict']['USD'],'debt',x['compound_market_interaction'],x['recognized_debt_events'],'assets',x['net_token_raw'])
if __name__=='__main__':main()
