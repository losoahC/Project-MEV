# 新研究计划执行记录

更新：2026-11-18。以 `research_plan_supplied.md` 为当前工作规格；教师原 PDF 第 8–10 页已读取，文本及 SHA-256 记录在本目录。旧目录的结论未作为本轮已验收结果直接沿用。

| 里程碑 | 当前状态 | 已有证据与剩余验收 |
|---|---|---|
| M1 数据与钱包 | 数据管线及图 1 已交付；身份验收部分未完成 | 16 个历史地址线索、8 个地址独立来源交叉支持；本次新读 Etherscan 编号标签 0/16。真实兑换已重算，逐边证据已核对。需补其余身份及独立 canonical-chain 交叉检查 |
| M2 DEX 套利 | 三个实际案例及图 2/3 已交付 | 三个独立区块的闭环、完整原生调用树、池价格/流动性前后状态、扣 gas 和直接付款的 PnL 已重算；一组完整两腿夹击。全事件因果归因、完整 V3 tick/LP 重放和独立价格源敏感性仍待推进 |
| M3 MEV 拍卖 | 三个链上付款匹配及图 4/5 已交付 | 2,939 个去重交付区块；三个 slot 7,958 条可见提交；三个实际 proposer 付款精确匹配。完整截止前竞价簿不具备，A3 builder 共同所有权及利润代理未解决 |
| M4 异常交易 | 已完成观察样本 | 810 条双向净交换，621 条严格估值，241 条合格；最大五案已调查，图 6 已生成；意图/因果损失未解决 |
| M5 THORChain | 已完成三条观察路径 | ETH 收据、THORNode、Midgard、已确认 BTC 输出多源匹配；资金关联有时间在先证据，非所有权推断；图 7 已生成 |
| M6 对账与报告 | 本地成果已生成，演示保存待批准 | 图 8、学术报告、64 资产库存账及 14 页预览/讲稿已生成；全事件未知数量明确列示 |

## M1 已验证结果

- 样本区块范围 26,300,640–26,303,950；实际上有转账事件的时间为 **2026-10-29 20:24:23 至 2026-10-30 07:02:47 UTC**。这是事件窗口，不是完整黑客历史。
- 导入 151 个旧钱包历史分页对象，选择 1,207 个有相关候选交易的区块，核对 1,640 笔交易的收据、区块哈希和区块内位置；没有因缺失区块头或收据被排除的所选交易组。
- 产生 57,042 条去重转账边及 1,155 个 V2/V3 兼容 Swap 事件。交易中的无关日志、垃圾代币及路由中间腿也保留；不能据此声称全部是黑客经济活动。
- 只有 1,110 条边拥有严格同合约 ETH/USDT/USDC 参考价格。其他边为 `null`，不设为零；估值覆盖不足以求全事件损失。
- 钱包 10、区块 26,300,886、第 2 号交易（0 开始编号）重算：支付 10,000,000 USDT，收到 3,552.228717651589845452 ETH，gas 0.351855780200757930 ETH。具体方法和逐笔边见 `reports/case_studies/m1_real_swap.json`。
- 图 1 的 HTML、PNG、SVG、底表和独立生成脚本已生成。HTML 已在 Chrome 实际打开；最低金额由 $1M 调至 $100M 时，匹配边数由 176 变为 11。静态图已做图像检查。
- 已通过第一轮 18 项测试，并从本目录归档对象完成离线重建；后续增加的完整调用树检查和测试以 `reports/validation.json` 为准。

## 口径纠正

教师 PDF 第 8 页的约 **$2B 是被冻结的稳定币**；第 9 页询问约 $4.3B 被盗资产中多少损失于 MEV。新计划中的“约 $2B 不可追回损失”尚无相同定义和估值日期支持，不作为既定事实。新阶段将检验冻结、未追回和经济损失的不同口径。

教师 PDF 没有明确给出“Transaction / Gas Fee / Auction Bid / Auction Result”四个原词；这些仅为本次计划中的暂定分析结构，不能标为教师逐字要求。

## 来源、权限和限制

