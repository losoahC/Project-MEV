import json,base64,hashlib
from decimal import Decimal
from eth_abi import decode
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.indirect_payments import fee_paths
from src.decoding.events import WETH,USDT,integer
P=ROOT/'data/processed/mev_full_window'

def test_pool_multicall_slot_and_parent_provenance():
    rows=json.loads((P/'pool_metadata_full.json').read_text());cache={};count=0
    for r in rows:
        if not r.get('batch_indices'):continue
        for field,index in r['batch_indices'].items():
            if field=='factory_lookup' and r.get('alternative_factory_method'):continue
            path=r['sources'][field]
            if path not in cache:
                d=json.loads((ROOT/path).read_text());assert hashlib.sha256(base64.b64decode(d['response_body_base64'])).hexdigest()==d['response_body_sha256'];params=d['request']['params'];jobs=decode(['(address,bool,bytes)[]'],bytes.fromhex(params[0]['data'][10:]))[0];ret=decode(['(bool,bytes)[]'],bytes.fromhex(d['response']['result'][2:]))[0];cache[path]=(params,jobs,ret)
            params,jobs,ret=cache[path];assert int(params[1],16)==r['block'];job=jobs[index];ok,raw=ret[index]
            if field in r['failures'] or field in r.get('original_Uniswap_factory_lookup_failures',{}):assert not ok or len(raw)!=32;continue
            assert ok and len(raw)==32
            if field=='factory_lookup':
                assert job[0].lower()==r['factory']
                if r['factory_lookup_matches_pool']:assert '0x'+raw[-20:].hex()==r['pool'] and r['planning_matches_parent']
            else:
                assert job[0].lower()==r['pool'];expected=Web3.keccak(text={'token0':'token0()','token1':'token1()','factory':'factory()','fee_pips':'fee()'}[field])[:4];assert job[2]==expected;assert r[field]==(int.from_bytes(raw,'big') if field=='fee_pips' else '0x'+raw[-20:].hex())
            count+=1
    assert count>2000

def test_comet_borrowed_money_is_liability_and_collateral_not_lost_cash():
    r=json.loads((P/'comet_resolver_equity.json').read_text());assert r['states']['before']['borrow_raw']=='0' and r['states']['before']['USDT_collateral_raw']=='0'
    assert int(r['position_equity_change_raw'][WETH])==-int(r['states']['after']['borrow_raw'])
    assert int(r['position_equity_change_raw'][USDT])==int(r['states']['after']['USDT_collateral_raw'])
    for t,v in r['combined_equity_change_raw'].items():assert int(v)==int(r['liquid_change_after_actual_gas_raw'].get(t,0))+int(r['position_equity_change_raw'].get(t,0))
    assert Decimal(r['reference_equity_gain_after_gas_USD'])==sum(Decimal(x['USD']) for x in r['reference_valuations'])
    for label,path in r['evidence']['prefix_state_diagnostics'].items():
        d=json.loads((ROOT/path).read_text());assert d['request']['params'][0]['validation'] and not d['request']['params'][0]['blockStateCalls'][0].get('stateOverrides');assert d['request']['params'][1]==hex(r['block']-1)

def test_actual_indirect_payment_keeps_helper_outside_bot_boundary():
    e=Reconstruction(ROOT.parent/'research',False);h,rs,tr,_=e.block(26301699);tx='0x7890dd1fecb9bdcbd805158c09919d7af515ae5fd2a0a13359812c27d04b3ac3';boundary={'0x45e9b04942176a513b22acc1ced75c34d2fd9215','0x4d92a9835f4768aac92531cf1a638e444912dada'};paths=fee_paths(rs[tx],tr[tx],boundary,h['miner'],set());p=next(x for x in paths if x['helper']=='0x3c26a02d1ccccb9079062ad07d0240cb975bdc2e');assert p['amount_wei']=='90495703247500838131' and p['helper'] not in boundary and not p['common_ownership_inferred']
    assert sum(int(f['amount_raw']) for f in p['helper_to_fee_recipient_native_traces'])==int(p['amount_wei'])
    assert fee_paths(rs[tx],tr[tx],boundary,'0x'+'1'*40,set())==[]

def test_order_reference_loss_partition_includes_actual_third_party_payment():
    r=json.loads((P/'order_reference_shortfall_partition.json').read_text());assert r['partition_reconciles_exactly'] and not r['MEV_incremental_loss_proven']
    assert sum((Decimal(v) for v in r['partition_USD'].values()),Decimal(0))==Decimal(r['maker_reference_shortfall_USD'])
    assert r['third_party_receiver'] not in [r['maker'],r['fee_recipient'],r['resolver']]
    flows=r['actual_native_flows'];payout=next(f for f in flows if f['sender']==r['settlement_carrier'] and f['recipient']==r['third_party_receiver']);assert Decimal(payout['amount_raw'])/10**18==Decimal(r['third_party_native_ETH_in'])

def test_nine_order_signed_counterparty_ledger_matches_independent_target_ledger():
    d=json.loads((P/'order_counterparty_redistribution.json').read_text());orders=json.loads((P/'order_filler_equity.json').read_text());assert len(d['summary_by_order'])==9 and len(d['rows'])==199
    assert sum(s['all_address_assets_priced'] for s in d['summary_by_order'])==3
    expected={r['tx_hash']:sum(Decimal(t['signed_reference_shortfall_USD']) for t in r['target_reference_shortfalls']) for r in orders['rows']}
    for s in d['summary_by_order']:
        assert Decimal(s['maker_reference_shortfall_USD'])==expected[s['tx_hash']]
        rows=[r for r in d['rows'] if r['tx_hash']==s['tx_hash']];assert sum((Decimal(r['known_asset_reference_USD']) for r in rows),Decimal(0))+Decimal(s['base_fee_burn_USD'])==0
