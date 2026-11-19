"""Match every retained relay delivery to actual block fees and native transfers."""
import json,csv
from collections import Counter,defaultdict
from decimal import Decimal
import pandas as pd
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows
from src.decoding.events import integer

def run():
    p=ROOT/'data/processed/mev_full_window';units=json.loads((p/'strategy_accounts_v4.json').read_text());links=defaultdict(set)
    for u in units:
        for r in u['transaction_evidence']:links[r['block']].add(u['unit_id'])
    deliveries=pd.read_parquet(ROOT/'data/processed/auction_deliveries.parquet').to_dict('records');engine=Reconstruction(ROOT.parent/'research',False);rows=[];payouts=[];E=Decimal(10)**18
    for i,w in enumerate(deliveries,1):
        n=int(w['block_number']);head,rs,tr,paths=engine.block(n);fee=head['miner'].lower();proposer=w['proposer_fee_recipient'].lower();expected=int(w['value_wei']);burn=priority=fee_gas=nin=nout=0;proposer_transfers=[]
        for h,rc in rs.items():
            gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);base=integer(rc['gasUsed'])*integer(head['baseFeePerGas']);burn+=base;priority+=gas-base
            if rc['from'].lower()==fee:fee_gas+=gas
            flows=native_flows(tr[h])
            for f in flows:
                raw=int(f['amount_raw'])
                if f['recipient']==fee and f['sender']!=fee:nin+=raw
                if f['sender']==fee and f['recipient']!=fee:nout+=raw
                if f['recipient']==proposer and f['sender']!=proposer:
                    proposer_transfers.append({'block':n,'tx_hash':h,'etherscan':'https://etherscan.io/tx/'+h,'root_sender':rc['from'].lower(),'sender':f['sender'],'recipient':proposer,'amount_raw':str(raw),'trace_address':f['trace_address'],'fee_recipient_is_root_payer':rc['from'].lower()==fee,'evidence':paths['traces']})
        paid=sum(int(f['amount_raw']) for f in proposer_transfers);funded=sum(int(f['amount_raw']) for f in proposer_transfers if f['fee_recipient_is_root_payer']);exact=paid==expected;proxy=priority+nin-nout-fee_gas
        rows.append({'block':n,'slot':int(w['slot']),'block_hash':head['hash'],'relay_expected_proposer_ETH':str(Decimal(expected)/E),'observed_proposer_incoming_ETH':str(Decimal(paid)/E),'proposer_payment_exact_match':exact,'fee_recipient_root_funded_proposer_ETH':str(Decimal(funded)/E),'proposer':proposer,'fee_recipient':fee,'builder_pubkey':w['builder_pubkey'],'proposer_pubkey':w['proposer_pubkey'],'priority_ETH':str(Decimal(priority)/E),'burn_ETH':str(Decimal(burn)/E),'fee_recipient_native_in_ETH':str(Decimal(nin)/E),'fee_recipient_native_out_ETH':str(Decimal(nout)/E),'fee_recipient_own_gas_ETH':str(Decimal(fee_gas)/E),'fee_recipient_native_balance_change_proxy_ETH':str(Decimal(proxy)/E),'builder_margin_proxy_ETH':str(Decimal(proxy)/E) if exact and funded==expected else None,'connected_strategy_units':sorted(links[n]),'evidence':paths,'interpretation':'Whole-block native execution balance proxy, excluding ERC20 receipts, withdrawals and offchain settlement. A separately funded proposer payout is not deducted again from this fee-recipient address. Searcher payment and proposer payout are sequential redistributions, not additive losses.'});payouts.extend(proposer_transfers);engine.cache.clear()
        if i%200==0:print('full auctions',i,'/',len(deliveries),flush=True)
    summary={'unique_observed_delivery_blocks':len(rows),'onchain_proposer_amount_matches':sum(r['proposer_payment_exact_match'] for r in rows),'amount_mismatches':[r['block'] for r in rows if not r['proposer_payment_exact_match']],'delivery_blocks_linked_to_strategy_units':sum(bool(r['connected_strategy_units']) for r in rows),'units_with_observed_delivery':len({u for r in rows for u in r['connected_strategy_units']}),'all_window_blocks':3311,'nonobserved_deliveries_are_not_zero':True,'builder_margin_exact_firm_profit':False};dest=p/'full_auction_allocation.json';dest.write_text(json.dumps({'summary':summary,'rows':rows,'proposer_transfers':payouts},indent=2));flat=[{**r,'connected_strategy_units':json.dumps(r['connected_strategy_units']),'evidence':json.dumps(r['evidence'])} for r in rows]
    with (ROOT/'reports/mev_expansion/全窗口拍卖与实际付款.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