检查了仓库现有数据和 API/RPC 类环境变量名称；未发现可直接使用的相关密钥，没有输出或硬编码凭据。依赖安装在临时目录；新代码和结果保存在 `new/`，原研究缓存未修改。

Etherscan 标签页无法访问、钱包 2 页面返回 HTTP 403。初次 Arkham 和 Stalkchain 支持 8 个地址；现经 PublicAML、Bitquery 和 ZachXBT 原始 Telegram 记录扩充至 15/16。钱包 9 的补证是 Arbitrum 冻结关联，不认证同址 Ethereum 控制；钱包 13 未独立证实。16 个 Etherscan 新读取均返回 HTTP 403，准确编号仍未逐一认证。

缓存原始采集时间无法可靠恢复，清单保留空值。原始字节哈希、收据及区块头一致性不等于独立 canonical-chain 或收据 Merkle inclusion proof。调用树完整性、失败祖先过滤和原生价值流另做检查。

## M2 / M3 新增进度

详见 [第二、三阶段报告](../reports/milestone23_report.md)，以及 `milestone23_summary.json` 和三份逐案 Markdown/JSON。三个独立原子套利净收益为 2.745812294499937065、0.000065472689682791、0.002184499542797343 ETH，均已扣 gas 和可识别直接付款；不外推为全事件损失。

一组夹击的前后腿完整重算净收益为 12.080033775421395622 ETH；不能把后腿约 567.68 ETH 的现金流当作整组利润。图 2 保存 210 个实际 ETH/USDT 池执行价观察，按实际区块时间或明确标示的交易顺序坐标显示。

三个区块的 proposer 收款分别为 36.437514095553389525、3.120166160586952436、0.578802351165718120 ETH，与 relay 交付值精确相等；均核对了转付合约的 SELFDESTRUCT 轨迹。其中 A3 由不同于 fee recipient 的地址出资，builder margin proxy 保留 null，没有默认共同控制。

新查询四家 relay 的历史 `builder_blocks_received`，共 7,958 条提交观测。初次 limit=1000 被部分接口拒绝后，以明确错误为依据重试 limit=500；原始错误保留。接口可能超出请求 limit 返回数据，因此结果只代表可见保留记录；非交付记录包括修订版本及可能晚到提交，不等于完整有效输家分布。

同一 payload 在不同 relay 可能使用不同 builder 签名公钥，交付次数按区块去重，身份保留未解决。全窗口 3,311 块中有 2,939 块得到一致 relay 交付支持；基线 130 块观测到 109 块，事件段 3,181 块观测到 2,830 块。基线/事件比较是描述性的，不是攻击因果效果。

四个案例区块哈希已通过本次公开 RPC 新读取核对。M2/M3 已分别用 `--legacy /private/tmp/group12-no-legacy` 验证归档重算，不需要父项目旧目录；M3 四个主要处理表/JSON 与读取旧目录得到的结果逐字节一致，指纹见 `reports/offline_replay_fingerprint.json`。公开网络请求结果也已缓存。37 项测试已通过，后续最终结果以测试 XML 和更新的 validation.json 为准。

图 2–5 的 HTML、PNG、SVG 和支持数据均已生成；静态图已做图像检查，并修正图 3 标签重叠。M4/M5/M6、价格/时间/钱包边界敏感性和最终全需求验收仍未完成。

下一步：进入 M4，统一合约身份与各时段行情，筛查损失超过 $1M 和接近/超过 $5M 的交易，并逐案解释；身份补证及拍卖数据覆盖检查同步推进。

## M4 / M5 已验证进展

详见 [异常与跨链报告](../reports/milestone45_report.md)。M4 新增五份完整 Markdown/JSON 案例，最大参考差额约 USD 8.374M，另有一案约 USD 6.047M。所有五案均存在零中间输出下限和非零最终 unwrap 下限并存；N3/N4 入口不支持的情况下，在成功内部调用找到实际 execute。未建立故意亏损、补偿性获利或反事实增量 MEV 损失。

