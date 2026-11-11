"""Continuous receipt scan. No native-ETH profit inference from token logs."""
import json, gzip, subprocess, time, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from identify_mev import TRANSFER, SWAP_V3, WETH, DEPOSIT, WITHDRAWAL
R=Path(__file__).resolve().parent
C=R/'window_raw'; C.mkdir(exist_ok=True)
URL='https://ethereum-rpc.publicnode.com'
def get(n):
 p=C/f'{n}.json.gz'
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))
 old=R/'chain_raw'/f'{n}_receipts.json'
 if old.exists():d=json.loads(old.read_text())['result']
 else:
  for attempt in range(3):
   z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getBlockReceipts','params':[hex(n)]}),URL],capture_output=True)
   try:
    d=json.loads(z.stdout)['result']
    if not isinstance(d,list):raise ValueError('not list')
    break
   except Exception:
    if attempt==2:raise RuntimeError(z.stderr.decode()[:180])
    time.sleep(1)
 p.write_bytes(gzip.compress(json.dumps(d).encode()));return d
def main():
 global C
 parser=argparse.ArgumentParser()
 parser.add_argument('--first',type=int,default=26300640)
 parser.add_argument('--last',type=int,default=26301940)
 parser.add_argument('--output',default='window_ledger.json')
 parser.add_argument('--cache',default='window_raw')
 args=parser.parse_args();C=R/args.cache;C.mkdir(exist_ok=True)
 leads=json.loads((R/'address_leads.json').read_text())['wallets']; aset={w['address'].lower() for w in leads}
 rows=[];errors=[];count=0; stats=[]
 lo,hi=args.first,args.last
 with ThreadPoolExecutor(max_workers=6) as pool:
  fs={pool.submit(get,n):n for n in range(lo,hi+1)}
  for i,f in enumerate(as_completed(fs),1):
   n=fs[f]
   try:recs=f.result()
   except Exception as e:errors.append({'block':n,'error':str(e)});continue
   count+=len(recs)
   times=[int(l['blockTimestamp'],16) for r in recs for l in r['logs'] if 'blockTimestamp' in l]
   stats.append({'block':n,'timestamp':times[0] if times else None,'transactions':len(recs),'gas_fee_wei':str(sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in recs))})
   for r in recs:
    net=defaultdict(int);flows=[];involved=set()
    for l in r['logs']:
     ts=l['topics']
     if len(ts)!=3 or ts[0]!=TRANSFER:continue
     a,b='0x'+ts[1][-40:],'0x'+ts[2][-40:]
     if a not in aset and b not in aset:continue
     v=int(l['data'],16);t=l['address'];flows.append({'token':t,'from':a,'to':b,'raw':str(v)})
     if a in aset:net[t]-=v;involved.add(a)
     if b in aset:net[t]+=v;involved.add(b)
    if not flows and r['from'] not in aset and r.get('to') not in aset:continue
    rows.append({'hash':r['transactionHash'],'block':n,'index':int(r['transactionIndex'],16),'timestamp':times[0] if times else None,'from':r['from'],'to':r['to'],'status':int(r['status'],16),'gas_fee_wei':str(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16)),'net_token_raw':{t:str(v) for t,v in net.items() if v},'flows':flows,'lead_addresses':sorted(involved),'v3_pools':sorted({l['address'] for l in r['logs'] if l['topics'] and l['topics'][0]==SWAP_V3})})
   if i%50==0:print('blocks',i,'/',len(fs),'transactions',count,'lead transactions',len(rows),'errors',len(errors),flush=True)
 rows.sort(key=lambda x:(x['block'],x['index']));stats.sort(key=lambda x:x['block'])
 out={'scope':'Continuous Ethereum receipts; 55 third-party address leads, not verified attribution; native-only internal transfers omitted','first_block':lo,'last_block':hi,'blocks_successful':len(stats),'transactions_scanned':count,'errors':errors,'block_stats':stats,'rows':rows}
 (R/args.output).write_text(json.dumps(out,indent=2));print('DONE',len(stats),count,len(rows),'errors',len(errors),flush=True)
if __name__=='__main__':main()
