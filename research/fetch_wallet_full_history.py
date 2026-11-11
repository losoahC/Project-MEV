"""Exhaust public explorer pagination; endpoint exhaustion is not chain completeness proof."""
import json,gzip,subprocess,time,threading
from pathlib import Path
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'wallet_history_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
wallets=json.loads((R/'exploiter_1_16_and_bot_audit.json').read_text())['wallets']
def fetch(w,kind):
 global last
 params={};seen=set();items=[];pages=[];error=None;exhausted=False
 for page in range(1000):
  key=json.dumps(params,sort_keys=True)
  if key in seen:error='pagination loop';break
  seen.add(key);url=f"https://eth.blockscout.com/api/v2/addresses/{w['address']}/{kind}"+('?' + urlencode(params) if params else '');p=C/f"{w['number']}_{kind}_{page:04}.json.gz"
  try:
   if p.exists():d=json.loads(gzip.decompress(p.read_bytes()))
   else:
    for attempt in range(3):
     with lock:time.sleep(max(0,.3-(time.monotonic()-last)));last=time.monotonic()
     z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30',url],capture_output=True)
     if z.returncode==0:
      d=json.loads(z.stdout)
      if isinstance(d.get('items'),list):break
     if attempt==2:raise RuntimeError(z.stderr.decode()[:200])
     time.sleep(2)
    p.write_bytes(gzip.compress(json.dumps(d).encode()))
   items.extend(d['items']);pages.append(str(p.relative_to(R)));params=d.get('next_page_params')
   if not params:exhausted=True;break
  except Exception as e:error=str(e);break
 return {'wallet':w['number'],'address':w['address'],'endpoint':kind,'pages':pages,'items':len(items),'pagination_exhausted':exhausted,'error':error,'scope':'Explorer indexed history at fetch date 2026-11-11; may include spam and post-study-cutoff events. Not independent proof against indexer omissions.'}
def main():
 results=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  fs=[pool.submit(fetch,w,k) for w in wallets for k in ['transactions','internal-transactions','token-transfers']]
  for f in as_completed(fs):
   r=f.result();results.append(r);print(r['wallet'],r['endpoint'],r['items'],r['pagination_exhausted'],r['error'],flush=True)
   (R/'wallet_history_coverage.json').write_text(json.dumps({'requested_endpoint_scans':48,'completed_endpoint_scans':len(results),'rows':results},indent=2))
if __name__=='__main__':main()
