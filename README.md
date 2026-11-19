# 最新交付：全事件统一分配账（2026-11-19）

打开 [中文交互核验报告](new/reports/event_allocation/全事件统一分配核验.html) 或 [中文研究正文](new/reports/event_allocation/全事件统一分配报告.md)。库存型交易、代币承接、TRON、LP 和区块付款已经汇入统一时间、价格与去重框架。

- 共同窗口：2026-10-29 20:30 至 2026-10-30 07:00 UTC；覆盖已识别事件集合的 **104,064 笔唯一交易、872,470 条实际资产/仓位变化**。
- **834 笔目标交易的事件钱包变化均已取得合约匹配历史报价**，参考损失合计 **$115,933,224.16**。参考价差、实际现金/本金变化和有反事实支持的因果 MEV 分别报告。
- [同一张分阶段总表 CSV.gz](new/reports/event_allocation/all_stages_allocation.csv.gz) 共 **650,900 行**；主预算 85,230 笔，二次结算 53,238 条原生币转账。二次付款的 `primary_additive_USD` 为 0，避免重复累计。
- [完整实际地址账](new/reports/event_allocation/actual_address_changes.csv.gz)、[全部交易索引（含零原币付款）](new/reports/event_allocation/transaction_index.csv.gz)、[逐池 LP 双估值](new/reports/event_allocation/lp_inventory_valuations.csv)、[全区块实际结算](new/reports/event_allocation/whole_block_native_settlements.csv.gz) 均已导出。
- **98 项测试、10 项独立核验通过**。见 [核验结果](new/reports/event_allocation/validation.json)；图谱可导出 [PNG](new/reports/event_allocation/event_allocation_graph.png) / [SVG](new/reports/event_allocation/event_allocation_graph.svg)。

未知报价凭证保留原币；全块付款的事件份额及最终受益所有权按证据标注。Bitquery 未公开逐笔全集，因此未声称与其全部交易已经逐笔全集匹配。新成果保存在本项目；先前批准保存的 Canva 副本保留。

复算：`PYTHONPATH=new python -m src.event_allocation.reproduce`（默认使用本地归档，不下载网络数据）。显式阶段 `--stage reconstruct` 重建原币账，`--stage collect` 采集原始数据，`--stage audit` 重做导出核验。

---

## 之前版本与研究背景

# 当前研究入口（2026-11-19）

先打开 [真实收支核对入口](new/reports/mev_expansion/真实收支核对入口.html)，可选真实案例查看收到、转出、Gas、原币净变化和 Etherscan 链接。完整解释见 [中文报告](new/reports/mev_expansion/完整套利与MEV核验报告.md) 或 [带图 HTML](new/reports/mev_expansion/完整套利与MEV核验报告.html)。本轮读取 Ethereum 3,311 块／751,258 回执；2,483 个 ETH/WETH 正收益闭合单元净留存 244.618801770585241269 ETH；471 个分配差额全部对平；2,939 个已观察 proposer 交付金额与链上实际收款一致；372 个目标完成 319 个区块的联合干预。87 项检查通过。

