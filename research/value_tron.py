import json,gzip,hashlib
from decimal import Decimal as D,getcontext
from pathlib import Path
getcontext().prec=60
R=Path(__file__).resolve().parent
U='a614f803b6fd780986a42c78ec9c7f77e6ded13c'
def main():
 ledger=json.loads((R/'tron_ledger.json').read_text());prices=json.loads((R/'tron_bitfinex_minutes.json').read_text());prices.sort();usdt={r[0]*1000:r for r in json.loads((R/'prices_raw/USDT.json').read_text())};hourly=json.loads((R/'tron_kraken_hourly.json').read_text())['result']['TRXUSD'];rows=[]
 for r in ledger['rows']:
  q=-D(r['token_net_raw'].get(U,'0'))/10**6;trx=D(r['trx_net_before_fee'])
  if not r['success'] or q<=0 or trx<=0:continue
  # Include all found USDT->TRX exchanges; main 16 large sales form an explicit subset.
  ts=r['timestamp_ms'];minute=ts//60000*60000;available=[p for p in prices if p[0]+60000<=minute];p=available[-1] if available else None
  staleness=minute-(p[0]+60000) if p else None
  usd=usdt.get(minute-60000);good=p is not None and staleness<=300000 and usd is not None
  uprice=D(str(usd[4])) if usd else None
  loss=q*uprice-trx*D(str(p[2])) if good else None
  low=q*D(str(usd[1]))-trx*D(str(p[3])) if good else None;high=q*D(str(usd[2]))-trx*D(str(p[4])) if good else None
  h=next((x for x in hourly if x[0]*1000==ts//3600000*3600000-3600000),None)
  hourly_loss=q*uprice-trx*D(h[4]) if h and usd else None
  url='https://api.trongrid.io/wallet/gettransactioninfobyid';key=hashlib.sha256((url+json.dumps({'value':r['hash']},sort_keys=True)).encode()).hexdigest();info=json.loads(gzip.decompress((R/'tron_raw'/(key+'.json.gz')).read_bytes()))
  topics={l['topics'][0] for l in info.get('log',[]) if l['topics']};swap=any(t.startswith('c42079f94') or t.startswith('d78ad95fa') for t in topics)
  rows.append({**r,'usdt_input':str(q),'observed_USDT_per_TRX':str(q/trx),'large_swap':q>=1000000,'compatible_swap_event':swap,'reference_TRX_USD':str(p[2]) if good else None,'reference_candle_ms':p[0] if good else None,'staleness_after_candle_end_ms':staleness,'reference_USDT_USD':str(uprice) if good else None,'shortfall_usd':str(loss) if loss is not None else None,'sensitivity_low_usd':str(low) if low is not None else None,'sensitivity_high_usd':str(high) if high is not None else None,'prior_hour_Kraken_shortfall_usd':str(hourly_loss) if hourly_loss is not None else None})
 main=[r for r in rows if r['large_swap']];summary={'large_swap_count':len(main),'priced_large_swaps':sum(r['shortfall_usd'] is not None for r in main),'USDT_input':str(sum(D(r['usdt_input']) for r in main)),'TRX_received':str(sum(D(r['trx_net_before_fee']) for r in main)),'fees_TRX':str(sum(D(r['fee_trx']) for r in main))}
 for k in ['shortfall_usd','sensitivity_low_usd','sensitivity_high_usd','prior_hour_Kraken_shortfall_usd']:summary[k]=str(sum(D(r[k]) for r in main if r[k] is not None))
 out={'method':'TRON net transfers and Swap-compatible logs; Bitfinex latest completed 1m spot candle with <=5m staleness, Coinbase prior-minute USDT/USD; gas excluded. Prior-hour Kraken is coarse sensitivity only, not equivalent benchmark.','source':'https://api-pub.bitfinex.com/v2/candles/trade:1m:tTRXUSD/hist?start=1793300400000&end=1793314800000&limit=1000&sort=1','summary':summary,'rows':rows};(R/'tron_valuation.json').write_text(json.dumps(out,indent=2));print(json.dumps(summary,indent=2));print('staleness',[(r['hash'][:8],r['staleness_after_candle_end_ms']//1000) for r in main]);print('swap events',sum(r['compatible_swap_event'] for r in main))
if __name__=='__main__':main()
