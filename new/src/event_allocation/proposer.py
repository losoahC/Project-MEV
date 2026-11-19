"""Observed proposer redistribution without claiming mixed-block event attribution."""
import json,csv,gzip,hashlib
from decimal import Decimal
from collections import defaultdict
from src.event_allocation.config import ROOT,OUT,REPORT,START,END
from src.event_allocation.quotes import Quotes
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows
from src.decoding.events import integer

def prepare_ethereum_fee_vectors():
    from src.event_allocation.allocate import Pools,target_allocation,subsequent_allocation
    pools=Pools();fees=defaultdict(lambda:defaultdict(int))
    with gzip.open(OUT/'ethereum_journal.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);rows,errors=target_allocation(r,pools) if r['association']=='target' else subsequent_allocation(r,pools)[:2];assert not errors
            for role,address,v in rows:
                if role=='block_recipient_receipts':
                    for a,raw in v.items():fees[r['block']][a]+=raw
    data={str(k):{a:str(v) for a,v in row.items() if v} for k,row in fees.items()};(OUT/'block_primary_fee_vectors.json').write_text(json.dumps(data,indent=2))

def run():
    p=ROOT/'data/processed/mev_full_window';d=json.loads((p/'full_auction_allocation.json').read_text());timestamps={r['block']:r['timestamp'] for r in json.loads((p/'blocks.json').read_text())};fees=json.loads((OUT/'block_primary_fee_vectors.json').read_text());q=Quotes();rows=[];transfer_rows=[];seen=set();paid=Decimal(0);budget=Decimal(0)
    for r in d['rows']:
        ts=timestamps[r['block']]
        if not START<=ts<END:continue
        vector=fees.get(str(r['block']),{});mark=q.vector(vector,ts);payout=Decimal(r['observed_proposer_incoming_ETH']);pvalue=q.value('native:eth',payout*10**18,ts);paid+=payout;budget+=pvalue or 0
        rows.append({'block':r['block'],'timestamp':ts,'block_hash':r['block_hash'],'fee_recipient':r['fee_recipient'],'proposer':r['proposer'],'builder_pubkey':r['builder_pubkey'],'whole_block_priority_ETH':r['priority_ETH'],'whole_block_native_receipts_excluding_priority_ETH':r['fee_recipient_native_in_ETH'],'whole_block_fee_recipient_native_out_ETH':r['fee_recipient_native_out_ETH'],'actual_proposer_payment_ETH':str(payout),'actual_proposer_payment_USD_same_frozen_mark':str(pvalue) if pvalue is not None else None,'relay_payment_exact_match':r['proposer_payment_exact_match'],'fee_recipient_root_funded_actual_payout_ETH':r['fee_recipient_root_funded_proposer_ETH'],'associated_primary_receipt_vector_raw':vector,'associated_primary_receipt_mark':mark,'incident_causal_payment_identified_ETH':None,'incident_causal_payment_lower_ETH':'0','incident_causal_payment_upper_ETH':str(payout),'primary_additive_amount_USD':'0','funding_attribution':'Observed whole-block payment; causal incident share is not identified. Both incident-associated and other transactions, existing balances and other funding can contribute. No proportional allocation is asserted. Interval [0, observed payment] describes identification uncertainty, not a measured zero.','evidence':r['evidence']})
    for r in rows:r['secondary_observation_status']='relay_matched_and_onchain_trace_confirmed'
    validblocks={r['block'] for r in rows};allblocks={n for n,ts in timestamps.items() if START<=ts<END};unmatched=[];engine=Reconstruction(ROOT.parent/'research',False)
    for n in sorted(allblocks-validblocks):
        h,rs,trs,paths=engine.block(n);recipient=h['miner'].lower();incoming=outgoing=priority=burn=own_gas=0
        for tx,rc in rs.items():
            gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);b=integer(rc['gasUsed'])*integer(h['baseFeePerGas']);priority+=gas-b;burn+=b
            if rc['from'].lower()==recipient:own_gas+=gas
            for flow in native_flows(trs[tx]):
                raw=int(flow['amount_raw']);incoming+=raw*(flow['recipient']==recipient);outgoing+=raw*(flow['sender']==recipient)
        unmatched.append({'block':n,'timestamp':timestamps[n],'block_hash':h['hash'],'fee_recipient':recipient,'proposer':None,'builder_pubkey':None,'whole_block_priority_ETH':str(Decimal(priority)/10**18),'whole_block_native_receipts_excluding_priority_ETH':str(Decimal(incoming)/10**18),'whole_block_fee_recipient_native_out_ETH':str(Decimal(outgoing)/10**18),'actual_proposer_payment_ETH':None,'actual_proposer_payment_USD_same_frozen_mark':None,'relay_payment_exact_match':None,'fee_recipient_root_funded_actual_payout_ETH':None,'associated_primary_receipt_vector_raw':fees.get(str(n),{}),'associated_primary_receipt_mark':q.vector(fees.get(str(n),{}),timestamps[n]),'incident_causal_payment_identified_ETH':None,'incident_causal_payment_lower_ETH':None,'incident_causal_payment_upper_ETH':None,'primary_additive_amount_USD':'0','funding_attribution':'No matched delivered relay bid in the archived relay census. Actual block recipient and whole-block native flows remain recorded. No independently identified proposer auction payout or zero payout is imputed; priority receipts already belong to the primary block-recipient category when selected.','secondary_observation_status':'no_matched_delivered_relay_record','evidence':paths});engine.cache.clear()
    for r in d['proposer_transfers']:
        if r['block'] not in validblocks:continue
        key=(r['block'],r['tx_hash'],tuple(r['trace_address']),r['recipient']);assert key not in seen;seen.add(key);transfer_rows.append(r)
    byblock=defaultdict(int)
    for r in transfer_rows:byblock[r['block']]+=int(r['amount_raw'])
    assert all(Decimal(byblock[r['block']])/10**18==Decimal(r['actual_proposer_payment_ETH']) for r in rows)
    summary={'total_common_window_blocks':len(allblocks),'blocks_without_matched_delivered_relay_record':len(unmatched),'matched_blocks_in_common_window':len(rows),'actual_payment_trace_rows':len(transfer_rows),'all_trace_amounts_match_block_payments':True,'all_relay_amounts_exact_match':all(r['relay_payment_exact_match'] for r in rows),'observed_whole_block_proposer_payments_ETH':str(paid),'observed_whole_block_proposer_payments_USD_same_frozen_marks':str(budget),'additional_primary_extraction_USD':'0','all_observed_payouts_causally_from_incident':False,'event_share_point_estimate_available':False,'primary_fee_vector_sha256':hashlib.sha256((OUT/'block_primary_fee_vectors.json').read_bytes()).hexdigest(),'lower_and_upper_are_identification_bounds_not_profit_estimates':True};rows.extend(unmatched);rows.sort(key=lambda r:r['block'])
    (OUT/'proposer_secondary_allocation.json').write_text(json.dumps({'summary':summary,'blocks':rows,'actual_payment_traces':transfer_rows},indent=2));fields=[k for k,v in rows[0].items() if not isinstance(v,(dict,list))]
    with (REPORT/'proposer_secondary_allocation.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    with (REPORT/'proposer_payment_traces.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(transfer_rows[0]));w.writeheader();w.writerows(transfer_rows)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
