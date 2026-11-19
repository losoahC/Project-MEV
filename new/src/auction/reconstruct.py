"""Match delivered payloads to cached canonical blocks, then reconcile three real auction outcomes."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal
import json

import pandas as pd

from src.arbitrage.reconstruct import Reconstruction,ROOT,save
from src.arbitrage.accounting import native_flows
from src.decoding.events import integer
from src.ingestion.evidence import read_json,unwrap,find_block

RELAYS={"flashbots":"https://boost-relay.flashbots.net","ultrasound":"https://relay.ultrasound.money","aestus":"https://aestus.live","agnostic":"https://agnostic-relay.net"}
FIRST,LAST,EVENT_FIRST=26300640,26303950,26300770
E=Decimal(10)**18


def fee_parts(receipt,base_fee):
    used,price=integer(receipt["gasUsed"]),integer(receipt["effectiveGasPrice"])
    assert price>=base_fee
    return {"gas_wei":used*price,"burn_wei":used*base_fee,"priority_wei":used*(price-base_fee)}


def run(online=False,legacy=None):
    engine=Reconstruction(legacy or ROOT.parent/"research",online)
    cases=read_json(ROOT/"data/processed/arbitrage_cases.json")
    pages=list((engine.legacy/"relay_history_raw").glob("*.json"))
    if not pages:
        pages=[p for origin,p in engine.archive_by_origin.items() if origin.startswith("relay_history_raw/")]
    delivered=[];rejected=[];seen=set()
    for path in sorted(pages):
        rows=read_json(path)
        if not isinstance(rows,list):
            continue
        origin=next((o for o,p in engine.archive_by_origin.items() if p==path),None) if not path.is_relative_to(engine.legacy) else str(path.relative_to(engine.legacy))
        relay=origin.split('/')[-1].split('_')[0]
        if relay not in RELAYS:
            continue
        if path.is_relative_to(engine.legacy):
            evidence=engine.store.archive(path,RELAYS[relay],"GET /relay/v1/data/bidtraces/proposer_payload_delivered; cached paginated response")
        else:
            evidence=str(path.relative_to(ROOT))
        for row in rows:
            n=int(row.get("block_number",0))
            if not FIRST<=n<=LAST:
                continue
            key=(relay,row['block_hash'],row['slot'],row['value'])
            if key in seen:
                continue
            seen.add(key)
            hp=engine.block_source(n,"header")
            if not hp:
                rejected.append({"reason":"missing_header","block":n,"relay":relay});continue
            header=unwrap(read_json(hp))
            if header['hash'].lower()!=row['block_hash'].lower():
                rejected.append({"reason":"nonmatching_block_hash","block":n,"relay":relay,"record_hash":row['block_hash'],"header_hash":header['hash']});continue
            if int(row['slot'])!=(integer(header['timestamp'])-1606824023)//12:
                rejected.append({"reason":"slot_timestamp_mismatch","block":n,"relay":relay});continue
            if hp.is_relative_to(engine.legacy):
                header_source=engine.store.archive(hp,"Ethereum execution RPC","eth_getBlockByNumber; cached")
            else:
                header_source=str(hp.relative_to(ROOT))
            delivered.append({**row,"relay":relay,"block_number":n,"slot":int(row['slot']),"value_wei":str(row['value']),"value_ETH":str(Decimal(row['value'])/E),
                "timestamp_utc":datetime.fromtimestamp(integer(header['timestamp']),timezone.utc).isoformat(),"period":"pre-event baseline" if n<EVENT_FIRST else "event window",
                "relay_evidence":evidence,"header_evidence":header_source,"verification":"relay delivery matched to cached execution header; selected case blocks also freshly RPC-crosschecked"})
    # De-duplicate reports by block hash/slot. Relay count is never auction count.
    byblock=defaultdict(list)
    for row in delivered:
        byblock[row['block_number']].append(row)
    winners=[]
    for n,rows in sorted(byblock.items()):
        rows=sorted(rows,key=lambda r:(r['relay'],r['relay_evidence'],r['value_wei']))
        signatures={(r['value_wei'],r['proposer_pubkey'].lower(),r['proposer_fee_recipient'].lower()) for r in rows}
        if len(signatures)!=1:
            rejected.append({"reason":"conflicting_relay_delivery_fields","block":n,"records":rows});continue
        builder_keys=sorted({r['builder_pubkey'].lower() for r in rows})
        winners.append({**rows[0],"builder_pubkey":builder_keys[0] if len(builder_keys)==1 else None,"builder_pubkeys":builder_keys,
            "builder_identity_status":"unique observed key" if len(builder_keys)==1 else "multiple relay-specific keys; common builder identity unresolved",
            "relays":sorted({r['relay'] for r in rows}),"delivery_reports":len(rows)})
    pd.DataFrame([{**r,"relays":json.dumps(r['relays']),"builder_pubkeys":json.dumps(r['builder_pubkeys'])} for r in winners]).to_parquet(ROOT/"data/processed/auction_deliveries.parquet",index=False)
    winning_by_number={r['block_number']:r for r in winners}
    outcomes=[];payment_rows=[]
    for c in cases:
        n=c['block'];header,receipts,traces,paths=engine.block(n)
        win=winning_by_number.get(n)
        assert win is not None,"Selected arbitrage case requires a unique matched auction delivery"
        fee_recipient=header['miner'].lower();proposer=win['proposer_fee_recipient'].lower()
        native_in=native_out=fee_gas=0;payout=0;fee_funded_payout=0;payment_payers=set();fees=defaultdict(int)
        for h,receipt in receipts.items():
            for k,v in fee_parts(receipt,integer(header['baseFeePerGas'])).items():
                fees[k]+=v
            if receipt['from'].lower()==fee_recipient:
                fee_gas+=fee_parts(receipt,integer(header['baseFeePerGas']))['gas_wei']
            # Missing traces must never silently become zero native inflow/outflow.
            assert traces[h],f"Missing trace: {h}"
            flows=native_flows(traces[h])
            proposer_in_tx=0
            for f in flows:
                value=int(f['amount_raw'])
                if f['recipient']==fee_recipient and f['sender']!=fee_recipient:
                    native_in+=value
                if f['sender']==fee_recipient and f['recipient']!=fee_recipient:
                    native_out+=value
                # Builder payments may pass through a forwarding / SELFDESTRUCT
                # contract. Match the complete successful tree, not just a direct CALL.
                if f['recipient']==proposer:
                    payout+=value
                    proposer_in_tx+=value
                    payment_payers.add(receipt['from'].lower())
                    if receipt['from'].lower()==fee_recipient:
                        fee_funded_payout+=value
                    payment_rows.append({"case_id":c['case_id'],"block":n,"slot":win['slot'],"tx_hash":h,"trace_address":json.dumps(f['trace_address']),"sender":f['sender'],"payment_payer":receipt['from'].lower(),"payer_is_fee_recipient":receipt['from'].lower()==fee_recipient,"proposer_fee_recipient":proposer,"amount_wei":str(value),"evidence_path":paths['traces']})
            if proposer_in_tx:
                root_funding=sum(int(f['amount_raw']) for f in flows if f['sender']==receipt['from'].lower() and not f['trace_address'])
                assert root_funding==proposer_in_tx,"Forwarded payout requires exact observable payer funding"
        assert payout==int(win['value_wei']),"Delivered value does not equal observable proposer transfer"
        assert fees['gas_wei']==fees['burn_wei']+fees['priority_wei']
        actor=fee_parts(receipts[c['tx_hash']],integer(header['baseFeePerGas']))
        other_out=native_out-fee_funded_payout
        proxy=fees['priority_wei']+native_in-native_out-fee_gas
        out={"case_id":c['case_id'],"block":n,"slot":win['slot'],"block_hash":header['hash'],"timestamp_utc":win['timestamp_utc'],"relays":win['relays'],
            "builder_pubkey":win['builder_pubkey'],"proposer_pubkey":win['proposer_pubkey'],"builder_fee_recipient":fee_recipient,"proposer_fee_recipient":proposer,
            "delivered_value_wei":win['value_wei'],"onchain_proposer_payment_wei":str(payout),"proposer_payment_exact_match":True,
            "proposer_payment_payers":sorted(payment_payers),"fee_recipient_funded_proposer_wei":str(fee_funded_payout),"separate_payer_proposer_wei":str(payout-fee_funded_payout),
            "whole_block_priority_wei":str(fees['priority_wei']),"whole_block_native_receipts_wei":str(native_in),"whole_block_other_native_outflow_wei":str(other_out),"fee_recipient_own_gas_wei":str(fee_gas),
            "builder_execution_balance_margin_proxy_wei":str(proxy),"whole_block_base_burn_wei":str(fees['burn_wei']),
            "builder_margin_proxy_wei":str(proxy) if fee_funded_payout==payout else None,
            "builder_margin_status":"partial execution-ETH proxy" if fee_funded_payout==payout else "unresolved: proposer payer differs from fee recipient; common economic ownership not assumed",
            "selected_searcher_gross_after_pool_fees_ETH":c['gross_after_pool_fees_before_gas_and_builder_ETH'],"selected_searcher_retained_ETH":c['net_after_gas_and_builder_ETH'],
            "selected_searcher_direct_builder_wei":c['identified_builder_payment_wei'],"selected_searcher_priority_wei":str(actor['priority_wei']),"selected_searcher_burn_wei":str(actor['burn_wei']),
            "selected_searcher_tx_hash":c['tx_hash'],"relay_evidence":win['relay_evidence'],"evidence":paths,
            "limits":"Builder proxy is execution-ETH cash flow, not exact realized profit: excludes token positions, withdrawals, offchain costs and financing. Whole-block proposer payment cannot be causally allocated to this single searcher. Searcher pool fees are already embedded in gross observed swap surplus."}
        assert abs(Decimal(out['selected_searcher_gross_after_pool_fees_ETH'])-Decimal(out['selected_searcher_retained_ETH'])-(Decimal(out['selected_searcher_direct_builder_wei'])+Decimal(out['selected_searcher_priority_wei'])+Decimal(out['selected_searcher_burn_wei']))/E)<Decimal('1e-70')
        outcomes.append(out)
        save(ROOT/f"reports/case_studies/{c['case_id']}_auction.json",out)

    # Observable received submissions are not equivalent to all losing auction bids.
    tasks=[(c['case_id'],winning_by_number[c['block']]['slot'],name,base) for c in cases for name,base in RELAYS.items()]
    def fetch(task):
        case_id,slot,relay,base=task
        url=base+f"/relay/v1/data/bidtraces/builder_blocks_received?slot={slot}&limit=1000"
        doc,ref=engine.public.get(url)
        # Retry a documented server-side limit rejection using a distinct URL;
        # retain the original failed response as immutable evidence.
        if doc.get('http_status')==400 and 'limit' in str(doc.get('response','')).lower():
            url=base+f"/relay/v1/data/bidtraces/builder_blocks_received?slot={slot}&limit=500"
            doc,ref=engine.public.get(url)
        return task,doc,ref
    submissions=[];coverage=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        for task,doc,ref in executor.map(fetch,tasks):
            case_id,slot,relay,base=task
            response=doc.get('response');valid=isinstance(response,list) and doc.get('http_status')==200
            rows=response if valid else []
            requested_limit=500 if 'limit=500' in doc.get('url','') else 1000
            coverage.append({"case_id":case_id,"slot":slot,"relay":relay,"http_status":doc.get('http_status'),"error":doc.get('error'),"returned_rows":len(rows),"requested_limit":requested_limit,"cap_reached":len(rows)>=requested_limit,"evidence_path":ref,"meaning":"Only successful-verified submissions retained by this endpoint; [] is not proof of no historical bids."})
            for bid in rows:
                if int(bid.get('slot',-1))!=slot:
                    continue
                win=next(o for o in outcomes if o['case_id']==case_id)
                submissions.append({**bid,"case_id":case_id,"relay":relay,"slot":slot,"value_ETH":str(Decimal(bid['value'])/E),"delivered_block_hash_match":bid['block_hash'].lower()==win['block_hash'].lower(),
                    "classification":"delivered payload candidate" if bid['block_hash'].lower()==win['block_hash'].lower() else "non-delivered submission (may be revision or losing bid)","evidence_path":ref})
    save(ROOT/"data/processed/auction_outcomes.json",outcomes)
    save(ROOT/"data/processed/auction_submissions.json",submissions)
    save(ROOT/"data/processed/auction_submission_coverage.json",coverage)
    save(ROOT/"data/processed/auction_rejected_records.json",sorted(rejected,key=lambda r:(r['block'],r['reason'],r.get('relay',''))))
    pd.DataFrame(payment_rows).to_parquet(ROOT/"data/processed/proposer_payments.parquet",index=False)
    save(ROOT/"data/processed/auction_coverage.json",{"raw_delivery_reports":len(delivered),"unique_nonconflicting_delivered_blocks":len(winners),"window_blocks":LAST-FIRST+1,"baseline_blocks":EVENT_FIRST-FIRST,"event_blocks":LAST-EVENT_FIRST+1,"baseline_observed_deliveries":sum(r['period']=='pre-event baseline' for r in winners),"event_observed_deliveries":sum(r['period']=='event window' for r in winners),"selected_outcomes_onchain_reconciled":len(outcomes),"submission_rows_observed":len(submissions),"historical_submission_coverage_limit":"Only queried relays / slots / retained endpoint data; counts do not identify all competitors or pre-selection bid timing."})
    engine.store.save();engine.public.write_index()
    print(f"Matched {len(winners)} unique delivered blocks; three exact on-chain proposer payments; {len(submissions)} observable submissions")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--legacy');args=p.parse_args();run(args.online,args.legacy)
