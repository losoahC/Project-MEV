import json,gzip
from pathlib import Path
from decimal import Decimal as D,getcontext
from rawtrace_native import parse
R=Path(__file__).resolve().parent
getcontext().prec=70
def load(n):return json.loads((R/n).read_text())
def main():
 checks=[]
 def check(name,ok,detail):checks.append({'check':name,'passed':bool(ok),'detail':detail})
 ledger=load('extension_ledger.json');old=load('window_ledger.json');v=load('extension_valuation.json');native=load('extension_rawtrace_native.json');cand=load('all_candidate_accounting.json');full=load('full_candidates.json')
 check('新增连续区块无缺失',not ledger['errors'] and ledger['blocks_successful']==ledger['last_block']-ledger['first_block']+1,ledger['blocks_successful'])
 check('两个时段连续且不重叠',old['last_block']+1==ledger['first_block'],'26301940 -> 26301941')
 check('所有净流出日志均有分类',len(v['rows'])==sum(any(int(x)<0 for x in r['net_token_raw'].values()) for r in ledger['rows']),len(v['rows']))
 check('新增原生币证据完整',native['completed']==native['requested']==len(native['rows']) and not native['errors'],len(native['rows']))
 check('原生币逐笔守恒',all(sum(map(int,r['native_net_wei'].values()))==0 for r in native['rows']),len(native['rows']))
 bad=[]
 for r in native['rows']:
  try:assert parse(r['hash'],json.loads(gzip.decompress((R/'rawtrace_raw'/(r['hash']+'.json.gz')).read_bytes())))['native_net_wei']==r['native_net_wei']
  except Exception as e:bad.append({'hash':r['hash'],'error':str(e)})
 check('调用树父子完整及重算一致',not bad,bad or len(native['rows']))
 check('十笔批量接口与完整轨迹一致',len(load('bulk_crosscheck.json'))==10 and all(r['matches'] for r in load('bulk_crosscheck.json')),10)
 oldnat={r['hash']:r for r in load('native_evidence.json')['rows']};matched=[]
 for r in load('rawtrace_crosscheck.json')['rows']:
  if r['hash'] not in oldnat:continue
  ref=oldnat[r['hash']];n={a:int(v) for a,v in r['native_net_wei'].items()}
  if not ref.get('includes_top_level_value') and not ref['source'].startswith('https://etherscan.io/'):
   value=int(r['root_value'],16);a=r['root_from'];b=r['root_to'];n[a]=n.get(a,0)+value;n[b]=n.get(b,0)-value
  matched.append({a:v for a,v in n.items() if v}=={a:int(D(v)*10**18) for a,v in ref['native_internal_net_eth'].items() if D(v)})
 check('五笔旧证据与新轨迹一致',len(matched)==5 and all(matched),len(matched))
 check('未核实合约不得估值',all(r['strict_shortfall_usd'] is None and r['up_to_5min_stale_shortfall_usd'] is None for r in v['rows'] if r['unverified_contracts']),v['summary']['unverified_contract_count'])
 check('完整候选无遗漏或重复',len(cand['rows'])==len(full['rows'])==len({r['hash'] for r in cand['rows']}) and {r['hash'] for r in cand['rows']}=={r['hash'] for r in full['rows']},len(cand['rows']))
 check('原生币缺失没有按零利润处理',all(r['net_ETH_WETH_after_gas'] is None for r in cand['rows'] if r['native_ETH'] is None),cand['summary']['native_missing'])
 check('严格与宽松价格分别核算',all(r['up_to_5min_stale_shortfall_usd']==r['strict_shortfall_usd'] for r in v['rows'] if r['strict_shortfall_usd'] is not None),'strict subset unchanged')
 for key in ['strict_shortfall_usd','up_to_5min_stale_shortfall_usd']:
  check('估值加总 '+key,sum((D(r[key]) for r in v['rows'] if r[key] is not None),D(0))==D(v['summary'][key]['sum_usd']),v['summary'][key])
 out={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'limitations':'Data consistency only; not completeness of event, entity ownership, economic inventory valuation, or causal MEV.'}
 (R/'extension_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
 if out['failed']:raise SystemExit(1)
if __name__=='__main__':main()
