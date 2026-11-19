import json,base64,hashlib
from decimal import Decimal
from src.arbitrage.discover import ROOT
P=ROOT/'data/processed/mev_full_window'

def test_full_window_census_covers_all_blocks_not_only_wallet_blocks():
    blocks=json.loads((P/'blocks.json').read_text());summary=json.loads((P/'summary.json').read_text())
    assert [r['block'] for r in blocks]==list(range(26300640,26303951))
    assert sum(r['receipts'] for r in blocks)==751258==summary['receipts']
    assert not json.loads((P/'failures.json').read_text())
    cs=json.loads((P/'candidates.json').read_text());assert len(cs)==len({r['tx_hash'] for r in cs})==12841
    v4=[e for c in cs for e in c['events'] if e['protocol'].startswith('V4')]
    assert len({e['pool_key'] for e in v4})>1
    assert all(e['pool_key']==e['pool']+':'+e['pool_id'] for e in v4)

def test_orders_reconcile_actual_usdt_debit_and_eth_delivery():
    v=json.loads((P/'valuation_summary.json').read_text())
    assert v['order_transactions']==9
    assert Decimal(v['order_USDT_net_out'])==325000000
    assert Decimal(v['order_ETH_WETH_net_in'])==Decimal('122316.323922299741513724')
    assert not v['focus_all_strategy_profit_established']
    assert v['focus_priced_ETH_sales']==20

def test_sender_ledger_counts_costs_once_and_includes_non_candidates():
    seen=set();candidates=0;other=0
    with (P/'all_sender_accounting.jsonl').open() as f:
        for line in f:
            r=json.loads(line);assert r['tx_hash'] not in seen;seen.add(r['tx_hash'])
            assert int(r['base_fee_burn_wei'])+int(r['priority_fee_wei'])==int(r['gas_wei'])
            assert not r['MEV_classified_from_gas']
            candidates+=r['is_discovery_candidate'];other+=not r['is_discovery_candidate']
    assert candidates==12841 and other==124172 and len(seen)==137013

def test_archived_execution_audit_preserves_negative_counterexample():
    r=json.loads((P/'replay_audit.json').read_text())
    assert r['baseline_transactions_status_gas_logs_reproduced']==1003
    a3=next(x for x in r['rows'] if x['case_id']=='A3')
    assert Decimal(a3['actual_minus_removed_target_cashflow_ETH'])<0
    assert not r['hacker_incremental_loss_proven']

def test_fresh_victim_replays_have_raw_response_bytes_and_valid_prefixes():
    data=json.loads((P/'victim_replays.json').read_text());ok=[x for x in data['rows'] if x['status']=='verified_fixed_call_victim_intervention'];assert len(ok)>=3
    for r in ok:
        assert r['actual_prefix_transactions_reproduced']>0
        for name in ['actual_simulation','without_front_simulation']:
            raw=json.loads((ROOT/r['evidence'][name]).read_text());body=base64.b64decode(raw['response_body_base64']);assert hashlib.sha256(body).hexdigest()==raw['response_body_sha256']
            assert raw['request']['params'][0]['validation'] and raw['request']['params'][0]['traceTransfers']
        assert all(x['inputs_unchanged'] for x in r['victim_effects'])
