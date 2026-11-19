# 最新交付：全事件统一分配账（2026-11-19）

打开 [中文交互核验报告](reports/event_allocation/全事件统一分配核验.html) 或 [中文研究正文](reports/event_allocation/全事件统一分配报告.md)。库存型交易、代币承接、TRON、LP 和区块付款已经汇入统一时间、价格与去重框架。

- 共同窗口：2026-10-29 20:30 至 2026-10-30 07:00 UTC；覆盖已识别事件集合的 **104,064 笔唯一交易、872,470 条实际资产/仓位变化**。
- **834 笔目标交易的事件钱包变化均已取得合约匹配历史报价**，参考损失合计 **$115,933,224.16**。参考价差、实际现金/本金变化和有反事实支持的因果 MEV 分别报告。
- [同一张分阶段总表 CSV.gz](reports/event_allocation/all_stages_allocation.csv.gz) 共 **650,900 行**；主预算 85,230 笔，二次结算 53,238 条原生币转账。二次付款的 `primary_additive_USD` 为 0，避免重复累计。
- [完整实际地址账](reports/event_allocation/actual_address_changes.csv.gz)、[全部交易索引（含零原币付款）](reports/event_allocation/transaction_index.csv.gz)、[逐池 LP 双估值](reports/event_allocation/lp_inventory_valuations.csv)、[全区块实际结算](reports/event_allocation/whole_block_native_settlements.csv.gz) 均已导出。
- **98 项测试、10 项独立核验通过**。见 [核验结果](reports/event_allocation/validation.json)；图谱可导出 [PNG](reports/event_allocation/event_allocation_graph.png) / [SVG](reports/event_allocation/event_allocation_graph.svg)。

未知报价凭证保留原币；全块付款的事件份额及最终受益所有权按证据标注。Bitquery 未公开逐笔全集，因此未声称与其全部交易已经逐笔全集匹配。新成果保存在本项目；先前批准保存的 Canva 副本保留。

复算：`PYTHONPATH=new python -m src.event_allocation.reproduce`（默认使用本地归档，不下载网络数据）。显式阶段 `--stage reconstruct` 重建原币账，`--stage collect` 采集原始数据，`--stage audit` 重做导出核验。

---

## 之前版本与研究背景

# Group 12：套利收益、真实转账与MEV核验

打开[真实收支核对入口](reports/mev_expansion/真实收支核对入口.html)，查看七个真实案例的收到、转出、Gas、凭证和逐地址净变化，并直接跳到Etherscan。完整叙述见[中文报告](reports/mev_expansion/完整套利与MEV核验报告.md)或[带图HTML](reports/mev_expansion/完整套利与MEV核验报告.html)。

当前结果：2,483个ETH/WETH正收益闭合单元净留存244.618801770585241269 ETH；471项分配对平；2,939个proposer付款匹配；372个目标经319区块联合干预。87项测试、27项交付核对通过。

[完整转账CSV.gz](reports/mev_expansion/逐笔真实转账与Etherscan链接.csv.gz) · [逐地址收支CSV.gz](reports/mev_expansion/逐交易逐地址实际收支.csv.gz) · [全部判据与操作单元](reports/mev_expansion/全部操作单元与判据.csv) · [池路径](reports/mev_expansion/全部候选池路径.csv) · [当前状态](docs/progress.md) · [八张基础图及早期案例](reports/final_research_report.md)

[更新后的14页实际预览](reports/presentation/completion_revision/review.html)及[中文讲稿](reports/presentation/completion_revision/speaker_notes_zh.md)已生成。原版保留；更新副本已按用户明确批准保存并读回核对，[打开已保存版本](https://www.canva.com/d/83U9CSo9ZRBAMU4)。

数量、参考估值和因果归因分别报告。7个闭合单元没有可靠美元报价，但原币数量完整；最终受益人、场外对冲及连续全事件均衡损失不由公开转账推定。详细查证结果和证据位置均在中文报告，未用空白待办替代计算。

## 复现

Python3.11+，依赖见requirements.lock.txt。本项目路径含冒号，macOS虚拟环境建议放在/tmp/group12-research-venv。以下从项目上一级运行：

```bash
PYTHONPATH=new python -m src.arbitrage.transfer_audit
PYTHONPATH=new python -m src.arbitrage.complete_surplus_ledger
PYTHONPATH=new python -m src.auction.full_window_allocation
PYTHONPATH=new python -m src.arbitrage.joint_front_replays
PYTHONPATH=new python -m src.arbitrage.position_principal_ledger
PYTHONPATH=new python -m src.reporting.completion_artifacts
PYTHONPATH=new python -m src.reporting.comprehensive_mev
PYTHONPATH=new python -m src.reporting.completion_presentation
PYTHONPATH=new python -m pytest -q new/tests
node new/tests/completion_review_smoke.mjs
```

旧阶段说明、首次归档流程和历史复现命令保存在[历史README](docs/README_history_before_2026-11-19.md)。原始响应、SHA256与归档文件一并保留；研究数据不能只交处理后的利润数字。
