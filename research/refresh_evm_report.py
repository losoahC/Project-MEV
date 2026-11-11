import json,re
from pathlib import Path
from collections import Counter
from decimal import Decimal as D
R=Path(__file__).resolve().parent
def main():
 v=json.loads((R/'expanded_EVM_validation.json').read_text());d=json.loads((R/'expanded_EVM_attribution.json').read_text());limits=json.loads((R/'EVM_execution_limit_classification.json').read_text());nonce=json.loads((R/'nonce_preserving_EVM_sensitivity.json').read_text());c=v['counts'];nr=[r for r in nonce['rows'] if r['status']=='verified_nonce_preserving_sensitivity'];neg=sum(D(r['cashflow_difference_ETH'])<0 for r in nr)
 text=f'''<!-- EVM_BATCH_START -->
### 批量执行归因核验

当前候选中有 {d['eligible_experiments']} 个无后续发送者 nonce 冲突的独立移除目标实验，已尝试 {len(d['rows'])} 个，{v['verified_experiments']} 个通过原始响应独立复算。覆盖 {v['verified_blocks']} 个区块，实际前缀去重 {v['unique_actual_prefix_transactions_checked']} 笔交易的状态、gas 和日志已核对。前缀验证只支持截至被评估交易的执行区间，不掩盖某些区块更晚交易的差异。

通过的实验中，现金流差为正 {c.get('positive_difference',0)} 个、负 {c.get('negative_difference',0)} 个、零 {c.get('zero_difference',0)} 个；反事实被评估交易回滚 {c.get('counterfactual_revert',0)} 个、成功 {c.get('counterfactual_success',0)} 个。这些是实验数量，不是新增套利交易数量；同一交易可对应不同目标干预，差额不可直接加总。未完成实验仍保留在分母中。

未解决项分类：{json.dumps(limits['counts'],ensure_ascii=False)}。余额不足表示固定交易序列无法合法继续，不能通过人为注资、把收益填零或删除失败交易来完成归因。暂时超时与模型执行约束分别记录。

另有 9 个后续 nonce 冲突案例：用同发送者、nonce 和费率的零金额空调用替换目标兑换，保留后续交易参数；{len(nr)} 个独立敏感性实验通过，{neg} 个现金流差为负。替换交易消耗 21000 gas，会改变目标钱包费用和余额，因此必须与直接删除目标的主实验分开，不能静默合并。

复现入口：verify_expanded_evm.py；结果：expanded_EVM_attribution.json、expanded_EVM_validation.json、EVM_execution_limit_classification.json、nonce_preserving_EVM_sensitivity.json。所有临时错误与成功请求响应均留存。
<!-- EVM_BATCH_END -->'''
 p=R/'最终研究报告_2026-11-11.md';s=p.read_text()
 if '<!-- EVM_BATCH_START -->' in s:s=re.sub(r'<!-- EVM_BATCH_START -->.*?<!-- EVM_BATCH_END -->',lambda _:text,s,flags=re.S)
 else:s=s.replace('## 老师要求的回应与实际限制',text+'\n\n## 老师要求的回应与实际限制')
 p.write_text(s);print('refreshed',v['verified_experiments'],'verified experiments')
if __name__=='__main__':main()
