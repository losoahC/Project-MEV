import json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
def main():
 rows={r['hash']:r for r in json.loads((R/'full_candidates.json').read_text())['rows']}
 for f,k in [('pancake_coverage_completion.json','candidates'),('late_candidate_completion.json','rows')]:
  for r in json.loads((R/f).read_text())[k]:
   if r['hash'] in rows:rows[r['hash']]={**rows[r['hash']],'prior_targets':rows[r['hash']]['prior_targets']+r['prior_targets']}
   else:rows[r['hash']]=r
 cl={r['hash']:r['category'] for f in ['candidate_classification.json','incremental_candidate_classification.json'] for r in json.loads((R/f).read_text())['rows']};out=[]
 for w in [0,1,3,5]:
  hs={h for h,r in rows.items() if any(p['block_distance']<=w for p in r['prior_targets'])};c=Counter(cl[h] for h in hs);out.append({'maximum_block_distance':w,'candidate_count':len(hs),'category_counts':dict(c),'strong_closed_cycle_count':c['strong_closed_cycle_evidence']})
 (R/'candidate_window_sensitivity.json').write_text(json.dumps({'method':'Same downloaded universe; union all recorded pool links per hash before filtering distance. Structural classification not causality. Counts at shorter windows are nested subsets, not independent estimates.','rows':out},indent=2));print('Candidate window checks',[(r['maximum_block_distance'],r['candidate_count']) for r in out])
if __name__=='__main__':main()
