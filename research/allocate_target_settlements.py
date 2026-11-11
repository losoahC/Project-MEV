import json,gzip
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D,getcontext
from rawtrace_native import parse
from screen_expanded import swaps
from identify_mev import TRANSFER,WETH,DEPOSIT,WITHDRAWAL
from value_inventory_ledger import token_value,price,HEAD,TOK
getcontext().prec=70
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
ZERO='0x'+'0'*40
BURN='BASE_FEE_BURN'
def main():
 scenarios={x['id']:x for x in load('oracle_assisted_scenarios.json')['rows'] if x['kind']=='target' and x['eligible'] and x['USD'] is not None};lead={x['address'].lower() for x in load('address_leads.json')['wallets']};orders=load('order_protocol_identification.json');fillers={x['filler'] for x in orders['orders'] if 'filler' in x};pan={x['pool'] for x in orders['pancake_events']};targetrows={r['hash']:r for r in load('unified_target_valuation.json')['rows']};byblock=defaultdict(list)
 for h,s in scenarios.items():byblock[s['block']].append(h)
 supplement={(r['block'],r['asset']):r['price_1e8'] for r in load('settlement_oracle_prices.json')['rows'] if r['price_1e8'] is not None and int(r['price_1e8'])>0} if (R/'settlement_oracle_prices.json').exists() else {}
 aggregate=defaultdict(lambda:defaultdict(D));result=[];checks=[];sig=load('classification_event_signatures.json');debt={v for k,v in sig.items() if k.startswith(('Borrow(','Repay(','Supply(','Withdraw(','LiquidationCall('))}
 for i,(n,hs) in enumerate(sorted(byblock.items()),1):
  folder='window_raw' if n<=26301940 else 'extension_raw';rs={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))};ts=defaultdict(list)
  for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result']:
   if t.get('transactionHash') in hs:ts[t['transactionHash']].append(t)
  for h in hs:
   r=rs[h];nr=parse(h,ts[h]);native={a:int(v) for a,v in nr['native_net_wei'].items()};tokens=defaultdict(lambda:defaultdict(int));pools={e['pool'].split(':')[1] for e in swaps(r)}|{l['address'] for l in r['logs'] if l['address'] in pan};protocols={l['address'] for l in r['logs'] if l['topics'] and l['topics'][0] in debt}|{'0xa17581a9e3356d9a858b789d68b4d866e593ae94'}
   for l in r['logs']:
    tt=l['topics'];a=l['address']
    if len(tt)==3 and tt[0]==TRANSFER and len(l['data'])==66:
     v=int(l['data'],16);src='0x'+tt[1][-40:];dst='0x'+tt[2][-40:];tokens[src][a]-=v;tokens[dst][a]+=v
    elif a==WETH and len(tt)==2 and tt[0] in [DEPOSIT,WITHDRAWAL]:
     owner='0x'+tt[1][-40:];v=int(l['data'],16)*(1 if tt[0]==DEPOSIT else -1);tokens[owner][a]+=v;tokens[WETH][a]-=v
   base=int(HEAD[n]['base_fee_wei']);miner=HEAD[n]['miner'];gas=int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16);burn=int(r['gasUsed'],16)*base
   native[r['from']]=native.get(r['from'],0)-gas;native[miner]=native.get(miner,0)+gas-burn;native[BURN]=native.get(BURN,0)+burn
   assert sum(native.values())==0
   tokentotal=defaultdict(int)
   for ns in tokens.values():
    for a,v in ns.items():tokentotal[a]+=v
   assert all(v==0 for v in tokentotal.values())
   ethprice=price('ETH',HEAD[n]['timestamp'],5)[0];unit={};missingprices=[]
   for a in tokentotal:
    mark=token_value(a,'1',HEAD[n]['timestamp'],5);unit[a]=D(mark['USD']) if mark['USD'] is not None else None
    if unit[a] is None:
     matched=next((x for x in scenarios[h]['assets'] if x['address']==a and x.get('USD') is not None and D(x['raw'])!=0),None)
     if matched:unit[a]=D(matched['USD'])/D(matched['raw'])
     elif (n-1,a) in supplement and a in TOK:unit[a]=D(supplement[(n-1,a)])/10**8/(D(10)**TOK[a]['decimals'])
     else:missingprices.append(a)
   accounts=[]
   for a in sorted(set(native)|set(tokens)):
    nets={t:str(v) for t,v in tokens[a].items() if v};unpriced={t:v for t,v in nets.items() if unit[t] is None};usd=D(native.get(a,0))/10**18*ethprice+sum((D(v)*unit[t] for t,v in nets.items() if unit[t] is not None),D(0))
    role='lead_set' if a in lead else 'base_fee_burn' if a==BURN else 'token_issuance_or_wrap_bookkeeping' if a in {ZERO,WETH} else 'block_fee_recipient' if a==miner else 'pool_inventory' if a in pools else 'lending_protocol_assets_excluding_liabilities' if a in protocols else 'identified_UniswapX_filler' if a in fillers else 'other_addresses'
    if usd or nets or native.get(a,0):accounts.append({'address':a,'role':role,'native_net_after_fees_wei':str(native.get(a,0)),'token_net_raw':nets,'priced_asset_change_USD':str(usd),'unpriced_asset_changes':unpriced});aggregate[a]['USD']+=usd;aggregate[a]['transactions']+=1
   total=sum((D(x['priced_asset_change_USD']) for x in accounts),D(0));assert abs(total)<D('1e-35'),total
   leadusd=sum((D(x['priced_asset_change_USD']) for x in accounts if x['role']=='lead_set'),D(0));expected=D(scenarios[h]['USD'])-D(targetrows[h]['lead_paid_gas_ETH'])*ethprice;assert abs(leadusd-expected)<D('1e-30'),(h,leadusd,expected)
   result.append({'hash':h,'block':n,'lead_change_including_own_gas_USD':str(leadusd),'conservation_residual_USD':str(total),'all_accounts_fully_priced':not any(x['unpriced_asset_changes'] for x in accounts),'accounts':accounts})
  if i%300==0:print('allocated target blocks',i,len(byblock),flush=True)
 roles=defaultdict(D)
 for r in result:
  for a in r['accounts']:roles[a['role']]+=D(a['priced_asset_change_USD'])
 out={'method':'Settlement-time allocation, NOT final beneficiary profit. Across every included transaction, native+ERC20 transfers balance by asset; gas splits into burn and priority. WETH deposit/withdrawal reserve liability uses contra token balance at WETH address. Market <=5min benchmarks with Aave fallback for missing lead assets, matching separate scenario. Other unpriced tokens retained explicitly; priced components alone conserve but are not full wealth. Pool inventory gains precede later arbitrage; lending asset outflows exclude offsetting loan claims. No sum with downstream profits or proposer payouts.','summary':{'transactions':len(result),'fully_priced_all_accounts':sum(r['all_accounts_fully_priced'] for r in result),'role_priced_asset_changes_USD':{k:str(v) for k,v in roles.items()},'sum_roles_USD':str(sum(roles.values(),D(0)))},'address_aggregates':{a:{k:str(v) for k,v in ns.items()} for a,ns in aggregate.items()},'rows':result};(R/'target_settlement_allocation.json').write_text(json.dumps(out,indent=2));print(out['summary'],flush=True)
if __name__=='__main__':main()
