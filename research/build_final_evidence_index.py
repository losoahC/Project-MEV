import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 rows={}
 incremental={r['hash'] for r in load('incremental_candidate_classification.json')['rows']}
 for r in load('candidate_classification.json')['rows']+load('incremental_candidate_classification.json')['rows']:
  rows[r['hash']]={'hash':r['hash'],'block':r['block'],'source':'incremental_candidate_classification.json' if r['hash'] in incremental else 'candidate_classification.json','classification':r['category'],'native_evidence':'scope_detail_raw or drpc_trace_raw; see source block' if r['hash'] in incremental else 'drpc_candidate_native.json','cashflow_ETH':r['operational_cashflow_ETH'],'boundary':'heuristic operational boundary; not ownership proof'}
 for name in ['pancake_coverage_completion.json','late_candidate_completion.json']:
  d=load(name)
  for r in d.get('candidates',d.get('rows',[])):
   if r['hash'] in rows:continue
   rows[r['hash']]={'hash':r['hash'],'block':r['block'],'source':name,'classification':'unclassified_pool_overlap_candidate','cashflow_ETH':r['native_after_gas_ETH'],'boundary':'root sender+entry only; not complete strategy','five_minute_marked_USD':r['five_minute']['USD'],'missing_assets':r['five_minute']['missing_assets']}
 assert len(rows)==16491
 (R/'全候选证据索引.json').write_text(json.dumps({'method':'One unique row per candidate hash; heterogeneous accounting boundaries explicitly retained. Do not sum cashflow as MEV.','count':len(rows),'rows':sorted(rows.values(),key=lambda r:(r['block'],r['hash']))},indent=2))
 hs=set();timeline=[];heads={r['block']:r['timestamp'] for r in load('full_window_evidence.json')['rows']}
 for name in ['unified_target_valuation.json','expanded_scope_valuation.json']:
  for r in load(name)['rows']:
   eligible=r.get('eligible_exchange_candidate',r.get('category')=='pool_swap_compatible')
   if not eligible:continue
   assert r['hash'] not in hs;hs.add(r['hash']);ts=r.get('timestamp',heads.get(r['block']))
   timeline.append({'hash':r['hash'],'block':r['block'],'UTC':datetime.fromtimestamp(ts,timezone.utc).isoformat(),'source':name,'strict_marked_change_USD':r['strict']['USD'],'five_minute_marked_change_USD':r['five_minute']['USD'],'five_minute_missing_assets':r['five_minute']['missing_assets']})
 assert len(timeline)==1352
 (R/'全部兑换时间线.json').write_text(json.dumps({'method':'Known-address exchange candidates, not all-event completeness; asset net change is negative of shortfall; gas excluded.','count':len(timeline),'rows':sorted(timeline,key=lambda r:(r['block'],r['hash']))},indent=2))
 files=[]
 for p in sorted(R.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.name=='evidence_manifest.json':continue
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  files.append({'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
 (R/'evidence_manifest.json').write_text(json.dumps({'note':'Integrity inventory; hashes do not certify ownership, source truth, counterfactual causality, or full event coverage. Superseded/failed raw responses retained as provenance, not automatically accepted evidence.','file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'files':files},indent=2))
 print('Indexed',len(rows),'candidates,',len(timeline),'exchanges;',len(files),'files;',sum(r['bytes'] for r in files),'bytes')
if __name__=='__main__':main()