M5 有界发现 441 个显式 memo 候选，只有三案完成全套验证，不把候选数当作已认证兑换数。三案于 2026-11-17 入金 36/61/40 ETH，到账 1.00484202/1.68897154/1.10797406 BTC；Coinbase 同时点参考差额约 USD 316.17/754.33/429.72。协议网络扣费已包含在到账差额中，gas 单列，RUNE 流动性 fee 未虚构 USD 换算。

初始发现来源中三笔地址关联转账晚于所选入金，已被时间检查排除；改查 filter=to 记录，逐笔新读取并认证入金前资金链，每案三段普通转账连接钱包 12。此为资金流关联，不证明共同控制或独占盗款单位归属。比特币 vout 金额、接收地址、OUT:入金哈希及确认状态均核对。三案已经完全离线重算。

图 6/7 的 HTML、PNG、SVG、支持 Parquet 和独立脚本已生成，静态图已检查。新增 6 项测试，当前全套 43 项通过；最终状态以 validation.json 和 pytest XML 为准。M6 已开始查询 ETH/WETH/USDT/USDC 开闭余额及稳定币黑名单状态；最终对账和图 8 尚待完成。

## M6 余额与稳健性

新增 [限定资产对账与稳健性报告](../reports/milestone6_report.md)。16 地址 × ETH/WETH/USDT/USDC 的 64 个期初/期末账户全部精确对平；期末区块为 26,303,950（2026-10-30 07:02:47 UTC）。固定同一参考时点，余额 USD 2,646,601,359.14，其中黑名单稳定币 USD 2,026,000,811.99，其他余额 USD 620,600,547.15。冻结是期末余额子集；不是链外已追回，也不是全事件持仓。USDC 无有效 Coinbase 分钟价时，明确采用 Binance USDCUSDT × 同期 Coinbase USDT/USD，不设恒定 1。

图 8 已生成 HTML/PNG/SVG，静态图已检查并修正说明文字重叠。图中限定余额账与所选三笔套利毛利分配分开，完整事件盗款/追回/不可追回/因果 MEV 仍为 null，不虚构最终瀑布总额。

经济样本 621 笔完整估值、无内部混合/仓位债务、互异哈希交易的交易时点净参考短缺为 USD 43,727,932.59；这不是全事件损失或 MEV 总额。固定期末价格覆盖 315 笔，不能直接将不同覆盖总额比较为价格敏感性；另输出同一交易集的配对敏感性。钱包边界三场景和逐一剔除 relay 已计算；剔除 Ultrasound 后 relay 交付来源支持降至 1/3，链上三笔付款仍可核对。

新增余额、稳定币报价、blacklist 原始调用、WETH、收益分区及敏感性测试；全套 48 项通过。余额与 M4 筛查均已使用不存在的 legacy 目录验证归档离线重算；THOR 三案也离线重算成功。查询层现有 23 个 Parquet 表。最终综合学术报告、演示材料和全需求验收正在整理，目标尚未标记完成。

## 综合报告与演示稿

综合学术报告和标题级 claim ledger 已生成：`reports/final_research_report.md`、`reports/claim_ledger.json`。14 页英文演示研究内容见 `reports/presentation/slide_content.md`。通过 Canva 生成了 14 页可编辑草稿，已读回全文和 presenter notes；发现第 4 页存在未提供原始数据的示意图，注释未完整保留精确数值/来源。因此未将草稿认证为最终演示成果。13 页缩略图尚无存储，浏览器主机不可用；检查记录为 `canva_draft_review.json`。只读编辑事务已关闭，没有提交修改。最终目标保持 active，下一步完成演示修正/可视检查及全需求验收。

## 最终审核新增证据与修订

对照计划核对 47 项要求，结果见 `reports/acceptance_audit.{json,md}`；不把数据受限项涂成已认证事实。重新查询缺价资产后，70 个历史行情请求（含等待后按至多每秒一次的 429 重试）均留档；严格完整估值仍为 621 条。图 6 增加可用行情/时间情景的最小–最大须线，明确不是统计置信区间。图 4 已用实际目标交易差额替换旧的估值待计算说明。

