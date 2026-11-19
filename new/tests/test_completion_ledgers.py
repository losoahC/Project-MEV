import json,base64,hashlib
from collections import Counter
from decimal import Decimal
from eth_abi import decode
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.complete_surplus_ledger import transaction_ledger,claim_event
from src.arbitrage.transfer_audit import receipt_movements
P=ROOT/'data/processed/mev_full_window'

def read(n):return json.loads((P/n).read_text())

def test_all_pool_distribution_gaps_have_signed_actual_address_allocations():
    d=read('complete_pool_surplus_distributions.json');assert d['summary']['still_not_reconciled']==0 and d['summary']['fully_reconciled']==len(d['rows'])
    wanted={r['unit_id'] for r in read('strategy_accounts_v4.json') if r['status']=='pool_closed_cycle_distribution_or_cost_gap'};assert wanted=={r['unit_id'] for r in d['rows']}
    for r in d['rows']:
        assert r['all_observable_ETH_WETH_distribution_reconciled'] and not r['errors']
        assert Decimal(r['pool_surplus_ETH'])==sum((Decimal(a['combined_ETH_WETH_delta_after_gas']) for a in r['address_changes']),Decimal(0))+Decimal(r['burn_ETH'])
        assert Decimal(r['pool_resource_difference_ETH'])==0
        assert all(a['in_original_boundary']==(a['address'] in r['original_boundary']) for a in r['address_changes'])

def test_v4_currency_claim_is_not_a_cash_transfer_or_public_manager_profit():
    engine=Reconstruction(ROOT.parent/'research',False);h,rs,tr,_=engine.block(26300838);tx='0x806f60e73e039527bdde0c36d797897a41bdaa74a0b827d6c5088b42d99b30ce';keys={r['pool_key']:r for r in read('v4_pool_keys.json')['rows']};x=transaction_ledger(h,rs[tx],tr[tx],keys);address='0x82ccba35ad0c7a62230ef8ff337ac67f4cce0ea5'
    assert x['claims'][address]==64521435779627872
    assert sum(x['cash'].values())+sum(x['claims'].values())+x['burn']==x['resource']
    claims=[c for l in rs[tx]['logs'] if (c:=claim_event(l))];assert any(c['recipient']==address and c['amount_raw']=='64521435779627872' for c in claims)

def test_observed_few_redemptions_require_both_underlying_transfer_and_share_burn():
    d=json.loads((ROOT/'data/processed/few_wrapper_backing.json').read_text());assert not d['all_snapshots_fully_backed'] and d['all_observed_conversions_1to1']
    for r in d['observed_conversions']:
        assert r['matching_wrapper_mint_or_burn'] and r['matching_underlying_transfers']
        assert all(int(f['amount_raw'])==int(r['amount_raw']) for f in r['matching_wrapper_mint_or_burn']+r['matching_underlying_transfers'])

def test_secondary_prices_do_not_look_beyond_prior_completed_minute():
    d=json.loads((ROOT/'data/processed/completion_secondary_prices.json').read_text());accepted=[r for r in d['rows'] if r['accepted']];assert accepted
    for r in accepted:
        q=r['quote'];assert q['timestamp']<r['requested_timestamp']+60 and 0<=r['requested_timestamp']+59-q['timestamp']<=659
        assert q['decimals']==r['token_metadata']['decimals'] and Decimal(str(q['confidence']))>=Decimal('.9') and Decimal(str(q['price']))>0
        doc=json.loads((ROOT/r['evidence']).read_text());assert hashlib.sha256(base64.b64decode(doc['response_body_base64'])).hexdigest()==doc['response_body_sha256']
        assert 'ethereum:'+r['address'] in doc['url'] if 'url' in doc else 'ethereum:'+r['address'] in str(doc['request'])

