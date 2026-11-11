"""Validate complete gap closure against frozen hashes and original receipts."""
import json,gzip,argparse
from pathlib import Path
from collections import defaultdict
from decimal import Decimal as D,getcontext
from rawtrace_native import parse
from screen_expanded import net_for
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--require-complete',action='store_true');args=p.parse_args()
 start=load('candidate_gap_start.json');initial=set(start['missing_hashes']);candidates=load('full_candidates.json')['rows'];account=load('all_candidate_accounting.json');byh={r['hash']:r for r in account['rows']};raw=load('candidates_rawtrace_native.json');rh={r['hash']:r for r in raw['rows']};checks=[]
 drpc=load('drpc_candidate_native.json') if (R/'drpc_candidate_native.json').exists() else {'rows':[],'coverage':[],'errors':[]}
 dr={r['hash']:r for r in drpc['rows']};overlap=set(rh)&set(dr)
 def check(name,ok,detail):checks.append({'check':name,'passed':bool(ok),'detail':detail})
 check('原始缺口清单唯一且数量正确',len(start['missing_hashes'])==len(initial)==12934,len(initial))
 check('全候选覆盖保持完整',len(byh)==len(candidates)==13623 and set(byh)=={r['hash'] for r in candidates},len(byh))
 remaining=[h for h in sorted(initial) if byh[h]['native_ETH'] is None]
 if args.require_complete:check('原始12934笔缺口全部补齐',not remaining,len(remaining))
 check('原有689笔证据没有丢失',all(r['native_ETH'] is not None for h,r in byh.items() if h not in initial),sum(h not in initial for h in byh))
 check('轨迹结果没有重复',len(rh)==len(raw['rows']),len(rh))
 check('区块轨迹没有重复候选',len(dr)==len(drpc['rows']),len(dr))
 check('两家公开来源逐地址原生币净额一致',all(rh[h]['native_net_wei']==dr[h]['native_net_wei'] for h in overlap),len(overlap))
 rh.update(dr)
 old93=load('candidate_accounting_93.json')['rows']
 applicable=[r for r in old93 if r['hash'] in byh];outside=[r for r in old93 if r['hash'] not in byh]
 check('原案例中91笔后续候选净现金流回归一致',len(applicable)==91 and all(D(r['net_ETH_WETH_after_gas'])==D(byh[r['hash']]['net_ETH_WETH_after_gas']) for r in applicable),{'compared':len(applicable),'old_pre_target_examples_not_in_current_candidate_scope':[r['hash'] for r in outside]})
 check('原案例范围差异仅为两笔目标前交易',len(outside)==2 and all(r['relative_position']<0 for r in outside),len(outside))
 bulk=load('bulk_native.json');bulk_checks=[]
 for c in candidates:
  h=c['hash']
  if h not in dr or not any(x['first']<=c['block']<=x['last'] for x in bulk['coverage']):continue
  n={a:int(v) for a,v in dr[h]['native_net_wei'].items()};v=int(dr[h]['root_value'],16);sender=dr[h]['root_from'];recipient=dr[h]['root_to'];n[sender]=n.get(sender,0)+v;n[recipient]=n.get(recipient,0)-v
  bulk_checks.append({a:v for a,v in n.items() if v}=={a:int(v) for a,v in bulk['internal_net_wei'].get(h,{}).items() if int(v)})
 check('原批量区间逐地址净额回归一致',all(bulk_checks),len(bulk_checks))
 errors=[];byblock=defaultdict(list)
 for c in candidates:byblock[c['block']].append(c)
 for n,cs in sorted(byblock.items()):
  folder='window_raw' if n<=26301940 else 'extension_raw'
  recs={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))}
  blocktraces=defaultdict(list)
  if any(c['hash'] in dr for c in cs):
   tracefile=R/'drpc_trace_raw'/f'{n}.json.gz'
   for t in json.loads(gzip.decompress(tracefile.read_bytes()))['result']:
    if t.get('transactionHash'):blocktraces[t['transactionHash']].append(t)
   if set(blocktraces)!=set(recs):errors.append([n,'block trace/receipt transaction coverage'])
   for h,ts in blocktraces.items():
    if any(t['blockNumber']!=n or t['blockHash']!=recs[h]['blockHash'] or t['transactionPosition']!=int(recs[h]['transactionIndex'],16) for t in ts):errors.append([h,'trace block identity'])
  for c in cs:
   h=c['hash'];a=byh[h];rec=recs[h]
   if int(rec['blockNumber'],16)!=n or rec['from']!=c['from'] or rec['to']!=c['to']:errors.append([h,'receipt identity'])
   if int(rec['gasUsed'],16)*int(rec['effectiveGasPrice'],16)!=int(c['gas_fee_wei']):errors.append([h,'gas'])
   if net_for(rec,{c['from'],c['to']})!=c['sender_and_to_token_net_raw']:errors.append([h,'token net'])
   if h not in rh:continue
   r=rh[h]
   try:
    d=blocktraces[h] if h in dr else json.loads(gzip.decompress((R/'rawtrace_raw'/(h+'.json.gz')).read_bytes()));rebuilt=parse(h,d)
    if any(rebuilt[k]!=r[k] for k in rebuilt if k!='source'):errors.append([h,'trace reparse'])
    if r['root_from'].lower()!=rec['from'] or (r['root_to'] or '').lower()!=(rec['to'] or ''):errors.append([h,'trace identity'])
    if bool(r['root_error'])!=(int(rec['status'],16)==0):errors.append([h,'trace status'])
    if sum(map(int,r['native_net_wei'].values())):errors.append([h,'native conservation'])
    value=sum((D(v)/D(10)**18 for x,v in r['native_net_wei'].items() if x in {rec['from'],rec['to']}),D(0))
    # During a live download, the trace snapshot can be newer than accounting.
    if a['native_ETH'] is not None and value!=D(a['native_ETH']):errors.append([h,'account-boundary cashflow'])
   except Exception as e:errors.append([h,str(e)])
 check('原始回执与完整调用树逐笔重算一致',not errors,{'candidate_receipts':len(candidates),'raw_traces':len(rh),'errors':errors[:30]})
 check('每笔净现金流只扣一次gas',all(r['native_ETH'] is None or D(r['net_ETH_WETH_after_gas'])==D(r['native_ETH'])+D(r['WETH_delta'])-D(r['gas_ETH']) for r in byh.values()),len(byh))
 check('缺失值保留为空',all(r['net_ETH_WETH_after_gas'] is None for r in byh.values() if r['native_ETH'] is None),len(remaining))
 closed=[r for r in byh.values() if r['native_ETH'] is not None and r['other_token_inventory_closed']]
 check('库存闭合子集汇总一致',sum((D(r['net_ETH_WETH_after_gas']) for r in closed),D(0))==D(account['summary']['closed_group_cashflow_ETH']),len(closed))
 out={'initial_missing':len(initial),'gap_filled':len(initial)-len(remaining),'remaining':len(remaining),'remaining_hashes':remaining,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'limitation':'Closes public native-cashflow data gap only. Does not establish beneficial ownership, complete portfolio P&L, or event-causal MEV.'}
 (R/'candidate_gap_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['remaining_hashes','checks']},ensure_ascii=False,indent=2))
 if out['failed']:raise SystemExit(1)
if __name__=='__main__':main()
