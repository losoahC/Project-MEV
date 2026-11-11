import json,subprocess,time,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;C=R/'relay_history_raw';C.mkdir(exist_ok=True)
ENDPOINTS={'flashbots':'https://boost-relay.flashbots.net','ultrasound':'https://relay.ultrasound.money','agnostic':'https://agnostic-relay.net','aestus':'https://aestus.live'}
def one(pair):
 name,base=pair;cursor=15543313;rows=[];seen=set();errors=[];pages=[]
 for page in range(60):
  url=base+f'/relay/v1/data/bidtraces/proposer_payload_delivered?limit=100&cursor={cursor}';p=C/(name+'_'+str(cursor)+'.json')
  try:
   if p.exists():d=json.loads(p.read_text())
   else:
    time.sleep(.5);z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35',url],capture_output=True)
    if z.returncode:raise ValueError(z.stderr.decode()[:180])
    d=json.loads(z.stdout);assert isinstance(d,list);p.write_text(json.dumps(d))
   if not d:break
   if any(int(r['slot'])>cursor for r in d):raise ValueError('cursor not respected')
   pages.append({'url':url,'count':len(d)})
   for r in d:
    key=(r['block_hash'],r['slot'])
    if key in seen:continue
    seen.add(key)
    if 26300640<=int(r['block_number'])<=26303950:rows.append(r)
   if min(int(r['block_number']) for r in d)<26300640:break
   nxt=min(int(r['slot']) for r in d)-1
   if nxt>=cursor:raise ValueError('pagination did not advance')
   cursor=nxt
  except Exception as e:errors.append({'url':url,'error':str(e)});break
 return {'relay':name,'base':base,'rows':rows,'pages':pages,'errors':errors}
def main():
 with ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(one,ENDPOINTS.items()))
 (R/'relay_history.json').write_text(json.dumps({'rows':rows,'warning':'Delivered records must match canonical block hashes. A relay bid value is not an additional revenue item to add to onchain payouts.'},indent=2));print([(r['relay'],len(r['rows']),r['errors']) for r in rows],flush=True)
if __name__=='__main__':main()
