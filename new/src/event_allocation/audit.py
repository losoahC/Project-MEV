"""Independent streaming checks of the exported ledgers and quote schedule."""
import json,gzip,csv,hashlib
from decimal import Decimal,getcontext
from collections import defaultdict,Counter
from datetime import datetime,timezone
from src.event_allocation.config import ROOT,OUT,REPORT,START,END
getcontext().prec=90

def check_csv(path,quotes,allocation=False,transaction_keys=None):
    counts=Counter();seen_txs=set();current=None;keys=set();raw=defaultdict(int);usd=Decimal(0);missing=Counter()
    def finish():
        if current is None:return
        assert not any(raw.values()),(current,dict(raw));assert abs(usd)<Decimal('1e-45'),(current,str(usd));counts['integer_conserving_transactions']+=1
    with gzip.open(path,'rt') as f:
        for r in csv.DictReader(f):
            k=(r['chain'],r['tx_hash'])
            if k!=current:
                finish();assert k not in seen_txs;seen_txs.add(k);current=k;raw=defaultdict(int);usd=Decimal(0);keys=set()
            assert START<=int(r['timestamp'])<END;rid=(r['allocation_record_index'],r['asset']) if allocation else (r['address'],r['component'],r['asset']);assert rid not in keys,(k,rid);keys.add(rid);counts['rows']+=1;raw[r['asset']]+=int(r['raw']);q=quotes[r['quote_id']];assert q['asof_minute']==int(r['timestamp'])//60*60 and q['asset']==r['asset']
            if q['price_USD'] is None:assert r['USD']=='';missing[r['asset']]+=1
            else:
                assert Decimal(q['price_USD'])>0;v=Decimal(r['raw'])*Decimal(q['price_USD'])/Decimal(10)**q['decimals'];assert v==Decimal(r['USD']);usd+=v
    finish()
    if transaction_keys is not None:transaction_keys.update(seen_txs)
    return {'transactions_with_asset_rows':len(seen_txs),**counts,'missing_asset_rows':dict(missing),'all_transaction_asset_vectors_conserve':True,'all_priced_components_use_exported_shared_quote':True,'all_missing_prices_exported_blank':True,'unique_export_record_keys':True}

