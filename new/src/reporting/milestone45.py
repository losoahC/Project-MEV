"""Write reviewed M4/M5 interpretations from processed evidence; never import old research conclusions."""
import json
from decimal import Decimal
from src.visualization.common import ROOT

def read(path):return json.loads((ROOT/path).read_text())
def money(v):return f'${Decimal(v):,.2f}'

def build():
    coverage=read('data/processed/anomaly_coverage.json')
    cases=read('data/processed/anomaly_case_studies.json')
    thor=read('data/processed/thorchain_paths.json')
    text=['# M4 / M5：异常执行与 THORChain 跨链证据','',
    '## 结论与研究边界','',
    f"M4 从事件窗口重算 {coverage['two_sided_swap_wallet_rows']} 条具有双向净资产交换的钱包/交易记录；{coverage['fully_valued_rows']} 条具备全部资产的严格合约身份及参考价格，{coverage['qualified_rows']} 条满足输入 > USD 100,000 且损失率 > 5%。其中 5 条超过 USD 1M，2 条超过 USD 5M。最大五案已逐笔调查，但仍不能证明故意亏损、补偿性获利或反事实增量 MEV 损失。",'',
    'M5 完成三条 ETH → THORChain → BTC 的真实兑换匹配。三条路径均找到时间在先的三段普通 ETH 转账连接涉案钱包；这只支持资金流关联，不认证共同控制，也不证明被换出的每个单位 ETH 都源自盗款。兑换发生于 2026-11-17，与 10 月 Ethereum MEV 样本分开报告。','',
    '## M4 方法与覆盖','',
    '用完整成功调用树计算各钱包原生 ETH 流，按日志计算 ERC20 净资产，修正 WETH Deposit/Withdrawal，合并 ETH/WETH；gas 单独记账。若涉及仓位、债务事件或 16 个钱包内部混合转移，不作为简单兑换损失候选。只对 Coinbase 精确 Ethereum 合约映射及通过历史 RPC decimals 核对的资产估值；未知资产、缺失价格和冲突价格保留 null。','',
    '主估值取兑换前一个已完成 Coinbase 分钟收盘价，输入输出使用相同时间参考。Binance ETHUSDT 替代行情用同期 USDT/USD 转换，不假定 USDT 永远等于 USD 1。另测 5/15 分钟前行情与允许向前寻找 5 分钟缺价的情形。币种引用与每个价格对象都有原始文件指针。','',
    '筛查只覆盖 M1 所选交易中可识别 swap、且钱包净资产有正有负的记录；单边净流、未被 M1 纳入的交易、全生命周期和其他链不在样本。记录单位为钱包/交易而非互斥事件，不能把筛查表金额机械求和当作事件总损失。','',
    '| 案例 | 钱包 | 输入参考价值 | 输出参考价值 | 差额估计 | 损失率 |','|---|---:|---:|---:|---:|---:|']
    for r in cases:
        text.append(f"| [{r['case_id']}](case_studies/{r['case_id']}_abnormal_swap.md) | {r['wallet']} | {money(r['input_reference_USD'])} | {money(r['output_reference_USD'])} | {money(r['loss_USD'])} | {Decimal(r['loss_rate']):.2%} |")
        guards=r['observed_nonzero_minimum_bounds']
        md=[f"# {r['case_id']}：钱包 {r['wallet']} 的异常执行调查",'',f"交易：[Ethereum 原始交易](https://etherscan.io/tx/{r['tx_hash']})。钱包 `{r['address']}`；区块 {r['block']:,}，交易索引 {r['transaction_index']}，UTC {r['timestamp_utc']}。",'',
        f"输入 {money(r['input_reference_USD'])}，输出 {money(r['output_reference_USD'])}，参考价值差额 **{money(r['loss_USD'])}（{Decimal(r['loss_rate']):.2%}）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。",'',
        f"同一钱包在样本中共 {r['wallet_qualifying_swap_count']} 条筛查合格记录。同块共享池邻居 {len(r['same_block_pool_neighbors'])} 条；完整重算套利关联：`{r['verified_arbitrage_cases_linked']}`。相邻顺序和共享池不证明利润来源或控制关系。",'',
        f"已解码 {r['observed_zero_minimum_bound_count']} 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `{r['router_limit_inspection']['status']}`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。",'',
        '## 流动性、价格影响与邻居核查','',
        'JSON 的 `major_ETH_USDT_pool_price_states` 保存主要 ETH/USDT 池实际执行前后价格与活动流动性；`v2_mechanical_leg_checks` 保存 V2 Sync 储备、常数乘积曲线/fee/residual 分解。该分解只适用于已检验的单腿，不能代表整笔混合 V2/V3/V4 多跳路由的无 MEV 反事实。','',
        '`observed_profitable_inventory_closed_neighbor_candidates` 是明确地址边界下的暂定流量；`other_incoming_transfers_next_10min` 是观察到的后续转账，未认定为补偿。逐项原始来源、共享池、完整哈希、交易顺序和资金流均见配套 JSON。','',
        '## 保护下限与敏感性','', '```json',json.dumps(guards,indent=2),'```','',
        '| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |','|---|---:|---:|---:|---|']
        for label,v in r['sensitivity'].items():
            md.append(f"| {label} | {money(v['input_reference_USD']) if v['input_reference_USD'] is not None else 'null'} | {money(v['output_reference_USD']) if v['output_reference_USD'] is not None else 'null'} | {money(v['loss_USD']) if v['loss_USD'] is not None else 'null'} | {v['qualifies']} |")
        md += ['',f"分类：**{r['final_classification']}**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：{r['classification_detail']}",'',f"完整可审计数据：[JSON]({r['case_id']}_abnormal_swap.json)。来源收据 `{r['receipt_evidence']}`、轨迹 `{r['trace_evidence']}`、新读取收据 `{r['fresh_receipt_evidence']}`；这些路径以项目 new/ 为根目录。"]
        (ROOT/f"reports/case_studies/{r['case_id']}_abnormal_swap.md").write_text('\n'.join(md)+'\n')
    text += ['', '五案均存在零中间限额与非零最终 unwrap 下限并存。N3/N4 入口不是 Universal Router execute，但成功内部调用中实际包含 execute；不能因入口不支持就宣称没有保护。没有足够证据在“普通滑点、紧急清算、可识别 MEV 增量损失、故意自损”间做确定分类，因此五案保留 insufficient_evidence。','',
    '## M5 三条完整配对','',
    '| 案例 | 入金 ETH | 到账 BTC | 参考差额 USD | ETH→BTC 区块时间差 |','|---|---:|---:|---:|---:|']
    for r in thor:
        text.append(f"| [{r['case_id']}](case_studies/{r['case_id']}_thorchain.md) | {r['input_ETH']} | {r['output_BTC']} | {money(r['estimated_execution_shortfall_USD'])} | {r['inclusion_delay_seconds']} 秒 |")
        md=[f"# {r['case_id']}：ETH → THORChain → BTC",'',f"入金 UTC **{r['deposit_utc']}**；[ETH 入金](https://etherscan.io/tx/{r['ethereum_deposit']}) → [BTC 出金](https://blockstream.info/tx/{r['bitcoin_txid']})。",'',
        f"`{r['source_address']}` 通过已核验 router `{r['router']}` 入金 {r['input_ETH']} ETH；vault `{r['vault']}`。memo `{r['memo']}`。",'',
        f"收款 `{r['destination_address']}`，实际输出 {r['output_BTC']} BTC（{r['BTC_per_ETH']} BTC/ETH）。比特币已确认区块 {r['bitcoin_confirmed_block']['block_height']}；ETH inclusion 至 BTC 区块时间相差 {r['inclusion_delay_seconds']} 秒。两链时间戳精度不同，这不是精确服务延迟。",'',
        '## 入出匹配','',
        'Ethereum RPC 核对成功收据、区块成员关系、ABI 入参、msg.value 与 Deposit 日志一致；THORNode 与 Midgard 按入金哈希核对来源、资产、memo、出金哈希/接收人/金额；独立 Bitcoin 索引核对确认状态、实际 vout 和 OUT:入金哈希的 OP_RETURN。THORChain ETH 数量是 1e8 精度，不能错按 Ethereum 的 1e18。','',
        '## 时间在先的资金流关联','', '| UTC | 转账哈希 | 发送方 → 接收方 | ETH |','|---|---|---|---:|']
        for l in r['funding_path']:
            md.append(f"| {l['timestamp_utc']} | `{l['tx_hash']}` | `{l['sender']}` → `{l['recipient']}` | {Decimal(l['amount_wei'])/10**18} |")
        md += ['', '每段均为实际成功普通 ETH 转账，时间递增且转账金额至少覆盖下一段金额。未穷尽其他来源和中途支出，不作独占盗款单位归属或地址共同控制结论。首次浏览器发现的另三笔 funding_link 晚于入金，已被重建器拒绝使用；当前路径改用入金之前的证据。','',
        '## 费用与估值','',
        f"ETH 与 BTC 均按入金前已完成分钟 {r['reference']['minute_utc']} 的 Coinbase USD 收盘价估值：ETH={r['reference']['ETH_USD']}，BTC={r['reference']['BTC_USD']}。输入 {money(r['input_reference_USD'])}，输出按同一参考时间估值 {money(r['output_reference_USD'])}，差额 {money(r['estimated_execution_shortfall_USD'])}。",'',
        f"入金 gas {r['ethereum_gas_ETH']} ETH（单列，约 {money(r['ethereum_gas_reference_USD'])}）；Midgard 报告网络扣费 {r['network_fee_BTC']} BTC，已包含在最终到账差额内。实际 BTC 整笔网络矿工费 {r['actual_bitcoin_network_fee_sats']} sat，与协议向用户扣费不同，不再重复相加。报告 LP fee 为 {r['reported_liquidity_fee_RUNE']} RUNE；未取得同口径 RUNE/USD 参考，保留原币种。",'',
        f"Streaming 片数 {r['streaming_swap']['count']}，报告 swapSlip={r['reported_swap_slip_bps']} bps。没有重建历史 THOR 池状态，因此不把 swapSlip 或 LP fee 再加为额外损失，也不将参考差额全部归为价格冲击。5/15 分钟前行情差额：`{r['sensitivity']}`。",'',
        '该跨链差额未与 Ethereum MEV 建立具体关联，不并入十月 MEV 总额。完整原始文件指针及字段：[JSON]('+r['case_id']+'_thorchain.json)。']
        (ROOT/f"reports/case_studies/{r['case_id']}_thorchain.md").write_text('\n'.join(md)+'\n')
    text += ['', '## M5 数据覆盖及限制','',
    '初步有界发现查询 43 个地址、828 条普通交易记录，找到 441 条可解码 THOR memo 候选。这个数字不是 441 条已认证的涉案兑换；仅上述三案完成多源匹配与入金前资金流关联。每地址普通发现查询只读第一页，部分存在未耗尽分页，内部转账和其他链未穷尽。','',
    '旧 Nine Realms 域名不可解析；按当前官方文档改用 Liquify 公共网关。地址过滤曾返回 403，保留失败响应；按文档支持的精确 txid 查询成功。一次 txid 请求网络失败后使用带 type/limit 的标准查询重试，两个响应均保留。没有绕过私人 API 权限或验证码。','',
    '费用字段依据 [Midgard 原生类型定义](https://pkg.go.dev/gitlab.com/thorchain/midgard/openapi/generated/oapigen) 及 [THORChain 数量约定](https://dev.thorchain.org/concepts/querying-thorchain.html)；memo 别名见 [官方 memo 文档](https://dev.thorchain.org/concepts/memos)。','',
    '## 图表和复现','',
    '图 6 是按参考差额排序的异常候选，不是意图或因果排行榜；HTML 提供五案详情与证据。图 7 用每条路径在自身入金时点的 USD 参考值统一宽度，ETH 和 BTC 的原币数量同时标注；差额支路已包括最终到账中的费用，不重复加费用。不同路径估值时点不同，不能当作同日资产存量。PNG/SVG 适用于浅底演示；静态版已做图像检查，HTML 已生成但本阶段未宣称完成浏览器交互测试。','',
    '```bash','python -m src.anomaly.screen','python -m src.anomaly.investigate','python -m src.thorchain.discover','python -m src.thorchain.reconstruct','python -m src.visualization.fig06_suspicious_wallets','python -m src.visualization.fig07_thorchain_flows','python -m src.reporting.milestone45','python -m src.ingestion.catalog','python -m pytest -q','```','',
    '初次缺失公开响应时，可对 screen / investigate / discover / reconstruct 使用 --online；当前证据齐备，THOR 三案无需旧 research/ 缓存即可离线重算。','',
    'M6 全事件资产对账、Figure 8、钱包边界和缺失拍卖敏感性、最终研究报告和 12–15 页演示仍需完成。不能用教师 PDF 约 USD 2B 冻结稳定币的背景数字替代这些缺口。']
    (ROOT/'reports/milestone45_report.md').write_text('\n'.join(text)+'\n')
    print('Wrote M4/M5 report and eight documented anomaly/cross-chain cases')

if __name__=='__main__':build()
