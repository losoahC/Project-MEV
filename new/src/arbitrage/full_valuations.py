"""Address-by-address marks for full-window targets and Bitquery's named seller.
Never pool funded addresses or allocate maker receipts as unqualified profit.
"""
import json
from collections import Counter
from decimal import Decimal,getcontext
from src.arbitrage.value_candidates import book_from_archive,mark,ROOT,E
from src.reconciliation.pricebook import PriceBook
from src.arbitrage.reconstruct import Reconstruction
from src.decoding.events import WETH,USDT,USDC
getcontext().prec=90

class FullWindowBook(PriceBook):
    def secondary_quote(self,address,timestamp):
        if not hasattr(self,'_completion_quotes'):
            path=ROOT/'data/processed/completion_secondary_prices.json'
            self._completion_quotes={(r['address'],r['requested_timestamp']):r for r in json.loads(path.read_text())['rows'] if r['accepted']} if path.exists() else {}
        r=self._completion_quotes.get((address,int(timestamp)//60*60-60))
        if r and r['quote']['timestamp']<int(timestamp)//60*60:return r
        return None

    def price(self,symbol,timestamp,stale=0,lookback=1,venue='Coinbase',field='close'):
        result=super().price(symbol,timestamp,stale,lookback,venue,field)
        if result is None and symbol=='USDT' and field=='close':
            r=self.secondary_quote(USDT,timestamp)
            if r:return Decimal(str(r['quote']['price'])),{'venue':'DefiLlama exact Ethereum USDT contract; explicit secondary market mark','symbol':'USDT','quote':'USD','bar_start':r['quote']['timestamp'],'sources':[r['evidence']],'confidence':r['quote']['confidence'],'prior_completed_minute_anchor':r['requested_timestamp']}
        return result

    def value(self,address,raw,timestamp,**kwargs):
        v=super().value(address,raw,timestamp,**kwargs)
        if address==USDC and v['USD'] is None:
            p=self.price('USDC',timestamp,venue='Binance')
            if p:
                m=self.registry[USDC];q=Decimal(raw)/Decimal(10)**m['decimals']
                return {'address':address,'raw':str(raw),**m,'quantity':str(q),'reference_USD':str(p[0]),'USD':str(q*p[0]),'price_evidence':p[1],'confidence':'USDCUSDT spot converted with actual USDTUSD; explicit secondary venue fallback'}
        if v['USD'] is None:
            if not hasattr(self,'_completion_binance'):
                path=ROOT/'data/processed/completion_binance_prices.json'
                self._completion_binance={(r['address'],r['timestamp']//60):r for r in json.loads(path.read_text())['rows'] if r['accepted']} if path.exists() else {}
            r=self._completion_binance.get((address,int(timestamp)//60))
            if r:
                meta=r['metadata'];quantity=Decimal(raw)/Decimal(10)**meta['decimals'];price=Decimal(r['USD_price'])
                return {'address':address,'raw':str(raw),**meta,'quantity':str(quantity),'reference_USD':str(price),'USD':str(quantity*price),'price_evidence':r['evidence'],'confidence':'Contract-matched independent Binance spot secondary venue; actual USDTUSD conversion','primary_missing_reason':v.get('reason')}
            r=self.secondary_quote(address,timestamp)
            if r:
                quote=r['quote'];dec=r['token_metadata']['decimals'];quantity=Decimal(raw)/Decimal(10)**dec;price=Decimal(str(quote['price']))
                return {'address':address,'raw':str(raw),'symbol':quote['symbol'],'decimals':dec,'quantity':str(quantity),'reference_USD':str(price),'USD':str(quantity*price),'identity_basis':'Historical price response keyed by exact Ethereum contract address','decimal_basis':r['token_metadata']['evidence'],'price_evidence':{'venue':'DefiLlama secondary exact-contract price','quote':'USD','timestamp':quote['timestamp'],'requested_prior_minute_anchor':r['requested_timestamp'],'sources':[r['evidence']],'confidence':quote['confidence']},'confidence':'Explicit secondary historical mark; primary CEX unavailable; not matched by ticker','primary_missing_reason':v.get('reason')}
        return v

def run():
    p=ROOT/'data/processed/mev_full_window';book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',True);book.binance_spot('USDC',('2026-10-29','2026-10-30'));targets=json.loads((p/'targets.json').read_text());focus=json.loads((p/'focus_address_ledger.json').read_text());rows=[]
    for t in targets:
        for w in t['wallets']:
            raw=dict(w['token_net_raw']);raw['native:eth']=w['native_net_wei'] or '0';v=mark(book,raw,t['timestamp']);complete=not v['missing_assets'] and w['native_net_wei'] is not None
            rows.append({'tx_hash':t['tx_hash'],'block':t['block'],'address':w['address'],'source_category':w['source_category'],'timestamp':t['timestamp'],'valuation':v,'valuation_complete':complete,'signed_reference_shortfall_USD':str(-Decimal(v['marked_net_USD'])) if complete else None,'gas_included':False,'MEV_incremental_loss_USD':None,'order_events':t['order_events'],'evidence':t['evidence']})
    (p/'target_reference_valuations.json').write_text(json.dumps(rows,indent=2))
    seller=[]
    for f in focus:
        raw=dict(f['token_net_raw']);raw['native:eth']=f['native_net_wei'] or '0';v=mark(book,raw,f['timestamp']);eth=book.price('ETH',f['timestamp']);gasusd=Decimal(f['gas_wei'])/E*eth[0] if eth else None
        ethraw=int(raw.get(WETH,'0'))+int(raw['native:eth']);stable=sum(int(raw.get(t,'0')) for t in [USDT,USDC]);others={t:v for t,v in raw.items() if int(v) and t not in [WETH,USDT,USDC,'native:eth']}
        simple_sale=bool(f['pool_events'] and ethraw<0 and stable>0 and not others)
        seller.append({**f,'valuation':v,'gas_USD':str(gasusd) if gasusd is not None else None,'marked_net_after_gas_USD':str(Decimal(v['marked_net_USD'])-gasusd) if gasusd is not None and v['marked_net_USD'] is not None and f['native_net_wei'] is not None else None,'simple_ETH_to_stable_sale':simple_sale,'note':'Address-only boundary. Reference-price gain is not historical cost-basis profit; gas paid by other senders and offchain hedges excluded.'})
    (p/'focus_address_valuations.json').write_text(json.dumps(seller,indent=2))
    sales=[x for x in seller if x['simple_ETH_to_stable_sale']];priced=[x for x in sales if x['marked_net_after_gas_USD'] is not None]
    ordertx={t['tx_hash'] for t in targets if t['order_events']};orderrows=[x for x in rows if x['tx_hash'] in ordertx]
    summary={'target_wallet_rows':len(rows),'complete_target_wallet_rows':sum(r['valuation_complete'] for r in rows),'focus_address_ledger_rows':len(seller),'focus_simple_ETH_sales':len(sales),'focus_priced_ETH_sales':len(priced),'focus_ETH_sales_reference_gain_after_own_gas_USD':str(sum((Decimal(x['marked_net_after_gas_USD']) for x in priced),Decimal(0))) if priced else None,'focus_all_strategy_profit_established':False,'order_transactions':len(ordertx),'order_wallet_rows':len(orderrows),'order_USDT_net_out':str(-sum((Decimal(a['quantity']) for r in orderrows for a in r['valuation']['assets'] if a.get('address')==USDT and a.get('quantity') is not None),Decimal(0))),'order_ETH_WETH_net_in':str(sum((Decimal(a['quantity']) for r in orderrows for a in r['valuation']['assets'] if a.get('address') in [WETH,'native:eth'] and a.get('quantity') is not None),Decimal(0)))}
    (p/'valuation_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