def run():
    summary=json.loads((OUT/'summary.json').read_text());assert not summary['draft_ethereum_only'] and not summary['mapping_failures'];schedule=json.loads((OUT/'quote_schedule_primary.json').read_text());quotes={f"{r['asset']}@{r['asof_minute']}":r for r in schedule['rows']};assert len(quotes)==len(schedule['rows']);checks=[]
    def quote_time(e,cutoff):
        if not isinstance(e,dict):return
        for k,v in e.items():
            if k in ['bar_start','quote_timestamp']:assert int(v)<cutoff,(k,v,cutoff)
            if isinstance(v,dict):quote_time(v,cutoff)
    for r in quotes.values():
        if r['price_USD'] is not None:quote_time(r['evidence'],r['asof_minute'])
    checks.append({'name':'No price observation reaches beyond its as-of cutoff','passed':True,'quotes':len(quotes)})
    actual_keys=set();budget_keys=set();actual=check_csv(REPORT/'actual_address_changes.csv.gz',quotes,transaction_keys=actual_keys);budget=check_csv(REPORT/'unified_allocation.csv.gz',quotes,True,budget_keys);expected_primary=set();zero_primary=set()
    with gzip.open(OUT/'transaction_valuations.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);k=(r['chain'],r['tx_hash']);assert k not in expected_primary;expected_primary.add(k)
            if not r['role_priced_USD'] and not r['unpriced_assets']:zero_primary.add(k)
    expected_actual=set();nonempty_actual=set();zero_actual=set();fields=['chain','tx_hash','block','timestamp','association','sender','asset_entry_count','observed_receipt_fee_raw','no_observed_fungible_or_known_principal_change','in_primary_reference_budget','evidence']
    with gzip.open(REPORT/'transaction_index.csv.gz','wt') as out:
        w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for chain in ['ethereum','tron']:
            with gzip.open(OUT/(chain+'_journal.jsonl.gz'),'rt') as f:
                for line in f:
                    r=json.loads(line);k=(chain,r['tx_hash']);assert k not in expected_actual;expected_actual.add(k)
                    if r['entries']:nonempty_actual.add(k)
                    else:zero_actual.add(k)
                    w.writerow({f:r[f] for f in ['chain','tx_hash','block','timestamp','association','sender']}|{'asset_entry_count':len(r['entries']),'observed_receipt_fee_raw':str(int(r['gas_raw'])+int(r['blob_burn_raw'])),'no_observed_fungible_or_known_principal_change':not r['entries'],'in_primary_reference_budget':k in expected_primary,'evidence':json.dumps(r['evidence'],separators=(',',':'))})
    assert actual_keys==nonempty_actual and expected_actual==actual_keys|zero_actual;assert len(expected_actual)==summary['counts']['actual_transactions'];assert actual['rows']==summary['counts']['actual_entries'];assert budget_keys==expected_primary-zero_primary and not budget_keys&zero_primary;assert len(expected_primary)==summary['counts']['primary_transactions'];actual['indexed_zero_asset_vector_transactions']=len(zero_actual);actual['total_indexed_transactions']=len(expected_actual);budget['indexed_zero_reference_vector_transactions']=len(zero_primary);budget['total_indexed_transactions']=len(expected_primary);checks.extend([{'name':'Actual all-address integer conservation, shared prices, and explicit zero-vector transaction index','passed':True,'result':actual},{'name':'Disjoint primary allocation, signed costs and explicit price gaps','passed':True,'result':budget}])
    for n in ['ethereum_journal_summary.json','tron_journal_summary.json']:
        d=json.loads((OUT/n).read_text());assert not d['failures'];checks.append({'name':n+' has no extraction failure','passed':True,'transactions':d['transactions']})
    tron=json.loads((OUT/'tron_journal_summary.json').read_text());assert tron['operator_histories_complete'] and tron['failed_receipts_complete'] and tron['all_fees_crosschecked'];checks.append({'name':'All TRON operators paginated, actual failed fees and all pool roots crosschecked','passed':True,'history':tron['history_crosscheck']})
    encoding=json.loads((OUT/'tron_encoding_summary.json').read_text());assert encoding['all_relevant_txid_encodings_verified'];assert encoding['relevant_pool_and_failed_transactions']==tron['transactions'];checks.append({'name':'Every monetary-relevant TRON transaction has a matching txID encoding hash','passed':True,'relevant_transactions':encoding['relevant_pool_and_failed_transactions'],'verified':encoding['relevant_txid_encodings_verified'],'explicit_zero_reconstruction_disclosed':True,'nonfinancial_history_encodings_not_blanket_certified':True})
    prop=json.loads((OUT/'proposer_secondary_allocation.json').read_text());assert prop['summary']['all_trace_amounts_match_block_payments'];assert all(r['primary_additive_amount_USD']=='0' and r['incident_causal_payment_identified_ETH'] is None for r in prop['blocks']);checks.append({'name':'Proposer payouts observed exactly; no duplicate primary extraction or invented event share','passed':True,'result':prop['summary']})
    settlements=json.loads((OUT/'whole_block_native_settlements.json').read_text());assert settlements['summary']['all_block_native_flows_and_matched_proposer_payouts_reconciled'];assert settlements['summary']['common_window_blocks']==len(prop['blocks']);combined=json.loads((OUT/'combined_ledger_summary.json').read_text());assert combined['secondary_additive_amount_USD']=='0' and combined['unique_stage_record_keys'];assert combined['rows']['primary_asset_rows']==budget['rows'];assert combined['rows']['secondary_actual_native_transfer_rows']==settlements['summary']['native_transfer_rows'];checks.append({'name':'All block-recipient native flows and one non-additive staged ledger','passed':True,'settlement_summary':settlements['summary'],'combined_export':combined})
    refs=set(json.loads((OUT/'used_evidence_paths.json').read_text()))
    def collect(x):
        if isinstance(x,dict):
            for v in x.values():collect(v)
        elif isinstance(x,list):
            for v in x:collect(v)
        elif isinstance(x,str) and x.startswith('data/raw/'):refs.add(x)
    collect(schedule);collect(prop);collect(settlements);collect(json.loads((OUT/'tron_encoding_node_overrides.json').read_text()));records=[]
    for s in sorted(refs):
        p=ROOT/s;assert p.exists(),s;records.append({'path':s,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    with gzip.open(OUT/'evidence_manifest.json.gz','wt') as f:json.dump({'purpose':'Byte integrity and provenance pointers; hashes do not establish ownership, price fairness or causality.','files':records},f)
    checks.append({'name':'All referenced raw evidence bytes present and hashed','passed':True,'files':len(records)})
    result={'status':'passed','checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'all_checks_passed':True,'scope':'Specified Ethereum/TRON event pools and window, reference-price allocation and observed payment redistribution. No claim of globally identified historical firm profit or causal MEV.'};(OUT/'validation.json').write_text(json.dumps(result,indent=2));(REPORT/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'checks':len(checks),'actual_transactions':len(expected_actual),'primary_transactions':len(expected_primary),'indexed_zero_asset_vector_transactions':len(zero_actual),'evidence_files':len(records)},indent=2))
if __name__=='__main__':run()
