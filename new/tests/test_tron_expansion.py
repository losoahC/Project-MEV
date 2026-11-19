import json,hashlib,base64
from decimal import Decimal
from src.arbitrage.discover import ROOT
P=ROOT/'data/processed/mev_tron'

def test_all_named_tron_receipts_are_collected_and_signatures_match_canonical_bodies():
    r=json.loads((P/'all_named_bot_accounting.json').read_text());sig=json.loads((P/'all_named_signature_audit.json').read_text());assert r['fully_collected_named_bots'] and not r['pending_collections'];assert len(r['rows'])==3541==r['owner_signature_matches'];assert sig['all_txid_verified'] and not sig['txid_discrepancies']
    fixes=json.loads((P/'canonical_transaction_overrides.json').read_text());assert len(fixes)==23 and all(f['canonical_hash_verified'] for f in fixes)
    for f in fixes:
        t=f['canonical_transaction'];assert hashlib.sha256(bytes.fromhex(t['raw_data_hex'])).hexdigest()==f['tx_hash'];assert f['canonical_evidence']!=f['indexed_transaction_evidence']
    for s in r['summary_by_bot']:
        assert Decimal(s['swap_edges_charged_all_window_paid_fees_USD'])==Decimal(s['priced_swap_reference_edge_after_trade_fees_USD'])-Decimal(s['nonpriced_trade_context_fees_USD'])
    # Successful inventory trades must not silently become closed cycles.
    seller=next(s for s in r['summary_by_bot'] if s['bot'].startswith('TDR4'));assert seller['closed_cycles']==0 and seller['priced_swap_edge_transactions']==38
    # A direct token-wrapper interaction must not add the public reserve contract
    # to the trader boundary; otherwise withdrawal backing would count twice.
    wraps=[x for x in r['rows'] if x['entrypoint']=='TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR'];assert wraps
    for x in wraps:assert x['boundary']==[x['owner']] and x['public_router_excluded']

def test_justlend_principal_conversion_offsets_jtoken_changes_and_new_borrowing():
    d=json.loads((P/'justlend_position_adjustments.json').read_text());assert len(d['rows'])==15
    for r in d['rows']:
        assert r['complete_for_principal_conversion'] and not r['unmatched_jtoken_transfers_raw'] and not r['unresolved_other_tokens_raw']
        assert r['actual_jtoken_delta_raw']==r['event_share_delta_raw']
        for e in r['decoded_position_events']:
            if e['name']=='Borrow':assert int(e['underlying_principal_equity_delta_raw'])==-int(e['decoded']['borrowAmount'])
            if e['name']=='Mint':assert int(e['underlying_principal_equity_delta_raw'])==int(e['decoded']['mintAmount'])

def test_tron_pool_metadata_does_not_claim_historical_state():
    rows=json.loads((P/'pool_metadata_current.json').read_text());assert len(rows)==143
    docs={}
    for r in rows:
        assert not r['historical_identity_proven'] and r['metadata_state']=='latest, NOT historical'
        assert r['current_factory_lookup_matches_pool']
        for e in r['evidence'].values():
            path=e['evidence']
            if path not in docs:
                d=json.loads((ROOT/path).read_text());assert hashlib.sha256(base64.b64decode(d['response_body_base64'])).hexdigest()==d['response_body_sha256'];docs[path]=d
            d=docs[path];job=next(x for x in d['request'] if x['id']==e['batch_id']);assert job['params'][1]=='latest'
