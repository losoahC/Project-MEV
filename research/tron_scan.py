"""TRON address history and transaction-info evidence, first 24 hours."""
import json,subprocess,gzip,hashlib,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict,Counter
from urllib.parse import urlencode,urlparse
from decimal import Decimal
R=Path(__file__).resolve().parent;C=R/'tron_raw';C.mkdir(exist_ok=True)
ABC='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def addrhex(a):
 n=0
 for c in a:n=n*58+ABC.index(c)
 b=n.to_bytes(25,'big');assert hashlib.sha256(hashlib.sha256(b[:-4]).digest()).digest()[:4]==b[-4:];return b[:-4].hex()
def request(url,payload=None):
 key=hashlib.sha256((url+json.dumps(payload,sort_keys=True)).encode()).hexdigest();p=C/(key+'.json.gz')
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 time.sleep(3)
 cmd=['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40',url]
 if payload is not None:cmd+=['-H','Content-Type: application/json','--data',json.dumps(payload)]
 z=subprocess.run(cmd,capture_output=True)
 if z.returncode:raise RuntimeError(z.stderr.decode()[:180])
 d=json.loads(z.stdout)
 if not d or d.get('success') is False:raise ValueError(str(d)[:180])
 p.write_bytes(gzip.compress(z.stdout));return d
def history(a):
 url='https://api.trongrid.io/v1/accounts/'+a+'/transactions?'+urlencode({'only_confirmed':'true','limit':200,'min_timestamp':1793304000000,'max_timestamp':1793390400000})
 rows=[];seen=set()
 while url:
  if url in seen:raise ValueError('pagination loop')
  if urlparse(url).netloc!='api.trongrid.io':raise ValueError('unexpected page host')
  seen.add(url);d=request(url);rows.extend(d['data']);url=d.get('meta',{}).get('links',{}).get('next')
 return rows
def main():
 state=json.loads((R/'tracker_state.json').read_text());leads=[w for w in state['wallets'] if w['chain']=='tron' and w['role'] in state['attackerSideRoles']];addresses={addrhex(w['address']):w['address'] for w in leads};aset=set(addresses)
 txs={};errors=[]
 with ThreadPoolExecutor(max_workers=1) as ex:
  fs={ex.submit(history,w['address']):w['address'] for w in leads}
  for i,f in enumerate(as_completed(fs),1):
   try:
    for t in f.result():txs[t['txID']]=t
   except Exception as e:errors.append({'address':fs[f],'error':str(e)})
   if i%10==0:print('TRON addresses',i,len(fs),'transactions',len(txs),'errors',len(errors),flush=True)
 (R/'tron_transactions.json').write_text(json.dumps({'from_ms':1793304000000,'to_ms':1793390400000,'address_count':len(leads),'errors':errors,'rows':list(txs.values())}))
 targets={h:t for h,t in txs.items() if any(c['type']=='TriggerSmartContract' and c['parameter']['value'].get('owner_address') in aset for c in t['raw_data']['contract'])}
 info={}
 with ThreadPoolExecutor(max_workers=1) as ex:
  fs={ex.submit(request,'https://api.trongrid.io/wallet/gettransactioninfobyid',{'value':h}):h for h in targets}
  for i,f in enumerate(as_completed(fs),1):
   try:info[fs[f]]=f.result()
   except Exception as e:errors.append({'hash':fs[f],'error':str(e)})
   if i%25==0:print('TRON receipts',i,len(fs),'errors',len(errors),flush=True)
 rows=[]
 for h,t in targets.items():
  d=info.get(h)
  if d is None:continue
  net=defaultdict(int);trx=0
  success=all(r.get('contractRet')=='SUCCESS' for r in t['ret']) and d.get('receipt',{}).get('result','SUCCESS')=='SUCCESS'
  if success:
   for l in d.get('log',[]):
    ts=l['topics']
    if len(ts)==3 and ts[0]=='ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
     a,b='41'+ts[1][-40:],'41'+ts[2][-40:];v=int(l['data'],16)
     if a in aset:net[l['address']]-=v
     if b in aset:net[l['address']]+=v
   for c in t['raw_data']['contract']:
    p=c['parameter']['value'];v=p.get('call_value',0)
    if p.get('owner_address') in aset:trx-=v
    if p.get('contract_address') in aset:trx+=v
   for x in d.get('internal_transactions',[]):
    if x.get('rejected'):continue
    v=sum(q.get('callValue',0) for q in x.get('callValueInfo',[]) if not q.get('tokenId'))
    if x.get('caller_address') in aset:trx-=v
    if x.get('transferTo_address') in aset:trx+=v
  rows.append({'hash':h,'timestamp_ms':t['block_timestamp'],'success':success,'contracts':[c['parameter']['value'].get('contract_address') for c in t['raw_data']['contract']],'token_net_raw':{a:str(v) for a,v in net.items() if v},'trx_net_before_fee':str(Decimal(trx)/10**6),'fee_trx':str(Decimal(d.get('fee',0))/10**6),'internal_call_count':len(d.get('internal_transactions',[])),'log_count':len(d.get('log',[]))})
 rows.sort(key=lambda r:r['timestamp_ms']);(R/'tron_ledger.json').write_text(json.dumps({'scope':'46 tracker lead addresses; 24h transaction history; owned-origin smart-contract calls only. Loans must be excluded from swaps before valuation','errors':errors,'rows':rows},indent=2));print('DONE TRON',len(txs),len(targets),len(rows),'errors',len(errors),flush=True)
if __name__=='__main__':main()
