from collections import defaultdict
from decimal import Decimal,localcontext
import base64
import hashlib
import json

import networkx as nx
import pandas as pd
import pytest

from src.arbitrage.accounting import v2_quote,v2_execution_decomposition
from src.auction.reconstruct import fee_parts
from src.decoding.events import WETH,integer
from src.ingestion.evidence import read_json,unwrap
from src.visualization.common import ROOT


@pytest.mark.parametrize("case_id,net",[("A1","2.745812294499937065"),("A2","0.000065472689682791"),("A3","0.002184499542797343")])
def test_real_arbitrage_after_all_identified_costs(case_id,net):
    c=read_json(ROOT/f"reports/case_studies/{case_id}_arbitrage.json")
    assert Decimal(c['net_after_gas_and_builder_ETH'])==Decimal(net)
    with localcontext() as ctx:
        ctx.prec=90
        gross=Decimal(c['gross_after_pool_fees_before_gas_and_builder_ETH'])
        assert gross-Decimal(c['gas_wei'])/Decimal(10)**18-Decimal(c['identified_builder_payment_wei'])/Decimal(10)**18==Decimal(net)
    assert not c['other_token_residual_raw']
    assert set(c['accounts'])=={c['sender'],c['executor']}
    assert c['target_index']<c['actor_index']


def test_every_pool_flow_edge_belongs_to_a_closed_directed_cycle():
    for case in read_json(ROOT/'data/processed/arbitrage_cases.json'):
        graph=nx.DiGraph()
        residual=defaultdict(int)
        for leg in case['route']:
            graph.add_edge(leg['input_token'],leg['output_token'])
            residual[leg['input_token']]-=int(leg['input_raw'])
            residual[leg['output_token']]+=int(leg['output_raw'])
        for a,b in graph.edges:
            assert nx.has_path(graph,b,a)
        assert not {t:v for t,v in residual.items() if t!=WETH and v}
        assert Decimal(residual[WETH])/Decimal(10)**18==Decimal(case['pool_flow_surplus_ETH'])
        assert Decimal(case['unallocated_pool_surplus_vs_operational_gross_ETH'])==0


def test_actual_v2_arbitrage_outputs_reproduced_from_pre_trade_reserves():
    cases=read_json(ROOT/'data/processed/arbitrage_cases.json')
    hashes={c['tx_hash'] for c in cases}
    rows=read_json(ROOT/'data/processed/v2_price_impact_decomposition.json')
    focal=[r for r in rows if r['tx_hash'] in hashes]
    assert len(focal)==5
    assert all(Decimal(r['unexplained_model_residual_raw'])==0 for r in focal)


def test_amm_impact_and_fee_effect_do_not_double_count():
    out=v2_quote(1000,10000,10000)
    d=v2_execution_decomposition(1000,out,10000,10000)
    with localcontext() as ctx:
        ctx.prec=90
        assert abs(Decimal(d['marginal_output_raw'])-Decimal(out)-Decimal(d['mechanical_impact_output_raw'])-Decimal(d['fee_effect_output_raw']))<Decimal('1e-24')
    assert Decimal(d['mechanical_impact_output_raw'])>0
    assert Decimal(d['fee_effect_output_raw'])>0
    assert Decimal(d['unexplained_model_residual_raw'])==0


def test_pool_states_preserve_log_order_and_signed_reserve_changes():
    rows=read_json(ROOT/'data/processed/pool_states.json')
    for r in rows:
        if r['protocol'].startswith('V2'):
            for i in (0,1):
                assert int(r['before'][f'reserve{i}_raw'])+int(r[f'amount{i}_raw'])==int(r['after'][f'reserve{i}_raw'])
        else:
            assert int(r['before']['sqrt_price_x96'])>0 and int(r['after']['sqrt_price_x96'])>0
            assert int(r['before']['active_liquidity'])>=0


def test_live_pool_identity_calls_support_token_and_decimals():
    for case in read_json(ROOT/'data/processed/arbitrage_cases.json'):
        for meta in case['metadata'].values():
            for i in (0,1):
                token=read_json(ROOT/meta['sources'][f'token{i}'])['response']['result']
                decimals=read_json(ROOT/meta['sources'][f'decimals{i}'])['response']['result']
                assert meta[f'token{i}']=='0x'+token[-40:].lower()
                assert meta[f'decimals{i}']==integer(decimals)


def test_sandwich_whole_episode_not_back_leg_receipts():
    case=read_json(ROOT/'reports/case_studies/S1_sandwich.json')
    front,back=[Decimal(case[k]['net_after_gas_and_builder_ETH']) for k in ['front_cashflow','back_cashflow']]
    assert front<0 and back>0
    assert front+back==Decimal(case['episode_net_ETH'])
    assert Decimal(case['episode_net_ETH'])==Decimal('12.080033775421395622')
    assert back>Decimal(case['episode_net_ETH'])*40
    assert case['transaction_indices']==[9,10,11]


