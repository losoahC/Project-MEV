import json
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from oracle_price_scenarios import rpc,sel,ORACLE,PROVIDER
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def one(task):
 n,a=task
 try:
  o=rpc(str(n)+'_provider',PROVIDER,sel('getPriceOracle()'),n);assert '0x'+o[-40:]==ORACLE
  raw=rpc(str(n)+'_asset_'+a,ORACLE,sel('getAssetPrice(address)')+a[2:].zfill(64),n);return {'block':n,'asset':a,'price_1e8':str(int(raw,16))}
 except Exception as e:return {'block':n,'asset':a,'error':str(e),'price_1e8':None}
def main():
 known={r['address'].lower() for r in load('coingecko_eth_tokenlist.json')['tokens'] if r['chainId']==1};tasks=set()
 for tx in load('target_settlement_allocation.json')['rows']:
  for a in tx['accounts']:
   for token in a['unpriced_asset_changes']:
    if token in known:tasks.add((tx['block']-1,token))
 with ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(one,sorted(tasks)))
 (R/'settlement_oracle_prices.json').write_text(json.dumps({'method':'Separate historical Aave oracle fallback for counterparty asset components only; nonpositive/missing responses are not prices.','rows':rows},indent=2));print('supplement oracle queries',len(rows),'positive',sum(r['price_1e8'] is not None and int(r['price_1e8'])>0 for r in rows))
if __name__=='__main__':main()
