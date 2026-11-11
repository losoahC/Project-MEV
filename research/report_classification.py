import json,csv,re,hashlib
from pathlib import Path
from decimal import Decimal as D,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
LABELS={'strong_closed_cycle_evidence':'闭环套利结构证据较强','closed_cycle_nonpositive_cashflow':'有循环路径但本笔净现金流非正','liquidity_position_operation':'流动性头寸操作，须扣除本金与核算费用','lending_or_liquidation_operation':'借贷或清算相关，须核算债务与抵押资产','nonfungible_position_operation':'NFT或其他非同质化头寸相关','other_token_inventory_open':'其他代币库存未闭合','external_funding_or_unresolved_protocol':'外部资金流入或协议事件待解释','multipool_positive_unproven_cycle':'多池正现金流，但未证实资产循环','insufficient_cycle_evidence':'循环套利证据不足'}
def main():
 c=load('candidate_classification.json');g=load('sandwich_structure_groups.json');case=load('strong_case_verified.json');v=load('classification_validation.json');assert v['failed']==0
 a={r['hash']:r for r in load('all_candidate_accounting.json')['rows']};strong=[r for r in c['rows'] if r['category']=='strong_closed_cycle_evidence'];paired={r['hash'] for x in g['groups'] for r in x['legs']};lpclosed=[r for r in c['rows'] if r['category']=='liquidity_position_operation' and a[r['hash']]['other_token_inventory_closed']]
 old_lp_cash=sum((D(r['root_boundary_cashflow_ETH']) for r in lpclosed),D(0));same=[r for r in strong if r['association']=='same_block_next_pool_swap_opposite'];paired_strong=[r for r in strong if r['hash'] in paired]
 lines=['# 套利与攻击关联判定报告','',
 '**已对全部 13,623 笔候选进行第一轮证据分类，并将前后交易配对核算。** 找到 1,170 笔闭环套利结构证据较强的记录，其中 144 笔在同块、目标池的下一笔可见兑换中反向交易；另识别 449 组同发起地址的前后夹击结构。它们是不同层次、相互重叠的证据集合，不能相加。','',
 '最重要的结论：不能把先前的 25,694.87 ETH 账户现金流小计当成套利总利润。它混有 LP 本金回收，也可能只记录了跨交易策略赚钱的一半。原始收支账仍然有效，本轮补的是经济含义。','',
 '## 1. 全体候选如何分类','',
 '| 主要类别 | 笔数 |','|---|---:|']
 for k in LABELS:lines.append(f"| {LABELS[k]} | {c['summary'][k]['count']:,} |")
 lines+=['',
 '类别互斥，按头寸/借贷风险、库存、外部资金与未知事件、循环路径依次判断。流动性和清算相关交易也可能包含 MEV，但不能直接使用纯循环套利的利润算法。库存未闭合也不等于亏损或没有套利。','',
 '本轮从交易发起地址和入口合约出发，沿实际调用纳入参与执行的辅助合约，并排除识别到的池和代币合约。这个“操作范围”不等于已证明同一实际所有人。因此，本轮库存计数不能直接与旧表仅合并发起/目标地址的计数相比。','',
 '强结构类须同时满足：可观察到至少两个不同池组成的定向代币循环；其他 ERC-20 净库存闭合；扣 gas 后 ETH/WETH 净额为正；未识别到 LP、债务、NFT 操作、未解释事件或外部资金流入。兼容事件签名不等于池工厂已全面验证；尚未观察到的协议负债和跨交易成本仍可能存在。','',
 f"这 1,170 笔单笔操作范围现金流小计为 {D(c['summary']['strong_closed_cycle_evidence']['operational_cashflow_ETH']):,.6f} ETH，但其中 {len(paired_strong)} 笔已匹配到前后夹击结构。**该小计不是已确认总利润，必须与前手和其他组成交易合并。**",'',
 '## 2. 本金回收为何不能当利润','',
 f"识别到 306 笔流动性头寸相关交易。其中原先被标记‘其他 ERC-20 库存为零’的 {len(lpclosed)} 笔，旧账户范围现金流小计达 {old_lp_cash:,.6f} ETH。这个数不能整体计作套利收益；还需核算 LP 份额减少、初始投入、领取手续费及价格变化。",'',
 '例如原现金流最大的一笔，先出现 V3 Burn 和 Collect，再兑换资产。这是撤出头寸并领取资产的证据，不是单靠“最后收到更多 WETH”就能证明获利。[Uniswap V3 事件定义](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/interfaces/pool/IUniswapV3PoolEvents.sol)区分了流动性移除、领取资产和交换。','',
 '## 3. 前后配对结果','',
 f"在目标池的相邻兑换中，要求前手、目标、后手处于同块，前后手由同一地址发起，前手与目标净交易方向一致、后手反向。得到 **{g['summary']['episode_count']} 组**，涉及 {g['summary']['unique_leg_count']} 笔唯一组成交易、{g['summary']['target_count']} 笔目标记录。共享组成交易会合并，避免重复扣费或计收益。",'',
 f"其中 **{g['summary']['closed_without_position_events']} 组**其他代币库存闭合，且未识别到头寸或债务事件；**{g['summary']['positive_closed_episodes']} 组**净现金流为正。84 组含负值在内的现金流合计为 **{D(g['summary']['closed_net_cashflow_ETH']):,.9f} ETH**。这个值只覆盖该条件子集，不是全事件 MEV，也不能与 1,170 笔的单笔小计相加。",'',
 '此规则会漏掉跨块、多地址、非相邻或其他协议上的策略，也没有证明所有参与地址归属。未被配对不意味着没有前手成本。','',
 '## 4. 已详细核对的一组夹击案例','',
 f"区块 **{case['block']}** 中，位置 **9 → 10 → 11** 分别是前手、目标兑换、后手。前后手发起地址一致，两个池均通过历史工厂登记核对。",'',
 '| 组成 | 扣费后操作范围现金流（ETH） |','|---|---:|',
 f"| [前手](https://etherscan.io/tx/{case['front_transaction']}) | {D(case['front_cashflow_ETH']):,.9f} |",
 f"| [后手](https://etherscan.io/tx/{case['hash']}) | {D(case['operational_net_ETH']):,.9f} |",
 f"| 两笔合计 | **{D(case['paired_net_ETH']):,.9f}** |",'',
 f"[目标兑换](https://etherscan.io/tx/{case['target']})位于两笔之间。后手路线是 **WETH → PEPE → WETH**：投入 {D(case['input_WETH']):,.9f} WETH，收回 {D(case['output_WETH']):,.9f} WETH；扣除 {D(case['direct_fee_recipient_payment_ETH']):,.9f} ETH 的直接区块费用接收者付款及 {D(case['gas_ETH']):,.9f} ETH gas，后手本身增加 567.68 ETH。但加上前手的损失，两笔净额只有 12.08 ETH。",'',
 '### 固定路径的局部反事实','',
 '从 V2 Sync/Swap 日志还原目标前后储备，并用官方 0.3% 费率整数公式精确复现第一腿。第二个 V3 池在同块前手中发生过变化，因此不能直接用前一区块报价；这里重建了报价相关的价格、活动流动性和 WETH 余额，再通过历史 Quoter 只读调用验证。[V2 公式](https://raw.githubusercontent.com/Uniswap/v2-periphery/master/contracts/libraries/UniswapV2Library.sol)、[V3 存储与交换逻辑](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/UniswapV3Pool.sol)、[Quoter](https://raw.githubusercontent.com/Uniswap/v3-periphery/main/contracts/lens/Quoter.sol)。','',
 f"实际条件下，重建报价精确返回 **{case['output_WETH']} WETH**，与链上成交一致。只移除中间目标交易的储备影响，保持前手、本金、路径及费用不变重新报价，第二腿输出变为 **{case['counterfactual_second_leg_output_WETH']} WETH**。",'',
 '| 模型条件 | 两笔合计净额（ETH） |','|---|---:|',
 f"| 实际目标兑换存在 | {D(case['paired_net_ETH']):,.9f} |",
 f"| 仅移除该目标，其他条件固定 | {D(case['counterfactual_paired_net_ETH']):,.9f} |",
 f"| 两种条件的差额 | {D(case['fixed_strategy_target_increment_ETH']):,.9f} |",'',
 '**判断：这组具有强烈的夹击套利证据。** 在上述固定策略模型中，中间目标交易使该组合从负值变为正值。它不意味着整场攻击造成的收益就是这个差额：更早的攻击交易和其他市场状态仍保留，费用与策略规模也被固定。模型不是完整区块重放；实际无目标时，交易可能不提交或因保护条件回滚，不能断言一定实现模型亏损。','',
 '## 5. 现在能回答到什么程度','',
 '- 已完成全体候选的第一轮分类，并发现了不能把本金及后手现金流直接当利润的具体问题。',
 '- 已识别同地址前后夹击结构，并完成一组有真实成交复现和局部反事实支持的详细案例。',
 '- 尚不能给出全事件准确套利总利润：其他币种库存、LP 初始本金、跨交易/跨地址主体、外部资产以及全事件反事实仍未闭合。',
 '- 优先后续工作是估值夹击组的其他资产、配对 LP 头寸初始投入，并扩大固定路径或完整重放检验；不把无法解释的金额直接累加。','',
 '## 6. 可复核交付','',
 '- [全部候选判定明细（中文）](套利判定明细_中文.csv)',
 '- [前后夹击组明细（中文）](夹击分组明细_中文.csv)',
 '- [完整分类证据](candidate_classification.json)、[夹击组证据](sandwich_structure_groups.json)',
 '- [详细案例及模型结果](strong_case_verified.json)、[历史报价原始请求与响应](strong_case_quoter_reconstruction.json)、[工厂核验](strong_case_factory_checks.json)',
 f"- [本轮验证](classification_validation.json)：{v['passed']} 项通过，0 项失败。",'']
 (R/'套利判定报告.md').write_text('\n'.join(lines))
 with (R/'套利判定明细_中文.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['交易哈希','区块','主要判定','目标关联等级','操作范围扣费后ETH现金流','匹配到夹击组','操作范围地址','其他代币净额','证据JSON文件'])
  for r in c['rows']:w.writerow([r['hash'],r['block'],LABELS[r['category']],r['association'],r['operational_cashflow_ETH'],'是' if r['hash'] in paired else '否',';'.join(r['operational_boundary']),json.dumps(r['other_token_net_raw']),'candidate_classification.json'])
 with (R/'夹击分组明细_中文.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['组号','区块','发起地址','组成交易','目标交易','其他代币库存闭合且无识别头寸事件','组净现金流ETH','其他代币净额'])
  for i,x in enumerate(g['groups'],1):w.writerow([i,x['block'],';'.join(x['senders']),';'.join(r['hash'] for r in x['legs']),';'.join(x['targets']),'是' if x['closed_without_recognized_position_events'] else '否',x['net_cashflow_ETH'],json.dumps(x['other_token_net_raw'])])
 marker='<!-- classification-update -->';end='<!-- classification-update-end -->'
 for name in ['研究报告_综合版.md','后续时段补充报告.md','候选收支缺口完成报告.md','任务完成度审查.md']:
  p=R/name;text=re.sub(re.escape(marker)+r'.*?'+re.escape(end)+r'\n\n','',p.read_text(),flags=re.S)
  banner=f'{marker}\n> **新增经济含义核查：** 已对 13,623 笔候选分类，识别 LP 本金回收和前后手成本。旧现金流小计不能当作套利利润。详见[套利判定报告](套利判定报告.md)：一组后手增加 567.68 ETH 的案例，合并前手后净额为 12.08 ETH，并有局部反事实检验。\n{end}\n\n';p.write_text(banner+text)
 print('Classification reports published; strong legs in paired episodes',len(paired_strong),'LP-affected old closed rows',len(lpclosed),'LP cashflow',old_lp_cash)
if __name__=='__main__':main()
