import json
from decimal import Decimal as D,getcontext
from pathlib import Path
getcontext().prec=90
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 checks=[]
 def check(n,x):checks.append({'check':n,'passed':bool(x)})
 q=load('research_quality_analysis.json');s=q['same_sample_price_robustness'];d=q['local_effect_decomposition'];cf=load('all_scope_v2_counterfactuals.json');good=[r for r in cf['rows'] if r['status']=='verified_local_fixed_input'];w=load('candidate_window_sensitivity.json')['rows'];old=load('v2_local_counterfactuals.json');original={r['target']:r for r in old['rows'] if r['status']=='verified_local_fixed_input'}
 check('共同价格样本哈希唯一且各时点均有数值',len({r['hash'] for r in s['rows']})==s['common_sample_count']==1094 and all(set(r['shortfall_USD_by_lag'])=={'1','5','15'} for r in s['rows']))
 check('共同价格样本各时点独立汇总一致',all(sum((D(r['shortfall_USD_by_lag'][k]) for r in s['rows']),D(0))==D(s['shortfall_USD_by_lag'][k]) for k in ['1','5','15']))
 check('96笔不具备共同价格的交易被排除而非填零',s['strict_base_count']-s['common_sample_count']==s['excluded_from_fixed_comparison']==96)
 check('77个目标唯一及251个链接分类齐全',len(good)==len({r['target'] for r in good})==77 and sum(cf['summary']['statuses'].values())==len(cf['rows'])==251)
 check('原70个局部结果保留不变',all(r['target_output_reduction_raw']==original[r['target']]['target_output_reduction_raw'] for r in good if r['target'] in original) and len({r['target'] for r in good}&set(original))==70)
 check('前手与目标实际成交整数公式复现',all(t['input']*997*t['before'][1-t['input_side']]//(1000*t['before'][t['input_side']]+997*t['input'])==t['output'] for r in good for t in [r['front_swap'],r['target_swap']]))
 check('移除前手的输出独立重算',all(int(r['without_front_output_raw'])==r['target_swap']['input']*997*r['front_swap']['before'][1-r['target_swap']['input_side']]//(1000*r['front_swap']['before'][r['target_swap']['input_side']]+997*r['target_swap']['input']) for r in good))
 check('局部分解逐笔加总与总额一致',all(abs(sum((D(x) for x in r['components_USD'].values()),D(0))-D(r['shortfall_from_prefront_spot_USD']))<D('1e-60') for r in d['rows']) and abs(sum(map(D,d['components_USD'].values()),D(0))-D(d['sum_components_USD']))<D('1e-60'))
 check('分解前置影响等于原始反事实估值合计',D(d['components_USD']['preceding_trade_local_effect'])==D(cf['summary']['marked_target_output_reduction_USD']))
 check('筛选窗口与分类计数守恒',all(sum(r['category_counts'].values())==r['candidate_count'] and r['strong_closed_cycle_count']<=r['candidate_count'] for r in w) and [r['candidate_count'] for r in w]==sorted(r['candidate_count'] for r in w))
 ident=load('price_identity_quality_audit.json');rs=ident['rows'];check('身份佐证子集汇总一致',sum(r['all_asset_identities_corroborated'] for r in rs)==ident['summary']['identity_corroborated_rows']==1175 and abs(sum((D(r['shortfall_USD']) for r in rs if r['all_asset_identities_corroborated']),D(0))-D(ident['summary']['identity_corroborated_shortfall_USD']))<D('1e-18'))
 check('候选主审查仍通过',load('event_completion_validation.json')['failed']==0)
 out={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks};(R/'research_quality_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,ensure_ascii=False));assert out['failed']==0
if __name__=='__main__':main()
