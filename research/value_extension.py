"""Incremental window valuation with contract identity and missingness guards."""
import json,gzip
from collections import Counter,defaultdict
from decimal import Decimal,getcontext
from pathlib import Path
from screen_expanded import net_for
getcontext().prec=70
R=Path(__file__).resolve().parent;D=Decimal;E=D(10)**18
def main():
 ledger=json.loads((R/'extension_ledger.json').read_text());swaps={r['hash'] for r in json.loads((R/'extension_swaps.json').read_text())['rows']}
 leads={r['address'].lower() for r in json.loads((R/'address_leads.json').read_text())['wallets']}
 tokenlist={r['address'].lower():r for r in json.loads((R/'coingecko_eth_tokenlist.json').read_text())['tokens'] if r['chainId']==1}
 identity={r['address']:r for r in json.loads((R/'extension_identity_audit.json').read_text())}
 native={r['hash']:r for r in json.loads((R/'extension_rawtrace_native.json').read_text())['rows']}
 fallback=R/'extension_native_fallback.json'
 if fallback.exists():native.update({r['hash']:r for r in json.loads(fallback.read_text())['rows']})
 prices={p.stem:{int(r[0]):r for r in json.loads(p.read_text())} for p in (R/'extension_prices_raw').glob('*.json') if '_' not in p.stem}
 def price(s,ts,stale=False):
  s={'WETH':'ETH','WBTC':'BTC'}.get(s.upper(),s.upper())
  if s in ['USDC','DAI']:return D(1),0,'par_assumption'
  t=ts//60*60-60;ps=prices.get(s,{})
  if t in ps:return D(str(ps[t][4])),0,'BTC_proxy' if s=='BTC' else 'previous_complete_minute'
  prior=[k for k in ps if 0<t-k<=300] if stale else []
  if prior:
   k=max(prior);return D(str(ps[k][4])),t-k,'stale_completed_minute'
  return None,None,'missing'
 rows=[];blocks={};receipts={};checks=[]
 for r in ledger['rows']:
  if not any(int(v)<0 for v in r['net_token_raw'].values()):continue
  n=r['block'];h=r['hash']
  if n not in blocks:blocks[n]=json.loads(gzip.decompress((R/'window_raw'/f'{n}_block.json.gz').read_bytes()))
  if n not in receipts:receipts[n]={x['transactionHash']:x for x in json.loads(gzip.decompress((R/'extension_raw'/f'{n}.json.gz').read_bytes()))}
  b=blocks[n];rec=receipts[n][h];tx=next(t for t in b['transactions'] if t['hash']==h);nr=native.get(h);ts=int(b['timestamp'],16)
  assert rec['blockHash']==b['hash'] and int(b['number'],16)==n
  eth=None
  if nr:
   assert nr['root_from'].lower()==tx['from'].lower() and (nr['root_to'] or '').lower()==(tx['to'] or '').lower()
   assert int(nr['root_value'] or '0x0',16)==int(tx['value'],16)
   assert bool(nr.get('root_error'))==(int(rec['status'],16)==0)
   assert sum(map(int,nr['native_net_wei'].values()))==0
   eth=sum(D(v)/E for a,v in nr['native_net_wei'].items() if a in leads)
  net=net_for(rec,leads);assets=[];unverified=[]
  for a,v in net.items():
   t=tokenlist.get(a);i=identity.get(a)
   valid=bool(t) and (not i or i['decimals_match'])
   sym=t['symbol'] if valid else (i or {}).get('symbol',a)
   amount=D(v)/D(10)**t['decimals'] if valid else None
   if not valid:unverified.append(a)
   assets.append({'address':a,'symbol':sym,'raw':v,'amount':str(amount) if amount is not None else None,'identity_verified_by_listing':valid})
  assets.append({'address':'native','symbol':'ETH','amount':str(eth) if eth is not None else None,'identity_verified_by_listing':True})
  if unverified:category='unverified_token_logs_excluded'
  elif h in swaps:category='pool_swap'
  elif eth is not None and eth>0:category='token_out_ETH_in_protocol_unconfirmed'
  else:category='other_outflow_not_priced'
  vals={};missing=[];stale_used=0
  for stale in [False,True]:
   loss=D(0);miss=[]
   for asset in assets:
    p,age,note=price(asset['symbol'],ts,stale)
    if asset['amount'] is None or p is None:
     if asset['amount']!='0':miss.append(asset['address'])
     continue
    loss-=D(asset['amount'])*p
    if stale:stale_used=max(stale_used,age or 0)
   vals['up_to_5min_stale_shortfall_usd' if stale else 'strict_shortfall_usd']=str(loss) if not miss and category in ['pool_swap','token_out_ETH_in_protocol_unconfirmed'] else None
   if not stale:missing=miss
  rows.append({'hash':h,'block':n,'timestamp':ts,'category':category,'assets':assets,'native_available':eth is not None,'native_source':nr['source'] if nr else None,'unverified_contracts':unverified,'missing_strict_assets':missing,'max_benchmark_staleness_seconds':stale_used,'gas_eth':str(D(r['gas_fee_wei'])/E),**vals})
 summary={'record_count':len(rows),'categories':dict(Counter(r['category'] for r in rows)),'native_available':sum(r['native_available'] for r in rows),'unverified_contract_count':len({a for r in rows for a in r['unverified_contracts']})}
 for k in ['strict_shortfall_usd','up_to_5min_stale_shortfall_usd']:
  values=[D(r[k]) for r in rows if r[k] is not None];summary[k]={'count':len(values),'sum_usd':str(sum(values,D(0)))}
 out={'method':'Lead-set external net assets; token identity corroborated by CoinGecko Ethereum token list and Blockscout decimals. Raw traces exclude reverted ancestors and include root value; gas excluded from shortfall. Strict prior-minute primary; up-to-five-minute stale is a separate expanded sensitivity, not a confidence interval. USDC/DAI par; WBTC uses BTC proxy. None is missing, never zero. Not causal MEV.','summary':summary,'rows':rows}
 (R/'extension_valuation.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
