import json,gzip,subprocess,time,threading
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from audit_active_wallet_history import receipt_block
from identify_mev import WETH,DEPOSIT,WITHDRAWAL
R=Path(__file__).resolve().parent;C=R/'wallet_token_balance_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0;cutoff=26349764
load=lambda n:json.loads((R/n).read_text())
def balance(token,a,n):
 global last
 p=C/f'{token}_{a}_{n}.json'
 if p.exists():d=json.loads(p.read_text())
 else:
  with lock:time.sleep(max(0,.25-(time.monotonic()-last)));last=time.monotonic()
  q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':token,'data':'0x70a08231'+a[2:].zfill(64)},hex(n)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':q,'response':json.loads(z.stdout)};p.write_text(json.dumps(d))
 raw=d['response'].get('result');assert raw and len(raw)==66,str(d['response'])[:200];return int(raw,16)
def main():
 wallets=load('exploiter_1_16_and_bot_audit.json')['wallets'];byid={w['number']:w for w in wallets};starts={r['wallet']:r['start_block'] for r in load('wallet_native_balance_reconciliation.json')['rows']};known={t['address'].lower() for t in load('coingecko_eth_tokenlist.json')['tokens'] if t['chainId']==1};known|={'0xea51d7853eefb32b6ee06b1c12e6dcca88be0ffe','0x23878914efe38d27c4d67ab83ed1b93a74d4086a'}
 pairs=defaultdict(dict);wrappers=defaultdict(set);excluded=defaultdict(set)
 for s in load('wallet_history_coverage.json')['rows']:
  wallet=s['wallet'];a=byid[wallet]['address']
  for p in s['pages']:
   for x in json.loads(gzip.decompress((R/p).read_bytes()))['items']:
    n=x.get('block_number')
    if n is None or n>cutoff:continue
    src=(x.get('from') or {}).get('hash','').lower();dst=(x.get('to') or {}).get('hash','').lower()
    if s['endpoint']=='token-transfers':
     token=x['token']['address_hash'].lower()
     if x['token']['type']!='ERC-20' or token not in known:excluded[wallet].add(token);continue
     value=int(x['total']['value']);key=(x['transaction_hash'],x['log_index']);pairs[(wallet,token)][key]=(int(dst==a)-int(src==a))*value
    elif WETH in {src,dst} and a in {src,dst}:
     h=x['hash'] if s['endpoint']=='transactions' else x['transaction_hash'];wrappers[n].add(h)
 wrapnet=defaultdict(int);wrapevents=[];address_ids={w['address']:w['number'] for w in wallets}
 for n,hs in wrappers.items():
  for r in receipt_block(n):
   if r['transactionHash'] not in hs:continue
   for l in r['logs']:
    ts=l['topics']
    if l['address']==WETH and len(ts)==2 and ts[0] in [DEPOSIT,WITHDRAWAL]:
     a='0x'+ts[1][-40:]
     if a in address_ids:
      value=int(l['data'],16)*(1 if ts[0]==DEPOSIT else -1);key=(address_ids[a],WETH);wrapnet[key]+=value;pairs[key];wrapevents.append({'wallet':key[0],'hash':r['transactionHash'],'log_index':int(l['logIndex'],16),'net_raw':str(value)})
 # Explorer represents WETH Withdrawal/Deposit as synthetic transfers. Replace, do not add twice.
 synthetic_removed=[]
 for e in wrapevents:
  key=(e['wallet'],WETH);eventkey=(e['hash'],e['log_index'])
  if eventkey in pairs[key]:
   observed=pairs[key].pop(eventkey);assert observed==int(e['net_raw']);synthetic_removed.append(e)
 requests={(t,byid[w]['address'],n) for w,t in pairs for n in [starts[w],cutoff]};values={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(balance,*q):q for q in requests}
  for f in as_completed(fs):
   try:values[fs[f]]=f.result()
   except Exception as e:errors.append({'query':fs[f],'error':str(e)})
 rows=[]
 for (w,t),entries in sorted(pairs.items()):
  a=byid[w]['address'];before=values.get((t,a,starts[w]));after=values.get((t,a,cutoff));net=sum(entries.values())+wrapnet[(w,t)];residual=after-before-net if before is not None and after is not None else None
  rows.append({'wallet':w,'address':a,'token':t,'start_block':starts[w],'cutoff_block':cutoff,'start_balance_raw':str(before) if before is not None else None,'end_balance_raw':str(after) if after is not None else None,'indexed_transfer_net_raw':str(sum(entries.values())),'WETH_wrap_net_raw':str(wrapnet[(w,t)]),'residual_raw':str(residual) if residual is not None else None,'reconciled':residual==0,'transfer_event_count':len(entries)})
 out={'scope':'Known metadata ERC20 tokens plus Aave claim/debt tokens in indexed 16-wallet history. Transfer net plus separately reconstructed WETH Deposit/Withdrawal compared to historical balanceOf. Residual may reflect interest/rebase/nonstandard token rules, not necessarily missing transfers. Unknown/NFT contracts enumerated separately, not priced.','rows':rows,'errors':errors,'WETH_wrap_events':wrapevents,'indexed_WETH_synthetic_events_replaced':synthetic_removed,'excluded_contracts':{str(k):sorted(v) for k,v in excluded.items()},'summary':{'pairs':len(rows),'reconciled':sum(r['reconciled'] for r in rows),'residual_nonzero':sum(r['residual_raw'] not in [None,'0'] for r in rows),'missing_balance':sum(r['residual_raw'] is None for r in rows)}};(R/'wallet_token_balance_reconciliation.json').write_text(json.dumps(out,indent=2));print(out['summary']);print([r for r in rows if not r['reconciled']]);print(errors)
if __name__=='__main__':main()
