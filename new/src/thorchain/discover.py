"""Discover explicit cross-chain memo candidates through verified fund-flow links, not ownership guesses."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from decimal import Decimal
import json
import re
from urllib.parse import urlencode
from eth_abi import decode
from web3 import Web3

import pandas as pd

from src.ingestion.public_evidence import PublicEvidence
from src.ingestion.evidence import read_json
from src.visualization.common import ROOT


def memo_candidate(transaction):
    raw=transaction.get('raw_input') or transaction.get('input') or '0x'
    for signature,types in [('depositWithExpiry(address,address,uint256,string,uint256)',['address','address','uint256','string','uint256']),('deposit(address,address,uint256,string)',['address','address','uint256','string'])]:
        selector='0x'+Web3.keccak(text=signature).hex().removeprefix('0x')[:8]
        if raw[:10].lower()==selector:
            try:
                return decode(types,bytes.fromhex(raw[10:]))[3]
            except Exception:
                pass
    try:
        text=bytes.fromhex(raw.removeprefix('0x')).decode('utf-8','ignore')
    except ValueError:
        return None
    match=re.search(r'(?:SWAP:|=:|s:)[A-Za-z0-9._/-]+:[A-Za-z0-9:._/-]{10,250}',text)
    return match.group(0).split('\x00')[0] if match else None


def run(online=False,max_hops=2):
    public=PublicEvidence(ROOT,online)
    wallets=read_json(ROOT/'data/processed/wallet_registry.json')
    known={w['address']:{'kind':'teacher_wallet_lead','identity_confidence':w['identity_confidence'],'funding_links':[]} for w in wallets}
    edges=pd.read_parquet(ROOT/'data/processed/wallet_edges.parquet')
    material=edges[edges.token.eq('native:eth') & edges.sender.isin(known) & ~edges.recipient.isin(known)]
    byrecipient=defaultdict(list)
    for row in material.to_dict('records'):
        if int(row['amount_raw'])>=1000*10**18:
            byrecipient[row['recipient']].append({'sender':row['sender'],'tx_hash':row['tx_hash'],'amount_raw':row['amount_raw'],'edge_id':row['edge_id'],'evidence_path':row['evidence_path']})
    for address,links in byrecipient.items():
        known[address]={'kind':'direct_material_ETH_recipient','identity_confidence':'fund-flow link only; common ownership NOT established','funding_links':links}
    observations=[];transactions={};candidates=[];queried=set();frontier=list(known)
    def fetch(address):
        url=f'https://eth.blockscout.com/api/v2/addresses/{address}/transactions?filter=from'
        doc,path=public.get(url)
        return address,doc,path
    for depth in range(max_hops+1):
        todo=[a for a in frontier if a not in queried]
        if not todo:
            break
        nextfrontier=[]
        with ThreadPoolExecutor(max_workers=4) as executor:
            for address,doc,path in executor.map(fetch,todo):
                queried.add(address);data=doc.get('response');items=data.get('items',[]) if isinstance(data,dict) and doc.get('http_status')==200 else []
                observations.append({'address':address,'depth':depth,'http_status':doc.get('http_status'),'error':doc.get('error'),'items':len(items),'next_page_params':data.get('next_page_params') if isinstance(data,dict) else None,'evidence_path':path,'source_context':known[address]})
                for tx in items:
                    sender=(tx.get('from') or {}).get('hash','').lower()
                    if sender!=address:
                        continue
                    h=tx['hash'].lower();transactions[h]={'source_address':address,'depth':depth,'transaction':tx,'evidence_path':path}
                    memo=memo_candidate(tx)
                    if memo:
                        candidates.append({'source_address':address,'tx_hash':h,'block':tx.get('block_number'),'timestamp':tx.get('timestamp'),'memo':memo,'evidence_path':path,'source_context':known[address]})
                    recipient=(tx.get('to') or {}).get('hash','').lower()
                    value=int(tx.get('value') or 0)
                    # Only follow explicit material ETH outflows after the incident;
                    # no recipient is relabeled as attacker-controlled.
                    threshold=1000*10**18 if depth==0 else 10*10**18
                    if recipient and recipient not in known and value>=threshold and (tx.get('timestamp') or '')>='2026-10-29':
                        known[recipient]={'kind':'material_outflow_recipient','identity_confidence':'fund-flow link only; common ownership NOT established','funding_links':[{'sender':address,'tx_hash':h,'amount_raw':str(value),'evidence_path':path}]}
                        nextfrontier.append(recipient)
        frontier=nextfrontier[:40]
        print(f'THORChain discovery depth {depth}: {len(queried)} addresses queried; {len(candidates)} explicit memo candidates',flush=True)
    (ROOT/'data/processed/thorchain_discovery.json').write_text(json.dumps({'method':'16 teacher wallet leads plus direct >1000 ETH recipients already evidenced in M1; follow material ordinary outflows up to bounded depth. Links are transfers, not ownership. First explorer page per address only; pagination and internal calls are not exhausted.','addresses':known,'observations':observations,'transactions':list(transactions.values()),'memo_candidates':candidates,'limits':['Current explorer records may include data after the Ethereum MEV event window.','A matching memo is a candidate, not proof of THORChain execution or stolen-unit attribution.','No address is inferred to be controlled by the hacker solely from receiving funds.']},indent=2))
    public.write_index()
    print(f'Found {len(candidates)} memo candidates; source-chain receipts and THORNode/Midgard matching still required')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--max-hops',type=int,default=2);a=p.parse_args();run(a.online,a.max_hops)
