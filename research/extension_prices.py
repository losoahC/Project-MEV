"""Contract metadata and historical minute candles; no spot-price substitution."""
import json,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;C=R/'extension_prices_raw';C.mkdir(exist_ok=True);M=R/'token_metadata_raw';M.mkdir(exist_ok=True)
def get(url,path):
 if path.exists():return json.loads(path.read_text())
 time.sleep(.5)
 z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35',url],capture_output=True)
 if z.returncode:raise ValueError(z.stderr.decode()[:120])
 d=json.loads(z.stdout);path.write_text(json.dumps(d));return d
def metadata(a):
 try:
  d=get('https://eth.blockscout.com/api/v2/tokens/'+a,M/(a+'.json'))
  assert d['address_hash'].lower()==a
  return {'address':a,'symbol':d['symbol'],'name':d['name'],'decimals':int(d['decimals'])}
 except Exception as e:return {'address':a,'error':str(e)}
def candles(s):
 out=[];sources=[]
 for i,(start,end) in enumerate([('2026-10-30T00:18:00Z','2026-10-30T04:58:00Z'),('2026-10-30T04:58:00Z','2026-10-30T07:04:00Z')]):
  url=f'https://api.exchange.coinbase.com/products/{s}-USD/candles?granularity=60&start={start}&end={end}'
  try:
   d=get(url,C/f'{s}_{i}.json')
   if not isinstance(d,list):raise ValueError(str(d))
   out.extend(d);sources.append({'url':url,'candles':len(d)})
  except Exception as e:sources.append({'url':url,'error':str(e)})
 if out:(C/f'{s}.json').write_text(json.dumps(sorted({int(r[0]):r for r in out}.values())))
 return {'symbol':s,'sources':sources}
def main():
 ledger=json.loads((R/'extension_ledger.json').read_text());addresses=sorted({t for r in ledger['rows'] for t,v in r['net_token_raw'].items() if int(v)<0})
 with ThreadPoolExecutor(max_workers=2) as ex:meta=list(ex.map(metadata,addresses))
 (R/'extension_token_metadata.json').write_text(json.dumps(meta,indent=2));print('metadata',len(meta),flush=True)
 symbols=sorted({'ETH','USDT','BTC'}|{m['symbol'] for m in meta if 'error' not in m and m['symbol'].isalnum()})
 with ThreadPoolExecutor(max_workers=2) as ex:prices=list(ex.map(candles,symbols))
 (R/'extension_price_sources.json').write_text(json.dumps({'warning':'Exchange symbol correspondence requires identity review before valuation; unavailable candles are not zero or current prices.','rows':prices},indent=2));print('prices',len(prices),flush=True)
if __name__=='__main__':main()
