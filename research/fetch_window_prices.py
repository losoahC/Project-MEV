import json,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'prices_raw';C.mkdir(exist_ok=True)
def one(symbol):
 url=f'https://api.exchange.coinbase.com/products/{symbol}-USD/candles?granularity=60&start=2026-10-29T19%3A57%3A00Z&end=2026-10-30T00%3A20%3A00Z'
 if (C/f'{symbol}.json').exists():return {'symbol':symbol,'url':url,'candles':len(json.loads((C/f'{symbol}.json').read_text()))}
 z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','30',url],capture_output=True)
 if z.returncode:return {'symbol':symbol,'url':url,'error':z.stderr.decode()[:150]}
 d=json.loads(z.stdout)
 if not isinstance(d,list):return {'symbol':symbol,'url':url,'error':str(d)}
 (C/f'{symbol}.json').write_text(json.dumps(d));return {'symbol':symbol,'url':url,'candles':len(d)}
with ThreadPoolExecutor(max_workers=3) as ex:
 rows=list(ex.map(one,['ETH','USDT','USDC','UNI','PEPE','ENA','LINK','AAVE','BTC','USDe','RLUSD','ONDO']))
(R/'window_price_sources.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
