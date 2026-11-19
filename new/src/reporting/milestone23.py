from decimal import Decimal
from pathlib import Path
import json

import pandas as pd

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT

E=Decimal(10)**18


def build():
    cases=read_json(ROOT/'data/processed/arbitrage_cases.json')
    sandwich=read_json(ROOT/'reports/case_studies/S1_sandwich.json')
    auctions=read_json(ROOT/'data/processed/auction_outcomes.json')
    coverage=read_json(ROOT/'data/processed/auction_coverage.json')
    delivery=pd.read_parquet(ROOT/'data/processed/auction_deliveries.parquet')
    price=pd.read_parquet(ROOT/'reports/tables/fig02_price_observations.parquet')
    comparison=pd.read_parquet(ROOT/'reports/tables/fig05_bid_comparison.parquet')
    lines=['# DEX 套利与 MEV 拍卖研究：第二、三阶段\n',
        '本阶段按新计划优先重建三笔真实 DEX 套利，再关联同区块拍卖交付与 proposer 收款。结论覆盖所选案例及已取得的 relay 窗口，不是全事件 MEV 总额。\n',
        '## 1. 三个可验证的套利案例\n',
        '| 案例 | 区块及 UTC 时间 | 扣池费后的毛价差 ETH | gas ETH | 可识别直接付款 ETH | 扣 gas/直接付款后净收益 ETH |',
        '|---|---|---:|---:|---:|---:|']
    for c in cases:
        lines.append(f"| [{c['case_id']}](case_studies/{c['case_id']}_arbitrage.md) | {c['block']} · {c['timestamp_utc']} | {c['gross_after_pool_fees_before_gas_and_builder_ETH']} | {Decimal(c['gas_wei'])/E} | {Decimal(c['identified_builder_payment_wei'])/E} | {c['net_after_gas_and_builder_ETH']} |")
        chapter=[f"# {c['case_id']} · {c['route_label']}\n",
            f"交易：[完整哈希](https://etherscan.io/tx/{c['tx_hash']}) `{c['tx_hash']}`。目标交易：[完整哈希](https://etherscan.io/tx/{c['target']}) `{c['target']}`。\n",
            f"区块 {c['block']}，UTC {c['timestamp_utc']}，目标索引 {c['target_index']}，套利索引 {c['actor_index']}。\n",
            f"记账边界是发送者 `{c['sender']}` 及本次执行合约 `{c['executor']}`；不把其他路由器归入共同所有权。\n",
            f"扣池费后的毛价差 {c['gross_after_pool_fees_before_gas_and_builder_ETH']} ETH，gas {Decimal(c['gas_wei'])/E} ETH，直接向区块 fee recipient 支付 {Decimal(c['identified_builder_payment_wei'])/E} ETH，净现金流 {c['net_after_gas_and_builder_ETH']} ETH。非 WETH 代币净库存为零，池流量层面的 WETH 盈余也与该毛价差精确一致。\n",
            '| 池地址 | 输入合约 / 数量 | 输出合约 / 数量 | Swap log index |', '|---|---|---|---|']
        for leg in c['route']:
            chapter.append(f"| `{leg['pool']}` | `{leg['input_token']}` / {leg['input_quantity']} | `{leg['output_token']}` / {leg['output_quantity']} | {leg['swap_log_indices']} |")
        chapter.extend(['\n上表按池的净流量列出经济腿；同一池可多次调用，不能将净腿顺序误作 EVM 回调顺序。精确的执行顺序、交易前后储备、V3 sqrtPrice/tick/活跃流动性、原始来源路径见 [完整 JSON](%s_arbitrage.json) 和 [图 3 交互附表](../figures/fig03_transaction_reconstruction.html)。'%c['case_id'],
            '\n所有代币数量按历史 RPC decimals 处理；池 token0/token1/factory 及 V3 fee tier 来自归档的历史合约调用。V3 重建是交易前后价格及活跃流动性状态，不代表已经重新计算全部 tick bitmap、fee growth、LP 头寸及协议债务。',
            '\n判定依据是实际库存闭合、跨池有向闭环、正净现金流和同区块同池反向关联。没有把全部净利润因果归到目标兑换；没有用钱包所有者或品牌的推测替代地址级收支。池费已经包含在实际输出里，不能再从净收益重复扣除。'])
        (ROOT/f"reports/case_studies/{c['case_id']}_arbitrage.md").write_text('\n'.join(chapter))
    lines.extend(['\n以上三笔均非本研究已识别夹击组的前后腿；它们分别在独立区块，且所关联目标均位于 16 个标签线索钱包的交易样本。选择包含一笔较大多池闭环及两笔容易核验的双池闭环，不是随机样本，也不宜外推事件总额。\n',
        '毛价差来自池净资金流和执行边界的 ETH/WETH 收支两套核算，两者在三个案例中精确相等；gas 来自真实收据；直接付款来自过滤回滚祖先后的完整调用树。零非 WETH 残余是交易内库存闭合，不证明交易前没有头寸或场外风险。\n',
        '## 2. 池状态、价格和费用机制\n',
        f"图 2 使用 A1 周围八个实际区块、{len(price)} 个 ETH/USDT 池 Swap 事件。每个点是该笔真实数量上的平均执行价，含池费，不是统一规模的假想报价或池中间价。外部参考为 Coinbase 前一完整 UTC 分钟 ETH/USD，USDT/USD 也按真实行情换算。没有可用 USDC/USD 分钟数据的池被排除，不假设 USDC 恰好等于 $1。",
        '\nHTML 可在真实 UTC 时间与交易顺序坐标之间切换。同区块各交易拥有相同区块时间；顺序视图用 `block offset + index / block transaction count`，它不是秒级时间，不伪造区块内时间戳。',
        '\n图中的价格在大额交易后进一步偏离，随后部分回落；这八个区块内没有回到外部参考价。不同池与不同交易规模的点不能直接等同于同一规模机会的收敛路径。',
        '\nV2 前状态由 Sync 后储备减 Swap 净变动恢复。三个套利中的五个 V2 实际腿均能由 997/1000 模型精确重现。完整底表中的其他交易可能选择次优输出，非零模型残差保持为残差，不能强制归到 MEV。输出单位上的无费曲线冲击、费率效果和模型残差分别保存，不与套利 ETH 利润相加。',
        '\nV3 前状态从 parent block 的 slot0/liquidity 开始，按交易和日志顺序推进，处理活跃 tick 范围内 Mint/Burn，再由 Swap 事件更新 sqrtPrice、tick 和活跃流动性。尚未把它当成完整 V3 EVM 重放。四个案例区块的哈希另经本次公开 RPC 新读取核对。',
        '\n## 3. 一例完整夹击机制\n',
        f"S1 的同一发送者在区块 {sandwich['block']} 索引 9 和 11 两腿夹住索引 10 的钱包兑换：前腿与目标在同一池同向、后腿反向，前后两腿非 WETH 库存闭合。前腿净现金流 {sandwich['front_cashflow']['net_after_gas_and_builder_ETH']} ETH，后腿 {sandwich['back_cashflow']['net_after_gas_and_builder_ETH']} ETH，两腿合计 **{sandwich['episode_net_ETH']} ETH**。",
        '\n单看后腿的约 567.68 ETH 会忽略前腿投入，不能把它当作整组利润。这是观测到的方向性夹击和现金流；受害者的额外损失仍需单独、可执行的反事实，不能用整组利润直接替代。详情见 [完整案例](case_studies/S1_sandwich.json)。',
        '\n## 4. 三个拍卖结果与链上付款\n',
        '| 案例 | Slot | Relay 声明及实际 proposer 收款 ETH | 实际付款发起地址 | Builder margin proxy |', '|---|---:|---:|---|---|'])
    for a in auctions:
        lines.append(f"| {a['case_id']} | {a['slot']} | {Decimal(a['onchain_proposer_payment_wei'])/E} | `{a['proposer_payment_payers'][0]}` | {str(Decimal(a['builder_margin_proxy_wei'])/E)+' ETH（部分代理）' if a['builder_margin_proxy_wei'] is not None else '未解决：payer 与 fee recipient 不同'} |")
    lines.extend(['\n三笔 proposer 收款全部通过转付合约的 SELFDESTRUCT 分支完成，金额与转付交易的顶层 funding value、relay 声明金额精确一致。每个内部转付只算一次。原始交易哈希与 traceAddress 见 `data/processed/proposer_payments.parquet`。',
        '\nA1/A2 的付款者就是对应区块 fee recipient，可以形成该地址的部分执行 ETH 余额代理。A3 使用另一个付款地址，未证明共同经济控制，因此其 builder margin proxy 为 `null`，没有将外部支付从 fee recipient 的余额重复减去。三个案例都区分了 proposer 总收款、fee recipient 实际承担的部分、其他流出以及自身 gas。',
        '\nBuilder proxy 不含代币头寸、共识提款、场外支出、融资和完整所有权边界，不是精确利润。整块 proposer 付款与其他策略和交易有关，不能把它全部归到所选一笔套利。',
        '\n## 5. 可见竞价竞争与基线\n',
        f"从四家 relay 的旧分页缓存中，按 block hash、slot、proposer 和金额核对后，共保留 **{coverage['unique_nonconflicting_delivered_blocks']} 个去重交付区块 / {coverage['window_blocks']} 个窗口区块**。某个历史记录的哈希与当前缓存区块头不同，已排除该条报告；其他 relay 的一致记录仍可支持同块。",
        f"\n本次查询三个目标 slot 的四家 relay `builder_blocks_received` 接口，取得 **{coverage['submission_rows_observed']} 条提交观测**。9 个初始请求因 limit=1000 被拒绝，按明确错误重试 limit=500，原失败响应和后续响应均归档。部分接口实际返回数超过请求 limit，因此只标为数量限制/覆盖不确定，不能凭返回数量断言穷尽。",
        '\n非 delivered block hash 的记录包括候选版本修订，也可能包括晚到竞价，不能统称为有效截止前的输家。可见其他提交的最高数值有时高于最终交付数值；缺乏选择时点、撤销和到达时序验证时，不能据此断言拍卖违反最高价规则。',
        '\n另按 relay 逐组检查了提交时间戳，保存在 `auction_timing_assessment.json` 和 `fig05_bid_timing.parquet`。例如 A1 的 Ultrasound 视图中，所保留交付 payload 最早提交在 slot 起点后 985 ms，而数值最高的其他提交在 1,494 ms；A3 对应是 947 ms 和 1,150 ms。这些是接口声明的到达时间，不是 proposer 的选择时间，不能把“早于首次可见交付候选”擅自当作有效竞价截止。',
        f"\n同一 delivered payload 在不同 relay 可能使用不同 builder 签名公钥，当前有 {int(delivery.builder_pubkey.isna().sum())} 个这种身份未解决的区块。交付只记一块，公钥不被合并成未经验证的品牌，也不重复计为多个获胜区块。",
        f"\n描述性基线是区块 {26300640}–{26300769} 的 130 块，观测交付 {coverage['baseline_observed_deliveries']} 块；事件阶段是 {26300770}–{26303950} 的 3,181 块，观测交付 {coverage['event_observed_deliveries']} 块。两段时长和数据覆盖不同，分布比较不能单独证明攻击造成的收入增量。", 
        '\n图 4 分开所选 searcher 毛价差的分配与整块付款账本；图 5 展示可见提交、交付与其他提交对比、公钥交付频次、付款时间序列、所选实际毛价差与整块付款关系，以及基线/事件分布。真实毛价差只是已实现机会的样本，不是可获得最大套利机会。',
        '\n## 6. 复现与证据边界\n',
        '从 `new/` 运行：\n\n```bash\npython -m src.arbitrage.reconstruct --online\npython -m src.auction.reconstruct --online\npython -m src.visualization.fig02_eth_price_dislocation\npython -m src.visualization.fig03_transaction_reconstruction\npython -m src.visualization.fig04_mev_value_attribution\npython -m src.visualization.fig05_auction_results\npython -m pytest -q\n```\n',
        '已取得公开来源后，去掉 `--online` 即使用归档请求结果；`--legacy /不存在的目录` 可验证 M2/M3 不读取父项目原缓存。原始 RPC、HTTP 响应含来源和 UTC 采集时间；`data/raw/public_index.json` 记录归档 JSON 的 SHA-256。部分早期 RPC 记录保存了解析响应及原响应体哈希；后续记录另保留原响应体 base64，不能声称早期记录拥有尚未保存的精确原响应字节。',
        '\n尚未完成的是全事件归因、完整竞价截止时序、全部 builder 所有权和收益、完整 LP 分配、外部价格源交叉敏感性，以及 M4 异常交易、M5 THORChain、M6 最终对账及演示稿。身份标签缺口仍按 M1 进度记录。',
        '\n协议方法参考：[Uniswap V2 池机制](https://developers.uniswap.org/docs/protocols/v2/concepts/pools)、[Flashbots Relay Fundamentals](https://docs.flashbots.net/flashbots-mev-boost/relay)、[Relay API 定义](https://github.com/flashbots/relay-specs/blob/main/apis/relay/data/builder_blocks_received.yaml)。参考文档解释机制；本文数值由所链接的本地原始交易及处理表计算。'])
    (ROOT/'reports/milestone23_report.md').write_text('\n'.join(lines))
    stats={'three_arbitrage_cases':len(cases),'selected_net_ETH':str(sum((Decimal(c['net_after_gas_and_builder_ETH']) for c in cases),Decimal(0))),'sandwich_episode_net_ETH':sandwich['episode_net_ETH'],'price_observations':len(price),'auction_coverage':coverage,'unresolved_relay_specific_builder_keys':int(delivery.builder_pubkey.isna().sum()),'complete_event_MEV_total_established':False}
    (ROOT/'reports/milestone23_summary.json').write_text(json.dumps(stats,indent=2))
    print('Generated M2/M3 report and three detailed case-study reports')


if __name__=='__main__':
    build()
