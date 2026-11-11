"""Public Blockscout range queries, paginated, cached, with explicit coverage."""
import argparse,gzip,json,subprocess,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--first',type=int,default=26300640);p.add_argument('--last',type=int,default=26303950);p.add_argument('--delay',type=float,default=7);a=p.parse_args()
 cache=R/'bulk_native_raw';cache.mkdir(exist_ok=True);coverage=[];errors=[];nets=defaultdict(lambda:defaultdict(int));seen=set()
 for lo in range(a.first,a.last+1,25):
  hi=min(lo+24,a.last);page=1;chunk=[];local=set()
  try:
   while True:
    url=f'https://eth.blockscout.com/api?module=account&action=txlistinternal&startblock={lo}&endblock={hi}&page={page}&offset=10000&sort=asc'
    path=cache/f'{lo}_{hi}_{page}.json.gz'
    if path.exists():d=json.loads(gzip.decompress(path.read_bytes()))
    else:
     for attempt in range(4):
      time.sleep(a.delay+attempt*30)
      z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','60',url],capture_output=True)
      try:
       if z.returncode:raise ValueError(z.stderr.decode()[:150])
       d=json.loads(z.stdout)
       if not isinstance(d.get('result'),list):raise ValueError(str(d)[:150])
       break
      except Exception as e:
       if attempt==3 or '429' in str(e):raise
     path.write_bytes(gzip.compress(json.dumps(d).encode()))
    rows=d['result']
    if len(rows)>10000:raise ValueError('unexpected page size')
    for r in rows:
     if not lo<=int(r['blockNumber'])<=hi:raise ValueError('out-of-range block')
     key=(r['transactionHash'].lower(),int(r['index']))
     if key in local or key in seen:raise ValueError('duplicate trace index or repeated page')
     local.add(key)
    chunk.extend(rows)
    if len(rows)<10000:break
    page+=1
   for r in chunk:
    if r.get('isError')!='0' or r.get('errCode') or int(r['index'])==0:continue
    typ=r.get('callType') or r.get('type')
    if typ not in ('call','create','create2','selfdestruct','suicide'):continue
    v=int(r['value'])
    if not v:continue
    sender=r['from'].lower();to=(r.get('to') or r.get('contractAddress') or '').lower()
    if not sender or not to:raise ValueError('missing transfer endpoint')
    h=r['transactionHash'].lower();nets[h][sender]-=v;nets[h][to]+=v
   seen.update(local);coverage.append({'first':lo,'last':hi,'pages':page,'rows':len(chunk)})
  except Exception as e:
   errors.append({'first':lo,'last':hi,'error':str(e)})
   if '429' in str(e):
    print('Rate limited; stopping and retaining completed ranges',flush=True);break
  if len(coverage)%10==0:print('covered chunks',len(coverage),'errors',len(errors),flush=True)
 out={'requested_first':a.first,'requested_last':a.last,'source':'https://eth.blockscout.com/api?module=account&action=txlistinternal','method':'Successful internal value-transferring calls; root/delegatecall/staticcall excluded. Empty transaction net only established within fully paginated covered ranges. Explorer indexing, not independent replay.','coverage':coverage,'errors':errors,'internal_net_wei':{h:{k:str(v) for k,v in n.items() if v} for h,n in nets.items()}}
 (R/'bulk_native.json').write_text(json.dumps(out,indent=2));print('DONE',len(coverage),len(errors),len(nets),flush=True)
if __name__=='__main__':main()
