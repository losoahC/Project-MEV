import json,subprocess
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from decimal import Decimal as D
R=Path(__file__).resolve().parent;C=R/'extra_price_raw';ADDRESS='0x419d0d8bdd9af5e606ae2232ed285aff190e711b'
def main():
 catalog=json.loads((R/'gate_currency_identity_catalog.json').read_text());match=next(c for c in catalog if c['currency']=='FUNTOKEN');assert any(n.get('addr','').lower()==ADDRESS and n['name']=='ETH' for n in match['chains']);bars={};sources=[]
 for day in ['2026-10-29','2026-10-30','2026-10-31']:
  for hour in ([18] if day=='2026-10-29' else [0,12]):
   t=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)+timedelta(hours=hour);q=urlencode({'currency_pair':'FUNTOKEN_USDT','interval':'1m','from':int(t.timestamp()),'to':int((t+timedelta(hours=min(12,24-hour))).timestamp())});url='https://api.gateio.ws/api/v4/spot/candlesticks?'+q;p=C/f'gate_FUNTOKEN_{day}_{hour}.json'
   if p.exists():data=json.loads(p.read_text())
   else:
    z=subprocess.run(['curl','--silent','--show-error','--max-time','30',url],capture_output=True)
    try:data=json.loads(z.stdout);assert isinstance(data,list)
    except Exception:sources.append({'url':url,'error':z.stdout.decode()[:200]+z.stderr.decode()[:100]});print('unavailable',day,hour,flush=True);continue
    p.write_bytes(z.stdout)
   assert isinstance(data,list),data;added=0
   for x in data:
    if D(x[1])<=0 or (len(x)>7 and x[7]!='true'):continue
    bars[str(int(x[0]))]={'close':x[2],'low':x[4],'high':x[3],'quote':'USDT','source':'Gate FUNTOKEN_USDT; Ethereum contract identity verified'};added+=1
   sources.append({'url':url,'bars':len(data),'nonzero_volume_bars':added});print(day,hour,len(data),added,flush=True)
 out={'symbol':'FUN','exchange_symbol':'FUNTOKEN','contract':ADDRESS,'identity_source':'https://api.gateio.ws/api/v4/spot/currencies','excluded_wrong_symbol_sources':['KuCoin FUN is Sport.fun on Base','Gate FUN is Sport.fun on Base'],'bars':bars,'sources':sources};(R/'verified_fun_market_prices.json').write_text(json.dumps(out,indent=2));v=json.loads((R/'verified_price_contracts.json').read_text());v[ADDRESS]={'symbol':'FUN','exchange_symbol':'FUNTOKEN','source':out['identity_source'],'name':match['name']}
 for c in catalog:
  if c['currency'] in ['SOPH','HYPER']:
   for n in c['chains']:
    if n['name']=='ETH' and n.get('addr','').startswith('0x'):v[n['addr'].lower()]={'symbol':c['currency'],'source':out['identity_source'],'name':c['name']}
 (R/'verified_price_contracts.json').write_text(json.dumps(v,indent=2));print('FUN prices',len(bars),flush=True)
if __name__=='__main__':main()
