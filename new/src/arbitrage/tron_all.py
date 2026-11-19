"""All named TRON traders: signed transactions, closed cycles and target chronology."""
import json,argparse
from decimal import Decimal
from collections import defaultdict,Counter
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_collect import BOT
from src.arbitrage.tron_more import BOTS
from src.arbitrage.tron_accounting import parse,U,W,PUBLIC
from src.arbitrage.tron_signature_audit import audit
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction

def poolkeys(r):return {e['pool_hex']+(':'+e['pool_id'] if e.get('pool_id') else '') for e in r['swap_events']}

def run(allow_partial=False):
    p=ROOT/'data/processed/mev_tron';raw=json.loads((p/'named_bot_receipts.json').read_text());pending=[]
    for filename,key in [('pool_metadata_current.json','pool_hex'),('token_metadata_current.json','token_hex')]:
        path=p/filename
        if path.exists():PUBLIC.update(r[key] for r in json.loads(path.read_text()))
    for bot in BOTS:
        path=p/bot/'receipts.json'
        if path.exists():raw+=json.loads(path.read_text())
        else:pending.append(bot)
    if pending and not allow_partial:raise RuntimeError('Receipt collections still running: '+str(pending))
    override_path=p/'canonical_transaction_overrides.json'
    overrides={r['tx_hash']:r for r in json.loads(override_path.read_text()) if r['canonical_hash_verified']} if override_path.exists() else {}
    for row in raw:
        if row['tx_hash'] in overrides:
            o=overrides[row['tx_hash']];row['indexed_transaction_evidence']=row['transaction_evidence'];row['transaction_evidence']=o['canonical_evidence'];row['transaction']={**row['transaction'],**o['canonical_transaction']}
    keys={(r['manager_hex'],r['pool_id']):r for r in json.loads((p/'sun_v4_pool_keys.json').read_text())};targets=[r for r in json.loads((p/'target_owner_accounting.json').read_text()) if r['success'] and Decimal(r['USDT_net'])<0 and Decimal(r['combined_TRX_WTRX_before_fee'])>0 and r['swap_events']];by_pool=defaultdict(list)
    for target in targets:
        for key in poolkeys(target):by_pool[key].append(target)
    book=book_from_archive();book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('TRX',('2026-10-29','2026-10-30'));book.loaded.add('TRX');rows=[];signatures=[]
    for row in raw:
        r=parse(row,keys);sig=audit(row);signatures.append(sig);usdt=book.price('USDT',r['timestamp']);trx=book.price('TRX',r['timestamp'],venue='Binance');fee=Decimal(r['fee_TRX'])*trx[0] if trx else None;priceok=usdt and trx;value=Decimal(r['USDT_net'])*usdt[0]+Decimal(r['combined_TRX_WTRX_before_fee'])*trx[0]-fee if priceok and r['mechanically_closed_positive_USDT_cycle'] else None
        links={t['tx_hash']:t for key in poolkeys(r) for t in by_pool[key]};chron=[]
        for t in links.values():
            before=t['timestamp']<r['timestamp'];chron.append({'target':t['tx_hash'],'target_owner':t['owner'],'target_block':t['block'],'seconds_after_target':r['timestamp']-t['timestamp'],'blocks_after_target':r['block']-t['block'],'same_pool_keys':sorted(poolkeys(t)&poolkeys(r)),'chronology':'after_target' if before else 'same_timestamp_order_unverified' if t['timestamp']==r['timestamp'] else 'before_target','target_reference_shortfall_USD':t['reference_shortfall_excluding_gas_USD'],'MEV_incremental_loss_USD':None})
        simple_edge=priceok and r['success'] and bool(r['swap_events']) and not r['other_token_residual_raw'] and (r['mechanically_closed_positive_USDT_cycle'] or Decimal(r['USDT_net'])*Decimal(r['combined_TRX_WTRX_before_fee'])<0)
        edge=Decimal(r['USDT_net'])*usdt[0]+Decimal(r['combined_TRX_WTRX_before_fee'])*trx[0]-fee if simple_edge else None
        r.update(marked_swap_reference_edge_after_fee_USD=str(edge) if edge is not None else None,reference_edge_inventory_closed=r['mechanically_closed_positive_USDT_cycle'],signature_txid_matches=sig['txID_matches_SHA256_raw_data'],signature_owner_match=sig['owner_is_recovered_signer'],fee_USD=str(fee) if fee is not None else None,closed_cycle_after_paid_fee_USD=str(value) if value is not None else None,price_evidence={'USDT':usdt[1] if usdt else None,'TRX':trx[1] if trx else None},target_pool_chronology=chron,MEV_criterion='Closed actual multi-pool asset surplus is arbitrage evidence. Prior target same-pool relation is association, not causal loss. TRON paid energy/bandwidth fees do not establish Ethereum-style priority bidding.',root_contract_types=[c['type'] for c in row['transaction']['raw_data']['contract']]);rows.append(r)
    summaries=[]
    for bot in [BOT]+BOTS:
        rr=[r for r in rows if r['owner']==bot];cycles=[r for r in rr if r['mechanically_closed_positive_USDT_cycle']];priced=[r for r in cycles if r['closed_cycle_after_paid_fee_USD'] is not None];summary={'bot':bot,'transactions':len(rr),'successful_transactions':sum(r['success'] for r in rr),'closed_cycles':len(cycles),'priced_closed_cycles':len(priced),'USDT_surplus':str(sum((Decimal(r['USDT_net']) for r in cycles),Decimal(0))),'TRX_WTRX_surplus':str(sum((Decimal(r['combined_TRX_WTRX_before_fee']) for r in cycles),Decimal(0))),'cycle_net_after_cycle_paid_fees_USD':str(sum((Decimal(r['closed_cycle_after_paid_fee_USD']) for r in priced),Decimal(0))),'all_window_observed_paid_fees_USD':str(sum((Decimal(r['fee_USD']) for r in rr if r['fee_USD'] is not None),Decimal(0))),'noncycle_paid_fees_USD':str(sum((Decimal(r['fee_USD']) for r in rr if r['fee_USD'] is not None and not r['mechanically_closed_positive_USDT_cycle']),Decimal(0))),'closed_cycles_with_prior_same_pool_target':sum(any(t['chronology']=='after_target' for t in r['target_pool_chronology']) for r in cycles),'not_firm_wide_PnL':True};covered=[r for r in rr if r['marked_swap_reference_edge_after_fee_USD'] is not None];summary['priced_swap_edge_transactions']=len(covered);summary['priced_swap_reference_edge_after_trade_fees_USD']=str(sum((Decimal(r['marked_swap_reference_edge_after_fee_USD']) for r in covered),Decimal(0)));summary['nonpriced_trade_context_fees_USD']=str(sum((Decimal(r['fee_USD']) for r in rr if r['fee_USD'] is not None and r['marked_swap_reference_edge_after_fee_USD'] is None),Decimal(0)));summary['swap_edges_charged_all_window_paid_fees_USD']=str(Decimal(summary['priced_swap_reference_edge_after_trade_fees_USD'])-Decimal(summary['nonpriced_trade_context_fees_USD']));summary['cycle_gains_charged_all_window_paid_fees_USD']=str(Decimal(summary['cycle_net_after_cycle_paid_fees_USD'])-Decimal(summary['noncycle_paid_fees_USD']));summaries.append(summary)
    result={'rows':rows,'summary_by_bot':summaries,'canonical_body_corrections':len(overrides),'pending_collections':pending,'target_transactions_with_positive_TRX_and_negative_USDT':len(targets),'fully_collected_named_bots':not pending,'all_incident_MEV_complete':False,'owner_signature_matches':sum(s['owner_is_recovered_signer'] for s in signatures),'unknown_delegated_energy_or_offchain_costs':True};(p/'all_named_bot_accounting.json').write_text(json.dumps(result,indent=2));(p/'all_named_signature_audit.json').write_text(json.dumps({'rows':signatures,'all_txid_verified':all(s['txID_matches_SHA256_raw_data'] for s in signatures),'txid_discrepancies':[s['tx_hash'] for s in signatures if not s['txID_matches_SHA256_raw_data']],'owner_signer_matches':result['owner_signature_matches']},indent=2));print(json.dumps({'summary':summaries,'pending':pending,'targets':len(targets)},indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args();run(args.allow_partial)
