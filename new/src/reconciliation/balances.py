"""Observed ETH/WETH/USDT/USDC snapshot ledger. Window coverage is tested, never assumed closed."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal
import json
import pandas as pd
from src.ingestion.public_evidence import PublicEvidence
from src.ingestion.evidence import read_json
from src.decoding.events import WETH,USDT,USDC
from src.visualization.common import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.reconciliation.pricebook import PriceBook

FIRST,LAST=26300640,26303950
ASSETS={'native:eth':('ETH',18),WETH:('WETH',18),USDT:('USDT',6),USDC:('USDC',6)}


def reconcile(opening,inflow,outflow,gas,closing,wrapper_adjustment=0):
    predicted=opening+inflow-outflow-gas+wrapper_adjustment
    return {'predicted_closing_raw':str(predicted),'observed_closing_raw':str(closing),'unexplained_change_raw':str(closing-predicted),'balanced':closing==predicted}


def run(online=False,legacy=None):
    public=PublicEvidence(ROOT,online);wallets=read_json(ROOT/'data/processed/wallet_registry.json');addresses={w['address'] for w in wallets}
    engine=Reconstruction(legacy or ROOT.parent/'research',online);book=PriceBook(engine)
    book.binance_spot('USDC',('2026-10-30',))
    headers={}
    for n in [FIRST-1,LAST]:
        h,p=public.rpc('eth_getBlockByNumber',[hex(n),False]);headers[n]={'header':h,'evidence':p}
    ts=int(headers[LAST]['header']['timestamp'],16)
    jobs=[(w,token,n) for w in wallets for token in ASSETS for n in [FIRST-1,LAST]]
    def fetch(job):
        w,token,n=job;address=w['address']
        if token=='native:eth':value,path=public.rpc('eth_getBalance',[address,hex(n)])
        else:value,path=public.rpc('eth_call',[{'to':token,'data':'0x70a08231'+address[2:].zfill(64)},hex(n)])
        return (address,token,n),{'raw':str(int(value,16)),'evidence':path}
    snapshots={}
    with ThreadPoolExecutor(max_workers=4) as e:
        for i,(key,val) in enumerate(e.map(fetch,jobs),1):
            snapshots[key]=val
            if i%32==0:print(f'Balance snapshots {i}/{len(jobs)}',flush=True)
    def frozen(job):
        w,token=job
        # Derive the exact historical view-function selector from its signature.
        from web3 import Web3
        sig='getBlackListStatus(address)' if token==USDT else 'isBlacklisted(address)'
        selector='0x'+Web3.keccak(text=sig).hex().removeprefix('0x')[:8]
        value,path=public.rpc('eth_call',[{'to':token,'data':selector+w['address'][2:].zfill(64)},hex(LAST)])
        assert int(value,16) in (0,1)
        return (w['address'],token),{'blacklisted':bool(int(value,16)),'evidence':path,'method':sig}
    with ThreadPoolExecutor(max_workers=4) as e:freeze=dict(e.map(frozen,[(w,t) for w in wallets for t in [USDT,USDC]]))
    edges=pd.read_parquet(ROOT/'data/processed/wallet_edges.parquet');txs=pd.read_parquet(ROOT/'data/processed/transactions.parquet')
    flows=defaultdict(lambda:{'in':0,'out':0,'internal_in':0,'internal_out':0,'edge_ids':[]})
    for r in edges[edges.token.isin(ASSETS)].to_dict('records'):
        amount=int(r['amount_raw'])
        if r['recipient'] in addresses:
            f=flows[(r['recipient'],r['token'])];f['in']+=amount;f['internal_in']+=amount if r['sender'] in addresses else 0;f['edge_ids'].append(r['edge_id'])
        if r['sender'] in addresses:
            f=flows[(r['sender'],r['token'])];f['out']+=amount;f['internal_out']+=amount if r['recipient'] in addresses else 0;f['edge_ids'].append(r['edge_id'])
    gas=defaultdict(int)
    for r in txs.to_dict('records'):
        if r['sender'] in addresses:gas[r['sender']]+=int(r['gas_fee_wei'])
    wrapper=defaultdict(lambda:{'mint':0,'burn':0,'evidence':[]})
    from src.arbitrage.accounting import DEPOSIT,WITHDRAWAL
    from src.decoding.events import integer
    touched=edges[((edges.token.eq(WETH)) & (edges.sender.isin(addresses)|edges.recipient.isin(addresses)))|((edges.token.eq('native:eth')) & ((edges.sender.isin(addresses)&edges.recipient.eq(WETH))|(edges.recipient.isin(addresses)&edges.sender.eq(WETH))))]
    for n,group in touched.groupby('block_number'):
        header,receipts,traces,paths=engine.block(int(n))
        for h in group.tx_hash.unique():
            for log in receipts[h]['logs']:
                topics=log.get('topics',[])
                if log['address'].lower()==WETH and len(topics)==2 and topics[0].lower() in (DEPOSIT,WITHDRAWAL):
                    actor='0x'+topics[1][-40:].lower()
                    if actor in addresses:
                        key='mint' if topics[0].lower()==DEPOSIT else 'burn'
                        wrapper[actor][key]+=integer(log['data']);wrapper[actor]['evidence'].append({'tx_hash':h,'log_index':integer(log['logIndex']),'kind':key,'raw':str(integer(log['data'])),'evidence':paths['receipts']})
        engine.cache.clear()
    rows=[]
    for w in wallets:
        for token,(symbol,decimals) in ASSETS.items():
            a=w['address'];f=flows[(a,token)];o=snapshots[a,token,FIRST-1];c=snapshots[a,token,LAST];g=gas[a] if token=='native:eth' else 0
            wr=wrapper[a] if token==WETH else {'mint':0,'burn':0,'evidence':[]}
            check=reconcile(int(o['raw']),f['in'],f['out'],g,int(c['raw']),wr['mint']-wr['burn'])
            price=book.value(token,10**decimals,ts)
            if token==USDC and price['USD'] is None:
                mark=book.price('USDC',ts,venue='Binance')
                assert mark is not None,'USDC needs an observed USD reference, never assumed parity'
                price={**price,'USD':str(mark[0]),'reference_USD':str(mark[0]),'quantity':'1','price_evidence':mark[1],'confidence':'Binance USDCUSDT prior minute converted using Coinbase USDT/USD; explicit alternate feed'}
                price.pop('reason',None)
            fr=freeze.get((a,token),{'blacklisted':False,'meaning':'not a supported blacklist asset'})
            row={'wallet':w['number'],'address':a,'identity_confidence':w['identity_confidence'],'token':token,'symbol':symbol,'decimals':decimals,'opening_raw':o['raw'],'inflow_raw':str(f['in']),'outflow_raw':str(f['out']),'internal_inflow_raw':str(f['internal_in']),'internal_outflow_raw':str(f['internal_out']),'external_inflow_raw':str(f['in']-f['internal_in']),'external_outflow_raw':str(f['out']-f['internal_out']),'gas_raw':str(g),'wrapper_mint_raw':str(wr['mint']),'wrapper_burn_raw':str(wr['burn']),'wrapper_evidence':wr['evidence'],**check,'blacklist_status':fr,'opening_evidence':o['evidence'],'closing_evidence':c['evidence'],'flow_edge_ids':sorted(set(f['edge_ids'])),'fixed_reference':price,'snapshot_classification':'blacklisted token balance at wallet lead' if fr['blacklisted'] else 'balance at wallet lead; beneficial control unresolved'}
            rows.append(row)
    result={'scope':'16 address leads; Ethereum ETH/WETH/USDT/USDC only. Opening state is not zero and external inflows are not automatically stolen assets. No full incident recovery/ownership total inferred.','opening_block':FIRST-1,'closing_block':LAST,'valuation_timestamp_utc':datetime.fromtimestamp(ts,timezone.utc).isoformat(),'valuation_method':'All snapshot ledger legs marked at the same prior completed Coinbase minute close preceding closing block. ETH/WETH parity explicit.','header_evidence':{str(k):v['evidence'] for k,v in headers.items()},'rows':rows,'balanced_rows':sum(r['balanced'] for r in rows),'total_rows':len(rows),'limits':['Only observed M1 flow edges are reconciled against fresh historical snapshots; residuals expose missing flows/wrapper effects rather than forced balancing.','Token blacklisting is an observed contract state, not proof of seizure or recovery by Binance.','Stablecoin balance destruction/redemption can change balances without ordinary transfer events.','Snapshot scope omits other tokens, other chains, recipients and post-window transfers.','Frozen balance is part of closing balance, never an additional loss.']}
    (ROOT/'data/processed/balance_reconciliation.json').write_text(json.dumps(result,indent=2))
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows]).to_parquet(ROOT/'data/processed/balance_reconciliation.parquet',index=False)
    engine.store.save();public.write_index();print('Balanced',result['balanced_rows'],'of',len(rows),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--legacy');a=p.parse_args();run(a.online,a.legacy)
