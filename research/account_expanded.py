import json,gzip
from decimal import Decimal,getcontext
from collections import defaultdict,Counter
from pathlib import Path
from screen_expanded import net_for
getcontext().prec=60
R=Path(__file__).resolve().parent;D=Decimal;E=D(10)**18
S=json.loads((R/'tracker_state.json').read_text());tokens=S['chains'][0]['tokens'];names={a:s for s,a in tokens.items()};names['0x6b175474e89094c44da98b954eedeac495271d0f']='DAI'
decimals={s:18 for s in tokens};decimals.update(USDT=6,USDC=6,WBTC=8,XAUt=6,DAI=18,aEthUSDT=6)
meta=R/'additional_token_metadata.json'
if meta.exists():
 m=json.loads(meta.read_text());names[m['address_hash'].lower()]=m['symbol'];decimals[m['symbol']]=int(m['decimals'])
prices={p.stem:{int(r[0]):r for r in json.loads(p.read_text())} for p in (R/'prices_raw').glob('*.json')}
native={r['hash']:r for r in json.loads((R/'native_evidence.json').read_text())['rows']}
aset={w['address'].lower() for w in S['wallets'] if w['chain']=='ethereum' and w['role'] in S['attackerSideRoles']}
blocks={};receipts={}
def block(n):
 if n not in blocks:
  p=R/'window_raw'/f'{n}_block.json.gz'
  if p.exists():blocks[n]=json.loads(gzip.decompress(p.read_bytes()))
  else:blocks[n]=json.loads((R/'chain_raw'/f'{n}_block.json').read_text())['result']
 return blocks[n]
def receipt(n,h):
 if n not in receipts:receipts[n]={r['transactionHash']:r for r in json.loads(gzip.decompress((R/'window_raw'/f'{n}.json.gz').read_bytes()))}
 return receipts[n][h]
