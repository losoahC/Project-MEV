"""Expand independently fetched evidence using a public tracker as address leads.
Tracker roles are unverified leads, not proof of ownership. Native ETH omitted
unless explicitly available; never infer proceeds from Transfer logs alone.
"""
import json, subprocess, time, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

R=Path(__file__).resolve().parent
C=R/'expanded_raw'; C.mkdir(exist_ok=True)
URL='https://ethereum-rpc.publicnode.com'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def rpc(method,params):
    key=hashlib.sha256(json.dumps([method,params],sort_keys=True).encode()).hexdigest()
    p=C/(method+'_'+key+'.json')
    if p.exists():return json.loads(p.read_text())['result']
    payload=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params})
    for attempt in range(3):
        z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','45','-H','Content-Type: application/json','--data',payload,URL],capture_output=True,text=True)
        try:
            d=json.loads(z.stdout)
            if 'error' in d or d.get('result') is None:raise ValueError(str(d)[:500])
            p.write_text(json.dumps(d));return d['result']
        except (ValueError,KeyError) as e:
            if attempt==2:raise RuntimeError(f'{method}: {z.stderr[:200]} {z.stdout[:300]}') from e
            time.sleep(1+attempt)

def main():
    state=json.loads((R/'tracker_state.json').read_text())
    leads=[w for w in state['wallets'] if w['chain']=='ethereum' and w['role'] in state['attackerSideRoles']]
    addrs=sorted({w['address'].lower() for w in leads}); aset=set(addrs)
    (R/'address_leads.json').write_text(json.dumps({'source':'https://binance.lamps.works/','snapshot':state['generatedAt'],'verification':'third-party lead only','wallets':leads},indent=2))
    topics=['0x'+a[2:].zfill(64) for a in addrs]
    lo,hi=26300740,state['blocks']['ethereum']
    jobs=[]
    for start in range(lo,hi+1,2000):
        for direction in ['out','in']:
            filt={'fromBlock':hex(start),'toBlock':hex(min(hi,start+1999)),'topics':[TRANSFER,topics] if direction=='out' else [TRANSFER,None,topics]}
            jobs.append((direction,start,filt))
    all_logs={};errors=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(rpc,'eth_getLogs',[f]):(d,n) for d,n,f in jobs}
        for i,f in enumerate(as_completed(futures),1):
            try:
                logs=f.result()
                for l in logs:all_logs[(l['transactionHash'],l['logIndex'])]=l
                print('logs',i,'/',len(jobs),'rows',len(logs),flush=True)
            except Exception as e:errors.append({'query':futures[f],'error':str(e)});print('ERROR',str(e),flush=True)
    logs=sorted(all_logs.values(),key=lambda x:(int(x['blockNumber'],16),int(x['transactionIndex'],16),int(x['logIndex'],16)))
    (R/'expanded_wallet_transfers.json').write_text(json.dumps({'from_block':lo,'to_block':hi,'address_count':len(addrs),'errors':errors,'logs':logs}))
    hashes=sorted({l['transactionHash'] for l in logs})
    print('Wallets',len(addrs),'logs',len(logs),'transactions',len(hashes),flush=True)
    receipts={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(rpc,'eth_getTransactionReceipt',[h]):h for h in hashes}
        for i,f in enumerate(as_completed(futures),1):
            try:receipts[futures[f]]=f.result()
            except Exception as e:errors.append({'hash':futures[f],'error':str(e)})
            if i%25==0:print('receipts',i,'/',len(hashes),flush=True)
    rows=[]
    for h,rec in receipts.items():
        net=defaultdict(int); wallet_net=defaultdict(lambda:defaultdict(int))
        for l in rec['logs']:
            t=l['topics']
            if len(t)!=3 or t[0]!=TRANSFER:continue
            fr='0x'+t[1][-40:];to='0x'+t[2][-40:];token=l['address'];amount=int(l['data'],16)
            if fr in aset:net[token]-=amount;wallet_net[fr][token]-=amount
            if to in aset:net[token]+=amount;wallet_net[to][token]+=amount
        out={t:str(v) for t,v in net.items() if v<0};inc={t:str(v) for t,v in net.items() if v>0}
        rows.append({'hash':h,'block':int(rec['blockNumber'],16),'index':int(rec['transactionIndex'],16),'from':rec['from'],'to':rec['to'],'outgoing_tokens_raw':out,'incoming_tokens_raw':inc,'wallet_net_raw':{a:{t:str(v) for t,v in ns.items() if v} for a,ns in wallet_net.items()},'classification':'external_token_outflow_requires_decode' if out else 'inflow_or_internal','log_count':len(rec['logs'])})
    rows.sort(key=lambda x:(x['block'],x['index']))
    (R/'expanded_transaction_ledger.json').write_text(json.dumps({'scope':'Ethereum third-party address leads; token log discovery only; native-only transfers and undiscovered addresses excluded','errors':errors,'rows':rows},indent=2))
    print('DONE rows',len(rows),'external outflow txs',sum(bool(x['outgoing_tokens_raw']) for x in rows),'errors',len(errors),flush=True)
if __name__=='__main__':main()
