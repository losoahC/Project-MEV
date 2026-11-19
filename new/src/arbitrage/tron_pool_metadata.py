"""Batched TRON current pool identity lookups. NEVER label them historical state.
TRON eth_call only executes latest state, even with certain block selectors.
"""
import json
from collections import Counter
from web3 import Web3
from eth_abi import encode
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_more import fetch
from src.arbitrage.tron_collect import decode_addr,encode_addr
V2=decode_addr('TKWJdrQkqHisa1X8HUdHEfREvTzw4pMAaY');V3=decode_addr('TThJt8zaJzJMhCEScH7zWKnp5buVZqys9x');V1=decode_addr('TXk8rQSAvPvBBNtqSoY6nCfsXWCSSpTVQF')

def selector(s):return Web3.keccak(text=s)[:4]
def batch(jobs):
    result={}
    for start in range(0,len(jobs),40):
        chunk=jobs[start:start+40];req=[{'jsonrpc':'2.0','id':i+1,'method':'eth_call','params':[{'to':'0x'+a[-40:],'data':inp},'latest']} for i,(_,_,a,inp) in enumerate(chunk)];doc,path=fetch('https://api.trongrid.io/jsonrpc',req);resp=doc.get('response',[])
        byid={x['id']:x for x in resp} if isinstance(resp,list) else {}
        for i,(pool,field,a,inp) in enumerate(chunk):result[(pool,field)]={'response':byid.get(i+1,{'transport_or_batch_error':resp}),'evidence':path,'batch_id':i+1,'contract_hex':a,'input':inp}
    return result

def run():
    p=ROOT/'data/processed/mev_tron';data=json.loads((p/'all_named_bot_accounting.json').read_text());needed={e['pool_hex']:e['protocol'] for r in data['rows'] for e in r['swap_events'] if not e['protocol'].startswith('SunSwap V4')};jobs=[];rows={}
    for pool,kind in sorted(needed.items()):
        rows[pool]={'pool_hex':pool,'pool_address':encode_addr(pool),'event_protocol':kind,'metadata_state':'latest, NOT historical','historical_identity_proven':False,'fields':{},'evidence':{},'failures':{}}
        fields=[('token0','token0()'),('token1','token1()'),('factory','factory()')]+([('fee_pips','fee()')] if kind.startswith('V3') else []) if not kind.startswith('SunSwap V1') else [('token0','tokenAddress()'),('factory','factoryAddress()')]
        for field,sig in fields:jobs.append((pool,field,pool,'0x'+selector(sig).hex()))
    result=batch(jobs)
    for (pool,field),doc in result.items():
        r=rows[pool];raw=doc['response'].get('result');r['evidence'][field]=doc
        if isinstance(raw,str) and len(raw)==66:r['fields'][field]=int(raw,16) if field=='fee_pips' else '41'+raw[-40:]
        else:r['failures'][field]=doc['response']
    jobs=[]
    for pool,r in rows.items():
        m=r['fields'];kind=r['event_protocol']
        if kind.startswith('SunSwap V1'):
            if m.get('factory') and m.get('token0'):jobs.append((pool,'factory_lookup',m['factory'],'0x'+(selector('getExchange(address)')+encode(['address'],['0x'+m['token0'][-40:]])).hex()))
        elif all(k in m for k in ['token0','token1','factory']) and (not kind.startswith('V3') or 'fee_pips' in m):
            v3=kind.startswith('V3');sig='getPool(address,address,uint24)' if v3 else 'getPair(address,address)';types=['address','address']+(['uint24'] if v3 else []);args=['0x'+m['token0'][-40:],'0x'+m['token1'][-40:]]+([m['fee_pips']] if v3 else []);jobs.append((pool,'factory_lookup',m['factory'],'0x'+(selector(sig)+encode(types,args)).hex()))
    for (pool,field),doc in batch(jobs).items():
        r=rows[pool];raw=doc['response'].get('result');r['evidence'][field]=doc;r['current_factory_lookup_matches_pool']=isinstance(raw,str) and len(raw)==66 and '41'+raw[-40:]==pool
    brands={V1:'SunSwap V1',V2:'SunSwap V2',V3:'SunSwap V3'}
    for r in rows.values():
        r['DEX_current_factory']=brands.get(r['fields'].get('factory')) if r.get('current_factory_lookup_matches_pool') else None;r['limit']='Latest state identity corroboration only. Original event/transfer amounts are historical; no historical reserves, historical proxy implementation or factory immutability proof is implied.';r['RPC_semantics_source']='https://developers.tron.network/reference/eth_call'
    (p/'pool_metadata_current.json').write_text(json.dumps(list(rows.values()),indent=2));print(json.dumps({'pools':len(rows),'current_factory_matches':sum(r.get('current_factory_lookup_matches_pool',False) for r in rows.values()),'current_brands':dict(Counter(r['DEX_current_factory'] or 'unnamed' for r in rows.values()))},indent=2))
if __name__=='__main__':run()
