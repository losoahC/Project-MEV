"""Explorer-linked observed transfer ledger; cash movements are separate from profit.

All successful native traces and ERC20 logs are exported once per transaction.
WETH mint/burn accounting and ERC6909 claims have explicit separate event types.
"""
import csv,json
from collections import defaultdict,Counter
from decimal import Decimal
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from eth_abi import decode
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows,DEPOSIT,WITHDRAWAL
from src.arbitrage.complete_surplus_ledger import claim_event,ZERO
from src.arbitrage.value_candidates import book_from_archive
from src.decoding.events import transfer,integer,WETH

def receipt_movements(receipt,traces):
    # None explicitly requests log-only extraction; an empty supplied trace tree
    # still fails validation rather than pretending native movements were absent.
    for f in (native_flows(traces) if traces is not None else []):
        yield {**f,'event_type':'native_ETH_transfer','reference':json.dumps(f['trace_address']),'asset':f['token']}
    for l in receipt['logs']:
        f=transfer(l)
        if f:yield {**f,'event_type':'ERC20_Transfer','reference':str(f['log_index']),'asset':f['token']}
        ts=l.get('topics',[])
        if len(ts)==4 and ts[0].lower()=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' and l['data']=='0x':
            yield {'asset':'erc721:'+l['address'].lower()+':'+str(integer(ts[3])),'sender':'0x'+ts[1][-40:].lower(),'recipient':'0x'+ts[2][-40:].lower(),'amount_raw':'1','event_type':'ERC721_ownership_transfer_not_fungible_profit','reference':str(integer(l['logIndex']))}
        if len(ts)==4 and ts[0].lower() in ['0x'+Web3.keccak(text='TransferSingle(address,address,address,uint256,uint256)').hex().removeprefix('0x'),'0x'+Web3.keccak(text='TransferBatch(address,address,address,uint256[],uint256[])').hex().removeprefix('0x')]:
            single=ts[0].lower()=='0x'+Web3.keccak(text='TransferSingle(address,address,address,uint256,uint256)').hex().removeprefix('0x');values=decode(['uint256','uint256'] if single else ['uint256[]','uint256[]'],bytes.fromhex(l['data'][2:]));pairs=[values] if single else list(zip(*values))
            for token_id,amount in pairs:yield {'asset':'erc1155:'+l['address'].lower()+':'+str(token_id),'sender':'0x'+ts[2][-40:].lower(),'recipient':'0x'+ts[3][-40:].lower(),'amount_raw':str(amount),'event_type':'ERC1155_balance_transfer_not_priced_profit','reference':str(integer(l['logIndex']))}
        if l['address'].lower()==WETH and len(ts)==2 and ts[0].lower() in [DEPOSIT,WITHDRAWAL]:
            a='0x'+ts[1][-40:].lower();deposit=ts[0].lower()==DEPOSIT
            yield {'asset':WETH,'sender':ZERO if deposit else a,'recipient':a if deposit else ZERO,'amount_raw':str(integer(l['data'])),'event_type':'WETH_Deposit_mint' if deposit else 'WETH_Withdrawal_burn','reference':str(integer(l['logIndex']))}
        c=claim_event(l)
        if c:yield {'asset':'erc6909:'+c['manager']+':'+c['currency'],'sender':c['sender'],'recipient':c['recipient'],'amount_raw':c['amount_raw'],'event_type':'ERC6909_claim_transfer_not_cash','reference':str(c['log_index'])}

