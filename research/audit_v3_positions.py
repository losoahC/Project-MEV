import json,gzip,subprocess,threading,time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from Crypto.Hash import keccak
R=Path(__file__).resolve().parent;C=R/'lp_state_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
def call(task):
 global last
 tag,to,data,block=task;p=C/(tag+'.json')
 if p.exists():d=json.loads(p.read_text())
 else:
  with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
  req={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},hex(block)]}
  z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35','-H','Content-Type: application/json','--data',json.dumps(req),'https://eth.drpc.org'],capture_output=True)
  d={'request':req,'response':json.loads(z.stdout)};p.write_text(json.dumps(d))
 return tag,d
def main():
 sig=json.loads((R/'classification_event_signatures.json').read_text());types={sig[k]:k.split('(')[0] for k in ['Mint(address,address,int24,int24,uint128,uint256,uint256)','Burn(address,int24,int24,uint128,uint256,uint256)','Collect(address,address,int24,int24,uint128,uint128)']}
 positions={}
 for r in json.loads((R/'candidate_classification.json').read_text())['rows']:
  for e in r['liquidity_events']:
   if e['topics'][0] in types:
    owner='0x'+e['topics'][1][-40:];lo=e['topics'][2][-6:];hi=e['topics'][3][-6:];key=e['emitter']+':'+owner+':'+lo+':'+hi
    positions[key]={'pool':e['emitter'],'owner':owner,'tick_lower_hex':lo,'tick_upper_hex':hi,'position_key':'0x'+keccak.new(digest_bits=256,data=bytes.fromhex(owner[2:]+lo+hi)).hexdigest(),'events':[]}
 for n in range(26300640,26303951):
  folder='window_raw' if n<=26301940 else 'extension_raw'
  for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes())):
   for l in r['logs']:
    t=l['topics']
    if len(t)!=4 or t[0] not in types:continue
    key=l['address']+':0x'+t[1][-40:]+':'+t[2][-6:]+':'+t[3][-6:]
    if key not in positions:continue
    words=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];typ=types[t[0]]
    if typ=='Mint':liquidity,a0,a1=words[1:4]
    elif typ=='Burn':liquidity,a0,a1=words[:3]
    else:liquidity=0;a0,a1=words[1:3]
    positions[key]['events'].append({'hash':r['transactionHash'],'block':n,'index':int(r['transactionIndex'],16),'log_index':int(l['logIndex'],16),'type':typ,'liquidity':str(liquidity),'amount0':str(a0),'amount1':str(a1)})
 tasks=[];pools={p['pool'] for p in positions.values()}
 for pool in pools:
  for field,sel in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155')]:tasks.append((pool+'_'+field,pool,sel,26300639))
 for i,(key,p) in enumerate(sorted(positions.items())):
  p['id']=i
  for tag,n in [('start',26300639),('end',26303950)]:tasks.append((f'position_{i}_{tag}',p['pool'],'0x514ea4bf'+p['position_key'][2:],n))
 replies={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(call,t):t[0] for t in tasks}
  for i,f in enumerate(as_completed(fs),1):
   try:k,d=f.result();replies[k]=d['response']
   except Exception as e:errors.append({'tag':fs[f],'error':str(e)})
   if i%100==0:print('LP state calls',i,len(fs),flush=True)
 rows=[]
 for key,p in positions.items():
  try:
   states={}
   for tag in ['start','end']:
    raw=replies[f'position_{p["id"]}_{tag}']['result']
    if raw=='0x' and tag=='start':
     proof=json.loads((C/(p['pool']+'_code_start.json')).read_text());assert proof['request']['params']==[p['pool'],hex(26300639)] and proof['response']['result']=='0x'
     raw='0x'+'0'*320;p['pool_absent_at_window_start']=True
    assert len(raw)==322;w=[int(raw[i:i+64],16) for i in range(2,len(raw),64)];states[tag]={'liquidity':str(w[0]),'owed0':str(w[3]),'owed1':str(w[4])}
   p['states']=states
   for field in ['token0','token1','factory']:
    raw=replies[p['pool']+'_'+field]['result']
    if raw=='0x' and p.get('pool_absent_at_window_start'):raw=json.loads((C/(p['pool']+'_'+field+'_end.json')).read_text())['response']['result']
    assert len(raw)==66;p[field]='0x'+raw[-40:]
   sums={typ:[sum(int(e[f'amount{j}']) for e in p['events'] if e['type']==typ) for j in [0,1]] for typ in ['Mint','Burn','Collect']}
   fee=[sums['Collect'][j]+int(states['end'][f'owed{j}'])-int(states['start'][f'owed{j}'])-sums['Burn'][j] for j in [0,1]]
   ldelta=sum(int(e['liquidity'])*(1 if e['type']=='Mint' else -1 if e['type']=='Burn' else 0) for e in p['events']);assert int(states['start']['liquidity'])+ldelta==int(states['end']['liquidity']);assert all(x>=0 for x in fee)
   p.update(principal_added_raw=list(map(str,sums['Mint'])),principal_released_raw=list(map(str,sums['Burn'])),collected_raw=list(map(str,sums['Collect'])),fees_credited_in_window_raw=list(map(str,fee)),liquidity_conservation=True,fully_opened_and_closed_in_window=int(states['start']['liquidity'])==int(states['end']['liquidity'])==0 and all(int(states[tag][f'owed{j}'])==0 for tag in ['start','end'] for j in [0,1]),status='reconciled')
  except Exception as e:p.update(status='unresolved',error=str(e))
  rows.append(p)
 (R/'v3_position_accounting.json').write_text(json.dumps({'method':'Per-owner/tick-range position accounting: collected + ending owed - beginning owed - burn principal = fees credited during window. Fees may have accrued before window; uncrystallized fee growth excluded. Not event-causal profit. Compatible V3 interfaces; factory recorded separately.','rows':rows,'request_errors':errors},indent=2));print('DONE',len(rows),'reconciled',sum(p['status']=='reconciled' for p in rows),'fully closed',sum(p.get('fully_opened_and_closed_in_window',False) for p in rows),flush=True)
if __name__=='__main__':main()
