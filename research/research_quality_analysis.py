"""Fixed-sample robustness, selection diagnostics, and an exact local decomposition."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal as D,getcontext
import value_inventory_ledger as v
getcontext().prec=80
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def marked_at(r,offset):
 t=r['timestamp']-offset*60;q=v.price('ETH',t,0)
 if q is None:return None
 total=D(r['strict']['ETH_cashflow'])*q[0]
 for a in r['strict']['assets']:
  p=v.price(a['price_evidence']['symbol'],t,0)
  if p is None:return None
  total+=D(a['raw'])/(D(10)**a['decimals'])*p[0]
 return total
def main():
 for p in load('scope_market_prices.json')['rows']:v.PRICES.setdefault(p['symbol'],{}).update({t:b for t,b in p['bars'].items() if int(t)>1793343767})
 heads={r['block']:r['timestamp'] for r in load('full_window_evidence.json')['rows']};rows=[dict(r,timestamp=heads[r['block']]) for r in load('unified_target_valuation.json')['rows'] if r['eligible_exchange_candidate']]+[r for r in load('expanded_scope_valuation.json')['rows'] if r['category']=='pool_swap_compatible'];strict=[r for r in rows if r['strict']['USD'] is not None]
 fixed=[]
 for r in strict:
  values={str(lag):marked_at(r,lag-1) for lag in [1,5,15]}
  assert abs(values['1']-D(r['strict']['USD']))<D('1e-20'),r['hash']
  if all(x is not None for x in values.values()):fixed.append({'hash':r['hash'],'block':r['block'],'shortfall_USD_by_lag':{k:str(-x) for k,x in values.items()}})
 totals={str(lag):str(sum((D(r['shortfall_USD_by_lag'][str(lag)]) for r in fixed),D(0))) for lag in [1,5,15]};base=D(totals['1']);sensitivity={'method':'Identical transaction hashes at all three lagged completed-minute close benchmarks; no stale-price fallback. Holdings and gas treatment fixed. Price mapping follows original evidence. Not confidence intervals or a causal MEV estimate.','strict_base_count':len(strict),'common_sample_count':len(fixed),'excluded_from_fixed_comparison':len(strict)-len(fixed),'shortfall_USD_by_lag':totals,'relative_change_vs_one_minute':{k:str((D(x)-base)/base) for k,x in totals.items()},'rows':fixed}
 losses=sorted([(-D(r['strict']['USD']),r['hash']) for r in strict],reverse=True);total=sum((x for x,h in losses),D(0));input_value=sum((-D(a['USD']) for r in strict for a in r['strict']['assets'] if D(a['USD'])<0),D(0))+sum((-D(r['strict']['ETH_cashflow_USD']) for r in strict if D(r['strict']['ETH_cashflow_USD'])<0),D(0));groups=defaultdict(lambda:{'count':0,'shortfall_USD':D(0),'input_USD':D(0)})
 for r in strict:
  syms=sorted({a.get('symbol',a['address']) for a in r['strict']['assets'] if D(a['USD'])<0});key='+'.join(syms) or 'ETH';g=groups[key];g['count']+=1;g['shortfall_USD']-=D(r['strict']['USD']);g['input_USD']+=sum((-D(a['USD']) for a in r['strict']['assets'] if D(a['USD'])<0),D(0))
 concentration={'priced_transactions':len(strict),'negative_shortfall_transactions':sum(x<0 for x,h in losses),'shortfall_USD':str(total),'gross_negative_net_asset_value_USD':str(input_value),'shortfall_fraction_of_priced_input':str(total/input_value),'top1_share_of_net_shortfall':str(losses[0][0]/total),'top10_share_of_net_shortfall':str(sum((x for x,h in losses[:10]),D(0))/total),'excluding_largest_transaction_shortfall_USD':str(total-losses[0][0]),'top_transactions':[{'hash':h,'shortfall_USD':str(x)} for x,h in losses[:10]],'by_outflow_asset_set':{k:{f:str(x) if isinstance(x,D) else x for f,x in g.items()} for k,g in sorted(groups.items(),key=lambda x:x[1]['shortfall_USD'],reverse=True)}}
 cf=load('all_scope_v2_counterfactuals.json');good=[r for r in cf['rows'] if r['status']=='verified_local_fixed_input'];decomp=[]
 for r in good:
  t=r['target_swap'];j=t['input_side'];x=D(t['input']);reserve=r['front_swap']['before'];spot=x*D(reserve[1-j])/D(reserve[j]);feeonly=spot*D('0.997');without=D(r['without_front_output_raw']);actual=D(t['output']);a=r['output_asset_valuation'];unit=D(a['price_USD'])/(D(10)**a['decimals']);components={'fee_at_unperturbed_spot':spot-feeonly,'own_impact_plus_integer_rounding':feeonly-without,'preceding_trade_local_effect':without-actual};assert abs(sum(components.values(),D(0))-(spot-actual))<D('1e-40');assert all(z>=0 for z in components.values())
  decomp.append({'hash':r['target'],'block':r['block'],'pool':r['pool'],'output_asset':a['address'],'components_USD':{k:str(z*unit) for k,z in components.items()},'shortfall_from_prefront_spot_USD':str((spot-actual)*unit),'same_target_input_raw':str(t['input'])})
 ds={k:str(sum((D(r['components_USD'][k]) for r in decomp),D(0))) for k in decomp[0]['components_USD']};poolcounts=Counter(r['pool'] for r in decomp);effect=sorted(D(r['components_USD']['preceding_trade_local_effect']) for r in decomp);sum_effect=sum(effect,D(0));assert sum_effect==D(cf['summary']['marked_target_output_reduction_USD'])
 decomposition={'method':'Exact telescoping local benchmark in raw output units: input at pre-front spot -> same spot with 0.3% fee -> finite-size no-front AMM output (integer rounded) -> actual target output. Components depend on this order, are not additive with CEX shortfall or beneficiary profits. Inputs fixed; not full route/slippage/behavioral replay.','verified_pool_links':len(decomp),'unique_target_transactions':len({r['hash'] for r in decomp}),'all_exchange_candidates':len(rows),'target_count_coverage':str(D(len({r['hash'] for r in decomp}))/len(rows)),'pool_counts':dict(poolcounts),'components_USD':ds,'sum_components_USD':str(sum(map(D,ds.values()),D(0))),'largest_local_effect_fraction':str(effect[-1]/sum_effect),'top5_local_effect_fraction':str(sum(effect[-5:],D(0))/sum_effect),'rows':decomp}
 out={'same_sample_price_robustness':sensitivity,'concentration':concentration,'local_effect_decomposition':decomposition};(R/'research_quality_analysis.json').write_text(json.dumps(out,indent=2));print('robustness', {k:x for k,x in sensitivity.items() if k!='rows'});print('concentration',{k:x for k,x in concentration.items() if k not in ['top_transactions','by_outflow_asset_set']});print('decomposition',{k:x for k,x in decomposition.items() if k!='rows'})
if __name__=='__main__':main()
