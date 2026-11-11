"""Reproducible mark-to-market scenarios; never label all candidate cashflow MEV."""
import json,csv
from pathlib import Path
from decimal import Decimal as D,getcontext
from collections import defaultdict,Counter
getcontext().prec=60
R=Path(__file__).resolve().parent
load=lambda f:json.loads((R/f).read_text())
HEAD={r['block']:r for r in load('full_window_evidence.json')['rows']}
TOK={r['address'].lower():r for r in load('coingecko_eth_tokenlist.json')['tokens'] if r['chainId']==1}
PRICES={r['symbol'].upper():r['bars'] for r in load('inventory_market_prices.json')['rows']}
if (R/'verified_fun_market_prices.json').exists():
 FUN_MARKET=load('verified_fun_market_prices.json');PRICES.setdefault('FUN',{}).update(FUN_MARKET['bars'])
WETH='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
VERIFIED=load('verified_price_contracts.json')
SYMS=defaultdict(set)
for a,t in TOK.items():SYMS[t['symbol'].upper()].add(a)
def price(symbol,ts,stale=0):
 minute=ts//60*60-60;bars=PRICES.get(symbol,{})
 for m in range(minute,minute-stale*60-1,-60):
  b=bars.get(str(m))
  if b:
   v=D(b['close']);e={'symbol':symbol,'bar_start':m,'stale_minutes':(minute-m)//60,'source':b['source'],'quote':b['quote']}
   if b['quote']=='USDT':
    u=price('USDT',ts,stale)
    if not u:return None
    v*=u[0];e['USDT_USD_conversion']=u[1]
   return v,e
 return None
def token_value(address,raw,ts,stale=0):
 t=TOK.get(address);raw=D(raw)
 if not raw:return {'address':address,'raw':'0','USD':'0'}
 if not t:return {'address':address,'raw':str(raw),'USD':None,'reason':'unknown_contract'}
 sym=VERIFIED.get(address,{}).get('symbol',t['symbol'].upper());proxy=None
 if address==WETH:sym='ETH';proxy='WETH redemption parity with ETH'
 elif sym=='WBTC':sym='BTC';proxy='WBTC marked at BTC; depeg/basis excluded'
 elif len(SYMS[sym])>1 and address not in VERIFIED:return {'address':address,'symbol':sym,'raw':str(raw),'USD':None,'reason':'ambiguous_symbol'}
 q=price(sym,ts,stale)
 if not q:return {'address':address,'symbol':sym,'raw':str(raw),'USD':None,'reason':'no_completed_minute_price'}
 return {'address':address,'symbol':sym,'raw':str(raw),'decimals':t['decimals'],'price_USD':str(q[0]),'USD':str(raw/(D(10)**t['decimals'])*q[0]),'price_evidence':q[1],'proxy_assumption':proxy,'identity_basis':VERIFIED.get(address,{'source':'CoinGecko Ethereum address list; CEX product matched by unique ticker, not independently verified deposit contract'})}
def portfolio(cash,nets,block,stale):
 ts=HEAD[block]['timestamp'];q=price('ETH',ts,stale);assets=[token_value(a,v,ts,stale) for a,v in sorted(nets.items()) if int(v)]
 missing=[a for a in assets if a['USD'] is None];native=D(cash)*q[0] if q else None
 return {'complete_under_price_mapping_assumptions':q is not None and not missing,'USD':str(native+sum((D(a['USD']) for a in assets),D(0))) if q and not missing else None,'ETH_cashflow':str(cash),'ETH_cashflow_USD':str(native) if native is not None else None,'ETH_price_evidence':q[1] if q else None,'assets':assets,'missing_assets':missing}
def main():
 groups=load('sandwich_structure_groups.json')['groups'];candidates=load('candidate_classification.json')['rows'];legs={l['hash'] for g in groups for l in g['legs']};rows=[]
 for i,g in enumerate(groups):
  rows.append({'id':'group:'+str(i),'kind':'paired_strategy','block':g['block'],'senders':g['senders'],'transaction_hashes':[l['hash'] for l in g['legs']],'position_or_debt_events':bool(g['position_or_debt_events']),'strict':portfolio(g['net_cashflow_ETH'],g['other_token_net_raw'],g['block'],0),'five_minute':portfolio(g['net_cashflow_ETH'],g['other_token_net_raw'],g['block'],5)})
 for c in candidates:
  if c['hash'] in legs:continue
  rows.append({'id':c['hash'],'kind':'unpaired_candidate','block':c['block'],'category':c['category'],'transaction_hashes':[c['hash']],'position_or_debt_events':bool(c['liquidity_events'] or c['debt_events'] or c['nft_event_present']),'strict':portfolio(c['operational_cashflow_ETH'],c['other_token_net_raw'],c['block'],0),'five_minute':portfolio(c['operational_cashflow_ETH'],c['other_token_net_raw'],c['block'],5)})
 summary={};missing=Counter()
 for kind in ['paired_strategy','unpaired_candidate']:
  for mode in ['strict','five_minute']:
   sample=[r for r in rows if r['kind']==kind and r[mode]['USD'] is not None and not r['position_or_debt_events']]
   summary[kind+':'+mode]={'fully_priced_without_recognized_position_events':len(sample),'positive':sum(D(r[mode]['USD'])>0 for r in sample),'marked_net_cashflow_USD':str(sum((D(r[mode]['USD']) for r in sample),D(0)))}
 for r in rows:
  for a in r['five_minute']['missing_assets']:missing[(a['address'],a.get('symbol','?'),a['reason'])]+=1
 out={'method':'Disjoint accounting units: paired front/back groups replace overlapping candidate legs. Net ETH/WETH already subtracts gas and native transfers; do not subtract again. Marked cashflow is not causal MEV or complete economic profit. CEX ticker mapping and WBTC/BTC parity are explicit assumptions. Unpriced assets remain missing, never zero. Previous completed minute primary; <=5 additional minutes stale separate scenario. Shared routers are not established common beneficial owners.','summary':summary,'paired_legs_in_candidate_set':len(legs & {c['hash'] for c in candidates}),'missing_assets':[{'address':a,'symbol':s,'reason':e,'units':n} for (a,s,e),n in missing.most_common()],'rows':rows}
 (R/'inventory_valued_ledger.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2));print('missing',out['missing_assets'][:8])
 lp=[]
 for p in load('v3_position_accounting.json')['rows']:
  if p['status']!='reconciled':lp.append({'id':p['id'],'status':p['status']});continue
  n=max(e['block'] for e in p['events']);assets=[token_value(p[f'token{j}'],p['fees_credited_in_window_raw'][j],HEAD[n]['timestamp'],5) for j in [0,1]]
  events=[]
  for e in p['events']:
   if e['type'] not in ['Mint','Collect']:continue
   vals=[token_value(p[f'token{j}'],e[f'amount{j}'],HEAD[e['block']]['timestamp'],5) for j in [0,1]]
   events.append({'hash':e['hash'],'block':e['block'],'type':e['type'],'assets':vals,'USD':str(sum((D(v['USD']) for v in vals),D(0))) if all(v['USD'] is not None for v in vals) else None})
  lp.append({'id':p['id'],'pool':p['pool'],'owner':p['owner'],'status':'reconciled','fully_opened_and_closed_in_window':p['fully_opened_and_closed_in_window'],'credited_fee_assets':assets,'credited_fee_USD_at_last_event':str(sum((D(v['USD']) for v in assets),D(0))) if all(v['USD'] is not None for v in assets) else None,'cashflow_events':events,'closed_position_marked_cashflow_before_gas_USD':str(sum((D(e['USD'])*(1 if e['type']=='Collect' else -1) for e in events),D(0))) if p['fully_opened_and_closed_in_window'] and all(e['USD'] is not None for e in events) else None})
 (R/'v3_position_valuation.json').write_text(json.dumps({'method':'Fees credited can predate window. Fee USD marks all credited tokens at last position event, not realized USD receipts. Closed-position cashflow includes inventory price movements, excludes gas/hedges and is not causal MEV. WBTC/BTC parity and unique-ticker CEX mapping are assumptions.','rows':lp},indent=2))
 with (R/'收益总账_去重估值.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['核算单元','类型','区块','交易哈希','包含仓位或债务事件','严格前一分钟美元净现金流','五分钟放宽美元净现金流','未估值资产数'])
  for r in rows:w.writerow([r['id'],r['kind'],r['block'],';'.join(r['transaction_hashes']),r['position_or_debt_events'],r['strict']['USD'],r['five_minute']['USD'],len(r['five_minute']['missing_assets'])])
if __name__=='__main__':main()
