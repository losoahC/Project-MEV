"""Bound the old-DAR fair price and the resulting shortfall of the one unpriced ETH purchase.

Inputs: dar_market_snapshot_geckoterminal.json (daily USD candles of every old-DAR pool listed by
GeckoTerminal, fetched 2026-11-13), DAR_price_identification_bounds.json (trade facts).
Rule: use the last daily close strictly before the trade day (2026-10-30) of each pool that still
traded within 30 days before the trade; never use the new D token price or post-trade candles.
Output: DAR_fair_price_range.json
"""
import json, time
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec = 40
R = Path(__file__).resolve().parent
SOLD_POOL = '0x4aadb3498f407e4d558589514bb9a4b341475e31'


def main():
    snap = json.loads((R / 'dar_market_snapshot_geckoterminal.json').read_text())
    trade = json.loads((R / 'DAR_price_identification_bounds.json').read_text())
    units, received = D(trade['DAR_units']), D(trade['received_reference_value_USD'])
    ts = snap['trade_block_timestamp']; day0 = ts - ts % 86400
    venues = []
    for pool, p in snap['pools'].items():
        candles = sorted(c for c in (p['ohlcv_day_usd'] or []) if c[0] < day0)
        if not candles:
            continue
        last = candles[-1]
        age = (day0 - last[0]) // 86400
        venues.append({'pool': pool, 'name': p['name'], 'last_pre_trade_day': time.strftime('%Y-%m-%d', time.gmtime(last[0])),
                       'days_before_trade_day': age, 'close_USD': str(last[4]), 'that_day_volume_USD': str(last[5]),
                       'is_pool_hacker_sold_into': pool == SOLD_POOL, 'live_within_30_days': age <= 30})
    live = [v for v in venues if v['live_within_30_days']]
    indep = [v for v in live if not v['is_pool_hacker_sold_into']]
    by_vol = max(indep, key=lambda v: D(v['that_day_volume_USD']))

    def shortfall(p):
        return str((units * D(p) - received).quantize(D('0.01')))

    prices = sorted(D(v['close_USD']) for v in live)
    out = {
        'trade': trade['hash'], 'DAR_units': str(units), 'received_reference_value_USD': str(received),
        'venues': venues,
        'rule': 'Last daily close before the trade day; pool must have traded within 30 days; the new D token and post-trade candles are excluded.',
        'central_estimate': {'basis': 'most active independent live venue (excludes the pool the hacker sold into)', 'pool': by_vol['pool'],
                             'price_USD': by_vol['close_USD'], 'shortfall_USD': shortfall(by_vol['close_USD'])},
        'range': {'low': {'price_USD': str(prices[0]), 'shortfall_USD': shortfall(prices[0])},
                  'high': {'price_USD': str(prices[-1]), 'shortfall_USD': shortfall(prices[-1])}},
        'executable_liquidity_note': 'Every live venue held well under USD 1,000 of quote assets, so the whole position could not be sold near any quoted price. The price range values the tokens at the market quote; executable value was close to what the hacker received.',
        'share_of_strict_wallet_shortfall': None,
    }
    strict = json.loads((R / 'wallet_strict_purchase_summary.json').read_text(encoding='utf8'))
    total = sum(D(r['overpayment_USD_excluding_gas']) for r in strict['rows'])
    if total:
        out['share_of_strict_wallet_shortfall'] = {'strict_total_USD': str(total),
                                                   'high_case_share_percent': str((D(out['range']['high']['shortfall_USD']) / total * 100).quantize(D('0.0001')))}
    (R / 'DAR_fair_price_range.json').write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ('central_estimate', 'range', 'share_of_strict_wallet_shortfall')}, indent=1))
    for v in venues: print(v['name'], v['last_pre_trade_day'], v['close_USD'], v['live_within_30_days'])


if __name__ == '__main__':
    main()
