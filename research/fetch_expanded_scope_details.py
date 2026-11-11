import json,gzip,subprocess,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict,Counter
from rawtrace_native import parse
from screen_expanded import net_for,swaps
R=Path(__file__).resolve().parent;C=R/'scope_detail_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0
PCAKE='0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83'
def call(n,kind):
 global last
 p=C/f'{n}_{kind}.json.gz'
 if p.exists():return json.loads(gzip.decompress(p.read_bytes()))['result']
 method,params={'receipts':('eth_getBlockReceipts',[hex(n)]),'block':('eth_getBlockByNumber',[hex(n),False]),'trace':('trace_block',[hex(n)])}[kind];req={'jsonrpc':'2.0','id':1,'method':method,'params':params}
 for attempt in range(3):
  with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
  z=subprocess.run(['curl','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data',json.dumps(req),'https://eth.drpc.org'],capture_output=True)
  try:
   d=json.loads(z.stdout);assert d.get('result') is not None,str(d)[:100];p.write_bytes(gzip.compress(z.stdout));return d['result']
  except Exception:
   if attempt==2:raise
   time.sleep(1)
def one(n,items):
 b=call(n,'block');rs=call(n,'receipts');tr=call(n,'trace');assert {r['transactionHash'] for r in rs}==set(b['transactions']);assert {t['transactionHash'] for t in tr if t.get('transactionHash') and t['traceAddress']==[]}==set(b['transactions']);assert all(r['blockHash']==b['hash'] for r in rs);rs={r['transactionHash']:r for r in rs};ts=defaultdict(list)
 for t in tr:
  if t.get('transactionHash'):ts[t['transactionHash']].append(t)
 leads={x['address'].lower() for x in json.loads((R/'address_leads.json').read_text())['wallets']};out=[]
 for x in items:
  r=rs[x['hash']];native=parse(x['hash'],ts[x['hash']]);ss=swaps(r);pancake=[{'pool':l['address'],'topic':PCAKE} for l in r['logs'] if l['topics'] and l['topics'][0]==PCAKE];net=net_for(r,leads)
  out.append({**x,'timestamp':int(b['timestamp'],16),'status':int(r['status'],16),'from':r['from'],'to':r['to'],'pool_events':ss,'pancake_events':pancake,'net_token_raw':net,'native':native,'lead_native_wei':str(sum(int(v) for a,v in native['native_net_wei'].items() if a in leads)),'gas_wei':str(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16)),'category':'pool_swap_compatible' if ss or pancake else 'non_pool_outflow_requires_classification'})
 return out
def main():
 data=json.loads((R/'expanded_scope_transactions.json').read_text());byblock=defaultdict(list)
 for r in data['rows']:
  if r['verified_token_net_out']:byblock[r['block']].append(r)
 rows=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(one,n,items):n for n,items in byblock.items()}
  for i,f in enumerate(as_completed(fs),1):
   try:rows+=f.result()
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%25==0:print('scope details blocks',i,len(fs),'rows',len(rows),'errors',len(errors),flush=True)
 (R/'expanded_scope_details.json').write_text(json.dumps({'rows':sorted(rows,key=lambda r:(r['block'],r['hash'])),'errors':errors},indent=2));print('DONE',len(rows),dict(Counter(r['category'] for r in rows)),errors,flush=True)
if __name__=='__main__':main()
