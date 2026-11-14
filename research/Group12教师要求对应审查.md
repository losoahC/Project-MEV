# Group 12 教师要求对应审查
来源：Advanced Blockchain Marching Orders.pdf，第 8–10 页。

| 钱包编号 | 净代币流出目标数 | 关联夹击组 | 关联闭环 |
|---|---:|---:|---:|
| 1 | 0 | 0 | 0 |
| 2 | 596 | 246 | 312 |
| 3 | 0 | 0 | 0 |
| 4 | 2 | 0 | 25 |
| 5 | 2 | 0 | 28 |
| 6 | 0 | 0 | 0 |
| 7 | 0 | 0 | 0 |
| 8 | 0 | 0 | 0 |
| 9 | 0 | 0 | 0 |
| 10 | 1 | 0 | 14 |
| 11 | 0 | 0 | 0 |
| 12 | 95 | 45 | 86 |
| 13 | 1 | 0 | 0 |
| 14 | 20 | 14 | 18 |
| 15 | 71 | 35 | 118 |
| 16 | 24 | 0 | 122 |

以上仅在已有 1,352 笔目标范围内逐地址检查 ERC20/WETH 净流出。零值不代表该钱包没有交易。跨钱包的组和环可能重叠，不可直接求和。

## 按教师原文逐项验收（2026-11-11 更新）

已重新读取根目录教师 PDF 第 8–10 页。第 8 页提供 Flashbots 研究线索，第 9 页要求评估黑客损失于 MEV 的金额及费用收益，第 10 页要求从 1–16 标签钱包查起、扫描交易、找 sandwich、计算 ETH 多付额。

| 要求 | 当前权威证据 | 验收结论与边界 |
|---|---|---|
| 找出 Exploiter 1–16 | exploiter_1_16_and_bot_audit.json、exploiter1_role_verification.json | 16 个地址有历史标签线索；1 号已核实（实时标签、最早活动、EIP-7702 控制热钱包并转出至 2 号）；2–16 号未逐一重读实时标签 |
| 扫描钱包交易历史 | wallet_history_coverage.json、wallet_nonce_header_crosscheck.json、wallet_nonce_authorization_reconciliation.json | 48 项分页穷尽；1024 笔主动交易逐笔对 RPC；3 次额外 nonce 增长由 EIP-7702 授权解释；不能声称未知资产及抵销流量均无遗漏 |
| 完整收支核查 | wallet_native_balance_reconciliation.json、wallet_token_balance_reconciliation.json、aave_token_balance_residual_proof.json | 16 钱包 ETH 精确守恒；106 已知资产组合闭合，其中 2 项 Aave 计息单独解释 |
| 找 sandwich | all_scope_sandwich_groups.json、bracket_EVM_validation.json | 564 结构组；111 正收益库存闭合组的 117 个目标实验全部核验。结构候选、执行依赖和恶意意图是不同判断 |
| 找非夹击 MEV 环 | standalone_ring_raw_replay.json、expanded_EVM_validation.json、nonce_preserving_EVM_sensitivity.json | 1063 单笔闭环原始收支重算；344 同块反向关联交易全部有干预证据；337 主实验中 331 数值结果、6 不可执行，另 9 个 nonce 敏感性实验 |
| 跨区块闭环 | extended_cycle_interval_verification.json、extended_cycle_eight_block_EVM.json | 新增六块间隔两腿闭环，实际净现金流 0.007843240319553997 ETH；完整八块 1851 笔收据复现；去掉 26302728 黑客兑换后机器人两腿回滚，因果依赖成立 |
| 逐钱包 ETH 多付 | wallet_ETH_purchase_audit.json、wallet_purchase_price_completion.json、wallet_strict_purchase_summary.json | 804 笔候选；794 严格价格、801 五分钟、803 混合场景。旧 DAR 一笔用独立旧 DAR 池价给出区间（中心约 9,796 美元，7,825–59,132 美元），单列不并入严格主估计，不用新 D 价或零值填补 |
| 活跃 bot 与收益分配 | 全范围策略发起者分配.json、execution_evidence_summary.json | 已定位活跃发送者和执行边界，单笔与夹击哈希去重；地址并不证明品牌或最终受益所有人 |
| gas 与区块生产者费用 | full_fee_distribution.json、recipient_distribution_ledger.json | 连续 3311 区块费用守恒，区分销毁、优先费、直接转账及 proposer 转付，不重复计算资金流转 |
| 精确全事件 MEV 总额 | event_MEV_total_bounds.json、未完成项收尾_2026-11-15.md | 本样本范围内给出带假设的区间：下界 312.7 ETH（约 70 万美元），上界 6,688 ETH（约 1,500 万美元），硬上限 5,303 万美元；搜索者自留部分 123–227 ETH。仍无无条件点估计 |

上述逐钱包映射保持旧 1352 目标范围；补查新增 ETH 卖出另见 missed_sale_and_followup_audit.json。历史报告中的“尚未核查逐钱包购买/nonce/余额”等表述已被新证据更新，正式判断以本表与最新主报告为准。

## 不能用合计掩盖的差异

- 111 正收益闭环组的实际现金流 81.108470400749882302 ETH，不是 117 次反事实差额之和。
- 109 个组的反事实包含失败腿，不能把前腿已投入但未回收的现金当作损益；2 个组两种场景均执行并闭合，提供更强的条件收益证据。
- 16 钱包严格购买多付约 5303 万美元，与扩展 55 地址旧样本差额约 1.068 亿美元范围不同。
- 全事件唯一因果点估计、标签最终所有权及 DAR 公允价值仍存在识别或证据限制；不声称老师的“精确全事件”问题已被无条件解决。

复现入口：verify_wallet_history_accounting.py、verify_expanded_evm.py、classify_evm_execution_limits.py、verify_bracket_evm.py、summarize_execution_evidence.py。最终 PDF、交接包与清单须在新增本地重演尝试结束后同步更新并验收。
