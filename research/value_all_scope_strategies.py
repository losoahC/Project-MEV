import json,gzip
from collections import Counter,defaultdict
from decimal import Decimal as D,getcontext
from pathlib import Path
import value_inventory_ledger as val
getcontext().prec=70
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 groups=load('all_scope_sandwich_groups.json')['groups'];candidates=load('candidate_classification.json')['rows']+load('incremental_candidate_classification.json')['rows'];legs={l['hash'] for g in groups for l in g['legs']};rows=[]
 for p in load('scope_market_prices.json')['rows']:val.PRICES.setdefault(p['symbol'],{}).update({t:b for t,b in p['bars'].items() if int(t)>1793343767})
 for n in {c['block'] for c in candidates if c['block']>26303950}|{g['block'] for g in groups if g['block']>26303950}:
  b=json.loads(gzip.decompress((R/'scope_detail_raw'/f'{n}_block.json.gz').read_bytes()))['result'];val.HEAD[n]={'timestamp':int(b['timestamp'],16)}
 for i,g in enumerate(groups):
  rows.append({'id':'all_group:'+str(i),'kind':'paired_strategy','block':g['block'],'senders':g['senders'],'transaction_hashes':[l['hash'] for l in g['legs']],'position_or_debt_events':bool(g['position_or_debt_events']),'strict':val.portfolio(g['net_cashflow_ETH'],g['other_token_net_raw'],g['block'],0),'five_minute':val.portfolio(g['net_cashflow_ETH'],g['other_token_net_raw'],g['block'],5)})
 for c in candidates:
  if c['hash'] in legs:continue
  rows.append({'id':c['hash'],'kind':'unpaired_candidate','block':c['block'],'category':c['category'],'transaction_hashes':[c['hash']],'position_or_debt_events':bool(c['liquidity_events'] or c['debt_events'] or c['nft_event_present']),'strict':val.portfolio(c['operational_cashflow_ETH'],c['other_token_net_raw'],c['block'],0),'five_minute':val.portfolio(c['operational_cashflow_ETH'],c['other_token_net_raw'],c['block'],5)})
 summary={}
 for kind in ['paired_strategy','unpaired_candidate']:
  for mode in ['strict','five_minute']:
   rs=[r for r in rows if r['kind']==kind and not r['position_or_debt_events'] and r[mode]['USD'] is not None];summary[kind+':'+mode]={'fully_priced_without_recognized_position_events':len(rs),'positive':sum(D(r[mode]['USD'])>0 for r in rs),'marked_net_cashflow_USD':str(sum((D(r[mode]['USD']) for r in rs),D(0)))}
 hashes=[h for r in rows for h in r['transaction_hashes']];assert len(hashes)==len(set(hashes));assert {r['hash'] for r in candidates}<=set(hashes)
 missing=Counter((a['address'],a.get('symbol','?'),a['reason']) for r in rows for a in r['five_minute']['missing_assets'])
 out={'method':'Full observed-scope accounting units: same-sender immediate-pool front/back groups replace all overlapping candidate legs. All 16491 candidates covered once; extra pre-target legs retained. Includes original and later Pancake. Gas/ETH transfers included once. Heuristic operational addresses are not established common beneficial ownership. Unknown assets/positions/cross-market hedges remain. Marked cashflow is not full-strategy profit or causal MEV.','summary':summary,'accounting_units':len(rows),'candidate_hashes':len(candidates),'unique_transaction_hashes_including_fronts':len(hashes),'paired_legs_in_candidate_set':len(legs & {c['hash'] for c in candidates}),'missing_assets':[{'address':a,'symbol':s,'reason':e,'units':n} for (a,s,e),n in missing.most_common()],'rows':rows}
 (R/'all_scope_strategy_valuation.json').write_text(json.dumps(out,indent=2));print('units',len(rows),'hashes',len(hashes),'summary',summary,flush=True)
if __name__=='__main__':main()
