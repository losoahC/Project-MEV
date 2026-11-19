"""Resolve pool identities at historical blocks; preserve raw RPC and failures."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import json,argparse,time,threading,hashlib,shutil
from datetime import datetime,timezone
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.ingestion.public_evidence import PublicEvidence
FACTORIES={'0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f':{'name':'Uniswap V2','source':'https://developers.uniswap.org/docs/protocols/v2/guides/getting-pair-addresses'},'0x1f98431c8ad98523631ae4a59f267346ea31f984':{'name':'Uniswap V3','source':'https://developers.uniswap.org/docs/protocols/v3/deployments/v3-ethereum-deployments'}}
FACTORIES.update({'0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac':{'name':'SushiSwap V2','source':'https://registry.npmjs.org/sushi/7.7.0'},'0x1097053fd2ea711dad45caccc45eff7548fcb362':{'name':'PancakeSwap V2','source':'https://registry.npmjs.org/@pancakeswap/v2-sdk/1.2.4'},'0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865':{'name':'PancakeSwap V3','source':'https://registry.npmjs.org/@pancakeswap/v3-sdk/3.10.4'}})

class PacedEvidence(PublicEvidence):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.pace_lock=threading.Lock();self.next_request=0
    def _rpc(self,method,params):
        key=hashlib.sha256(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params},sort_keys=True).encode()).hexdigest()
        path=self.directory/(key+'.json')
        if path.exists() and json.loads(path.read_text())['response'].get('result') is not None:return super()._rpc(method,params)
        with self.pace_lock:
            time.sleep(max(0,self.next_request-time.monotonic()));self.next_request=time.monotonic()+1.1
        return super()._rpc(method,params)

def run(online=False,retry_failures=False):
    out=ROOT/'data/processed/mev_discovery';directory=out/'pool_metadata';directory.mkdir(exist_ok=True);api=PacedEvidence(ROOT,online)
    cs=json.loads((out/'candidates.json').read_text());spec={}
    for c in cs:
        for l in c['pool_legs']:
            p=l['pool'];n=c['block']-1
            if p not in spec or n<spec[p]['block']:spec[p]={'block':n,'event_protocol':l['swap_events_in_log_order'][0]['protocol']}
    def one(p):
        dest=directory/(p+'.json')
        if dest.exists():
            old=json.loads(dest.read_text())
            if not retry_failures or not old.get('failures'):return old
            attempts=directory/'attempts';attempts.mkdir(exist_ok=True)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            shutil.copyfile(dest,attempts/(p+'-'+stamp+'.json'))
        s=spec[p];r={'pool':p,**s,'sources':{},'failures':{},'dex_name':None}
        for field,sig in [('token0','token0()'),('token1','token1()'),('factory','factory()')]+([('fee_pips','fee()')] if s['event_protocol'].startswith('V3') else []):
            try:
                v,src=api.call(p,sig,s['block']);assert len(v)==66
                r[field]=int(v,16) if field=='fee_pips' else '0x'+v[-40:].lower();r['sources'][field]=src
            except Exception as ex:r['failures'][field]=str(ex)
        if all(k in r for k in ['token0','token1','factory']):
            v3=s['event_protocol'].startswith('V3');sig='getPool(address,address,uint24)' if v3 else 'getPair(address,address)'
            data='0x'+Web3.keccak(text=sig).hex().removeprefix('0x')[:8]+r['token0'][2:].rjust(64,'0')+r['token1'][2:].rjust(64,'0')
            if not v3 or 'fee_pips' in r:
                if v3:data+=hex(r['fee_pips'])[2:].rjust(64,'0')
                try:
                    v,src=api.rpc('eth_call',[{'to':Web3.to_checksum_address(r['factory']),'data':data},hex(s['block'])]);r['factory_lookup_matches_pool']=('0x'+v[-40:].lower())==p;r['sources']['factory_lookup']=src
                    if r['factory_lookup_matches_pool'] and r['factory'] in FACTORIES:r['dex_name']=FACTORIES[r['factory']]['name'];r['dex_label_source']=FACTORIES[r['factory']]['source']
                except Exception as ex:r['failures']['factory_lookup']=str(ex)
        r['identity_note']='Unknown factory stays unnamed. Metadata read at earliest candidate parent block; no assumption of proxy immutability across window.'
        dest.write_text(json.dumps(r,indent=2));return r
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,p) for p in sorted(spec)]
        for f in as_completed(futures):
            results.append(f.result())
            if len(results)%50==0:print('pool metadata',len(results),'/',len(spec),flush=True)
    results.sort(key=lambda x:x['pool']);(out/'pool_metadata.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'pools':len(results),'named':dict(Counter(r['dex_name'] or 'unnamed' for r in results)),'factory_lookup_matches':sum(r.get('factory_lookup_matches_pool',False) for r in results),'with_failures':sum(bool(r['failures']) for r in results)},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--retry-failures',action='store_true');a=p.parse_args();run(a.online,a.retry_failures)
