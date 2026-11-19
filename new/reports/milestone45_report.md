# M4 / M5：异常执行与 THORChain 跨链证据

## 结论与研究边界

M4 从事件窗口重算 810 条具有双向净资产交换的钱包/交易记录；621 条具备全部资产的严格合约身份及参考价格，241 条满足输入 > USD 100,000 且损失率 > 5%。其中 5 条超过 USD 1M，2 条超过 USD 5M。最大五案已逐笔调查，但仍不能证明故意亏损、补偿性获利或反事实增量 MEV 损失。

M5 完成三条 ETH → THORChain → BTC 的真实兑换匹配。三条路径均找到时间在先的三段普通 ETH 转账连接涉案钱包；这只支持资金流关联，不认证共同控制，也不证明被换出的每个单位 ETH 都源自盗款。兑换发生于 2026-11-17，与 10 月 Ethereum MEV 样本分开报告。

## M4 方法与覆盖

用完整成功调用树计算各钱包原生 ETH 流，按日志计算 ERC20 净资产，修正 WETH Deposit/Withdrawal，合并 ETH/WETH；gas 单独记账。若涉及仓位、债务事件或 16 个钱包内部混合转移，不作为简单兑换损失候选。只对 Coinbase 精确 Ethereum 合约映射及通过历史 RPC decimals 核对的资产估值；未知资产、缺失价格和冲突价格保留 null。

主估值取兑换前一个已完成 Coinbase 分钟收盘价，输入输出使用相同时间参考。Binance ETHUSDT 替代行情用同期 USDT/USD 转换，不假定 USDT 永远等于 USD 1。另测 5/15 分钟前行情与允许向前寻找 5 分钟缺价的情形。币种引用与每个价格对象都有原始文件指针。

筛查只覆盖 M1 所选交易中可识别 swap、且钱包净资产有正有负的记录；单边净流、未被 M1 纳入的交易、全生命周期和其他链不在样本。记录单位为钱包/交易而非互斥事件，不能把筛查表金额机械求和当作事件总损失。

| 案例 | 钱包 | 输入参考价值 | 输出参考价值 | 差额估计 | 损失率 |
|---|---:|---:|---:|---:|---:|
| [N1](case_studies/N1_abnormal_swap.md) | 5 | $29,961,300.00 | $21,587,296.08 | $8,374,003.92 | 27.95% |
| [N2](case_studies/N2_abnormal_swap.md) | 4 | $29,962,500.00 | $23,915,444.58 | $6,047,055.42 | 20.18% |
| [N3](case_studies/N3_abnormal_swap.md) | 5 | $19,974,400.00 | $15,695,652.83 | $4,278,747.17 | 21.42% |
| [N4](case_studies/N4_abnormal_swap.md) | 4 | $19,975,200.00 | $16,718,091.17 | $3,257,108.83 | 16.31% |
| [N5](case_studies/N5_abnormal_swap.md) | 10 | $9,987,600.00 | $7,986,831.05 | $2,000,768.95 | 20.03% |

五案均存在零中间限额与非零最终 unwrap 下限并存。N3/N4 入口不是 Universal Router execute，但成功内部调用中实际包含 execute；不能因入口不支持就宣称没有保护。没有足够证据在“普通滑点、紧急清算、可识别 MEV 增量损失、故意自损”间做确定分类，因此五案保留 insufficient_evidence。

## M5 三条完整配对

| 案例 | 入金 ETH | 到账 BTC | 参考差额 USD | ETH→BTC 区块时间差 |
|---|---:|---:|---:|---:|
| [T1](case_studies/T1_thorchain.md) | 36 | 1.00484202 | $316.17 | 2899 秒 |
| [T2](case_studies/T2_thorchain.md) | 61 | 1.68897154 | $754.33 | 1511 秒 |
| [T3](case_studies/T3_thorchain.md) | 40 | 1.10797406 | $429.72 | 1296 秒 |

## M5 数据覆盖及限制

初步有界发现查询 43 个地址、828 条普通交易记录，找到 441 条可解码 THOR memo 候选。这个数字不是 441 条已认证的涉案兑换；仅上述三案完成多源匹配与入金前资金流关联。每地址普通发现查询只读第一页，部分存在未耗尽分页，内部转账和其他链未穷尽。

旧 Nine Realms 域名不可解析；按当前官方文档改用 Liquify 公共网关。地址过滤曾返回 403，保留失败响应；按文档支持的精确 txid 查询成功。一次 txid 请求网络失败后使用带 type/limit 的标准查询重试，两个响应均保留。没有绕过私人 API 权限或验证码。

费用字段依据 [Midgard 原生类型定义](https://pkg.go.dev/gitlab.com/thorchain/midgard/openapi/generated/oapigen) 及 [THORChain 数量约定](https://dev.thorchain.org/concepts/querying-thorchain.html)；memo 别名见 [官方 memo 文档](https://dev.thorchain.org/concepts/memos)。

## 图表和复现

图 6 是按参考差额排序的异常候选，不是意图或因果排行榜；HTML 提供五案详情与证据。图 7 用每条路径在自身入金时点的 USD 参考值统一宽度，ETH 和 BTC 的原币数量同时标注；差额支路已包括最终到账中的费用，不重复加费用。不同路径估值时点不同，不能当作同日资产存量。PNG/SVG 适用于浅底演示；静态版已做图像检查，HTML 已生成但本阶段未宣称完成浏览器交互测试。

```bash
python -m src.anomaly.screen
python -m src.anomaly.investigate
python -m src.thorchain.discover
python -m src.thorchain.reconstruct
python -m src.visualization.fig06_suspicious_wallets
python -m src.visualization.fig07_thorchain_flows
python -m src.reporting.milestone45
python -m src.ingestion.catalog
python -m pytest -q
```

初次缺失公开响应时，可对 screen / investigate / discover / reconstruct 使用 --online；当前证据齐备，THOR 三案无需旧 research/ 缓存即可离线重算。

M6 全事件资产对账、Figure 8、钱包边界和缺失拍卖敏感性、最终研究报告和 12–15 页演示仍需完成。不能用教师 PDF 约 USD 2B 冻结稳定币的背景数字替代这些缺口。
