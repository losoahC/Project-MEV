"""Identify conservative same-transaction WETH unwrap payments to block coinbase.
The payment helper is NOT merged into the bot's operational boundary.
"""
from collections import defaultdict
from src.arbitrage.accounting import token_net,native_flows,WITHDRAWAL
from src.decoding.events import transfer,WETH,integer

def fee_paths(receipt,traces,boundary,fee_recipient,pool_addresses):
    fee_recipient=fee_recipient.lower();by=defaultdict(list);result=[];flows=native_flows(traces)
    for l in receipt['logs']:
        f=transfer(l)
        if f and f['token']==WETH and f['sender'] in boundary and f['recipient'] not in boundary and f['recipient'] not in pool_addresses:by[f['recipient']].append(f)
    for helper,transfers in by.items():
        amount=sum(int(f['amount_raw']) for f in transfers)
        if helper==fee_recipient:
            result.append({'kind':'direct_WETH_to_fee_recipient','helper':helper,'fee_recipient':fee_recipient,'amount_wei':str(amount),'transfer_logs':transfers});continue
        if helper==WETH:continue
        withdrawals=[l for l in receipt['logs'] if l['address'].lower()==WETH and len(l.get('topics',[]))==2 and l['topics'][0].lower()==WITHDRAWAL and '0x'+l['topics'][1][-40:].lower()==helper]
        if sum(integer(l['data']) for l in withdrawals)!=amount:continue
        # Canonical wrapper synthetic burn must fully offset this helper's inflows.
        if token_net(receipt,{helper}):continue
        incoming=[f for f in flows if f['recipient']==helper and f['sender']!=helper];outgoing=[f for f in flows if f['sender']==helper and f['recipient']!=helper]
        if not incoming or not outgoing:continue
        if any(f['sender']!=WETH for f in incoming) or any(f['recipient']!=fee_recipient for f in outgoing):continue
        if sum(int(f['amount_raw']) for f in incoming)!=amount or sum(int(f['amount_raw']) for f in outgoing)!=amount:continue
        result.append({'kind':'WETH_unwrap_helper_to_fee_recipient','helper':helper,'fee_recipient':fee_recipient,'amount_wei':str(amount),'transfer_logs':transfers,'withdrawal_log_indices':[integer(l['logIndex']) for l in withdrawals],'wrapper_to_helper_native_traces':incoming,'helper_to_fee_recipient_native_traces':outgoing,'helper_terminal_asset_change_zero':True,'common_ownership_inferred':False})
    return result