def run():
    p=ROOT/'data/processed/mev_full_window';out=ROOT/'reports/mev_expansion';units=json.loads((p/'strategy_units.json').read_text());tx_units={t['tx_hash']:u['unit_id'] for u in units for t in u['txs']};jobs=defaultdict(set)
    for u in units:
        for t in u['txs']:jobs[t['block']].add(t['tx_hash'])
    for r in json.loads((p/'order_filler_equity.json').read_text())['rows']:jobs[r['block']].add(r['tx_hash'])
    for line in (p/'named_full_window_ledger.jsonl').open():
        r=json.loads(line);jobs[r['block']].add(r['tx_hash'])
    book=book_from_archive();metadata=dict(book.registry)
    for row in json.loads((ROOT/'data/processed/completion_secondary_prices.json').read_text())['rows']:
        metadata.setdefault(row['address'],{'decimals':row['token_metadata']['decimals'],'symbol':row.get('quote',{}).get('symbol','')})
    engine=Reconstruction(ROOT.parent/'research',False);counts=Counter();failures=[]
    fields=['tx_hash','etherscan_transaction','etherscan_internal_transfers','etherscan_logs','block','transaction_index','timestamp_America_New_York','unit_id','event_type','sender','recipient','asset_contract','symbol','amount_raw','decimals','amount','log_index_or_trace_address','raw_evidence']
    afields=['tx_hash','etherscan_transaction','block','transaction_index','timestamp_America_New_York','unit_id','address','asset_contract','symbol','decimals','received_raw','sent_raw','net_raw','received','sent','net','cash_or_claim','raw_evidence']
    with (out/'逐笔真实转账与Etherscan链接.csv').open('w') as f,(out/'逐交易逐地址实际收支.csv').open('w') as a:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();aw=csv.DictWriter(a,fieldnames=afields);aw.writeheader()
        for n,hashes in sorted(jobs.items()):
            head,rs,tr,paths=engine.block(n)
            for h in sorted(hashes,key=lambda h:integer(rs[h]['transactionIndex'])):
                rc=rs[h];counts['transactions']+=1;url='https://etherscan.io/tx/'+h;common={'tx_hash':h,'etherscan_transaction':url,'block':n,'transaction_index':integer(rc['transactionIndex']),'timestamp_America_New_York':datetime.fromtimestamp(integer(head['timestamp']),timezone.utc).astimezone(ZoneInfo('America/New_York')).isoformat(),'unit_id':tx_units.get(h,'named_address_context_or_order')};account=defaultdict(lambda:[0,0])
                try:movements=list(receipt_movements(rc,tr[h]))
                except Exception as ex:failures.append({'tx_hash':h,'error':repr(ex)});continue
                gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);burn=integer(rc['gasUsed'])*integer(head['baseFeePerGas'])
                movements += [{'asset':'native:eth','sender':rc['from'].lower(),'recipient':'protocol:base_fee_burn','amount_raw':str(burn),'event_type':'gas_base_fee_burn','reference':'receipt gasUsed × block baseFeePerGas'},{'asset':'native:eth','sender':rc['from'].lower(),'recipient':head['miner'].lower(),'amount_raw':str(gas-burn),'event_type':'gas_priority_fee','reference':'receipt gasUsed × (effectiveGasPrice − baseFeePerGas)'}]
                for m in movements:
                    asset=m['asset'];meta=metadata.get(asset,{'decimals':18,'symbol':'ETH'} if asset=='native:eth' else {'decimals':0,'symbol':'NFT_units'} if asset.startswith(('erc721:','erc1155:')) else {});decimals=meta.get('decimals');symbol=meta.get('symbol','')
                    if asset.startswith('erc6909:'):
                        base=asset.split(':')[-1];meta=metadata.get(base,{'decimals':18,'symbol':'ETH'} if base=='eth' else {});decimals=meta.get('decimals');symbol='claim:'+meta.get('symbol','')
                    raw=int(m['amount_raw']);source=paths['traces'] if m['event_type']=='native_ETH_transfer' else paths['receipts'];row={**common,'etherscan_internal_transfers':url+'#internal','etherscan_logs':url+'#eventlog','event_type':m['event_type'],'sender':m['sender'],'recipient':m['recipient'],'asset_contract':asset,'symbol':symbol,'amount_raw':str(raw),'decimals':decimals,'amount':str(Decimal(raw)/Decimal(10)**decimals) if decimals is not None else '', 'log_index_or_trace_address':m['reference'],'raw_evidence':source};w.writerow(row);counts['movement_rows']+=1;counts[m['event_type']]+=1
                    account[(m['sender'],asset)][1]+=raw;account[(m['recipient'],asset)][0]+=raw
                for (address,asset),(received,sent) in sorted(account.items()):
                    meta=metadata.get(asset,{'decimals':18,'symbol':'ETH'} if asset=='native:eth' else {});d=meta.get('decimals');scale=Decimal(10)**d if d is not None else None
                    aw.writerow({**common,'address':address,'asset_contract':asset,'symbol':meta.get('symbol',''),'decimals':d,'received_raw':str(received),'sent_raw':str(sent),'net_raw':str(received-sent),'received':str(Decimal(received)/scale) if scale else '', 'sent':str(Decimal(sent)/scale) if scale else '', 'net':str(Decimal(received-sent)/scale) if scale else '', 'cash_or_claim':'V4 currency claim; not liquid ETH' if asset.startswith('erc6909:') else 'observed token/native movement, not profit','raw_evidence':json.dumps(paths)});counts['address_asset_rows']+=1
            engine.cache.clear();counts['blocks']+=1
            if counts['blocks']%100==0:print('transfer audit',dict(counts),flush=True)
    summary={**counts,'failures':failures,'scope':'Disjoint strategy-unit transactions, nine orders, and complete-window activity touching the 13 Bitquery-named Ethereum addresses. Every observed transfer exported once per tx/event; intermediary receipts are not summed as profit.','explorer_role':'Links permit manual review. Automated amounts are decoded from archived receipts and complete successful traces; Etherscan page availability is not falsely claimed as independently verified.'};(p/'transfer_audit_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
