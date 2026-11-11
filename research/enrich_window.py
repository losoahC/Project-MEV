import json,subprocess,gzip
from concurrent.futures import ThreadPoolExecutor,as_completed
from native_evidence import R,fetch
from datetime import datetime,timezone
def block(n):
 p=R/'window_raw'/f'{n}_block.json.gz'
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 old=R/'chain_raw'/f'{n}_block.json'
 if old.exists():d=json.loads(old.read_text())['result']
 else:
  z=subprocess.check_output(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBlockByNumber','params':[hex(n),True]}),'https://ethereum-rpc.publicnode.com'])
  d=json.loads(z)['result']
 p.write_bytes(gzip.compress(json.dumps(d).encode()));return d
def main():
 s=json.loads((R/'window_ledger.json').read_text());rows=[r for r in s['rows'] if any(int(v)<0 for v in r['net_token_raw'].values())]
 hashes={r['hash'] for r in rows}
 for b in json.loads((R/'mev_candidates.json').read_text())['blocks']:hashes.update(c['hash'] for c in b['candidates'])
 errors=[];native=[];blocks={r['block'] for r in rows}
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(fetch,h):h for h in hashes}
  for i,f in enumerate(as_completed(fs),1):
   try:native.append(f.result())
   except Exception as e:errors.append({'hash':fs[f],'error':str(e)})
   if i%50==0:print('native',i,len(fs),'errors',len(errors),flush=True)
 (R/'native_evidence.json').write_text(json.dumps({'source':'Etherscan displayed summaries, not independent call traces','errors':errors,'rows':native},indent=2))
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(block,n):n for n in blocks}
  for i,f in enumerate(as_completed(fs),1):
   try:f.result()
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%50==0:print('blocks',i,len(fs),'errors',len(errors),flush=True)
 (R/'enrichment_errors.json').write_text(json.dumps(errors,indent=2));print('DONE',len(native),len(blocks),len(errors),flush=True)
if __name__=='__main__':main()