[逐笔真实转账 CSV.gz](new/reports/mev_expansion/逐笔真实转账与Etherscan链接.csv.gz) · [逐地址实际收支 CSV.gz](new/reports/mev_expansion/逐交易逐地址实际收支.csv.gz) · [全部操作单元与判据](new/reports/mev_expansion/全部操作单元与判据.csv) · [交付审计](new/reports/mev_expansion/expanded_requirements_audit.json) · [最新14页演示预览](new/reports/presentation/completion_revision/review.html)。原 Canva 已保存；用户批准的新14页副本也已提交并读回核对，[打开更新稿](https://www.canva.com/d/83U9CSo9ZRBAMU4)。全事件因果量、最终控制人及缺乏可靠行情的资产估值保留识别边界，不填假数。以下仅为历史记录。

# 历史核验交付（2026-11-11）

请先阅读 [最终研究报告](research/最终研究报告_2026-11-11.md)。本稿包含新历史核查、逐钱包 ETH 购买及交易环重算；原 PDF 为早期版本。

**2026-11-15 更新**：原报告自认未完成的四项已收尾，详见 [未完成项收尾](research/未完成项收尾_2026-11-15.md)：

- Exploiter 1 已由链上 EIP-7702 控制证据核实。
- 八块跨区块因果实验完成（基准 1,851 笔收据全部复现）。
- 旧 DAR 给出公允价区间，中心值多付约 9,796 美元。
- 本样本范围内的 MEV 总额给出带假设的区间：下界 312.7 ETH（约 70 万美元），上界 6,688 ETH（约 1,500 万美元）；其中搜索者自留 123–227 ETH。

# FT565 · Group 12：Flashbots / MEV 事件研究

优先阅读 [正式研究报告 PDF](output/pdf/MEV研究报告_正式版.pdf)，或其[可编辑正文](research/研究报告_正式版.md)。原来的“提交版”保留为详细技术附录，不再作为最新的简明主报告。

本项目检验急迫兑换、价格冲击、交易排序与费用竞争。**成交差额、策略净现金流和局部反事实影响是不同估计对象，不能相加或互相替代。**

## 本轮改进

- 固定 1,094 笔共同样本，比较提前 1、5、15 分钟的价格，区分价格敏感性与扩大覆盖范围。
- 严格局部反事实从 70 笔扩至 77 笔，新增费率、自身价格冲击与前置交易影响的精确分解。
- 检查最大交易、前十大交易、代币身份和候选区块窗口的敏感性。
- 完成 8 页正式研究报告、3 张可导出的科学图、答辩准备及离线复现入口。

## 如何复现

在本目录运行：

```bash
python3 research/reproduce_quality_upgrade.py
```

该入口使用 Python 标准库和已有本地缓存，不请求网络；重算本轮新增反事实、稳健性和候选窗口结果，并执行 12 项质量检查。原 34 项主审查结果另保存在 `research/event_completion_validation.json`。这不是从空目录重新下载整个链上数据集。

绘图和 PDF 是独立的可选生成阶段：`research/plot_research_results.py` 使用 Matplotlib；`research/build_research_paper.py` 使用 ReportLab 和本机 Arial Unicode 字体。数据分析入口不依赖这些排版工具。

## 文件导航

| 用途 | 文件 |
|---|---|
| 主报告 | [正式正文](research/研究报告_正式版.md) |
| 本轮审查与改进说明 | [质量改进记录](research/项目质量改进记录.md) |
| 答辩 | [答辩问题与回答](research/答辩问题与回答.md) |
| 逐笔兑换索引 | `research/全部兑换时间线.json` |
| 全部候选索引 | `research/全候选证据索引.json` |
| 新增实证结果 | `research/research_quality_analysis.json` |
| 新增核验 | `research/research_quality_validation.json` |
| 逐笔局部反事实 | `research/all_scope_v2_counterfactuals.json` |
| 地址级策略分配 | `research/全范围策略发起者分配.json` |
| 结算资产流 | `research/all_scope_settlement_allocation.json` |
| 原始证据完整性 | `research/evidence_manifest.json` |

缺失行情和未知身份均明确保留；全事件总额只给出带假设的区间，不给点估计。文件哈希只验证完整性，不保证数据来源、所有权或因果假设真实。教师未提供详细评分量表，本项目不自称已获得或保证 100 分。

## GitHub 版本范围

仓库保留报告、全部分析代码、逐笔结果、价格数据和离线质量复现所需的选定原始收据。大型原始缓存、临时文件和重复交接压缩包仅保留在本地；不是整个原始数据目录的完整备份。`research/evidence_manifest.json` 是历史完整目录清单，包含未上传缓存。

最新地址与 bot 进度请阅读 [Exploiter 与活跃 Bot 核对](research/Exploiter与活跃Bot核对.md)。MEV 区间只覆盖本研究的 3,311 区块、55 地址范围，不是跨链、跨期的全事件总额。
