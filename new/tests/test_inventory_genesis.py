import json
import pytest
from eth_abi import encode
from src.visualization.common import ROOT
from src.reconciliation.inventory import decode_results
from src.ingestion.genesis import recover_authority,VICTIM


def test_multicall_failure_remains_missing_and_result_count_is_checked():
    payload='0x'+encode(['(bool,bytes)[]'],[[(True,(123).to_bytes(32,'big')),(False,b'')]]).hex()
    assert decode_results(payload,2)==[123,None]
    with pytest.raises(AssertionError):decode_results(payload,1)


def test_all_64_initial_asset_ledgers_use_exact_integer_snapshots():
    d=json.loads((ROOT/'data/processed/asset_inventory.json').read_text())
    assert d['asset_count']==64 and d['wallet_asset_rows']==1024
    assert len({(r['token'],r['address']) for r in d['rows']})==1024
    assert d['balanced_rows']==1024 and d['missing_balance_calls']==0
    assert len(d['initial_tx_hashes'])==3
    for r in d['rows']:
        assert int(r['opening_raw'])+int(r['inflow_raw'])-int(r['outflow_raw'])-int(r['gas_raw'])+int(r['wrapper_adjustment_raw'])==int(r['observed_closing_raw'])
        assert r['opening_evidence']!=r['closing_evidence']
    assert all(int(r['unexplained_change_raw'])==0 for r in d['assets'])
    raw_cache={}
    addresses=[r['address'] for r in d['rows'][:16]]
    for r in d['rows']:
        expected=16 if r['token']=='native:eth' else 17
        for evidence,field in [(r['opening_evidence'],'opening_raw'),(r['closing_evidence'],'observed_closing_raw')]:
            if evidence not in raw_cache:
                raw=json.loads((ROOT/evidence).read_text())
                raw_cache[evidence]=decode_results(raw['response']['result'],expected)
            assert raw_cache[evidence][addresses.index(r['address'])]==int(r[field])
    import pandas as pd,subprocess
    graph=pd.read_parquet(ROOT/'data/processed/fund_flow_graph_edges.parquet')
    assert len(graph)==57052 and not graph.edge_id.duplicated().any()
    btc=graph[graph.chain.eq('bitcoin')]
    assert len(btc)==3 and all(btc.event_location.eq('vout:0'))
    assert all(btc.valuation_status.eq('estimated_at_matched_ETH_deposit_reference_not_BTC_inclusion_time'))
    assert set(btc.crosschain_case)=={'T1','T2','T3'}
    result=subprocess.run(['node',str(ROOT/'tests/html_filter_smoke.mjs')],capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)['bitcoin_outputs']==3


def test_actual_50_delegation_signatures_and_tamper_changes_authority():
    d=json.loads((ROOT/'data/processed/incident_delegation.json').read_text())
    raw=json.loads((ROOT/d['evidence']['transaction']).read_text())['response']['result']
    assert len(raw['authorizationList'])==50
    assert {recover_authority(a) for a in raw['authorizationList']}=={VICTIM}
    changed={**raw['authorizationList'][0],'chainId':'0x2'}
    assert recover_authority(changed)!=VICTIM
    assert d['historical_code'][str(d['block']-1)]['code']=='0x'
    assert d['historical_code'][str(d['block'])]['code']=='0xef0100'+d['delegate'][2:]


def test_figure4_target_shortfalls_are_observed_estimates_not_placeholder():
    d=json.loads((ROOT/'reports/tables/fig04_attribution_status.json').read_text())
    for case,v in d['hacker_execution_loss'].items():
        assert v['shortfall_USD'] is not None and v['gas_excluded']
        assert not v['causal_MEV_loss_established']
    assert d['hacker_execution_loss']['A1']['shortfall_USD']=='8374003.920207953308621180'
