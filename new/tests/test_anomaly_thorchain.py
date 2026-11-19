import copy
import json
from decimal import Decimal
from eth_abi import encode
import pytest
from src.anomaly.screen import classify_loss,value_net
from src.decoding.router import inspect_router
from src.reconciliation.pricebook import PriceBook
from src.thorchain.reconstruct import units,btc_match,prior_close
from src.visualization.common import ROOT


def test_strict_screen_thresholds_and_missing_or_mixed_flows():
    assert not classify_loss('100000','90000')['qualifies']
    assert not classify_loss('200000','190000')['qualifies']
    assert classify_loss('200000','189999.99')['qualifies']
    assert not classify_loss(None,'1')['qualifies']
    assert not classify_loss('200000','1',position_events=True)['qualifies']
    assert not classify_loss('200000','1',internal_wallet_transfer=True)['qualifies']
    assert Decimal(classify_loss('200000','210000')['loss_USD'])<0


def book():
    b=PriceBook.__new__(PriceBook);b.registry={'known':{'symbol':'ETH','decimals':18}};b.bars={};b.conflicts=[];b.loaded={'ETH','USDT'}
    return b


def test_prices_contract_identity_timing_conflicts_and_quote_conversion():
    b=book();b.add_bar('ETH',120,2000,1990,2010,'raw')
    assert b.value('unknown',10**18,180)['USD'] is None
    assert b.value('known',10**18,179)['USD'] is None
    assert b.value('known',10**18,180)['USD']=='2000'
    b.add_bar('ETH',120,2001,1990,2010,'other')
    assert b.value('known',10**18,180)['USD'] is None
    b.add_bar('ETH',120,2000,1990,2010,'binance',venue='Binance',quote='USDT')
    assert b.value('known',10**18,180,eth_venue='Binance')['USD'] is None
    b.add_bar('USDT',120,'.99','.98','1','usd')
    assert Decimal(b.value('known',10**18,180,eth_venue='Binance')['USD'])==1980
    assert value_net(b,{'unknown':-10**18,'known':10**18},180)['input_reference_USD'] is None


def test_router_zero_intermediate_and_nonzero_final_guard_coexist():
    recipient='0x'+'0'*39+'2';token='0x'+'1'*40
    swap=encode(['address','uint256','uint256','address[]','bool'],[recipient,1000000,0,[token,token],True])
    unwrap=encode(['address','uint256'],[recipient,123456])
    data='0x3593564c'+encode(['bytes','bytes[]','uint256'],[bytes([8,12]),[swap,unwrap],99999]).hex()
    result=inspect_router(data)
    assert [l['bound_raw'] for l in result['limits']]==['0','123456']
    assert result['limits'][1]['bound_kind']=='unwrap_minimum'
    assert inspect_router('0x3593564c00')['status']=='decode_error'


def test_top_five_real_cases_have_cautious_classifications_and_internal_router_calls():
    cases=[json.loads((ROOT/f'reports/case_studies/N{i}_abnormal_swap.json').read_text()) for i in range(1,6)]
    assert all(Decimal(c['loss_USD'])>1000000 and not c['intentional_self_loss_established'] for c in cases)
    assert sum(Decimal(c['loss_USD'])>=5000000 for c in cases)==2
    assert all(c['observed_nonzero_minimum_bounds'] and c['observed_zero_minimum_bound_count']>0 for c in cases)
    assert all(c['counterfactual_incremental_MEV_loss_USD'] is None for c in cases)
    for c in cases[2:4]:
        assert c['router_limit_inspection']['status']=='unsupported_selector'
        assert any(x['inspection']['status']=='ABI_compatible_fields_decoded' for x in c['successful_router_call_inspections'])
    assert all(c['sensitivity']['binance_ETH_same_minute']['qualifies'] for c in cases)


def test_thor_1e8_not_ethereum_wei_and_completed_reference():
    assert units('3600000000')==36
    assert units('100484202')==Decimal('1.00484202')
    assert prior_close([[120,1,3,1,2,5]],180)==(Decimal(2),120)
    with pytest.raises(AssertionError):prior_close([[180,1,3,1,2,5]],180)


def test_real_crosschain_matches_and_rejects_wrong_destination_amount_memo():
    rows=json.loads((ROOT/'data/processed/thorchain_paths.json').read_text())
    assert len(rows)==3
    for r in rows:
        btc=json.loads((ROOT/r['evidence']['bitcoin']).read_text())['response']
        amount=str(int(Decimal(r['output_BTC'])*10**8))
        assert btc_match(btc,r['bitcoin_txid'],r['destination_address'],amount,r['ethereum_deposit'])
        with pytest.raises(AssertionError):btc_match(btc,r['bitcoin_txid'],'wrong',amount,r['ethereum_deposit'])
        with pytest.raises(AssertionError):btc_match(btc,r['bitcoin_txid'],r['destination_address'],str(int(amount)+1),r['ethereum_deposit'])
        with pytest.raises(AssertionError):btc_match(btc,r['bitcoin_txid'],r['destination_address'],amount,'ff'*32)
        path=r['funding_path'];assert len(path)==3
        assert all(a['timestamp']<b['timestamp'] for a,b in zip(path,path[1:]))
        assert path[-1]['timestamp']<r['deposit_timestamp']
        assert path[-1]['recipient']==r['source_address'] and path[0]['sender']==r['incident_anchor_address']
        assert all(int(a['amount_wei'])>=int(b['amount_wei']) for a,b in zip(path,path[1:]))
        assert not r['common_control_established'] and not r['ethereum_MEV_link_established']
        assert Decimal(r['input_reference_USD'])-Decimal(r['output_reference_USD'])==Decimal(r['estimated_execution_shortfall_USD'])
        assert Decimal(r['network_fee_BTC'])==units(int(r['streaming_swap']['outCoin']['amount'])-int(amount))
        assert r['price_impact_USD'] is None
