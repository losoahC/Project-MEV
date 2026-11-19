"""Recover Ethereum V4 PoolKey from actual manager calldata and verify PoolId hash.
No RPC guessing, no manager-wide pooling, no token ticker inference.
"""
import json
from collections import defaultdict,Counter
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.decoding.events import signed_word
SELECTORS={'0x'+Web3.keccak(text=s).hex().removeprefix('0x')[:8]:s for s in ['swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)','modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)','initialize((address,address,uint24,int24,address),uint160)']}

def decode_key(data):
    if data[:10].lower() not in SELECTORS or len(data)<10+320:return None
    raw=data[10:330];w=[raw[i:i+64] for i in range(0,320,64)]
    if any(int(w[i][0:24],16) for i in [0,1,4]):return None
    fee=int(w[2],16);spacing=signed_word(w[3])
    if fee>=2**24 or not -2**23<=spacing<2**23:return None
    return {'pool_id':'0x'+Web3.keccak(bytes.fromhex(raw)).hex().removeprefix('0x'),'currency0':'0x'+w[0][-40:].lower(),'currency1':'0x'+w[1][-40:].lower(),'fee':fee,'tick_spacing':spacing,'hooks':'0x'+w[4][-40:].lower(),'encoded_pool_key':'0x'+raw,'selector':data[:10].lower()}

def run():
    p=ROOT/'data/processed/mev_full_window';cs=json.loads((p/'candidates.json').read_text());needed=defaultdict(set);byblock=defaultdict(set)
    for c in cs:
        for e in c['events']:
            if e['protocol'].startswith('V4'):needed[e['pool']].add(e['pool_id']);byblock[c['block']].add(c['tx_hash'])
    engine=Reconstruction(ROOT.parent/'research',False);found={};conflicts=[];calls=0
    for i,(n,hs) in enumerate(sorted(byblock.items()),1):
        _,_,tr,paths=engine.block(n)
        for h in hs:
            for t in tr[h]:
                a=t.get('action',{});manager=a.get('to','').lower()
                if manager not in needed:continue
                key=decode_key(a.get('input',''))
                if not key:continue
                calls+=1;pid=key['pool_id']
                if pid not in needed[manager]:continue
                ident=manager+':'+pid;record={'pool_key':ident,'manager':manager,**key,'evidence':paths['traces'],'tx_hash':h,'block':n,'trace_address':t['traceAddress'],'hash_matches_event_pool_id':True,'source':'https://raw.githubusercontent.com/Uniswap/v4-core/main/src/types/PoolKey.sol','sign_convention':'V4 event raw BalanceDelta; positive received by swapper, negative paid. Hook or settlement differences must reconcile before profit classification.'}
                if ident in found and found[ident]['encoded_pool_key']!=record['encoded_pool_key']:conflicts.append({'first':found[ident],'other':record})
                else:found.setdefault(ident,record)
        engine.cache.clear()
        if i%200==0:print('V4 key blocks',i,'found',len(found),flush=True)
    missing=[m+':'+pid for m,ids in needed.items() for pid in ids if m+':'+pid not in found];assert not conflicts
    (p/'v4_pool_keys.json').write_text(json.dumps({'rows':list(found.values()),'missing':sorted(missing),'conflicts':conflicts,'summary':{'requested_pool_ids':sum(len(v) for v in needed.values()),'resolved_pool_ids':len(found),'recognized_manager_calls':calls,'blocks_read':len(byblock)}},indent=2));print('V4 keys',len(found),'missing',len(missing))
if __name__=='__main__':run()