def price(symbol,ts,mode='close'):
 symbol={'WETH':'ETH','WBTC':'BTC'}.get(symbol,symbol)
 if symbol in ['USDC','DAI']:return D(1),'par_assumption'
 t=(ts//60)*60-60
 r=prices.get(symbol,{}).get(t)
 if r is None:return None,'missing_previous_minute'
 return D(str(r[{'close':4,'low':1,'high':2}[mode]])),'previous_complete_Coinbase_minute'+('_BTC_proxy_for_WBTC' if symbol=='BTC' else '')
def native_net(h,tx,accounts):
 row=native.get(h)
 if not row:return None
 if D(row['net_conservation_eth'])!=0:return None
 x=sum((D(v) for a,v in row['native_internal_net_eth'].items() if a in accounts),D(0))
 if row.get('includes_top_level_value') or row['source'].startswith('https://etherscan.io/'):return x
 value=D(int(tx['value'],16))/E
 if tx['from'] in accounts:x-=value
 if tx['to'] in accounts:x+=value
 return x
def main():
 targets={r['hash']:r for r in json.loads((R/'expanded_swaps.json').read_text())['rows']}
 ledger=json.loads((R/'window_ledger.json').read_text());result=[];summary=defaultdict(lambda:{'count':0,'priced_count':0,'input_amount':D(0),'eth_received':D(0),'shortfall_usd':D(0),'low_usd':D(0),'high_usd':D(0)})
 for r in ledger['rows']:
  if not any(int(v)<0 for v in r['net_token_raw'].values()):continue
  h=r['hash'];b=block(r['block']);tx=next(x for x in b['transactions'] if x['hash']==h);rec=receipt(r['block'],h)
  net=net_for(rec,aset);eth=native_net(h,tx,aset)
  ns={names.get(t,t):D(v)/(D(10)**decimals[names[t]]) if t in names else None for t,v in net.items()}
  ns['ETH']=eth
  is_lending=any(x in ns for x in ['aEthUSDT','variableDebtEthWETH'])
  if is_lending:category='lending_not_swap'
  elif h in targets:category='pool_swap'
  elif eth is not None and eth>0:category='token_out_ETH_in_order_or_otc_requires_protocol_confirmation'
  else:category='unresolved_outflow'
  outsyms=[names.get(t,t) for t,v in net.items() if int(v)<0]
  fees=D(r['gas_fee_wei'])/E if r['from'] in aset else D(0)
  base=int(b['baseFeePerGas'],16)*int(rec['gasUsed'],16)
  row={'hash':h,'block':r['block'],'index':r['index'],'timestamp':int(b['timestamp'],16),'category':category,'net_assets':{s:str(v) if v is not None else None for s,v in ns.items()},'native_source_available':eth is not None,'attacker_paid_gas_eth':str(fees),'total_tx_gas_eth':str(D(r['gas_fee_wei'])/E),'base_burn_eth':str(D(base)/E),'priority_fee_eth':str((D(r['gas_fee_wei'])-base)/E),'valuation_assumptions':{},'missing_prices':[]}
  loss=D(0);low=D(0);high=D(0)
  for sym,v in ns.items():
   if v==0:continue
   p,note=price(sym,row['timestamp']);row['valuation_assumptions'][sym]=note
   if p is None or v is None:row['missing_prices'].append(sym);continue
   pl,_=price(sym,row['timestamp'],'low');ph,_=price(sym,row['timestamp'],'high')
   loss-=v*p;low-=v*(ph if v>0 else pl);high-=v*(pl if v>0 else ph)
  row['shortfall_usd']=str(loss) if not row['missing_prices'] and eth is not None and category in ['pool_swap','token_out_ETH_in_order_or_otc_requires_protocol_confirmation'] else None
  row['sensitivity_low_usd']=str(low) if row['shortfall_usd'] is not None else None;row['sensitivity_high_usd']=str(high) if row['shortfall_usd'] is not None else None
  result.append(row)
  if category in ['pool_swap','token_out_ETH_in_order_or_otc_requires_protocol_confirmation']:
   key='+'.join(sorted(outsyms));a=summary[key];a['count']+=1
   if len(outsyms)==1 and ns.get(outsyms[0]) is not None:a['input_amount']-=ns[outsyms[0]]
   if eth is not None:a['eth_received']+=eth
   if row['shortfall_usd'] is not None:a['priced_count']+=1;a['shortfall_usd']+=loss;a['low_usd']+=low;a['high_usd']+=high
 summary={k:{a:str(v) if isinstance(v,D) else v for a,v in d.items()} for k,d in summary.items()}
 for key,d in summary.items():
  if d['priced_count']==0:
   for field in ['shortfall_usd','low_usd','high_usd']:d[field]=None
  if key.startswith('0x'):d['input_amount']=None
 (R/'expanded_valuation.json').write_text(json.dumps({'method':'Lead-set net assets, previous complete Coinbase minute; gross execution shortfall EXCLUDES gas and is NOT MEV; USDC/DAI par and WBTC/BTC proxy are explicit assumptions','summary':summary,'rows':result},indent=2))
 print('SWAPS',json.dumps(summary,indent=2))
 cand=[]
 for group in json.loads((R/'mev_candidates.json').read_text())['blocks']:
  b=block(group['block']);txs={x['hash']:x for x in b['transactions']}
  for c in group['candidates']:
   h=c['hash'];tx=txs[h];accounts={tx['from'],tx['to']};eth=native_net(h,tx,accounts);net=net_for(receipt(group['block'],h),accounts)
   weth=D(net.pop(tokens['WETH'],'0'))/E
   others={t:v for t,v in net.items() if int(v)}
   tip=D(native[h]['native_internal_net_eth'].get(b['miner'],'0')) if h in native else None
   profit=eth+weth-D(c['gas_fee_wei'])/E if eth is not None else None
   cand.append({'hash':h,'block':group['block'],'index':c['index'],'relative_position':c['relative_position'],'boundary_accounts':sorted(accounts),'native_eth_before_gas':str(eth) if eth is not None else None,'weth_delta':str(weth),'other_token_net_raw':others,'net_ETH_WETH_after_gas':str(profit) if profit is not None else None,'fully_closed_non_ETH_assets':not bool(others),'gas_eth':str(D(c['gas_fee_wei'])/E),'base_burn_eth':str(D(c['base_fee_burn_wei'])/E),'priority_fee_eth':str(D(c['priority_fee_wei'])/E),'builder_internal_net_eth':str(tip) if tip is not None else None,'interpretation':'Account-boundary cashflow, not ownership proof or event-causal profit; nonzero other assets mean inventory exposure'})
 (R/'candidate_accounting_93.json').write_text(json.dumps({'rows':cand},indent=2));print('CANDIDATES',len(cand),'native',sum(x['native_eth_before_gas'] is not None for x in cand),'closed',sum(x['native_eth_before_gas'] is not None and x['fully_closed_non_ETH_assets'] for x in cand))
if __name__=='__main__':main()
