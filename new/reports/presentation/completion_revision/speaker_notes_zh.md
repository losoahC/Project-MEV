# 14页修订稿中文讲稿与证据

对应Canva副本 `DAHbVfFZRn0`。原版 `DAHbT7iYK6M` 保留。下面是本轮更新的权威配套讲稿与精确来源；Canva内部继承的通用备注没有被冒充成已同步的逐项来源。

## 第1页：研究问题与资料范围

本研究说明套利者如何通过实际交易赚钱，以及价值如何分配。先区分链上观察、价格估计和因果假设。以太坊原窗口为纽约时间2026年10月29日16:24至10月30日03:02左右；THORChain三例在11月，单列。不能将冻结稳定币说成已发生、不可追回的交易损失。

来源：[完整套利与MEV核验报告.md](../../mev_expansion/完整套利与MEV核验报告.md)；[research_plan_supplied.md](../../../docs/research_plan_supplied.md)

## 第2页：金额、估值与归因

收到和转出多少，可以用回执、ERC20日志、成功的内部ETH调用核对。净利润需要本金、偿还、Gas、区块付款和仓位变化。参考成交差额衡量与参考市场的价格差，不自动等于MEV抽取；收款地址也不证明最终控制人。

来源：[MEV判定标准.md](../../../docs/MEV判定标准.md)；[](https://info.etherscan.com/explore-eoa-address/)

## 第3页：数据覆盖

完整读取3311块、751258张回执。34397笔转账审计交易产生397776条转账、包装、凭证和费用记录；不是把这些行相加当盗损。12249个去重操作单元包含12967笔交易，并补入126笔区间成本腿。13个Bitquery点名地址的全部窗口触碰记录也列入明细。16个历史地址只是线索，部分标签仍未独立证实。

来源：[summary.json](../../../data/processed/mev_full_window/summary.json)；[transfer_audit_summary.json](../../../data/processed/mev_full_window/transfer_audit_summary.json)；[逐笔真实转账与Etherscan链接.csv.gz](../../mev_expansion/逐笔真实转账与Etherscan链接.csv.gz)

## 第4页：MEV的明确标准

高Gas、盈利或时间相邻均不是充分条件。跨池套利需要至少两个不同池／PoolId、本金和中间库存闭合及完整成本；前—目标—后同操作者、前腿同向、后腿反向支持夹子结构。指定前腿的执行删除实验才检验条件输出影响。Gas拆燃烧和priority，额外区块付款另外计一次；池费已经体现在成交结果里。

来源：[MEV判定标准.md](../../../docs/MEV判定标准.md)；[joint_front_replays.json](../../../data/processed/mev_full_window/joint_front_replays.json)

## 第5页：A1实际如何赚钱

实际交易 0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c，21次swap、14个聚合池腿，可连续拼接6段token路径。毛剩余12.137824203978034597 ETH；Gas1.1390642976 ETH；直接区块付款8.252947611878097532 ETH；净留存2.745812294499937065 ETH。毛额等于Gas、付款与净额之和。目标的约837.4万美元参考差额不等于本笔bot利润。

来源：[0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c](https://etherscan.io/tx/0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c)；[arbitrage_cases.json](../../../data/processed/arbitrage_cases.json)；[真实收支核对入口.html](../../mev_expansion/真实收支核对入口.html)

## 第6页：从三个案例扩大到完整闭合单元

幻灯片中的A1/A2/A3仍是三个已核实案例，总净2.7480622667 ETH。扩展后的ETH/WETH正净额闭合集合是2483个，合计244.618801770585241269 ETH。多利润资产集合为2685个，2678个可估值，参考净额572914.45148178971463508054436104879128902美元，保留34个非正净额。ETH集合是多资产集合的子集，不能相加；标价不等于已兑换成美元。

来源：[covered_surplus_distribution.json](../../../data/processed/mev_full_window/covered_surplus_distribution.json)；[terminal_cycle_summary.json](../../../data/processed/mev_full_window/terminal_cycle_summary.json)；[闭合循环逐地址净变化.csv](../../mev_expansion/闭合循环逐地址净变化.csv)

## 第7页：夹子利润与目标影响

S1完整前后腿净额12.080033775421395622 ETH。不能把后腿约567.68 ETH当净利润，前腿约负555.60 ETH也是投入。新完成372组前腿删除，360组目标两情景成功，12组回滚；进一步按319个区块联合删除并将372个目标去重。354个可估值、成功且投入不变的输出改善量合计约434.41万美元，仅为逐块独立历史父状态、固定调用的敏感度，不是连续全事件无MEV损失或bot利润。

来源：[replay_audit.json](../../../data/processed/mev_full_window/replay_audit.json)；[joint_front_replays.json](../../../data/processed/mev_full_window/joint_front_replays.json)；[recovered_target_removals.json](../../../data/processed/mev_full_window/recovered_target_removals.json)

## 第8页：实际proposer收款

全窗口2939/2939个已观察relay交付金额，都与完整成功调用树里的proposer收款一致。覆盖11396个操作单元、1264个区块。页面三个案例保留原始完整精度，A3付款payer与fee recipient不同。Builder付款给proposer是其收入的后续分配，不应重复扣同一笔Searcher利润。

来源：[full_auction_allocation.json](../../../data/processed/mev_full_window/full_auction_allocation.json)；[全窗口拍卖与实际付款.csv](../../mev_expansion/全窗口拍卖与实际付款.csv)

## 第9页：拍卖覆盖与竞争

2939个交付记录覆盖3311块；没有观察到的372块不能按零付款。7958条submission只覆盖3个slot和4个relay，不等于7958个有效竞标者。未交付的记录可能是修改报价、晚到或无效报价，历史竞标资格与到达时间不足时不称其有效输家。Native builder余额代理不包含公司所有ERC20、其他地址、场外结算和费用，不称公司最终净利润。

来源：[auction_coverage.json](../../../data/processed/auction_coverage.json)；[auction_timing_assessment.json](../../../data/processed/auction_timing_assessment.json)；[full_auction_allocation.json](../../../data/processed/mev_full_window/full_auction_allocation.json)

## 第10页：五个异常交易案例

五个最大异常案例仍采用原始限定样本和统一估值口径。每案有实际输入、输出、滑点保护及相邻操作。N1约837.4万美元参考成交差额，最高损失率约27.95%。中间最小输出为0不代表整个交易没有保护，最终unwrap有非零最低额。异常成交支持经济上不利的执行，不能据此证明故意损失或补偿性关联交易。

来源：[anomaly_case_studies.json](../../../data/processed/anomaly_case_studies.json)；[anomaly_coverage.json](../../../data/processed/anomaly_coverage.json)；[milestone45_report.md](../../milestone45_report.md)

## 第11页：真实收款与本金分账

旧452项加上新认证协议的19项，形成471个完整分配单元，全部对平，1322条带符号地址记录，107个单元有V4凭证。现金和凭证分别列出，零地址仅代表mint/burn记账。另对200个仓位单元解码1025事件，分出借款负债及流动性本金。最大Comet订单权益增量6144583.89909572876889079美元，包括抵押减新债务；实际Gas地址收到111.7408864984377235 ETH并支付0.0647557070413734 ETH Gas，不能将全部借款算利润。

来源：[complete_pool_surplus_distributions.json](../../../data/processed/mev_full_window/complete_pool_surplus_distributions.json)；[position_principal_ledger.json](../../../data/processed/mev_full_window/position_principal_ledger.json)；[order_reference_shortfall_partition.json](../../../data/processed/mev_full_window/order_reference_shortfall_partition.json)

## 第12页：THORChain三个匹配路径

三例分别36、61、40 ETH，转成1.00484202、1.68897154、1.10797406 BTC，实际inbound/outbound及BTC vout均匹配。参考差额约316.17、754.33、429.72美元。链间时间差使用粗区块时间戳，不称服务实际延迟。它们发生在11月17日，与10月事件MEV金额不混加；支持与历史线索的钱流关联，不证明全部资金来源或共同控制。

来源：[thorchain_paths.json](../../../data/processed/thorchain_paths.json)；[milestone45_report.md](../../milestone45_report.md)

## 第13页：资产存量与经济损失

图示限定16条线索的ETH/WETH/USDT/USDC期末账，64/64准确对平。四资产余额约26.466亿美元，其中被黑名单冻结的稳定币约20.260亿美元，是余额子集。冻结不等于追回或已没收，资产存量不能和交易损失混成一张加总表。扩展库存另有1024个钱包／资产台账，原始账和限定价格库存表同时交接。

来源：[asset_inventory.json](../../../data/processed/asset_inventory.json)；[initial_asset_inventory.md](../../initial_asset_inventory.md)；[milestone6_report.md](../../milestone6_report.md)

## 第14页：可以明确下的结论

可以给出实际转账、交易路径、每个闭合策略的净留存和每个费用地址。核验集合净留存244.618801770585241269 ETH，绝非全部链、全部机构最终利润。Bitquery部分卖出腿价差数量级接近，但卖出腿、整条路径、历史成本和最终受益人必须分开。Hyperliquid1分钟历史请求为空，补取15分钟高低价范围作敏感度，不冒充精确分钟复现。四种Few的14次真实兑换为1:1，源码亦允许无原币mint，准备金不足以证明全量按面值兑现。公开证据不能确认的美元标价、全事件因果量和最终控制人作为识别边界保留，不填假数字。

来源：[完整套利与MEV核验报告.md](../../mev_expansion/完整套利与MEV核验报告.md)；[named_pool_edge_comparison.json](../../../data/processed/mev_full_window/named_pool_edge_comparison.json)；[few_wrapper_backing.json](../../../data/processed/few_wrapper_backing.json)；[info-endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)
