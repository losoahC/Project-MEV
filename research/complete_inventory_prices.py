import json,subprocess,zipfile,io,csv,time,threading
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'inventory_price_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
def get(url,p):
 global last
 if p.exists():return p.read_bytes()
 with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
 z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','30',url],capture_output=True)
 if z.returncode:raise ValueError(z.stderr.decode()[:100])
 p.write_bytes(z.stdout);return z.stdout
def fetch(symbol,coinbase):
 bars={};sources=[]
 if symbol in coinbase:
  windows=[('2026-10-29T19:57:00Z','2026-10-30T00:30:00Z'),('2026-10-30T00:30:00Z','2026-10-30T04:55:00Z'),('2026-10-30T04:55:00Z','2026-10-30T07:05:00Z')]
  for i,(start,end) in enumerate(windows):
   url=f'https://api.exchange.coinbase.com/products/{symbol}-USD/candles?granularity=60&start={start}&end={end}'
   try:
    d=json.loads(get(url,C/f'coinbase_{symbol}_{i}.json'));assert isinstance(d,list)
    for r in d:bars[int(r[0])]={'close':str(r[4]),'low':str(r[1]),'high':str(r[2]),'quote':'USD','source':'Coinbase'}
    sources.append({'url':url,'count':len(d)})
   except Exception as e:sources.append({'url':url,'error':str(e)})
 # Independent USDT-quoted fallback also fills missing trading minutes.
 for date in ['2026-10-29','2026-10-30']:
  pair=symbol+'USDT';url=f'https://data.binance.vision/data/spot/daily/klines/{pair}/1m/{pair}-1m-{date}.zip'
  if symbol=='USDT':continue
  try:
   z=zipfile.ZipFile(io.BytesIO(get(url,C/f'binance_{pair}_{date}.zip')));count=0
   for r in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())):
    if not r[0].isdigit():continue
    raw=int(r[0]);ts=raw//(1000000 if raw>10**14 else 1000)
    if 1793303820<=ts<=1793343900 and ts not in bars and float(r[5])>0:
     bars[ts]={'close':r[4],'low':r[3],'high':r[2],'quote':'USDT','source':'Binance public daily archive'};count+=1
   sources.append({'url':url,'added_bars':count})
  except Exception as e:sources.append({'url':url,'error':str(e)})
 return {'symbol':symbol,'bars':bars,'sources':sources}
def main():
 m={r['address'].lower():r for r in json.loads((R/'coingecko_eth_tokenlist.json').read_text())['tokens'] if r['chainId']==1};ts={t for r in json.loads((R/'candidate_classification.json').read_text())['rows'] for t in r['other_token_net_raw']}
 symbols={m[t]['symbol'].upper() for t in ts if t in m};symbols|={'ETH','USDT','BTC','USDC','DAI'};symbols={s for s in symbols if s.isascii() and s.isalnum()}
 cb={r['base_currency'] for r in json.loads((R/'coinbase_products.json').read_text()) if r['quote_currency']=='USD'};rows=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(fetch,s,cb):s for s in sorted(symbols)}
  for i,f in enumerate(as_completed(fs),1):
   rows.append(f.result())
   if i%25==0:print('price symbols',i,len(fs),flush=True)
 (R/'inventory_market_prices.json').write_text(json.dumps({'method':'Completed minute candles only; Binance quotes are USDT and require contemporaneous USDT/USD conversion. Missing zero-volume archive bars excluded. Contract identity must be checked independently.','rows':rows},indent=2));print('DONE',len(rows),sum(bool(r['bars']) for r in rows),flush=True)
if __name__=='__main__':main()
