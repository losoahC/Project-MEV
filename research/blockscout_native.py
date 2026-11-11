"""Public explorer internal calls, with pagination and zero-sum checks."""
import json,gzip,subprocess,hashlib,time
from pathlib import Path
from urllib.parse import urlencode
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent;C=R/'blockscout_raw';C.mkdir(exist_ok=True)
def fetch(h):
 base='https://eth.blockscout.com/api/v2/transactions/'+h+'/internal-transactions';url=base;seen=set();calls=[];pages=0
 while url:
  if url in seen:raise ValueError('pagination loop')
  seen.add(url);p=C/(h+'_'+hashlib.sha256(url.encode()).hexdigest()[:12]+'.json.gz')
  if p.exists():d=json.loads(gzip.decompress(p.read_bytes()))
  else:
   time.sleep(1.1)
   z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35',url],capture_output=True)
   if z.returncode:raise ValueError(z.stderr.decode()[:200])
   d=json.loads(z.stdout)
   if not isinstance(d.get('items'),list):raise ValueError(str(d)[:200])
   p.write_bytes(gzip.compress(z.stdout))
  calls.extend(d['items']);pages+=1;params=d.get('next_page_params');url=base+'?'+urlencode(params) if params else None
 net=defaultdict(int);keys=set();excluded=[]
 for c in calls:
  if c['transaction_hash'].lower()!=h:raise ValueError('hash mismatch')
  k=c['index']
  if k in keys:raise ValueError('duplicate call index')
  keys.add(k)
  if c.get('error') or not c.get('success'):continue
  v=int(c.get('value') or '0')
  if not v:continue
  if k==0:excluded.append('root index zero excluded');continue
  if c['type'] not in ['call','create','create2','selfdestruct','suicide']:continue
  to=c.get('to') or c.get('created_contract')
  if not to:raise ValueError('nonzero transfer without recipient')
  a=c['from']['hash'].lower();b=to['hash'].lower();net[a]-=v;net[b]+=v
 out={a:str(Decimal(v)/Decimal(10)**18) for a,v in net.items() if v}
 return {'hash':h,'source':base,'method':'Blockscout paginated successful value-transfer calls; delegatecall/staticcall excluded; top-level value and gas excluded','summary_present':bool(out),'native_internal_net_eth':out,'net_conservation_eth':str(sum(map(Decimal,out.values()),Decimal(0))),'call_count':len(calls),'pages':pages,'excluded':excluded}
def main():
 p=R/'native_evidence.json';d=json.loads(p.read_text());rows={r['hash']:r for r in d['rows']}
 missing={e['hash'] for e in d['errors']};sample=json.loads((R/'swaps_observed.json').read_text())['swaps'];missing.update(r['tx_hash'] for r in sample)
 results=[];errors=[];cross=[]
 with ThreadPoolExecutor(max_workers=1) as ex:
  fs={ex.submit(fetch,h):h for h in sorted(missing)}
  for i,f in enumerate(as_completed(fs),1):
   h=fs[f]
   try:
    r=f.result();results.append(r)
    if h in rows:cross.append({'hash':h,'matches':{a:Decimal(v) for a,v in rows[h]['native_internal_net_eth'].items() if Decimal(v)}=={a:Decimal(v) for a,v in r['native_internal_net_eth'].items() if Decimal(v)}})
    else:rows[h]=r
   except Exception as e:errors.append({'hash':h,'error':str(e)})
   if i%25==0:print('native fallback',i,len(fs),'errors',len(errors),flush=True)
 (R/'blockscout_native_evidence.json').write_text(json.dumps({'rows':results,'errors':errors,'crosschecks':cross},indent=2))
 p.write_text(json.dumps({'source':'Etherscan displayed summaries and Blockscout paginated calls; not own-node replays','errors':[e for e in errors if e['hash'] not in rows],'rows':list(rows.values())},indent=2))
 print('DONE',len(rows),'errors',len(errors),'crosschecks',cross,flush=True)
if __name__=='__main__':main()
