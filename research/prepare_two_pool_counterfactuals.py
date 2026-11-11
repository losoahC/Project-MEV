import json
from pathlib import Path
from audit_target_v2_fees import call,FACTORY
R=Path(__file__).resolve().parent
xs=[r for r in json.loads((R/'two_pool_counterfactual_triage.json').read_text())['rows'] if r['event_protocols']==['V2']];meta={}
for r in xs:
 for p in r['pools']:
  p=p[3:];m={'block':r['block']}
  for k,s in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155')]:m[k]='0x'+call('twopool_'+p+'_'+k,p,s,r['block']-1)[-40:]
  pair='0x'+call('twopool_'+p+'_pair',m['factory'],'0xe6a43905'+m['token0'][2:].zfill(64)+m['token1'][2:].zfill(64),r['block']-1)[-40:];m['factory_pair_matches']=pair==p;m['official_uniswap_v2']=m['factory']==FACTORY;meta[p]=m
(R/'two_pool_counterfactual_metadata.json').write_text(json.dumps({'pools':meta,'candidates':xs},indent=2));print(meta)
