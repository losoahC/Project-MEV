"""Historical verification of Few token underlying identity, reserves and 1:1 unwrap events."""
import json
from collections import defaultdict
from eth_abi import encode,decode
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.enrich import PacedEvidence
from src.arbitrage.reconstruct import Reconstruction
from src.reconciliation.inventory import MULTICALL,selector
from src.decoding.events import integer,transfer
WRAPPERS={'0x0492560fa7cfd6a85e50d8be3f77318994f8f429':'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0x2078f336fdd260f708bec4a20c82b063274e1b23':'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599','0xa250cc729bb3323e7933022a67b52200fe354767':'0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2','0xef87f4608e601e8564800265aee1c1ffadf73283':'0xdac17f958d2ee523a2206206994597c13d831ec7'}
UNWRAP='0x'+Web3.keccak(text='Unwrap(address,uint256,address)').hex().removeprefix('0x')
WRAP='0x'+Web3.keccak(text='Wrap(address,uint256,address)').hex().removeprefix('0x')

def run():
    p=ROOT/'data/processed/mev_full_window';orders=json.loads((p/'order_filler_equity.json').read_text())['rows'];api=PacedEvidence(ROOT,True);engine=Reconstruction(ROOT.parent/'research',False);rows=[];conversion=[]
    for n in sorted({r['block'] for r in orders}):
        jobs=[]
        for w,u in WRAPPERS.items():
            for field,contract,data in [('underlying',w,selector('token()')),('supply',w,selector('totalSupply()')),('wrapped_decimals',w,selector('decimals()')),('underlying_decimals',u,selector('decimals()')),('backing',u,selector('balanceOf(address)')+encode(['address'],[w]))]:jobs.append((w,field,contract,data))
        inp='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(a,True,data) for _,_,a,data in jobs]])).hex();raw,path=api.rpc('eth_call',[{'to':MULTICALL,'data':inp},hex(n)]);out=decode(['(bool,bytes)[]'],bytes.fromhex(raw[2:]))[0];rr={w:{'wrapper':w,'block':n,'evidence':path,'batch_indices':{}} for w in WRAPPERS}
        for i,((w,f,_,_),(ok,v)) in enumerate(zip(jobs,out)):
            assert ok and len(v)==32;rr[w][f]='0x'+v[-20:].hex() if f=='underlying' else str(int.from_bytes(v,'big'));rr[w]['batch_indices'][f]=i
        for w,r in rr.items():r['fully_backed_at_snapshot']=r['underlying']==WRAPPERS[w] and r['wrapped_decimals']==r['underlying_decimals'] and int(r['backing'])>=int(r['supply']);rows.append(r)
        head,receipts,traces,paths=engine.block(n)
        for order in orders:
            if order['block']!=n:continue
            logs=receipts[order['tx_hash']]['logs'];flows=[f for l in logs if (f:=transfer(l))]
            for log in logs:
                w=log['address'].lower();ts=log.get('topics',[])
                if w not in WRAPPERS or len(ts)!=3 or ts[0].lower() not in [WRAP,UNWRAP] or len(log['data'])!=66:continue
                actor='0x'+ts[1][-40:].lower();to='0x'+ts[2][-40:].lower();amount=integer(log['data']);wrapping=ts[0].lower()==WRAP
                matches=[f for f in flows if f['token']==WRAPPERS[w] and int(f['amount_raw'])==amount and ((f['recipient']==w) if wrapping else f['sender']==w and f['recipient']==to)]
                shares=[f for f in flows if f['token']==w and int(f['amount_raw'])==amount and ((f['sender']=='0x'+'0'*40 and f['recipient']==to) if wrapping else f['recipient']=='0x'+'0'*40 and f['sender']==actor)]
                conversion.append({'tx_hash':order['tx_hash'],'wrapper':w,'underlying':WRAPPERS[w],'event':'Wrap' if wrapping else 'Unwrap','actor':actor,'recipient':to,'amount_raw':str(amount),'one_to_one_underlying_transfer_found':bool(matches),'matching_underlying_transfers':matches,'matching_wrapper_mint_or_burn':shares,'underlying_and_share_amount_match':bool(matches) and bool(shares),'evidence':paths['receipts']})
        engine.cache.clear()
    result={'historical_backing_snapshots':rows,'observed_conversions':conversion,'wrapper_underlying_map':WRAPPERS,'all_snapshots_fully_backed':all(r['fully_backed_at_snapshot'] for r in rows),'all_observed_conversions_1to1':bool(conversion) and all(r['underlying_and_share_amount_match'] for r in conversion),'interpretation':'Historical token() identity and decimals verified. Each observed conversion separately checks the actual underlying transfer and wrapper mint/burn. Direct underlying reserves are below totalSupply at these snapshots; this alone does not establish global redemption coverage, circulating supply, or insolvency. A 1:1 face-value sensitivity is not an independently observed market price.'};(ROOT/'data/processed/few_wrapper_backing.json').write_text(json.dumps(result,indent=2));print('Few snapshots',len(rows),'fullybacked',result['all_snapshots_fully_backed'],'conversions',len(conversion),'1:1',result['all_observed_conversions_1to1'])
if __name__=='__main__':run()
