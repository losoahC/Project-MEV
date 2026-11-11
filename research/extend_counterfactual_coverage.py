import json,gzip
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from audit_target_v2_fees import call,FACTORY
R=Path(__file__).resolve().parent
def main():
 groups=json.loads((R/'all_scope_sandwich_groups.json').read_text())['groups'];meta=json.loads((R/'target_v2_fee_accounting.json').read_text())['pools'];needed={l['pool'][3:]:g['block'] for g in groups for l in g['links'] if l['pool'].startswith('V2:') and l['pool'][3:] not in meta}
 def one(item):
  p,n=item;m={'block':n}
  for field,s in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155')]:m[field]='0x'+call('all_cf_'+p+'_'+field,p,s,n)[-40:]
  m['verified_uniswap_v2']=False
  if m['factory']==FACTORY:m['verified_uniswap_v2']='0x'+call('all_cf_'+p+'_getPair',FACTORY,'0xe6a43905'+m['token0'][2:].zfill(64)+m['token1'][2:].zfill(64),n)[-40:]==p
  return p,m
 errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(one,x):x[0] for x in needed.items()}
  for f in as_completed(fs):
   try:p,m=f.result();meta[p]=m
   except Exception as e:errors.append({'pool':fs[f],'error':str(e)})
 (R/'all_scope_v2_pool_metadata.json').write_text(json.dumps({'pools':meta,'errors':errors},indent=2));print('new pools',len(needed),'errors',errors)
if __name__=='__main__':main()
