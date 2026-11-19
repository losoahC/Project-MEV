"""Resolve non-Uniswap factory ABIs, at each pool's original parent block."""
import json
from collections import defaultdict,Counter
from eth_abi import encode,decode
from src.arbitrage.discover import ROOT
from src.arbitrage.enrich import PacedEvidence
from src.reconciliation.inventory import MULTICALL,selector

ALG='0x44b7fbd4d87149efa5347c451e74b9fd18e89c55'
TICK={'0xf4fd2e6c5b60c5b365cd1b96dd6245e6d60414c2','0x70fe4a44ea505cfa3a57b95cf2862d4fd5f0f687'}

def run():
    p=ROOT/'data/processed/mev_full_window';dest=p/'pool_metadata_full.json';rows=json.loads(dest.read_text());original=json.loads(dest.read_text());api=PacedEvidence(ROOT,True);sources={r['address']:r['evidence'] for r in json.loads((ROOT/'data/processed/completion_factory_sources.json').read_text())};groups=defaultdict(list);audit=[]
    def batch(jobs,n):
        data='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(a,True,d) for a,d in jobs]])).hex();out,path=api.rpc('eth_call',[{'to':MULTICALL,'data':data},hex(n)]);return decode(['(bool,bytes)[]'],bytes.fromhex(out[2:]))[0],path
    for r in rows:
        if not r.get('factory_lookup_matches_pool') and r.get('factory') in ({ALG}|TICK):groups[r['block']].append(r)
    for n,rr in sorted(groups.items()):
        ticks={};needed=[r for r in rr if r['factory'] in TICK]
        if needed:
            result,path=batch([(r['pool'],selector('tickSpacing()')) for r in needed],n)
            for i,(r,(ok,v)) in enumerate(zip(needed,result)):
                if ok and len(v)==32:ticks[r['pool']]=int.from_bytes(v,'big',signed=True);r['tick_spacing_evidence']={'evidence':path,'index':i};r['tick_spacing']=ticks[r['pool']]
        jobs=[];valid=[]
        for r in rr:
            if r['factory']==ALG:sig='poolByPair(address,address)';types=['address','address'];args=[r['token0'],r['token1']]
            elif r['pool'] in ticks:sig='getPool(address,address,int24)';types=['address','address','int24'];args=[r['token0'],r['token1'],ticks[r['pool']]]
            else:continue
            jobs.append((r['factory'],selector(sig)+encode(types,args)));valid.append((r,sig))
        if not jobs:continue
        result,path=batch(jobs,n)
        for i,((r,sig),(ok,v)) in enumerate(zip(valid,result)):
            matched=ok and len(v)==32 and '0x'+v[-20:].hex()==r['pool'];audit.append({'pool':r['pool'],'block':n,'factory':r['factory'],'method':sig,'matched':bool(matched),'evidence':path,'batch_index':i,'ABI_source_evidence':sources[r['factory']]})
            if matched:
                r['original_Uniswap_factory_lookup_failures']=r['failures'];r['failures']={k:v for k,v in r['failures'].items() if k!='factory_lookup'};r['factory_lookup_matches_pool']=True;r['alternative_factory_method']=sig;r['alternative_factory_lookup_evidence']=path;r['alternative_factory_lookup_batch_index']=i;r['ABI_source_evidence']=sources[r['factory']];r['identity_note']='Pool currencies from historical getters; verified published factory ABI selects poolByPair or signed tickSpacing lookup. Historical parent lookup matches actual pool. Dynamic fee is not used as a pool identifier.'
    backup=p/'pool_metadata_before_alternative_ABI.json'
    if not backup.exists():backup.write_text(json.dumps(original,indent=2))
    dest.write_text(json.dumps(rows,indent=2));summary=json.loads((p/'pool_metadata_full_summary.json').read_text());summary.update(factory_matches=sum(r.get('factory_lookup_matches_pool',False) for r in rows),failed_records=sum(bool(r['failures']) for r in rows),alternative_ABI_new_matches=sum(r['matched'] for r in audit));(p/'pool_metadata_full_summary.json').write_text(json.dumps(summary,indent=2));(p/'alternative_factory_audit.json').write_text(json.dumps({'rows':audit,'summary':summary},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
