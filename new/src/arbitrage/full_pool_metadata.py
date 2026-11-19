"""Batch missing pool metadata, verifying it at each pool's first parent block.
End snapshot only plans factory lookup arguments; parent values must agree.
"""
import json
from collections import defaultdict,Counter
from eth_abi import encode,decode
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.enrich import PacedEvidence,FACTORIES
from src.reconciliation.inventory import MULTICALL,selector
LAST=26303950

def run():
    p=ROOT/'data/processed/mev_full_window';api=PacedEvidence(ROOT,True);cs=json.loads((p/'candidates.json').read_text());spec={};old={r['pool']:r for r in json.loads((ROOT/'data/processed/mev_discovery/pool_metadata.json').read_text())}
    for c in cs:
        for e in c['events']:
            if e['protocol'].startswith('V4'):continue
            a=e['pool'];n=c['block']-1
            if a not in spec or n<spec[a]['block']:spec[a]={'block':n,'protocol':e['protocol'],'v3':e['protocol'].startswith(('V3','Pancake-V3'))}
    wanted={a:s for a,s in spec.items() if a not in old or old[a]['failures']};planning={};outdir=p/'pool_metadata_full';outdir.mkdir(exist_ok=True)
    def batch(calls,n):
        data='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(a,True,bytes.fromhex(inp.removeprefix('0x'))) for a,inp in calls]])).hex();raw,path=api.rpc('eth_call',[{'to':MULTICALL,'data':data},hex(n)]);result=decode(['(bool,bytes)[]'],bytes.fromhex(raw[2:]))[0];assert len(result)==len(calls);return result,path
    def meta_calls(a,s):return [(field,(a,'0x'+selector(sig).hex())) for field,sig in [('token0','token0()'),('token1','token1()'),('factory','factory()')]+([('fee_pips','fee()')] if s['v3'] else [])]
    addresses=sorted(wanted)
    for start in range(0,len(addresses),20):
        chunk=addresses[start:start+20];jobs=[(a,field,call) for a in chunk for field,call in meta_calls(a,wanted[a])];result,path=batch([j[2] for j in jobs],LAST)
        for i,((a,field,_),(ok,data)) in enumerate(zip(jobs,result)):
            r=planning.setdefault(a,{'sources':{}})
            if ok and len(data)==32:r[field]=int.from_bytes(data,'big') if field=='fee_pips' else '0x'+data[-20:].hex();r['sources'][field]={'evidence':path,'index':i}
    groups=defaultdict(list)
    for a,s in wanted.items():groups[s['block']].append(a)
    for count,(n,aa) in enumerate(sorted(groups.items()),1):
        jobs=[]
        for a in aa:
            jobs.extend((a,field,call) for field,call in meta_calls(a,wanted[a]));m=planning.get(a,{})
            if all(k in m for k in ['factory','token0','token1']) and (not wanted[a]['v3'] or 'fee_pips' in m):
                sig='getPool(address,address,uint24)' if wanted[a]['v3'] else 'getPair(address,address)';types=['address','address']+(['uint24'] if wanted[a]['v3'] else []);values=[m['token0'],m['token1']]+([m['fee_pips']] if wanted[a]['v3'] else []);inp='0x'+(selector(sig)+encode(types,values)).hex();jobs.append((a,'factory_lookup',(m['factory'],inp)))
        results={a:{'pool':a,'block':n,'event_protocol':wanted[a]['protocol'],'sources':{},'batch_indices':{},'failures':{},'dex_name':None,'planning_snapshot_block':LAST} for a in aa}
        for start in range(0,len(jobs),100):
            chunk=jobs[start:start+100];ret,path=batch([j[2] for j in chunk],n)
            for i,((a,field,_),(ok,data)) in enumerate(zip(chunk,ret)):
                r=results[a];r['sources'][field]=path;r['batch_indices'][field]=i
                if ok and len(data)==32:r[field]=int.from_bytes(data,'big') if field=='fee_pips' else '0x'+data[-20:].hex()
                else:r['failures'][field]='Call reverted or non-32-byte ABI return; allowFailure preserved'
        for a,r in results.items():
            lookup=r.pop('factory_lookup',None);r['planning_matches_parent']=all(r.get(k)==planning.get(a,{}).get(k) for k in ['token0','token1','factory']+(['fee_pips'] if wanted[a]['v3'] else []));r['factory_lookup_matches_pool']=lookup==a and r['planning_matches_parent']
            if r['factory_lookup_matches_pool'] and r.get('factory') in FACTORIES:r['dex_name']=FACTORIES[r['factory']]['name'];r['dex_label_source']=FACTORIES[r['factory']]['source']
            r['identity_note']='Metadata and factory lookup are historical first-parent multicalls. End snapshot only planned query arguments; mismatches are not silently accepted.';(outdir/(a+'.json')).write_text(json.dumps(r,indent=2));old[a]=r
        if count%25==0:print('historical pool batches',count,'/',len(groups),flush=True)
    merged=[old[a] for a in sorted(spec)];(p/'pool_metadata_full.json').write_text(json.dumps(merged,indent=2));(p/'pool_metadata_full_summary.json').write_text(json.dumps({'pools':len(merged),'new_or_retried':len(wanted),'parent_block_groups':len(groups),'factory_matches':sum(r.get('factory_lookup_matches_pool',False) for r in merged),'named':dict(Counter(r.get('dex_name') or 'unnamed' for r in merged)),'failed_records':sum(bool(r['failures']) for r in merged)},indent=2));print('Full pool metadata done',len(merged))
if __name__=='__main__':run()
