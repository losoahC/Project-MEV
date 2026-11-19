"""Document the snapshot reconciliation and robustness checks; unresolved totals remain null."""
import json
from decimal import Decimal
from src.visualization.common import ROOT

def build():
    d=json.loads((ROOT/'data/processed/loss_reconciliation.json').read_text());b=json.loads((ROOT/'data/processed/balance_reconciliation.json').read_text());a=d['asset_ledger_USD']
    def m(v):return f'USD {Decimal(v):,.2f}'
    lines=['# M6：资产快照、经济归因及稳健性','',
    '## 主要发现与边界','',
    f"在 Ethereum 区块 {b['opening_block']:,} 的期初状态与 {b['closing_block']:,} 的期末状态之间，16 个地址的 ETH/WETH/USDT/USDC 共 64 个账户全部对平。期末余额按 {d['valuation_timestamp_utc']} 前一个已完成分钟的统一市场价格估值，合计 **{m(a['closing'])}**；其中黑名单状态下的稳定币余额为 **{m(a['frozen_closing'])}**，其余地址余额为 {m(a['nonblacklisted_closing'])}。这只是限定资产、限定地址、限定区块的快照，不能称为全事件存量或黑客最终控制资产。",'',
    '教师 PDF 第 8 页约 USD 2B 的原意是冻结的稳定币；本次独立历史合约状态和余额核查支持这一量级。黑名单余额不证明资产已归还 Binance，也不证明发生了相同金额的经济交易损失。全事件初始盗款、已追回/扣押、不可追回和因果 MEV 总额仍为 null。','',
    '## 两类账的定义','',
    '资产账使用同一固定期末参考价格，逐币种与逐地址核对：期初余额 + 观测流入 − 观测流出 − gas + WETH 发行/销毁 = 历史 RPC 期末余额。聚合 16 地址时内部转账抵消。链上转账的流入可能包含 DEX 买入、解包及其他转换，因此不能求和当作初始盗款。','',
    '经济账用净资产交换计算参考短缺；主表对每笔兑换取该笔执行前已完成分钟的独立市场价格。逐笔同口径，但其总和是交易时点短缺，不是固定估值日的资产存量。另在固定期末价格下重估，作为价格与时间敏感性；该差额也包含之后的市场运动，不是纯执行损失。','',
    '| 固定期末价格下的资产账分录 | USD |','|---|---:|']
    for k,label in [('opening','期初余额'),('external_inflow','外部流入，含转换'),('external_outflow','外部流出，含转换'),('gas','gas 支出'),('wrapper_net','WETH 发行/销毁净额'),('closing','期末余额'),('frozen_closing','其中：黑名单稳定币余额'),('nonblacklisted_closing','其中：其他余额'),('unexplained_change','未解释余额差额')]:lines.append(f'| {label} | {m(a[k])} |')
    lines += ['', 'WETH 初次出现约 668.132228390272982085 WETH 的负差额，源于 canonical WETH 解包销毁没有普通 Transfer 事件。补入原始 Withdrawal 日志后对平；没有把该销毁解释为丢失资金。gas 依据实际收据，币数使用整数最小单位，价格估值另行计算。','',
    '| 资产 | 期末数量 | 其中黑名单余额 | 固定参考 USD/单位 |','|---|---:|---:|---:|']
    for r in d['fixed_mark_assets']:lines.append(f"| {r['symbol']} | {r['units']['closing']} | {r['units']['frozen_closing']} | {r['reference_USD']} |")
    lines += ['',
    'ETH/WETH 使用明确的封装兑付平价。USDT 使用 Coinbase USDT/USD；期末 Coinbase USDC/USD 无有效分钟记录，改用实际 Binance USDCUSDT 日档分钟价乘同期 Coinbase USDT/USD。该替代来源在每条记录中明确标注，没有假定 USDC/USD 或 USDT/USD 恒等于 1。USDT getBlackListStatus 与 USDC isBlacklisted 在同一历史期末区块读取；该状态为 observed，USD 为 estimated。','',
    '## 执行短缺与选定套利收益','',
    f"经过唯一交易哈希及仓位/债务/内部混合流排除后，{d['economic_trade_time_sample']['rows']} 笔完整估值交换的交易时点参考短缺净额为 {m(d['economic_trade_time_sample']['signed_net_shortfall_USD'])}。其中不利短缺 {m(d['economic_trade_time_sample']['adverse_only_USD'])}，有利差额 {m(d['economic_trade_time_sample']['favorable_only_USD'])}。这是受覆盖限制的观测样本，不是全事件损失，不是其上限或因果 MEV 下限。189 条原双向交换缺少完整交易时点价格，未填零。",'',
    f"固定期末价格可估值 {d['economic_fixed_mark_sample']['rows']} 笔，净差额为 {m(d['economic_fixed_mark_sample']['signed_net_shortfall_USD'])}。它与 621 笔交易时点样本的覆盖不同，不能把两个总额之差解释成纯价格敏感性。",'',
    '| 三个选定套利案例的 ETH 收益分配 | ETH |','|---|---:|']
    p=d['selected_3_arbitrage_ETH']
    for k,label in [('gross_after_pool_fees_before_gas_and_builder_ETH','已含池手续费的毛利'),('gas_ETH','gas'),('direct_builder_ETH','可识别直接 builder 付款'),('net_after_gas_and_builder_ETH','searcher 保留净收益')]:lines.append(f'| {label} | {p[k]} |')
    lines += ['',
    '上述三个互异区块/互异交易的收益完整按明确地址边界重算，但不代表全事件套利收益。gas 和 builder 付款是这笔毛利内部的分配，不能再加到毛利之上当作额外受害损失。整块 proposer 收款有其他交易来源；A3 builder/proposer 出资控制边界未知，不能反推出精确 builder 利润。完整 sandwich 净收益另作案例，不能用后腿现金流替代整组利润，也没有反事实受害增量损失。','',
    '## 稳健性','',
    '1. **行情及时间**：最大五个异常交易的 Coinbase/Binance ETH 替代行情与 1/5/15 分钟参考均有逐笔表。Binance ETHUSDT 经 USDT/USD 换算；不借助稳定币恒等假设。THOR 三案另测试 5/15 分钟前 ETH/BTC 同时点价格。','']
    pair=d['paired_price_timing_sensitivity']
    lines += [f"同一交易集合配对检验：{pair['same_transactions']} 笔；交易时点净短缺 {m(pair['trade_time']['signed_net_shortfall_USD'])}，固定期末净短缺 {m(pair['fixed_closing_mark']['signed_net_shortfall_USD'])}。这一区别同时包含执行后的市场变化；主结论不把它等同为 MEV。",'',
    '2. **钱包边界**：保留 16 个教师线索、排除未独立证实的钱包 13、再排除仅有 Arbitrum 关联补证的钱包 9，分别计算；不合并任何未知接收人。','',
    '| 钱包场景 | 交易时点样本数 | 交易时点净短缺 | 固定价格期末余额 |','|---|---:|---:|---:|']
    for s in d['ownership_sensitivity']:lines.append(f"| {s['scenario']} | {s['primary_trade_time']['rows']} | {m(s['primary_trade_time']['signed_net_shortfall_USD'])} | {m(s['snapshot_closing_USD'])} |")
    lines += ['', '3. **缺失拍卖数据**：逐一剔除 relay，报告保留提交记录数、仍有 relay 交付证据的所选结果数、以及独立链上 proposer 付款匹配数。','',
    '| 剔除 relay | 保留提交观测 | 保留交付来源支持的结果 | 链上付款匹配 |','|---|---:|---:|---:|']
    for s in d['missing_relay_sensitivity']:lines.append(f"| {s['removed_relay'] or '无'} | {s['submission_observations']} | {s['selected_delivered_outcomes_with_retained_relay_support']} | {s['selected_onchain_proposer_payment_matches']} |")
    lines += ['',
    '剔除 Ultrasound 后 relay 交付支持降至 1/3，而链上实际付款仍为 3/3。这反映来源集中，不能用链上付款补造历史有效输家出价、截止时间或完整竞争强度。','',
    '## 图 8 解读与限制','',
    '左上是四资产固定价格余额账，右上将期末余额拆为黑名单稳定币和其他余额；冻结是期末余额子集。左下仅展示三笔已重建套利毛利的去向，单位为 ETH，避免跨域拼出虚假总额。右下补充 621 笔互异完整估值交易的交易时点参考短缺，并列明全事件尚无足够证据的总量；与固定期末余额和 ETH 利润不相加。图不把未识别项填零，也不将教师背景数字放进不闭合的全事件瀑布。','',
    '本样本没有穷尽链外追回、交易所账户、其他链、其他代币、最终受益控制关系或无 MEV 反事实。因此不能给出“被盗额 − 冻结额 = MEV 损失”的等式，也不能认证全事件不可追回余额。对于无法独立核验的教师近似背景金额，仅保留其原始定义并明确研究缺口。','',
    '每条快照、价格、黑名单调用、转账边和 wrapper 日志均附原始路径；支持表见 `data/processed/balance_reconciliation.{json,parquet}`、`loss_reconciliation.json`、`economic_fixed_mark_rows.json` 及 `reports/tables/fig08_asset_ledger.parquet`。','',
    '## 复现','', '```bash','python -m src.reconciliation.balances --legacy /不存在的目录','python -m src.reconciliation.summary','python -m src.visualization.fig08_loss_reconciliation','python -m src.reporting.milestone6','python -m pytest -q','```','',
    '本次公开响应已缓存，可离线执行；初次缺少历史 RPC/行情对象才使用 balances --online。当前尚待完成最终综合学术报告、12–15 页可演示结果与逐项最终验收。']
    lines += ['', '## 扩展原币种库存核对', '', '三笔来源地址 sweep 中出现的全部 64 种资产已按 16 地址逐一核对历史余额，共 1,024 个账户全部对平，无缺失调用。详见 [初始资产库存报告](initial_asset_inventory.md) 与 asset_inventory.json。该表按原币种报告，不能跨币种求和；其他来源、其他链、独占盗款单位及最终所有权仍未认证。', '', '另重新查询缺价币种的公开 Coinbase 分钟行情，保留全部成功、404 和 429 响应；限流后等待并以每秒至多一次请求重试。未取得精确有效分钟成交或价格的记录仍为 null，当前主筛查 621 条完整估值未改变。']
    (ROOT/'reports/milestone6_report.md').write_text('\n'.join(lines)+'\n');print('Wrote snapshot reconciliation and robustness report')

if __name__=='__main__':build()
