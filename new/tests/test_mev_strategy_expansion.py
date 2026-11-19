import json,bisect,hashlib
from decimal import Decimal
from collections import defaultdict
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.ingestion.evidence import read_json
P=ROOT/'data/processed/mev_full_window'

def test_strategy_units_cover_candidates_once_and_include_interval_costs():
    units=read_json(P/'strategy_units.json');candidates=read_json(P/'candidates.json');allhashes=[tx['tx_hash'] for u in units for tx in u['txs']];assert len(allhashes)==len(set(allhashes))==12967
    assert {h for u in units for h in u['candidate_hashes']}=={r['tx_hash'] for r in candidates}
    public=set(read_json(P/'public_boundary_exclusions.json')['addresses']);by=defaultdict(list)
    for u in units:
        assert not (set(u['boundary'])-{u['sender']})&public
        if u['kind']=='same_sender_bracketing_interval':by[u['sender']].append((u['txs'][0]['block']*10000+u['txs'][0]['index'],u['txs'][-1]['block']*10000+u['txs'][-1]['index'],{t['tx_hash'] for t in u['txs']}))
    for rs in by.values():rs.sort()
    with (P/'all_sender_accounting.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['sender'] not in by:continue
            pos=r['block']*10000+r['index'];rs=by[r['sender']];i=bisect.bisect_right([x[0] for x in rs],pos)-1
            if i>=0 and pos<=rs[i][1]:assert r['tx_hash'] in rs[i][2]

def test_v4_key_metadata_matches_original_trace_calldata_not_just_labels():
    data=read_json(P/'v4_pool_keys.json');assert data['summary']['resolved_pool_ids']==808 and not data['missing']
    files={}
    for r in data['rows']:
        assert '0x'+Web3.keccak(bytes.fromhex(r['encoded_pool_key'][2:])).hex().removeprefix('0x')==r['pool_id']
        if r['evidence'] not in files:
            doc=read_json(ROOT/r['evidence']);files[r['evidence']]=doc.get('result',doc) if isinstance(doc,dict) else doc
        tr=next(t for t in files[r['evidence']] if t.get('transactionHash')==r['tx_hash'] and t['traceAddress']==r['trace_address'])
        assert tr['action']['input'][10:330].lower()==r['encoded_pool_key'][2:].lower()

def test_terminal_profit_vector_requires_capital_closure_and_keeps_losses():
    rows=read_json(P/'terminal_cycle_profits.json');summary=read_json(P/'terminal_cycle_summary.json');assert len(rows)==summary['verified_disjoint_cycle_units']
    assert summary['multiple_surplus_asset_units']==sum(r['retained_profit_asset_count']>1 for r in rows)
    assert summary['nonpositive_after_cost_units']==sum(r['net_reference_positive'] is False for r in rows)>0
    for r in rows:
        assert not r['MEV_causally_attributed']
        assert Decimal(r['pool_WETH_surplus_ETH'])>=0
        assert all(int(v)>0 for v in r['pool_inventory_residual_nonWETH_raw'].values())
        assert r['pool_inventory_residual_nonWETH_raw']==r['other_token_residual_raw']
        assert Decimal(r['pool_WETH_surplus_ETH'])==Decimal(r['gross_before_gas_direct_fee_recipient_ETH'])
        assert not r['position_events'] and not r['v4_nonzero_hooks'] and not r['unknown_pools']

def test_fee_distribution_conserves_surplus_and_does_not_add_proposer_twice():
    r=read_json(P/'covered_surplus_distribution.json');a={k:Decimal(v) for k,v in r['totals_ETH'].items()};assert r['covered_units']==read_json(P/'strategy_accounting_v4_summary.json')['verified_positive_cycle_units']
    assert a['gross']==a['burn']+a['priority']+a['direct']+a['indirect']+a['retained']
    assert sum((Decimal(x['priority_ETH']) for x in r['fee_recipients']),Decimal(0))==a['priority']
    assert sum((Decimal(x['direct_native_ETH']) for x in r['fee_recipients']),Decimal(0))==a['direct']
    assert sum((Decimal(x['indirect_or_WETH_ETH']) for x in r['fee_recipients']),Decimal(0))==a['indirect']

def test_tron_named_bot_has_valid_signed_raw_transactions_and_pool_reconciliation():
    p=ROOT/'data/processed/mev_tron';sig=read_json(p/'named_bot_signature_audit.json');rows=read_json(p/'named_bot_receipts.json');assert sig['transactions']==sig['owner_signer_matches']==63
    for r in rows:assert hashlib.sha256(bytes.fromhex(r['transaction']['raw_data_hex'])).hexdigest()==r['tx_hash']==r['receipt']['id']
    accounts=read_json(p/'named_bot_accounting.json');cycles=[r for r in accounts if r['mechanically_closed_positive_USDT_cycle']];assert len(cycles)==38
    for r in cycles:
        assert r['pool_boundary_USDT_gap_raw']=='0' and r['pool_boundary_TRX_gap_raw']=='0'
        assert Decimal(r['USDT_net'])>=0 and Decimal(r['combined_TRX_WTRX_before_fee'])>=0