def test_alternative_factory_membership_is_historical_and_not_dynamic_fee():
    rows=read('pool_metadata_full.json');cache={};count=0
    for r in rows:
        if not r.get('alternative_factory_method'):continue
        src=r.get('alternative_factory_lookup_evidence') or r['sources']['factory_lookup'];doc=json.loads((ROOT/src).read_text());params=doc['request']['params'];assert int(params[1],16)==r['block']
        if params[0]['to'].lower()==r['factory']:
            raw=doc['response']['result'];assert '0x'+raw[-40:]==r['pool']
        else:
            result=decode(['(bool,bytes)[]'],bytes.fromhex(doc['response']['result'][2:]))[0];ok,raw=result[r['alternative_factory_lookup_batch_index']];assert ok and '0x'+raw[-20:].hex()==r['pool']
        count+=1
    assert count>=42

def test_joint_interventions_count_each_target_once_and_keep_reverts():
    d=read('joint_front_replays.json');targets=[e['target'] for r in d['rows'] for e in r['target_effects']];assert len(targets)==len(set(targets))==372 and len(d['rows'])==319
    assert all(r['status']=='verified_joint_block_intervention' for r in d['rows'])
    assert any(e['counterfactual_status']==0 for r in d['rows'] for e in r['target_effects'])
    for r in d['rows']:
        actual=json.loads((ROOT/r['evidence']['actual_simulation']).read_text());cf=json.loads((ROOT/r['evidence']['without_fronts_simulation']).read_text());assert actual['request']['params'][0]['validation'] and cf['request']['params'][0]['validation']
        assert actual['request']['params'][1]==cf['request']['params'][1]==hex(r['block']-1)
        assert not cf['request']['params'][0]['blockStateCalls'][0].get('stateOverrides')

def test_failed_target_removals_are_funding_infeasibility_not_zero_profit():
    d=read('recovered_target_removals.json');assert d['original_response_errors']==d['funding_infeasible_after_target_removal']==6 and d['unexplained_transport_or_execution_errors']==0
    for r in d['rows']:
        doc=json.loads((ROOT/r['fresh_evidence']).read_text());assert 'insufficient funds for gas * price + value' in doc['response']['error']['message'];assert 'counterfactual_net_ETH' not in r

def test_all_observed_auction_values_match_actual_signed_payout_rows():
    d=read('full_auction_allocation.json');assert d['summary']['onchain_proposer_amount_matches']==len(d['rows'])==2939
    payments=Counter()
    for r in d['proposer_transfers']:payments[r['block']]+=int(r['amount_raw'])
    for r in d['rows']:
        assert Decimal(r['relay_expected_proposer_ETH'])*10**18==payments[r['block']]
        assert Decimal(r['fee_recipient_native_balance_change_proxy_ETH'])==Decimal(r['priority_ETH'])+Decimal(r['fee_recipient_native_in_ETH'])-Decimal(r['fee_recipient_native_out_ETH'])-Decimal(r['fee_recipient_own_gas_ETH'])

def test_position_borrowing_is_liability_and_withdrawal_is_not_free_profit():
    d=read('position_principal_ledger.json');assert d['summary']['principal_does_not_equal_profit'] and d['summary']['decoded_events']>500
    for r in d['rows']:
        assert r['profit_not_inferred_from_principal']
        for z in r['loan_collateral_principal_changes']:assert int(z['net_principal_equity_delta_raw'])==int(z['collateral_delta_raw'])-int(z['debt_delta_raw'])

def test_erc721_token_id_is_not_a_fungible_transfer_amount():
    log={'address':'0x'+'a'*40,'topics':['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef','0x'+'0'*64,'0x'+'0'*24+'b'*40,hex(1000000000000000000000)],'data':'0x','logIndex':'0x1'}
    traces=[{'traceAddress':[],'subtraces':0,'type':'call','action':{'from':'0x'+'b'*40,'to':'0x'+'a'*40,'value':'0x0','callType':'call'}}];rows=list(receipt_movements({'logs':[log]},traces));assert len(rows)==1 and rows[0]['amount_raw']=='1' and rows[0]['asset'].endswith(':1000000000000000000000')

def test_zero_address_is_issuance_sink_not_a_profit_recipient():
    d=read('order_counterparty_redistribution.json');rows=[r for r in d['rows'] if r['address']=='0x'+'0'*40];assert rows
    assert all(r['role'].startswith('token issuance/burn accounting sink') for r in rows)
