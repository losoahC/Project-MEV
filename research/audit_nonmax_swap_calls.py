import json
from pathlib import Path
from classify_incremental_candidates import traces
R=Path(__file__).resolve().parent;d=json.loads((R/'extended_cycle_counterfactual.json').read_text());failures=[r for r in d['fixed_input_mismatches'] if not r['exact_output_inverse_matches']];rows=[];cache={}
for f in failures:
 n=f['block'];h=f['hash']
 if n not in cache:cache[n]=traces(n)
 ts=[t for t in cache[n] if t.get('transactionHash')==h];calls=[]
 for t in ts:
  a=t.get('action',{});inp=a.get('input','')
  if a.get('to')==d['pool'] and inp.startswith('0x022c0d9f'):
   words=[inp[i:i+64] for i in range(10,len(inp),64)];calls.append({'trace_path':t['traceAddress'],'caller':a['from'],'amount0Out':str(int(words[0],16)),'amount1Out':str(int(words[1],16)),'recipient':'0x'+words[2][-40:],'raw_input':inp})
 ev=next(e for e in d['actual_swaps'] if e['hash']==h and e['log_index']==f['log_index']);matches=[c for c in calls if int(c['amount1Out' if ev['side']==0 else 'amount0Out'])==ev['output']];assert len(matches)==1
 rows.append({**f,'observed_swap':ev,'matching_pool_call':matches[0],'root_call':next(t['action'] for t in ts if not t['traceAddress']),'classification':'explicit_output_below_fixed_input_maximum','explanation':'Pool calldata requests the observed lower output. No evidence for recalculating this amount with a maximum-output rule under changed reserves. Need executor logic/whole-transaction replay.'})
(R/'nonmax_swap_call_audit.json').write_text(json.dumps({'rows':rows,'count':len(rows),'all_outputs_matched_explicit_calldata':True},indent=2));print('verified explicit output calls',len(rows))