扩展到三笔 sweep 的全部 64 种资产、每种资产在全部 16 个线索地址的期初/期末余额：1,024/1,024 全部对平，没有缺失调用。128 个原始 Multicall 响应逐项解码与表核对，重叠四资产结果与直接 RPC 一致。新增 EIP-7702 签名恢复证据，50 个授权签名均恢复至来源地址；历史代码从空变成实际委托指示符。库存和签名的缓存离线重放输出逐字节相同。

图 1 新增 10 条有实际交易来源的 THORChain 伴随边，包含 3 条确认 BTC 输出；提供双链过滤和逐边价格时点。原始 October 账表不改写。实际生成 HTML 的筛选/点击逻辑通过 Node 验证；没有把这一验证称为新浏览器渲染测试。

全套 52 项测试通过。演示稿 14 页的预览均已检查，第 4 页无来源示意图在修订草稿中删除并改为 N1 实际数值；第 6 页精确数值提示改指向配套讲稿；第 14 页更新为 1,024 账户、52 测试。Canva API 的备注修改参数未被连接器接受，精确逐页来源以 `presenter_notes.md` 和 `slide_notes.json` 提供，未声称已写入 Canva 内部备注。

`presentation_review.pdf` 汇编工具返回的 600px 页面预览，并经 PDFium 渲染检查 14 页；不是全分辨率 PowerPoint 导出。Canva 修订事务保持未提交状态，工具明确要求展示预览并取得用户明确批准后才能保存。完整目标尚未标记完成。

## 保存批准等待状态

同一保存批准条件已连续三个 goal turn 存在。再次读取确认事务 8806185782869367486 的修订草稿仍可读取，末页正文为 52 tests；已保存版本末页正文仍为 48 tests。没有收到用户明确批准，也没有执行 commit。目标据此标记 blocked，等待输入；研究文件、14 页审核 PDF、逐页精确来源和经过验证的待保存操作均已保留。用户明确批准后，先核对现有事务再提交；不因等待时间经过就重建或推断批准。


### 2026-11-19T01:29:39.152272+00:00 — Approved presentation saved

User explicitly approved “保存这版修订稿”. Prior transaction returned not_found; identical approved changes were restored on the existing design, compared against before/after previews, committed, and read back from saved design. All 14 pages retained; corrected pages 4, 6, 14 verified. Exact figures and sources remain in companion presenter notes. Prior approval block resolved; scientific data limits remain explicit. See reports/presentation/canva_saved_verification.json.


## New active objective: comprehensive arbitrage and MEV tracing

The previous 3-case study is insufficient for the expanded objective. Implemented sample-wide discovery: 1,207 blocks / 283,706 receipts / 3,210 associated transactions, full-sender same-block episode accounting, and explicit MEV criteria. Candidate profit sums are not approved aggregates. See reports/mev_expansion/progress.md. The expanded objective remains active.


Expanded routes and valuations: 3210 ordered route records, 30 Chinese case records, 21 swaps / 14 pools / 6 closed rounds reconciled for A1. Full episode valuation replaces positive-leg ranking; price-mark cashflows remain provisional. Pool metadata paced retry is live (exec session 97291; /private/tmp/mev-enrich-retry.log). All-incident total and counterfactual victim losses remain unfinished.


Expanded full original-window scan complete: 3311 blocks / 751258 receipts / 12841 candidates; full-sender accounting 137013 unique transactions. Nine order fills reconcile 325M USDT→122316.323922299741513724 ETH/WETH. 22 fresh front-removal historical prefix interventions verified and linked to actual operator cashflows/payouts; original three simulation response audits independently reproduce 1003 receipt sequences and preserve negative AXS counterexample. Metadata retry session 97291 has completed (528 factory matches, 14 records with failures). Remaining expanded scope is active; see reports/mev_expansion/progress.md.


## 当前交付状态

扩展研究已形成 [中文完整报告](../reports/mev_expansion/完整套利与MEV核验报告.md) 与逐笔账，76 项检查通过、20 项扩展交付核对通过。上文早期 active／pending 及保存批准等待属于历史；已批准的 14 页 Canva 保存已经核实。新增扩展结果以独立报告交付，未声称同步到旧演示。全事件 MEV 总额、未定价资产和未知实际控制人保持未识别，详见新报告及 expanded_requirements_audit.json。
