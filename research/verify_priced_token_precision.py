import json
from concurrent.futures import ThreadPoolExecutor,as_completed
from audit_target_v2_fees import R,call
def one(item):
 a,m=item;n=m['block'];actual=int(call('priced_precision_'+a+'_'+str(n),a,'0x313ce567',n),16)
 return {'address':a,'block':n,'metadata_decimals':m['decimals'],'chain_decimals':actual,'match':actual==m['decimals']}
def main():
 tasks=json.loads((R/'priced_token_precision_tasks.json').read_text());rows=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  fs={ex.submit(one,item):item[0] for item in tasks.items()}
  for f in as_completed(fs):
   try:rows.append(f.result())
   except Exception as e:errors.append({'address':fs[f],'error':str(e)})
 out={'method':'Historical decimals() at one observed transaction block for each priced contract. Does not prove decimals constant or market ticker identity.','rows':rows,'errors':errors,'mismatches':[r for r in rows if not r['match']]}
 (R/'priced_token_precision_validation.json').write_text(json.dumps(out,indent=2));print('checked',len(rows),'errors',errors,'mismatches',out['mismatches'])
if __name__=='__main__':main()
