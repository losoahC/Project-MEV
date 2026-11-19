"""Expand raw-unit accounting to every token observed in three exchange-to-lead sweeps.

Read-only historical multicalls. Raw scope is not a whole-incident theft/ownership claim.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import hashlib,json
import pandas as pd
from eth_abi import encode,decode
from web3 import Web3
from src.ingestion.public_evidence import PublicEvidence
from src.ingestion.evidence import read_json
from src.visualization.common import ROOT
from src.reconciliation.balances import FIRST,LAST,reconcile

MULTICALL='0xca11bde05977b3631167028862be2a173976ca11'
EXCHANGE='0x28c6c06298d514db089934071355e5743bf21d60'

def selector(signature):return Web3.keccak(text=signature)[:4]

def decode_results(raw,expected):
    decoded=decode(['(bool,bytes)[]'],bytes.fromhex(raw.removeprefix('0x')))[0]
    assert len(decoded)==expected,'Multicall result length mismatch'
    return [int.from_bytes(data,'big') if success and len(data)==32 else None for success,data in decoded]

def run(online=False):
    public=PublicEvidence(ROOT,online);wallets=read_json(ROOT/'data/processed/wallet_registry.json');addresses=[w['address'] for w in wallets];addressset=set(addresses)
    edges=pd.read_parquet(ROOT/'data/processed/wallet_edges.parquet');initial=edges[edges.sender.eq(EXCHANGE)&edges.recipient.isin(addressset)]
    tokens=sorted(set(initial.token));sources={}
    doc,path=public.get('https://raw.githubusercontent.com/mds1/multicall3/main/deployments.json');sources['official_deployments']=path
    assert doc.get('http_status')==200 and any(d.get('chainId')==1 and MULTICALL in d['url'].lower() for d in doc['response'])
    for n in [FIRST-1,LAST]:
        code,path=public.rpc('eth_getCode',[MULTICALL,hex(n)]);assert len(code)>100;sources[str(n)]={'code_evidence':path,'code_keccak':'0x'+Web3.keccak(hexstr=code).hex().removeprefix('0x')}
    def fetch(job):
        token,n=job;calls=[]
        for a in addresses:
            if token=='native:eth':target=MULTICALL;data=selector('getEthBalance(address)')+encode(['address'],[a])
            else:target=token;data=selector('balanceOf(address)')+encode(['address'],[a])
            calls.append((target,True,data))
        if token!='native:eth':calls.append((token,True,selector('decimals()')))
        calldata=selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[calls])
        raw,path=public.rpc('eth_call',[{'to':MULTICALL,'data':'0x'+calldata.hex()},hex(n)])
        values=decode_results(raw,len(calls));decimals=18 if token=='native:eth' else values[-1]
        assert decimals is None or 0<=decimals<=36,'Unreasonable decimals require investigation'
        return (token,n),{'balances':dict(zip(addresses,values[:16])),'decimals':decimals,'evidence':path}
    jobs=[(token,n) for token in tokens for n in [FIRST-1,LAST]];snapshots={}
    with ThreadPoolExecutor(max_workers=3) as e:
        for i,(key,val) in enumerate(e.map(fetch,jobs),1):
            snapshots[key]=val
            if i%24==0:print('Inventory snapshot batches',i,'/',len(jobs),flush=True)
    flows=defaultdict(lambda:defaultdict(int));edgeids=defaultdict(list)
    for r in edges[edges.token.isin(tokens)].to_dict('records'):
        t=r['token'];v=int(r['amount_raw'])
        for a,kind in [(r['recipient'],'in'),(r['sender'],'out')]:
            if a in addressset:flows[a,t][kind]+=v;edgeids[a,t].append(r['edge_id'])
        if r['sender']==EXCHANGE and r['recipient'] in addressset:flows[r['recipient'],t]['initial_exchange_sweep_in']+=v
    gas=defaultdict(int)
    for r in pd.read_parquet(ROOT/'data/processed/transactions.parquet').to_dict('records'):
        if r['sender'] in addressset:gas[r['sender']]+=int(r['gas_fee_wei'])
    existing=read_json(ROOT/'data/processed/balance_reconciliation.json');existing_map={(r['address'],r['token']):r for r in existing['rows']}
    rows=[];totals=[]
    for token in tokens:
        opening=snapshots[token,FIRST-1];closing=snapshots[token,LAST]
        assert opening['decimals']==closing['decimals'],'Decimals changed across snapshots'
        for w in wallets:
            a=w['address'];o=opening['balances'][a];c=closing['balances'][a];f=flows[a,token];g=gas[a] if token=='native:eth' else 0
            previous=existing_map.get((a,token));wr=int(previous['wrapper_mint_raw'])-int(previous['wrapper_burn_raw']) if previous else 0
            check=reconcile(o,f['in'],f['out'],g,c,wr) if o is not None and c is not None else {'balanced':False,'unexplained_change_raw':None,'observed_closing_raw':str(c) if c is not None else None}
            if previous:
                assert o==int(previous['opening_raw']) and c==int(previous['observed_closing_raw']),'Direct RPC / Multicall disagreement'
            row={'wallet':w['number'],'address':a,'token':token,'decimals':closing['decimals'],'opening_raw':str(o) if o is not None else None,'inflow_raw':str(f['in']),'outflow_raw':str(f['out']),'initial_exchange_sweep_in_raw':str(f['initial_exchange_sweep_in']),'gas_raw':str(g),'wrapper_adjustment_raw':str(wr),**check,'opening_evidence':opening['evidence'],'closing_evidence':closing['evidence'],'flow_edge_ids':sorted(set(edgeids[a,token]))}
            rows.append(row)
        group=[r for r in rows if r['token']==token];decs=closing['decimals']
        total={k:str(sum(int(r[k]) for r in group)) if all(r.get(k) is not None for r in group) else None for k in ['opening_raw','initial_exchange_sweep_in_raw','observed_closing_raw','unexplained_change_raw']}
        names=initial[initial.token.eq(token)].symbol.dropna().unique().tolist()
        totals.append({'token':token,'symbol_from_legacy_metadata_only':names[0] if len(names)==1 else None,'decimals':decs,**total,'all_wallet_rows_balanced':all(r['balanced'] for r in group),'initial_edge_ids':initial[initial.token.eq(token)].edge_id.tolist(),'meaning':'Observed three exchange-address-to-lead sweeps only; not all incident chains or all original inflows. USD unvalued here; symbol is not a market identity assertion.'})
    result={'scope':'Every asset appearing in the three observed exchange-address-to-16-lead sweeps, across all16 address balances at both historical endpoints. Other assets/chains and exclusive control unresolved.','exchange_source_address':EXCHANGE,'opening_block':FIRST-1,'closing_block':LAST,'initial_tx_hashes':sorted(initial.tx_hash.unique()),'initial_edges':len(initial),'asset_count':len(tokens),'wallet_asset_rows':len(rows),'balanced_rows':sum(r['balanced'] for r in rows),'missing_balance_calls':sum(r['opening_raw'] is None or r['observed_closing_raw'] is None for r in rows),'multicall_sources':sources,'assets':totals,'rows':rows,'limits':['Sweep source address attribution is reported exchange association, not an independent legal theft determination for every unit.','Unexplained residuals are not forced to zero; rebasing/fee-on-transfer/nonstandard token events and missing flows need separate interpretation.','No ticker-only USD assignment. Raw per-token balances cannot be added across currencies.','Receipts/traces/headers are source evidence, not cryptographic state proofs.']}
    (ROOT/'data/processed/asset_inventory.json').write_text(json.dumps(result,indent=2))
    for filename,data in [('asset_inventory',rows),('initial_sweep_assets',totals)]:pd.DataFrame([{k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in data]).to_parquet(ROOT/f'data/processed/{filename}.parquet',index=False)
    public.write_index();print('Inventory',len(tokens),'assets,',len(rows),'wallet/asset pairs,',result['balanced_rows'],'balanced;',result['missing_balance_calls'],'missing calls',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');a=p.parse_args();run(a.online)
