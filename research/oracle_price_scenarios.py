import json,subprocess,time,threading,hashlib
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from decimal import Decimal as D,getcontext
from Crypto.Hash import keccak
getcontext().prec=60
R=Path(__file__).resolve().parent;C=R/'oracle_price_raw';C.mkdir(exist_ok=True);ORACLE='0x54586be62e3c3580375ae3723c145253060ca0c2';PROVIDER='0x2f39d218133afab8f2b819b1066c7e434ad94e9e';lock=threading.Lock();last=0
sel=lambda s:'0x'+keccak.new(digest_bits=256,data=s.encode()).hexdigest()[:8]
load=lambda n:json.loads((R/n).read_text())
def rpc(tag,to,data,n):
 global last
 p=C/(tag+'.json')
 if p.exists():return json.loads(p.read_text())['response']['result']
 with lock:time.sleep(max(0,.2-(time.monotonic()-last)));last=time.monotonic()
 q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},hex(n)]};z=subprocess.run(['curl','--silent','--show-error','--max-time','35','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True);d={'request':q,'response':json.loads(z.stdout)};p.write_text(json.dumps(d));return d['response']['result']
def fetch(task):
 n,assets=task;assets=sorted(assets);oracle=rpc(str(n)+'_provider',PROVIDER,sel('getPriceOracle()'),n);assert '0x'+oracle[-40:]==ORACLE
 try:
  raw=rpc(str(n)+'_prices_'+hashlib.sha256(','.join(assets).encode()).hexdigest()[:16],ORACLE,sel('getAssetsPrices(address[])')+hex(32)[2:].zfill(64)+hex(len(assets))[2:].zfill(64)+''.join(a[2:].zfill(64) for a in assets),n);w=[int(raw[i:i+64],16) for i in range(2,len(raw),64)];assert w[0]==32 and w[1]==len(assets) and len(w)==len(assets)+2
  return n,{a:str(v) for a,v in zip(assets,w[2:])},[]
 except Exception:
  values={};failures=[]
  for a in assets:
   try:values[a]=str(int(rpc(str(n)+'_asset_'+a,ORACLE,sel('getAssetPrice(address)')+a[2:].zfill(64),n),16))
   except Exception as e:failures.append({'block':n,'asset':a,'error':str(e)})
  return n,values,failures
def main():
 for n in [26300639,26303950]:assert int(rpc(str(n)+'_unit',ORACLE,sel('BASE_CURRENCY_UNIT()'),n),16)==10**8
 token={x['address'].lower():x for x in load('coingecko_eth_tokenlist.json')['tokens'] if x['chainId']==1};collections={'target':load('unified_target_valuation.json')['rows'],'paired_strategy':[x for x in load('inventory_valued_ledger.json')['rows'] if x['kind']=='paired_strategy'],'filler':load('order_filler_accounting.json')['rows']};tasks=defaultdict(set)
 for kind,rows in collections.items():
  for r in rows:
   for a in r['five_minute']['missing_assets']:
    if a['address'] in token:tasks[r['block']-1].add(a['address'])
 prices={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(fetch,t):t[0] for t in tasks.items()}
  for i,f in enumerate(as_completed(fs),1):
   try:n,d,es=f.result();prices[n]=d;errors+=es
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
   if i%50==0:print('oracle blocks',i,len(fs),'errors',len(errors),flush=True)
 out=[]
 for kind,rows in collections.items():
  for r in rows:
   base=r['five_minute'];assets=[];missing=[];used=[]
   for a in base['assets']:
    a=dict(a)
    if a['USD'] is None:
     pr=prices.get(r['block']-1,{}).get(a['address']);t=token.get(a['address'])
     if pr and int(pr)>0 and t:
      a['USD']=str(D(a['raw'])/(D(10)**t['decimals'])*D(pr)/10**8);a['oracle_price_USD']=str(D(pr)/10**8);a['oracle_block']=r['block']-1;used.append(a['address'])
     else:missing.append(a['address'])
    assets.append(a)
   total=str(D(base['ETH_cashflow_USD'])+sum((D(a['USD']) for a in assets),D(0))) if base['ETH_cashflow_USD'] is not None and not missing else None
   eligible=r.get('eligible_exchange_candidate',True) if kind=='target' else not r.get('position_or_debt_events',False) if kind=='paired_strategy' else not r.get('compound_market_interaction',False) and not r.get('recognized_debt_events')
   out.append({'kind':kind,'id':r.get('hash',r.get('id')),'block':r['block'],'eligible':eligible,'USD':total,'oracle_assets_used':used,'missing_assets':missing,'assets':assets})
 summary={}
 for k in collections:
  rs=[r for r in out if r['kind']==k and r['eligible'] and r['USD'] is not None];summary[k]={'count':len(rs),'sum_marked_change_USD':str(sum((D(r['USD']) for r in rs),D(0))),'oracle_assisted_rows':sum(bool(r['oracle_assets_used']) for r in rs)}
 (R/'oracle_assisted_scenarios.json').write_text(json.dumps({'method':'Separate mixed-benchmark sensitivity: retain <=5-minute completed CEX candles; fill missing known assets using Aave oracle at previous block, provider address verified each requested block, BASE_CURRENCY_UNIT=1e8 checked endpoints. Aave valuation may use caps/redemption ratios/stale feeds and is not an executable market quote; feed update timestamps not audited. Do not replace primary market-only results or label exact profit.','summary':summary,'errors':errors,'rows':out},indent=2));print(summary,flush=True)
if __name__=='__main__':main()
