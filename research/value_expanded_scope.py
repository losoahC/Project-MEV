import json,zipfile,io,csv
from pathlib import Path
from collections import defaultdict,Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from decimal import Decimal as D
import complete_inventory_prices as fetcher
import value_inventory_ledger as valuation
R=Path(__file__).resolve().parent;C=R/'scope_prices_raw';C.mkdir(exist_ok=True)
load=lambda n:json.loads((R/n).read_text())
def fetch(task):
 symbol,dates,hours,cb=task;bars={};sources=[]
 for hour in sorted(hours) if symbol in cb else []:
  start=datetime.fromtimestamp(hour-360,timezone.utc).isoformat().replace('+00:00','Z');end=datetime.fromtimestamp(hour+3600,timezone.utc).isoformat().replace('+00:00','Z');url=f'https://api.exchange.coinbase.com/products/{symbol}-USD/candles?granularity=60&start={start}&end={end}'
  try:
   d=json.loads(fetcher.get(url,C/f'coinbase_{symbol}_{hour}.json'));assert isinstance(d,list)
   for r in d:
    if D(str(r[5]))>0:bars[int(r[0])]={'close':str(r[4]),'low':str(r[1]),'high':str(r[2]),'quote':'USD','source':'Coinbase'}
   sources.append({'url':url,'count':len(d)})
  except Exception as e:sources.append({'url':url,'error':str(e)})
 if symbol!='USDT':
  for date in sorted(dates):
   pair=symbol+'USDT';url=f'https://data.binance.vision/data/spot/daily/klines/{pair}/1m/{pair}-1m-{date}.zip'
   try:
    z=zipfile.ZipFile(io.BytesIO(fetcher.get(url,C/f'{pair}_{date}.zip')));count=0
    for r in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())):
     if not r[0].isdigit() or D(r[5])<=0:continue
     raw=int(r[0]);ts=raw//(1000000 if raw>10**14 else 1000)
     if ts not in bars:bars[ts]={'close':r[4],'low':r[3],'high':r[2],'quote':'USDT','source':'Binance public daily archive'};count+=1
    sources.append({'url':url,'added_bars':count})
   except Exception as e:sources.append({'url':url,'error':str(e)})
 # Alternative public market; zero-volume bars are not fresh quotes.
 if not bars and symbol not in ['ETH','USDT','FUN']:
  for hour in sorted(hours):
   url=f'https://api.kucoin.com/api/v1/market/candles?type=1min&symbol={symbol}-USDT&startAt={hour-360}&endAt={hour+3600}'
   try:
    d=json.loads(fetcher.get(url,C/f'kucoin_{symbol}_{hour}.json'));assert d.get('code')=='200000',str(d)[:100]
    for r in d['data']:
     if D(r[5])>0:bars[int(r[0])]={'close':r[2],'low':r[4],'high':r[3],'quote':'USDT','source':'KuCoin public candles (ticker mapping assumption)'}
    sources.append({'url':url,'count':len(d['data'])})
   except Exception as e:sources.append({'url':url,'error':str(e)})
 return {'symbol':symbol,'bars':{str(k):v for k,v in bars.items()},'sources':sources}
def main():
 rows=load('expanded_scope_details.json')['rows'];tasks=defaultdict(lambda:{'dates':set(),'hours':set()});cb={r['base_currency'] for r in load('coinbase_products.json') if r['quote_currency']=='USD'}
 for r in rows:
  symbols={'ETH','USDT'}|{valuation.VERIFIED.get(a,{}).get('symbol',valuation.TOK.get(a,{}).get('symbol','')).upper() for a in r['net_token_raw']};ts=r['timestamp']
  for s in symbols:
   if s and s.isascii() and s.isalnum():tasks[s]['dates'].add(datetime.fromtimestamp(ts,timezone.utc).strftime('%Y-%m-%d'));tasks[s]['hours'].add(ts//3600*3600)
 prices=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(fetch,(s,t['dates'],t['hours'],cb)):s for s,t in tasks.items()}
  for f in as_completed(fs):prices.append(f.result());print('scope price',fs[f],len(prices[-1]['bars']),flush=True)
 (R/'scope_market_prices.json').write_text(json.dumps({'rows':prices},indent=2))
 for p in prices:valuation.PRICES.setdefault(p['symbol'],{}).update(p['bars'])
 out=[]
 for r in rows:
  valuation.HEAD[r['block']]={'timestamp':r['timestamp']};cash=str(D(r['lead_native_wei'])/D(10**18));out.append({**r,'strict':valuation.portfolio(cash,r['net_token_raw'],r['block'],0),'five_minute':valuation.portfolio(cash,r['net_token_raw'],r['block'],5),'fifteen_minute_sensitivity':valuation.portfolio(cash,r['net_token_raw'],r['block'],15)})
 summary={}
 for mode in ['strict','five_minute','fifteen_minute_sensitivity']:
  good=[r for r in out if r['category']=='pool_swap_compatible' and r[mode]['USD'] is not None];summary[mode]={'count':len(good),'execution_shortfall_USD':str(-sum((D(r[mode]['USD']) for r in good),D(0)))}
 (R/'expanded_scope_valuation.json').write_text(json.dumps({'method':'Additional known-token net outflows only, not every transaction on chain. Full receipts/traces matched to block. Market-only prior-minute versus separate <=5 minute stale. Compatible Swap signatures are classification, not factory proof. Gas excluded from lead execution shortfall. No zero substitution for missing prices; not causal MEV.','summary':summary,'rows':out},indent=2));print('DONE',summary,flush=True)
if __name__=='__main__':main()
