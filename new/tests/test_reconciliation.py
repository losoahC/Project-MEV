from decimal import Decimal
import json
from src.reconciliation.balances import reconcile
from src.visualization.common import ROOT


def test_integer_ledger_exposes_missing_amount_and_wrapper_conversion():
    assert reconcile(10,100,20,1,89)['balanced']
    assert not reconcile(10,100,20,1,90)['balanced']
    assert reconcile(0,668,0,0,0,wrapper_adjustment=-668)['balanced']
    assert reconcile(0,668,0,0,0)['unexplained_change_raw']=='-668'


def test_actual_64_snapshots_and_blacklist_contracts():
    data=json.loads((ROOT/'data/processed/balance_reconciliation.json').read_text())
    assert data['balanced_rows']==data['total_rows']==64
    assert len({r['address'] for r in data['rows']})==16
    for r in data['rows']:
        o=Decimal(r['opening_raw']);inc=Decimal(r['inflow_raw']);out=Decimal(r['outflow_raw']);gas=Decimal(r['gas_raw'])
        assert o+inc-out-gas+Decimal(r['wrapper_mint_raw'])-Decimal(r['wrapper_burn_raw'])==Decimal(r['observed_closing_raw'])
        assert r['fixed_reference']['USD'] is not None
        status=r['blacklist_status']
        if r['symbol'] in ('USDT','USDC'):
            raw=json.loads((ROOT/status['evidence']).read_text())
            assert bool(int(raw['response']['result'],16))==status['blacklisted']
            assert raw['request']['params'][1]==hex(data['closing_block'])
    weth=[r for r in data['rows'] if r['symbol']=='WETH' and r['wallet']==2][0]
    assert Decimal(weth['wrapper_burn_raw'])==Decimal('668132228390272982085')
    assert weth['wrapper_evidence']


def test_usdc_alternate_quote_has_observed_usdt_usd_conversion():
    data=json.loads((ROOT/'data/processed/balance_reconciliation.json').read_text())
    ref=next(r['fixed_reference'] for r in data['rows'] if r['symbol']=='USDC')
    assert ref['price_evidence']['venue']=='Binance'
    assert ref['price_evidence']['quote']=='USDT'
    assert ref['price_evidence']['USDT_USD_conversion']['venue']=='Coinbase'
    assert Decimal(ref['reference_USD'])!=1


def test_fixed_mark_and_searcher_partitions_never_count_frozen_twice():
    data=json.loads((ROOT/'data/processed/loss_reconciliation.json').read_text());a={k:Decimal(v) for k,v in data['asset_ledger_USD'].items()}
    assert a['opening']+a['external_inflow']-a['external_outflow']-a['gas']+a['wrapper_net']==a['closing']
    assert a['frozen_closing']+a['nonblacklisted_closing']==a['closing']
    assert a['frozen_closing']<a['closing']
    arb={k:Decimal(v) for k,v in data['selected_3_arbitrage_ETH'].items()}
    assert arb['gross_after_pool_fees_before_gas_and_builder_ETH']==arb['net_after_gas_and_builder_ETH']+arb['gas_ETH']+arb['direct_builder_ETH']
    assert all(data[k] is None for k in ['whole_incident_initial_stolen_USD','whole_incident_unrecovered_USD','whole_incident_MEV_loss_USD','causal_mev_share_of_execution_loss'])


def test_economic_sample_uniqueness_and_sensitivity_disclosure():
    data=json.loads((ROOT/'data/processed/loss_reconciliation.json').read_text());rows=json.loads((ROOT/'data/processed/economic_fixed_mark_rows.json').read_text())
    assert len({r['tx_hash'] for r in rows})==len(rows)
    assert len({r['fixed_reference_timestamp_utc'] for r in rows})==1
    assert Decimal(data['economic_fixed_mark_sample']['signed_net_shortfall_USD'])==sum((Decimal(r['signed_shortfall_fixed_USD']) for r in rows),Decimal(0))
    assert len(data['ownership_sensitivity'])==3
    assert 13 not in data['ownership_sensitivity'][1]['wallet_numbers']
    assert 9 not in data['ownership_sensitivity'][2]['wallet_numbers']
    scenarios=data['missing_relay_sensitivity'];assert scenarios[0]['removed_relay'] is None
    assert any(s['selected_delivered_outcomes_with_retained_relay_support']<3 for s in scenarios[1:])
    assert all(s['selected_onchain_proposer_payment_matches']==3 for s in scenarios)
