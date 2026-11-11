"""Pool-event candidate scan; event signatures do not certify pool factory."""
import json,gzip,argparse
from collections import defaultdict,Counter
from pathlib import Path
from identify_mev import TRANSFER,SWAP_V3,WETH,DEPOSIT,WITHDRAWAL
R=Path(__file__).resolve().parent
V2='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
V4='0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
def swaps(r):
 out=[]
 for l in r['logs']:
  ts=l['topics']
  if not ts:continue
  if ts[0] not in [V2,SWAP_V3,V4]:continue
  typ={V2:'V2',SWAP_V3:'V3',V4:'V4'}[ts[0]]
  key=typ+':'+l['address']+(':'+ts[1] if typ=='V4' else '')
  a=int(l['data'][2:66],16);b=int(l['data'][66:130],16)
  if typ=='V2':a-=int(l['data'][130:194],16);b-=int(l['data'][194:258],16)
  else:
   if a>=2**255:a-=2**256
   if b>=2**255:b-=2**256
  out.append({'pool':key,'amount0':str(a),'amount1':str(b),'log_index':int(l['logIndex'],16)})
 return out
def net_for(r,accounts):
 net=defaultdict(int)
 for l in r['logs']:
  ts=l['topics'];token=l['address']
  if token==WETH and len(ts)==2 and ts[0] in [DEPOSIT,WITHDRAWAL]:
   if '0x'+ts[1][-40:] in accounts:net[token]+=int(l['data'],16)*(1 if ts[0]==DEPOSIT else -1)
  elif len(ts)==3 and ts[0]==TRANSFER:
   a,b='0x'+ts[1][-40:],'0x'+ts[2][-40:];v=int(l['data'],16)
   if a in accounts:net[token]-=v
   if b in accounts:net[token]+=v
 return {t:str(v) for t,v in net.items() if v}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--extension',action='store_true');parser.add_argument('--combined',action='store_true');args=parser.parse_args()
 prefix='full_' if args.combined else ('extension_' if args.extension else 'expanded_')
 ledger=json.loads((R/('extension_ledger.json' if args.extension else 'window_ledger.json')).read_text());lead={r['hash']:r for r in ledger['rows']}
 if args.combined:lead.update({r['hash']:r for r in json.loads((R/'extension_ledger.json').read_text())['rows']})
 targets={};events=[];pending=[];failed=0
 paths=list((R/('extension_raw' if args.extension else 'window_raw')).glob('[0-9]*.json.gz'))
 if args.combined:paths+=list((R/'extension_raw').glob('[0-9]*.json.gz'))
 for i,p in enumerate(sorted(paths,key=lambda p:p.name),1):
  if '_block' in p.name:continue
  n=int(p.name.split('.')[0]);rs=json.loads(gzip.decompress(p.read_bytes()))
  for r in rs:
   if int(r['status'],16)==0:failed+=1
   ss=swaps(r)
   if not ss:continue
   h=r['transactionHash'];li=lead.get(h)
   if li and any(int(v)<0 for v in li['net_token_raw'].values()):targets[h]={**li,'pool_events':ss}
   pending.append((n,r,ss))
  if i%300==0:print('read',i,flush=True)
 pools={s['pool'] for t in targets.values() for s in t['pool_events']}
 last={};candidates=[]
 for n,r,ss in pending:
  h=r['transactionHash'];idx=int(r['transactionIndex'],16)
  matched=[s for s in ss if s['pool'] in pools]
  if not matched:continue
  prior=[]
  for s in matched:
   prev=last.get(s['pool'])
   if prev and 0<=n-prev['block']<=5 and prev['hash']!=h:
    a=int(s['amount0']);b=int(prev['amount0']);prior.append({'pool':s['pool'],'target':prev['hash'],'block_distance':n-prev['block'],'opposite_amount0':a*b<0})
  if h in targets:
   for s in ss:last[s['pool']]={'hash':h,'block':n,'amount0':s['amount0']}
  elif prior:
   candidates.append({'hash':h,'block':n,'index':idx,'from':r['from'],'to':r['to'],'status':int(r['status'],16),'gas_fee_wei':str(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16)),'prior_targets':prior,'pool_events':ss,'sender_and_to_token_net_raw':net_for(r,{r['from'],r['to']}),'warning':'from+to boundary is provisional; shared routers and offchain balances require separate attribution'})
  events.append({'hash':h,'block':n,'index':idx,'target':h in targets,'pool_events':matched})
 (R/(prefix+'swaps.json')).write_text(json.dumps({'scope':'Successful lead-address net-token-outflow transactions with V2/V3/V4-compatible Swap events','rows':list(targets.values())},indent=2))
 (R/(prefix+'candidates.json')).write_text(json.dumps({'method':'Affected pool overlap after target in same or next five blocks; NOT proof of arbitrage or causality','failed_transactions_in_entire_window':failed,'affected_pool_count':len(pools),'affected_pool_transaction_count':len(events),'rows':candidates},indent=2))
 (R/('full_pool_events.json' if args.combined else ('extension_pool_events.json' if args.extension else 'affected_pool_events.json'))).write_text(json.dumps(events))
 print('DONE targets',len(targets),'pools',len(pools),'all pool transactions',len(events),'candidates',len(candidates),'failed',failed,flush=True)
if __name__=='__main__':main()
