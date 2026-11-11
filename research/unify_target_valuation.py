import json,gzip
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal as D
from rawtrace_native import parse
from screen_expanded import net_for
from value_inventory_ledger import portfolio
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 old=load('expanded_valuation.json')['rows']+load('extension_valuation.json')['rows'];leads={r['address'].lower() for r in load('address_leads.json')['wallets']};byblock=defaultdict(list)
 for r in old:byblock[r['block']].append(r)
 rows=[]
 for i,(n,items) in enumerate(sorted(byblock.items()),1):
  folder='window_raw' if n<=26301940 else 'extension_raw';rs={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))};tr=defaultdict(list)
  wanted={r['hash'] for r in items}
  for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result']:
   if t.get('transactionHash') in wanted:tr[t['transactionHash']].append(t)
  for r in items:
   rec=rs[r['hash']];nr=parse(r['hash'],tr[r['hash']]);cash=sum(D(v)/D(10**18) for a,v in nr['native_net_wei'].items() if a in leads);net=net_for(rec,leads);eligible=r['category']=='pool_swap' or r['category'].startswith('token_out_ETH_in');paid=D(int(rec['gasUsed'],16)*int(rec['effectiveGasPrice'],16))/D(10**18) if rec['from'] in leads else D(0)
   vals={mode:portfolio(str(cash),net,n,stale) for mode,stale in [('strict',0),('five_minute',5)]}
   rows.append({'hash':r['hash'],'block':n,'category':r['category'],'eligible_exchange_candidate':eligible,'lead_native_ETH':str(cash),'lead_net_token_raw':net,'lead_paid_gas_ETH':str(paid),'gas_excluded_from_shortfall':True,'strict':vals['strict'],'five_minute':vals['five_minute']})
  if i%300==0:print('unified target blocks',i,len(byblock),flush=True)
 summary={}
 for mode in ['strict','five_minute']:
  selected=[r for r in rows if r['eligible_exchange_candidate'] and r[mode]['USD'] is not None];summary[mode]={'count':len(selected),'execution_shortfall_USD':str(-sum((D(r[mode]['USD']) for r in selected),D(0))),'pool_only_count':sum(r['category']=='pool_swap' for r in selected),'pool_only_shortfall_USD':str(-sum((D(r[mode]['USD']) for r in selected if r['category']=='pool_swap'),D(0)))}
 (R/'unified_target_valuation.json').write_text(json.dumps({'method':'All original+extension net-token-outflow records recomputed from complete trace+receipts at lead-set boundary. One price helper across windows. Gas excluded. Previous completed minute, with separate <=5-minute stale expansion; no stablecoin par assumption. WETH/ETH and WBTC/BTC mapping explicit. Price mapping, address attribution, inventory and protocol classification limitations remain. Execution shortfall is not causal MEV.','summary':summary,'rows':rows},indent=2));print(summary,flush=True)
if __name__=='__main__':main()