def test_price_chart_uses_real_timestamps_and_real_executable_trade_sizes():
    rows=pd.read_parquet(ROOT/'reports/tables/fig02_price_observations.parquet')
    assert len(rows)>100
    assert (rows.ETH_quantity.astype(float)>0).all()
    assert rows.groupby('block').timestamp.nunique().eq(1).all()
    assert set(rows.classification)=={'Other observed swap','Wallet-sample swap','Selected arbitrage'}
    for r in rows.to_dict('records'):
        expected=(Decimal(r['execution_USD_per_ETH'])/Decimal(r['reference_ETH_USD'])-1)*100
        assert abs(expected-Decimal(r['dislocation_pct']))<Decimal('1e-24')


def test_fees_are_partitioned_once():
    receipt={'gasUsed':hex(21000),'effectiveGasPrice':hex(30)}
    parts=fee_parts(receipt,20)
    assert parts=={'gas_wei':630000,'burn_wei':420000,'priority_wei':210000}
    with pytest.raises(AssertionError):
        fee_parts(receipt,31)


def test_fresh_block_hash_read_agrees_with_cached_execution_header():
    rows=read_json(ROOT/'data/processed/canonical_block_crosscheck.json')
    assert len(rows)==4
    for row in rows:
        response=read_json(ROOT/row['fresh_read_evidence'])['response']['result']
        assert response['hash']==row['block_hash'] and integer(response['number'])==row['block']


def test_auction_reports_deduplicated_across_relays():
    rows=pd.read_parquet(ROOT/'data/processed/auction_deliveries.parquet')
    assert rows.block_hash.is_unique
    assert rows.slot.is_unique
    assert rows.delivery_reports.max()>1


def test_every_delivery_header_discoverable_without_original_cache():
    from src.arbitrage.reconstruct import Reconstruction
    engine=Reconstruction(ROOT/'__absent_legacy_directory__')
    rows=pd.read_parquet(ROOT/'data/processed/auction_deliveries.parquet')
    for number in rows.block_number:
        assert engine.block_source(number,'header') is not None
    assert not any(r['reason']=='missing_header' for r in read_json(ROOT/'data/processed/auction_rejected_records.json'))


def test_three_proposer_payments_match_exactly_once_through_forwarder():
    outcomes=read_json(ROOT/'data/processed/auction_outcomes.json')
    payments=pd.read_parquet(ROOT/'data/processed/proposer_payments.parquet')
    assert len(outcomes)==3
    for row in outcomes:
        subset=payments[payments.case_id.eq(row['case_id'])]
        assert subset.amount_wei.map(int).sum()==int(row['delivered_value_wei'])
        assert int(row['onchain_proposer_payment_wei'])==int(row['delivered_value_wei'])
        # The physical sender is the forwarding contract, not the block fee recipient.
        assert not subset.sender.eq(row['builder_fee_recipient']).any()
        for payment in subset.to_dict('records'):
            traces=unwrap(read_json(ROOT/payment['evidence_path']))
            leaf=next(t for t in traces if t.get('transactionHash')==payment['tx_hash'] and t['traceAddress']==json.loads(payment['trace_address']))
            assert leaf['type'] in ('suicide','selfdestruct')
            assert integer(leaf['action']['balance'])==int(payment['amount_wei'])


def test_distinct_payer_never_silently_clustered_into_builder_profit():
    outcomes=read_json(ROOT/'data/processed/auction_outcomes.json')
    a3=next(r for r in outcomes if r['case_id']=='A3')
    assert a3['builder_margin_proxy_wei'] is None
    assert int(a3['separate_payer_proposer_wei'])>0
    for row in outcomes:
        receipts=int(row['whole_block_priority_wei'])+int(row['whole_block_native_receipts_wei'])
        costs=int(row['fee_recipient_funded_proposer_wei'])+int(row['whole_block_other_native_outflow_wei'])+int(row['fee_recipient_own_gas_wei'])
        assert receipts-costs==int(row['builder_execution_balance_margin_proxy_wei'])


def test_public_source_record_integrity_and_captured_response_bytes():
    for row in read_json(ROOT/'data/raw/public_index.json'):
        raw=(ROOT/row['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['sha256']
        doc=json.loads(raw)
        if 'response_body_base64' in doc:
            assert hashlib.sha256(base64.b64decode(doc['response_body_base64'])).hexdigest()==doc['response_body_sha256']
