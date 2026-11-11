import json,subprocess
from pathlib import Path
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from decimal import Decimal as D
R=Path(__file__).resolve().parent;C=R/'extra_price_raw';ADDRESS='0x419d0d8bdd9af5e606ae2232ed285aff190e711b'
def main():
 identity=json.loads((C/'hitbtc_FUN_identity.json').read_text());assert any(n.get('contract_address','').lower()==ADDRESS for n in identity['networks']);bars={};sources=[]
 for day in ['2026-10-29','2026-10-30','2026-10-31']:
  for hour in [0,12]:
   t=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)+timedelta(hours=hour);q=urlencode({'period':'M1','from':t.isoformat().replace('+00:00','Z'),'till':(t+timedelta(hours=12)).isoformat().replace('+00:00','Z'),'limit':1000,'sort':'ASC'});url='https://api.hitbtc.com/api/3/public/candles/FUNUSDT?'+q;p=C/f'hitbtc_FUN_{day}_{hour}.json'
   if p.exists():data=json.loads(p.read_text())
   else:
    z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30',url],capture_output=True,check=True);data=json.loads(z.stdout);p.write_bytes(z.stdout)
   assert isinstance(data,list),data;added=0
   for x in data:
    if D(x['volume'])<=0:continue
    ts=int(datetime.fromisoformat(x['timestamp'].replace('Z','+00:00')).timestamp());bars[str(ts)]={'close':x['close'],'low':x['min'],'high':x['max'],'quote':'USDT','source':'HitBTC FUNUSDT; Ethereum contract identity verified'};added+=1
   sources.append({'url':url,'bars':len(data),'nonzero_volume_bars':added});print(day,hour,len(data),added,flush=True)
 out={'symbol':'FUN','contract':ADDRESS,'identity_source':'https://api.hitbtc.com/api/3/public/currency/FUN','excluded_wrong_symbol_sources':['KuCoin FUN is Sport.fun on Base','Gate FUN is Sport.fun on Base'],'bars':bars,'sources':sources};(R/'verified_fun_market_prices.json').write_text(json.dumps(out,indent=2));v=json.loads((R/'verified_price_contracts.json').read_text());v[ADDRESS]={'symbol':'FUN','source':out['identity_source'],'name':identity['full_name']};(R/'verified_price_contracts.json').write_text(json.dumps(v,indent=2));print('FUN prices',len(bars),flush=True)
if __name__=='__main__':main()
