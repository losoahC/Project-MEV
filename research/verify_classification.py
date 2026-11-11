import json,gzip
from pathlib import Path
from decimal import Decimal as D,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 c=load('candidate_classification.json');groups=load('sandwich_structure_groups.json');case=load('strong_case_analysis.json');quote=load('strong_case_quoter_reconstruction.json');checks=[]
 def check(name,ok,detail):checks.append({'check':name,'passed':bool(ok),'detail':detail})
 check('全候选唯一分类且无遗漏',len(c['rows'])==13623==len({r['hash'] for r in c['rows']}) and {r['hash'] for r in c['rows']}=={r['hash'] for r in load('full_candidates.json')['rows']},13623)
 strong=[r for r in c['rows'] if r['category']=='strong_closed_cycle_evidence']
 check('强结构类通过所有排除条件',all(not r['other_token_net_raw'] and not r['liquidity_events'] and not r['debt_events'] and not r['nft_event_present'] and not r['unresolved_events'] and not r['external_funding_addresses'] and D(r['operational_cashflow_ETH'])>0 for r in strong),len(strong))
 check('强结构类资产路径闭环',all(len(r['token_cycle'])>=2 and len({e['pool'] for e in r['token_cycle']})==len(r['token_cycle']) and all(r['token_cycle'][i]['output_token']==r['token_cycle'][(i+1)%len(r['token_cycle'])]['input_token'] for i in range(len(r['token_cycle']))) for r in strong),len(strong))
 check('分类加总一致',sum(v['count'] for v in c['summary'].values())==13623 and all(D(v['operational_cashflow_ETH'])==sum((D(r['operational_cashflow_ETH']) for r in c['rows'] if r['category']==k),D(0)) for k,v in c['summary'].items()),len(c['summary']))
 legs=[r['hash'] for g in groups['groups'] for r in g['legs']]
 check('夹击分组没有重复计算同笔交易',len(legs)==len(set(legs)),len(legs))
 check('夹击组目标在前后交易之间',all(x['front_index']<x['target_index']<x['back_index'] for g in groups['groups'] for x in g['links']),len(groups['groups']))
 check('夹击组净额等于全部组成交易之和',all(D(g['net_cashflow_ETH'])==sum((D(r['cashflow_ETH']) for r in g['legs']),D(0)) for g in groups['groups']),len(groups['groups']))
 group=next(g for g in groups['groups'] if any(r['hash']==case['hash'] for r in g['legs']));assert len(group['legs'])==2
 check('重点案例首尾资产闭合且无已识别头寸操作',group['closed_without_recognized_position_events'],group['other_token_net_raw'])
 actual=D(int(quote['quotes']['actual']['response']['result'],16))/D(10)**18;baseline=D(int(quote['quotes']['without_target_first_leg']['response']['result'],16))/D(10)**18
 check('重建报价精确复现真实第二腿输出',actual==D(case['output_WETH']),str(actual))
 check('两个模型使用相同的第二池状态',quote['quotes']['actual']['request']['params'][2]==quote['quotes']['without_target_first_leg']['request']['params'][2],'Only input amount changes')
 check('重点案例两池通过历史工厂登记核查',len(load('strong_case_factory_checks.json'))==2 and all('0x'+r['response']['result'][-40:]==r['expected_pool'] for r in load('strong_case_factory_checks.json')),2)
 check('重点案例成本守恒',D(case['gross_spread_WETH'])-D(case['direct_fee_recipient_payment_ETH'])-D(case['gas_ETH'])==D(case['operational_net_ETH']),case['operational_net_ETH'])
 net=D(group['net_cashflow_ETH']);uplift=actual-baseline;counter=net-uplift
 case.update(front_transaction=group['legs'][0]['hash'],front_cashflow_ETH=group['legs'][0]['cashflow_ETH'],paired_net_ETH=str(net),counterfactual_second_leg_output_WETH=str(baseline),fixed_strategy_target_increment_ETH=str(uplift),counterfactual_paired_net_ETH=str(counter),actual_second_leg_quote_exactly_reproduced=True,counterfactual_scope='Remove only the immediately preceding target trade; hold front leg, route, WETH input, earlier trades, gas and direct payment fixed. Reconstruct second-pool price/liquidity and WETH balance after the front leg. Not a full-block reexecution, event-wide attribution, or behavioral equilibrium model.')
 case['interpretation']='Same-sender front/target/back sandwich structure. Back-leg positive cashflow must be combined with front-leg cost. A fixed-input, fixed-route two-pool quote model reproduces actual output exactly and measures removal of one target trade. The actual transaction could revert or not be submitted without the target; this is not full execution replay or event-wide MEV.'
 (R/'strong_case_verified.json').write_text(json.dumps(case,indent=2))
 check('重点案例移除目标后固定策略由盈利变负',net>0 and counter<0,{'actual_paired_net_ETH':str(net),'without_target_paired_net_ETH':str(counter),'increment_ETH':str(uplift)})
 out={'passed':sum(r['passed'] for r in checks),'failed':sum(not r['passed'] for r in checks),'checks':checks,'limitation':'Classifier coverage does not certify all protocols, ownership or global causal MEV. Counterfactual is fixed-strategy local sensitivity only.'}
 (R/'classification_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
 if out['failed']:raise SystemExit(1)
if __name__=='__main__':main()
