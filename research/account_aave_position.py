import json,gzip
from pathlib import Path
from decimal import Decimal as D
from concurrent.futures import ThreadPoolExecutor
from oracle_price_scenarios import rpc,sel
from screen_expanded import net_for
import value_inventory_ledger as v
R=Path(__file__).resolve().parent;POOL='0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2';USER='0x8d53903625b8e839b9df4bd28b0efb1cd6b8639a';AT='0x23878914efe38d27c4d67ab83ed1b93a74d4086a';DEBT='0xea51d7853eefb32b6ee06b1c12e6dcca88be0ffe'
load=lambda n:json.loads((R/n).read_text())
def main():
 sig=load('classification_event_signatures.json');types={val:key.split('(')[0] for key,val in sig.items() if key.startswith(('Supply(','Withdraw(','Borrow(','Repay(','LiquidationCall('))};paths={}
 for lr in load('window_ledger.json')['rows']+load('extension_ledger.json')['rows']:
  n=lr['block'];paths[n]=R/('window_raw' if n<=26301940 else 'extension_raw')/f'{n}.json.gz'
 for lr in load('expanded_scope_details.json')['rows']:paths[lr['block']]=R/'scope_detail_raw'/f"{lr['block']}_receipts.json.gz"
 events=[];liquidations=[]
 for n,p in sorted(paths.items()):
  data=json.loads(gzip.decompress(p.read_bytes()));rs=data['result'] if isinstance(data,dict) else data
  for r in rs:
   for l in r['logs']:
    ts=l['topics']
    if l['address']!=POOL or not ts or ts[0] not in types:continue
    typ=types[ts[0]];words=[l['data'][i:i+64] for i in range(2,len(l['data']),64)];account='0x'+ts[3][-40:] if typ=='LiquidationCall' else '0x'+ts[2][-40:]
    if account!=USER:continue
    e={'hash':r['transactionHash'],'block':n,'type':typ,'user':account,'topics':ts,'data':l['data']}
    if typ in ['Supply','Borrow']:e.update(asset='0x'+ts[1][-40:],initiator='0x'+words[0][-40:],amount_raw=str(int(words[1],16)))
    elif typ in ['Repay','Withdraw']:e.update(asset='0x'+ts[1][-40:],amount_raw=str(int(words[0],16)))
    else:
     e.update(collateral_asset='0x'+ts[1][-40:],debt_asset='0x'+ts[2][-40:],debt_covered_raw=str(int(words[0],16)),collateral_received_raw=str(int(words[1],16)),liquidator='0x'+words[2][-40:],receive_a_token=bool(int(words[3],16)))
     tx=next(x for x in load('expanded_scope_details.json')['rows'] if x['hash']==e['hash']);v.HEAD[n]={'timestamp':tx['timestamp']}
     for pr in load('scope_market_prices.json')['rows']:v.PRICES.setdefault(pr['symbol'],{}).update(pr['bars'])
     col=v.token_value(e['collateral_asset'],e['collateral_received_raw'],tx['timestamp'],5);debt=v.token_value(e['debt_asset'],e['debt_covered_raw'],tx['timestamp'],5);e['collateral_market_valuation']=col;e['repaid_debt_market_valuation']=debt;e['gross_liquidation_spread_USD']=str(D(col['USD'])-D(debt['USD'])) if col['USD'] is not None and debt['USD'] is not None else None
     group={r['from'],r['to'],e['liquidator']};cash=sum((D(x)/10**18 for a,x in tx['native']['native_net_wei'].items() if a in group),D(0))-D(tx['gas_wei'])/10**18;net=net_for(r,group);e['liquidator_root_boundary']=sorted(group);e['liquidator_root_net_token_raw']=net;e['liquidator_root_cashflow_ETH']=str(cash);e['liquidator_root_valuation']=v.portfolio(str(cash),net,n,5);liquidations.append(e)
    events.append(e)
 cutoff=int(load('scope_latest_cutoff.json')['result']['number'],16);ns=sorted({26300639,26303950,cutoff}|{e['block']+offset for e in liquidations for offset in [-1,0]});tasks=[(n,k,a,s) for n in ns for k,a,s in [('account',POOL,sel('getUserAccountData(address)')),('collateral',AT,'0x70a08231'),('debt',DEBT,'0x70a08231')]]
 def get(t):
  n,k,a,s=t;raw=rpc(f'aave_user_{n}_{k}',a,s+USER[2:].zfill(64),n);return n,k,[int(raw[i:i+64],16) for i in range(2,len(raw),64)]
 states={n:{} for n in ns}
 with ThreadPoolExecutor(max_workers=3) as ex:
  for n,k,words in ex.map(get,tasks):
   if k=='account':assert len(words)==6;states[n].update(total_collateral_oracle_USD=str(D(words[0])/10**8),total_debt_oracle_USD=str(D(words[1])/10**8),available_borrow_oracle_USD=str(D(words[2])/10**8),liquidation_threshold_bps=words[3],ltv_bps=words[4],health_factor=str(D(words[5])/10**18))
   elif k=='collateral':states[n]['aUSDT_balance']=str(D(words[0])/10**6)
   else:states[n]['variable_WETH_debt_balance']=str(D(words[0])/10**18)
 out={'method':'Aave pool events for known lead borrower and historical account/interest-bearing collateral/debt balances. Debt burn is liability reduction, NOT an additional asset loss. Liquidation gross spread excludes gas, flash-loan fees, hedges and protocol split. Root boundary valuation is conditional and not automatically full liquidator profit. Account USD uses protocol oracle, not CEX execution quote.','user':USER,'sources':['https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/interfaces/IPool.sol','https://raw.githubusercontent.com/bgd-labs/aave-address-book/main/src/AaveV3Ethereum.sol'],'events':events,'historical_states':states,'liquidations':liquidations};(R/'aave_borrower_accounting.json').write_text(json.dumps(out,indent=2));print('events',[(e['type'],e.get('amount_raw'),e['block']) for e in events]);print('states',states);print('liquidation spread',[(e['gross_liquidation_spread_USD'],e['liquidator_root_valuation']['USD']) for e in liquidations])
if __name__=='__main__':main()
