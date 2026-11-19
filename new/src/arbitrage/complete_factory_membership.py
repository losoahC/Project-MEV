"""Historical registry membership and fork-specific factory-address getters."""
import json
from collections import defaultdict
from eth_abi import encode,decode
from src.arbitrage.discover import ROOT
from src.arbitrage.enrich import PacedEvidence
from src.reconciliation.inventory import MULTICALL,selector
ALG='0x44b7fbd4d87149efa5347c451e74b9fd18e89c55'

def run():
    p=ROOT/'data/processed/mev_full_window';dest=p/'pool_metadata_full.json';rows=json.loads(dest.read_text());api=PacedEvidence(ROOT,True);audit=[]
    def batch(jobs,n):
        data='0x'+(selector('aggregate3((address,bool,bytes)[])')+encode(['(address,bool,bytes)[]'],[[(a,True,d) for a,d in jobs]])).hex();out,path=api.rpc('eth_call',[{'to':MULTICALL,'data':data},hex(n)]);return decode(['(bool,bytes)[]'],bytes.fromhex(out[2:]))[0],path
    def matched(r,path,i,method,factory=None):
        r.setdefault('original_Uniswap_factory_lookup_failures',r['failures']);r['failures']={k:v for k,v in r['original_Uniswap_factory_lookup_failures'].items() if k!='factory_lookup'};r['factory_lookup_matches_pool']=True;r['alternative_factory_method']=method;r['alternative_factory_lookup_evidence']=path;r['alternative_factory_lookup_batch_index']=i
        if factory:r['factory']=factory
        audit.append({'pool':r['pool'],'factory':r['factory'],'block':r['block'],'evidence':path,'index':i,'method':method,'matched':True})
    # Both default and custom Algebra pools enter allPairs; token-pair default
    # mapping alone excludes custom deployers. Final snapshot only discovers index.
    v,src=api.rpc('eth_call',[{'to':ALG,'data':'0x'+selector('allPairsLength()').hex()},hex(26303950)]);length=int(v,16);ret,path=batch([(ALG,selector('allPairs(uint256)')+encode(['uint256'],[i])) for i in range(length)],26303950);indices={'0x'+v[-20:].hex():i for i,(ok,v) in enumerate(ret) if ok and len(v)==32}
    for r in rows:
        if r.get('factory')==ALG and not r.get('factory_lookup_matches_pool') and r['pool'] in indices:
            i=indices[r['pool']];v,source=api.rpc('eth_call',[{'to':ALG,'data':'0x'+(selector('allPairs(uint256)')+encode(['uint256'],[i])).hex()},hex(r['block'])]);assert '0x'+v[-40:]==r['pool'];matched(r,source,0,'allPairs(uint256)');r['historical_factory_registry_index']=i;r['registry_index_discovery_evidence']=path
    special=json.loads((ROOT/'data/processed/completion_special_factory_calls.json').read_text());by={r['pool']:r for r in rows}
    for c in special:
        r=by[c['pool']]
        for i,res in enumerate(c['results']):
            if res['ok'] and res['method']=='getPair(address,address,bool)' and res['data'][-40:]==r['pool'][2:]:matched(r,c['evidence'],i,'getPair(address,address,bool)');r['stable']=False
        factory=next(('0x'+res['data'][-40:] for res in c['results'] if res['ok'] and res['method']=='factoryAddress()'),None)
        if factory:
            data=selector('getPair(address,address,bool)')+encode(['address','address','bool'],[r['token0'],r['token1'],False]);v,source=api.rpc('eth_call',[{'to':factory,'data':'0x'+data.hex()},hex(r['block'])]);assert '0x'+v[-40:]==r['pool'];matched(r,source,0,'factoryAddress() then getPair(address,address,bool)',factory);r['factory_address_getter_evidence']=c['evidence'];r['stable']=False
    # Preserve getter failures even where a different factory lookup succeeded.
    for r in rows:
        if r.get('original_Uniswap_factory_lookup_failures'):
            r['failures']={k:v for k,v in r['original_Uniswap_factory_lookup_failures'].items() if k!='factory_lookup'}
    identity_path=ROOT/'data/processed/ammalgam_historical_identity.json';source_path=ROOT/'data/processed/ammalgam_historical_implementation_source.json'
    if identity_path.exists() and source_path.exists():
        identity=json.loads(identity_path.read_text());source=json.loads(source_path.read_text());r=by[identity['pool']];v=identity['calls']['underlyingTokens']['value'];assert len(v)==130 and identity['block']==r['block'] and source['contract']['ContractName']=='AmmalgamPair'
        r.update(token0='0x'+v[26:66],token1='0x'+v[90:130],historical_asset_identity_verified=True,historical_implementation='0x'+identity['calls']['implementation_slot']['value'][-40:],historical_implementation_evidence=identity['calls']['implementation_slot']['evidence'],underlying_tokens_evidence=identity['calls']['underlyingTokens']['evidence'],verified_implementation_source=source['evidence'],protocol_risk='Ammalgam combines swaps and lending; borrow/repay, share and debt accounting requires distinct balance-sheet treatment. Do not certify plain AMM profit from transfer closure alone.',identity_note='Historical EIP1967 implementation points to the verified AmmalgamPair implementation; historical underlyingTokens() returns USDC/WETH. Standard token0()/factory() getters are inapplicable, not missing transfer amounts.')
    dest.write_text(json.dumps(rows,indent=2));summary=json.loads((p/'pool_metadata_full_summary.json').read_text());summary.update(factory_matches=sum(r.get('factory_lookup_matches_pool',False) for r in rows),historical_asset_identities_verified=sum(r.get('factory_lookup_matches_pool',False) or r.get('historical_asset_identity_verified',False) for r in rows),failed_records=sum(bool(r['failures']) for r in rows),remaining_unmatched_pools=[r['pool'] for r in rows if not r.get('factory_lookup_matches_pool') and not r.get('historical_asset_identity_verified')]);(p/'pool_metadata_full_summary.json').write_text(json.dumps(summary,indent=2));(p/'complete_factory_membership_audit.json').write_text(json.dumps({'rows':audit,'summary':summary},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
