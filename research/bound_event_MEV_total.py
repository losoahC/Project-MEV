"""Assumption-labelled lower / upper bounds for MEV extracted around the hacker's swaps.

Estimand: value captured by third-party searchers (and the builders they paid) because of the
hacker's swaps, inside the 3,311-block window and the 55-address scope. Every component is
hash-disjoint from the others; assumptions are written next to each number.

Inputs (all existing project outputs): all_scope_sandwich_groups.json, bracket_EVM_validation.json,
expanded_EVM_attribution.json, nonce_preserving_EVM_sensitivity.json, standalone_ring_raw_replay.json,
all_scope_strategy_valuation.json, full_fee_distribution.json, wallet_strict_purchase_summary.json,
extended_cycle_eight_block_EVM.json (optional).
Output: event_MEV_total_bounds.json
"""
import json
from decimal import Decimal as D
from pathlib import Path

R = Path(__file__).resolve().parent
ETH_USD = D('2243.93')  # Coinbase 1-minute ETH reference already used in the project; stated, not re-estimated
WEI = D(10) ** 18
L = lambda f: json.loads((R / f).read_text(encoding='utf8'))
clip = lambda x, lo, hi: max(lo, min(hi, x))


def main():
    groups = L('all_scope_sandwich_groups.json')['groups']
    bracket = L('bracket_EVM_validation.json')
    attrib = [r for r in L('expanded_EVM_attribution.json')['rows'] if r['status'].startswith('verified')]
    nonce = [r for r in L('nonce_preserving_EVM_sensitivity.json')['rows'] if r['status'].startswith('verified')]
    rings = {r['hash']: r for r in L('standalone_ring_raw_replay.json')['rows']}
    strat = [r for r in L('all_scope_strategy_valuation.json')['rows'] if r['kind'] == 'paired_strategy']
    fee = L('full_fee_distribution.json')
    prio = {t['hash']: int(t['priority_wei']) for t in fee['selected_transactions']}
    recipient = {b['block']: b['fee_recipient'].lower() for b in fee['blocks']}
    strict_total = sum(D(r['overpayment_USD_excluding_gas']) for r in L('wallet_strict_purchase_summary.json')['rows'])

    # ---- lower bound -------------------------------------------------------------------------
    closed = [g for g in groups if g['closed_without_recognized_position_events']]
    sandwich_closed = sum(D(g['net_cashflow_ETH']) for g in closed)
    sandwich_legs = {l['hash'] for g in closed for l in g['legs']}
    sandwich_builder_prio = sum(prio.get(h, 0) for h in sandwich_legs)

    per_hash = {}
    for r in attrib + nonce:
        diff = D(r['cashflow_difference_ETH'])
        actual = D(r['scenarios']['actual']['net_ETH_after_gas'])
        per_hash.setdefault(r['hash'], []).append((diff, actual, r))
    backrun_attr, backrun_builder, backrun_net_causal, negatives = D(0), 0, D(0), 0
    for h, xs in per_hash.items():
        diff, actual, r = min(xs, key=lambda x: x[0])          # most conservative target
        backrun_net_causal += diff
        negatives += diff < 0
        a = clip(diff, D(0), max(actual, D(0)))
        backrun_attr += a
        cf = r['scenarios'].get('remove_target') or r['scenarios'].get('replace_target_with_nonce_only') or {}
        if a > 0 and (cf.get('status') == '0x0' or D(cf.get('net_ETH_after_gas', '0')) <= 0):
            ring = rings.get(h, {})
            direct = int(ring.get('native_net_wei', {}).get(recipient.get(r['block'], ''), '0'))
            backrun_builder += prio.get(h, 0) + max(direct, 0)

    e53 = {'status': 'not available'}
    p = R / 'extended_cycle_eight_block_EVM.json'
    if p.exists():
        d = json.loads(p.read_text())
        base = next((s for s in d['scenarios'] if s['label'] == 'baseline' and s.get('all_receipts_match')), None)
        both = next((s for s in d['scenarios'] if s['label'] == 'remove_all_hacker_window_txs' and 'bot_net_ETH_after_gas' in s), None) \
            or next((s for s in d['scenarios'] if s['label'] == 'remove_both' and 'bot_net_ETH_after_gas' in s), None)
        if base and both:
            diff = D(base['bot_net_ETH_after_gas']) - D(both['bot_net_ETH_after_gas'])
            e53 = {'status': 'eight-block EVM intervention', 'scenario': both['label'], 'difference_ETH': str(diff),
                   'attributable_ETH': str(clip(diff, D(0), D(base['bot_net_ETH_after_gas'])))}
    e53_attr = D(e53.get('attributable_ETH', '0'))

    lower_searcher = sandwich_closed + backrun_attr + e53_attr
    lower_builder = D(sandwich_builder_prio + backrun_builder) / WEI
    lower = lower_searcher + lower_builder

    # ---- upper bound (scope-limited) ---------------------------------------------------------
    priced = [s for s in strat if s['five_minute']['complete_under_price_mapping_assumptions'] and not s['position_or_debt_events']]
    sandwich_pos_usd = sum(max(D(0), D(s['five_minute']['USD'])) for s in priced)
    closed_pos_eth = sum(max(D(0), D(g['net_cashflow_ETH'])) for g in closed)
    sandwich_upper_eth = max(sandwich_pos_usd / ETH_USD, closed_pos_eth)
    rings_pos = sum(max(D(0), D(r['net_ETH_after_gas'])) for r in rings.values())
    mev_cats = ['candidate:strong_closed_cycle_evidence', 'candidate:other_token_inventory_open', 'candidate:multipool_positive_unproven_cycle',
                'candidate:insufficient_cycle_evidence', 'candidate:closed_cycle_nonpositive_cashflow']
    cats = fee['categories']
    builder_upper = sum(D(cats[c]['priority_wei']) + D(cats[c]['direct_fee_recipient_inflow_wei']) for c in mev_cats) / WEI
    upper_searcher = sandwich_upper_eth + rings_pos
    upper = upper_searcher + builder_upper

    usd = lambda x: str((x * ETH_USD).quantize(D('1')))
    q = lambda x: str(x.quantize(D('0.000001')))
    out = {
        'estimand': 'Value captured by third-party searchers, and the builders they paid, because of the hacker swaps; 3,311-block window, 55-address scope.',
        'ETH_USD_reference': str(ETH_USD),
        'lower_bound': {
            'ETH': q(lower), 'USD': usd(lower),
            'components': {
                'sandwich_closed_groups_net_ETH': {'value': q(sandwich_closed), 'groups': len(closed),
                    'assumption': 'Closed same-sender front/back groups; EVM removal of the target breaks the exit leg in all %d verified experiments; includes the one non-positive closed group.' % bracket['attempted']},
                'backrun_intervention_ETH': {'value': q(backrun_attr), 'transactions': len(per_hash),
                    'assumption': 'Per transaction: actual minus target-removed cashflow, smallest across removed targets, clipped to [0, actual profit].'},
                'cross_block_E53_ETH': e53,
                'builder_payments_ETH': {'value': q(lower_builder),
                    'assumption': 'Priority fees of closed sandwich legs plus priority fees and direct fee-recipient transfers of back-runs that revert or lose money without the target.'},
            },
            'excludes': 'Open-inventory sandwiches, unlinked cycles, other chains, and any payment not visible on the execution layer.',
        },
        'net_causal_effect_on_backrun_bots_ETH': {'value': q(backrun_net_causal), 'negative_transactions': negatives,
            'meaning': 'Sum of signed differences. Negative cases are bots that would have earned more without the hacker swap (the hacker swap removed an existing price gap). They reduce other bots\' income; they do not reduce what was extracted from the hacker, so they are not netted into the lower bound.'},
        'upper_bound': {
            'ETH': q(upper), 'USD': usd(upper),
            'components': {
                'all_sandwich_groups_positive_ETH': {'value': q(sandwich_upper_eth), 'priced_groups': len(priced), 'unpriced_groups': len(strat) - len(priced),
                    'assumption': 'Max of positive five-minute marked value of priced groups and positive closed ETH net. Unpriced groups are not valued.'},
                'all_single_tx_cycles_positive_ETH': {'value': q(rings_pos), 'transactions': len(rings),
                    'assumption': 'Every closed single-transaction cycle in scope is treated as caused by the hacker, linked or not.'},
                'builder_payments_by_all_MEV_candidates_ETH': {'value': q(builder_upper),
                    'assumption': 'Priority fees and direct fee-recipient transfers of every MEV-candidate transaction in the window, all treated as hacker-caused.'},
            },
            'not_covered': 'Unpriced sandwich groups and non-Ethereum venues.',
        },
        'hard_ceiling': {'USD': str(strict_total.quantize(D('1'))),
            'meaning': 'Total strict execution shortfall of the 16 wallets. Ordering profit cannot exceed what the hacker lost against the reference price; most of this stayed with liquidity providers as price impact.'},
        'summary': 'MEV extracted around the hacker swaps lies between %s and %s ETH (about USD %s-%s at ETH = %s). That is at most %.2f%% of the USD %s execution shortfall.'
                   % (q(lower), q(upper), usd(lower), usd(upper), ETH_USD, float(upper * ETH_USD / strict_total * 100), strict_total.quantize(D('1'))),
    }
    (R / 'event_MEV_total_bounds.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    print(out['summary'])
    for side in ('lower_bound', 'upper_bound'):
        for k, v in out[side]['components'].items():
            print(side, k, v.get('value', v))
    print('net causal', out['net_causal_effect_on_backrun_bots_ETH'])


if __name__ == '__main__':
    main()
