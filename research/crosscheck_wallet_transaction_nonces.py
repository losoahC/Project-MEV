import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parent;C=R/'wallet_header_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
load=lambda n:json.loads((R/n).read_text())
def block(n):
 global last
 for p in [R/'window_raw'/f'{n}_block.json.gz',R/'full_headers_raw'/f'{n}.json.gz',C/f'{n}.json.gz']:
  if p.exists():
   b=json.loads(gzip.decompress(p.read_bytes()));b=b.get('result',b)
   if b['transactions'] and isinstance(b['transactions'][0],dict):return b
 with lock:time.sleep(max(0,.25-(time.monotonic()-last)));last=time.monotonic()
 q={'jsonrpc':'2.0','id':1,'method':'eth_getBlockByNumber','params':[hex(n),True]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True,check=True);d=json.loads(z.stdout);assert isinstance(d.get('result'),dict);(C/f'{n}.json.gz').write_bytes(gzip.compress(z.stdout));return d['result']
def main():
 xs=load('wallet_active_history.json')['rows'];cache={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(block,n):n for n in {x['block_number'] for x in xs}}
  for f in as_completed(fs):
   try:cache[fs[f]]=f.result()
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
 rows=[]
 for x in xs:
  n=x['block_number']
  if n not in cache:continue
  b=cache[n];ts={t['hash']:t for t in b['transactions']};t=ts.get(x['hash']);ok=t is not None and t['from'].lower()==x['from']['hash'].lower() and int(t['nonce'],16)==x['nonce'] and int(t['blockNumber'],16)==n and t['blockHash']==b['hash']
  rows.append({'hash':x['hash'],'block':n,'block_hash':b['hash'],'from':x['from']['hash'].lower(),'indexed_nonce':x['nonce'],'rpc_nonce':int(t['nonce'],16) if t else None,'verified':ok})
 out={'method':'Indexed outgoing transaction hash, sender, nonce and containing block cross-checked with full RPC block transaction objects.','expected':len(xs),'checked':len(rows),'mismatches':sum(not r['verified'] for r in rows),'errors':errors,'rows':rows};(R/'wallet_nonce_header_crosscheck.json').write_text(json.dumps(out,indent=2));print(out['expected'],out['checked'],out['mismatches'],errors);assert out['expected']==out['checked'] and not out['mismatches'] and not errors
if __name__=='__main__':main()
