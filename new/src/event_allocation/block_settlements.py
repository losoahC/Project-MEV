"""Every native block-recipient flow, including actual non-proposer recipients.
This is observed whole-block secondary settlement, not another incident loss.
"""
import json,gzip,csv
from collections import defaultdict,Counter
from decimal import Decimal
from src.event_allocation.config import ROOT,OUT,REPORT,START,END
from src.event_allocation.quotes import Quotes
from src.ingestion.evidence import read_json,unwrap
from src.arbitrage.accounting import native_flows
from src.decoding.events import integer

def run():
    blocks=[r for r in json.loads((ROOT/'data/processed/mev_full_window/blocks.json').read_text()) if START<=r['timestamp']<END];secondary=json.loads((OUT/'proposer_secondary_allocation.json').read_text());observed={r['block']:r for r in secondary['blocks']};terminals={(r['tx_hash'],tuple(r['trace_address'])):r for r in secondary['actual_payment_traces']};payout_txs={r['tx_hash'] for r in secondary['actual_payment_traces']};old={r['block']:r for r in json.loads((ROOT/'data/processed/mev_full_window/full_auction_allocation.json').read_text())['rows']};primary=set();operators=set();byblock=defaultdict(set);boundaries=defaultdict(set)
    with gzip.open(OUT/'ethereum_journal.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line)
            if r['association'] in ['target','after_prior_target','failed_attempt_after_target']:primary.add(r['tx_hash']);operators.add(r['sender']);byblock[r['block']].add(r['sender'])
    for u in json.loads((ROOT/'data/processed/mev_full_window/strategy_accounts_v4.json').read_text()):
        if u['sender'] in operators:
            for a in u['boundary']:boundaries[a].add(u['sender'])
    for a in operators:boundaries[a].add(a)
    q=Quotes();fields=['block','timestamp','tx_hash','sender','recipient','amount_raw','ETH','USD','trace_address','category','in_primary_transaction','linked_operating_addresses','linked_operator_traded_in_same_block','evidence','etherscan'];counts=Counter();recipients=defaultdict(lambda:{'raw':0,'outside_primary_raw':0,'usd':Decimal(0),'outside_primary_usd':Decimal(0),'rows':0,'classes':Counter()});blockrows=[];total_extra=Decimal(0);outpath=REPORT/'whole_block_native_settlements.csv.gz';seen=set()
    with gzip.open(outpath,'wt') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for i,b in enumerate(blocks,1):
            n=b['block'];paths=b['evidence'];head=unwrap(read_json(ROOT/paths['header']));assert head['hash']==b['block_hash'];fee=head['miner'].lower();traces=unwrap(read_json(ROOT/paths['traces']));groups=defaultdict(list);valid_hashes={(x['hash'] if isinstance(x,dict) else x).lower() for x in head['transactions']}
            for t in traces:
                h=t.get('transactionHash','').lower()
                if h:assert h in valid_hashes;groups[h].append(t)
            incoming=outgoing=0;paid_terminal=0
            for h,ts in groups.items():
                involved=h in payout_txs or any(fee in [(t.get('action') or {}).get(k,'').lower() for k in ['from','to','address','refundAddress']]+[(t.get('result') or {}).get('address','').lower()] for t in ts)
                if not involved:continue
                for flow in native_flows(ts):
                    sender,recipient=flow['sender'],flow['recipient'];raw=int(flow['amount_raw']);key=(h,tuple(flow['trace_address']));terminal=key in terminals
                    if sender!=fee and recipient==fee:incoming+=raw
                    if sender==fee and recipient!=fee:outgoing+=raw
                    if terminal:assert raw==int(terminals[key]['amount_raw']);paid_terminal+=raw
                    if sender!=fee and recipient!=fee and h not in payout_txs:continue
                    assert key not in seen;seen.add(key);linked=sorted(boundaries.get(recipient,set()));outside=h not in primary;cat='actual_proposer_terminal_payment' if terminal else 'block_recipient_out_to_operating_address_or_boundary' if sender==fee and recipient!=fee and linked else 'block_recipient_other_native_out' if sender==fee and recipient!=fee else 'block_recipient_native_in' if recipient==fee and sender!=fee else 'payout_transaction_other_native_context';v=q.value('native:eth',raw,b['timestamp']);assert v is not None;counts[cat]+=1;counts['native_transfer_rows']+=1
                    w.writerow({'block':n,'timestamp':b['timestamp'],'tx_hash':h,'sender':sender,'recipient':recipient,'amount_raw':str(raw),'ETH':str(Decimal(raw)/10**18),'USD':str(v),'trace_address':json.dumps(flow['trace_address']),'category':cat,'in_primary_transaction':not outside,'linked_operating_addresses':json.dumps(linked),'linked_operator_traded_in_same_block':bool(set(linked)&byblock[n]),'evidence':paths['traces'],'etherscan':'https://etherscan.io/tx/'+h})
                    if sender==fee and recipient!=fee:
                        rr=recipients[recipient];rr['raw']+=raw;rr['usd']+=v;rr['rows']+=1;rr['classes'][cat]+=1
                        if outside:rr['outside_primary_raw']+=raw;rr['outside_primary_usd']+=v
                        if linked and outside:total_extra+=v
            ref=observed[n];assert Decimal(incoming-outgoing)/10**18==Decimal(ref['whole_block_native_receipts_excluding_priority_ETH'])-Decimal(ref['whole_block_fee_recipient_native_out_ETH']),(n,incoming,outgoing)
            if ref['actual_proposer_payment_ETH'] is not None:assert Decimal(paid_terminal)/10**18==Decimal(ref['actual_proposer_payment_ETH'])
            if n in old:own_gas=int(Decimal(old[n]['fee_recipient_own_gas_ETH'])*10**18)
            else:
                receipts=unwrap(read_json(ROOT/paths['receipts']));own_gas=sum(integer(r['gasUsed'])*integer(r['effectiveGasPrice'])+integer(r.get('blobGasUsed',0))*integer(r.get('blobGasPrice',0)) for r in receipts if r['from'].lower()==fee)
            priority=int(Decimal(ref['whole_block_priority_ETH'])*10**18);withdrawals=sum(integer(r['amount'])*10**9 for r in head.get('withdrawals',[]) if r['address'].lower()==fee);proxy=priority+incoming-outgoing-own_gas;blockrows.append({'block':n,'timestamp':b['timestamp'],'fee_recipient':fee,'priority_wei':str(priority),'native_in_wei':str(incoming),'native_out_wei':str(outgoing),'own_execution_and_known_blob_gas_wei':str(own_gas),'consensus_withdrawals_to_fee_recipient_wei':str(withdrawals),'execution_native_balance_change_proxy_wei':str(proxy),'execution_native_balance_change_proxy_ETH':str(Decimal(proxy)/10**18),'all_native_in_out_and_proposer_traces_reconciled':True,'primary_additive_extraction_USD':'0','interpretation':'Actual native flow plus priority minus own gas. Token holdings, consensus income and offchain accounts are separate. Recipient linkage does not prove a refund, common control or event causation.','evidence':paths})
            if i%250==0:print('Whole-block native settlements',i,'/',len(blocks),'transfers',counts['native_transfer_rows'],flush=True)
    receiver_rows=[{'recipient':a,'actual_received_ETH':str(Decimal(r['raw'])/10**18),'actual_received_USD':str(r['usd']),'received_outside_primary_transactions_ETH':str(Decimal(r['outside_primary_raw'])/10**18),'received_outside_primary_transactions_USD':str(r['outside_primary_usd']),'transfer_rows':r['rows'],'classes':dict(r['classes']),'linked_operating_addresses':sorted(boundaries.get(a,set())),'ultimate_owner_and_event_share_established':False} for a,r in recipients.items()];receiver_rows.sort(key=lambda r:Decimal(r['actual_received_ETH']),reverse=True);summary={'common_window_blocks':len(blocks),**counts,'all_block_native_flows_and_matched_proposer_payouts_reconciled':True,'observed_block_recipient_payments_to_known_operating_addresses_or_boundaries_outside_primary_USD':str(total_extra),'these_payments_all_proven_incident_refunds':False,'additional_primary_extraction_USD':'0','whole_block_execution_native_balance_change_proxy_ETH':str(sum((Decimal(r['execution_native_balance_change_proxy_ETH']) for r in blockrows),Decimal(0))),'not_exact_builder_firm_profit':True};(OUT/'whole_block_native_settlements.json').write_text(json.dumps({'summary':summary,'blocks':blockrows,'actual_outgoing_recipients':receiver_rows},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
