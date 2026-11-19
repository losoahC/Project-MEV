"""Current observed-transfer results and explicit closure of prior calculation gaps."""
import json
from collections import Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT

def build():
    p=ROOT/'data/processed/mev_full_window';read=lambda n:json.loads((p/n).read_text());d=read('complete_pool_surplus_distributions.json');audit=read('transfer_audit_summary.json');au=read('full_auction_allocation.json');joint=read('joint_front_replays.json');pos=read('position_principal_ledger.json');price=read('terminal_cycle_summary.json');pool=read('pool_metadata_full_summary.json');recovered=read('recovered_target_removals.json');few=json.loads((ROOT/'data/processed/few_wrapper_backing.json').read_text());rows=[];add=rows.append
    add('## 补算结果：先核实实际收支，再谈套利利润\n')
    add(f'**可以直接在 Etherscan 对照收到多少、转出多少。** 新的[真实收支核对入口](真实收支核对入口.html)提供可点击交易、收款地址、原币数量及证据指针；批量金额来自归档回执与完整成功调用树。Etherscan 页面抓取遇到访问限制，不声称已经逐页独立看过 {audit["transactions"]:,} 个网页。浏览器页面是人工复核入口，底层链上回执／trace 是批量可复算依据。\n')
    add(f'当前导出 **{audit["transactions"]:,} 笔唯一交易、{audit["movement_rows"]:,} 条实际转账／费用／凭证记录、{audit["address_asset_rows"]:,} 条逐交易逐地址资产收支**。每行有原始 raw 数量、小数位（有依据时）、合约地址、交易哈希、log index 或 trace path，区分 ETH、ERC20、WETH 包装变化、ERC-6909 凭证及 NFT。相同资金在多个地址周转的收款总额不是利润。下载[完整转账 CSV](逐笔真实转账与Etherscan链接.csv)、[逐地址收支 CSV](逐交易逐地址实际收支.csv)。\n')
    add('### 先看一个能完整对账的实际套利\n')
    a1=next(r for r in read('full_ordered_routes.json') if r['tx_hash'].startswith('0x722001'))
    add(f'A1 交易 [`{a1["tx_hash"]}`](https://etherscan.io/tx/{a1["tx_hash"]}) 的池侧毛剩余为 **12.137824203978034597 ETH**，给实际区块收款地址 **8.252947611878097532 ETH**，Gas **1.1390642976 ETH**，操作边界实际净留存 **2.745812294499937065 ETH**。池内本金和中间币种闭合，池费已包含在成交中，不再重复扣除。这个净额才是此边界的套利收益；不能把收到的全部本金或 hacker 的参考成交差额当作收益。\n')
    add('### 旧分配差额已补全\n')
    add(f'扩大协议认证后，需要完整分配账的单元由原 452 个增为 **{d["summary"]["previous_gap_units"]} 个，{d["summary"]["fully_reconciled"]} 个全部对平**。原算法漏掉的混合交易 helper 付款、manager 原币清算和 ERC-6909 凭证负债均已进入账。拆出 {d["summary"]["actual_receiver_rows"]} 条地址记录，{d["summary"]["units_with_6909_claims"]} 个单元有 V4 凭证。负融资及费用保持负号，收款人不被自动并入 bot 所有权。\n')
    add('例如区块 26,301,634 的 helper `0x5aae4d2f360e156de3416936049837a7bb685588` 实际向本块 fee recipient 支付 **47.500710754933580679 ETH**。它同时参与交易，旧的“只解包、不交易”费用识别器漏掉了该付款。现在直接按成功调用树计入实际收款。另一笔 [`0x806f60…b30ce`](https://etherscan.io/tx/0x806f60e73e039527bdde0c36d797897a41bdaa74a0b827d6c5088b42d99b30ce)向 `0x82ccba35ad0c7a62230ef8ff337ac67f4cce0ea5` 铸出 **0.064521435779627872 ETH 的 V4 凭证**；它是可核实的资产权利，不能写成已经到账的原生 ETH。\n')
    add('![完整分配对账](complete_transfer_allocation.png)\n')
    add('### 历史执行干预：保留成功、失败和输入变化\n')
    effects=[(r,e,a) for r in joint['rows'] for e in r['target_effects'] for a in e['addresses']];qualified=[x for x in effects if x[1]['actual_status']==x[1]['counterfactual_status']==1 and x[2]['inputs_unchanged'] and x[2]['weakly_dominates_actual']];priced=[x for x in qualified if x[2]['reference_output_difference_USD'] is not None];amount=sum((Decimal(a['reference_output_difference_USD']) for r,e,a in priced),Decimal(0));reverts=sum(e['counterfactual_status']==0 for r in joint['rows'] for e in r['target_effects']);changed=sum(e['counterfactual_status']==1 and not a['inputs_unchanged'] for r,e,a in effects)
    add(f'372 组前腿删除实验全部完成；进一步在 **{joint["summary"]["blocks"]} 个区块**内联合删除相关前腿，372 个目标交易只出现一次。实际前缀逐笔 status/gas/logs 均复现。{reverts} 个目标在删除后回滚，{changed} 个成功目标发生投入变化，均没有计作“同输入收款改善”；{len(qualified)} 个满足成功且投入不变，其中 {len(priced)} 个改善量有价格。\n')
    add(f'这些可估值输出改善量之和为 **${amount:,.2f}**，定义严格限定为“每个区块独立从历史父状态开始，固定其余调用、联合删除指定前腿”的敏感度汇总。不同区块之间没有传递反事实状态，不能写成全事件 no-MEV 损失，也不是 bot 净利润。[完整联合干预数据](../../data/processed/mev_full_window/joint_front_replays.json)。\n')
    add(f'旧批量实验的 {recovered["original_response_errors"]} 个失败已重新请求并定位：删除目标后，后续调用资金不足，属于**干预情景不可执行**，而不是应填成 0 的收益。错误原文、所需金额和现有金额均归档；未通过伪造余额使实验通过。[六项失败诊断](../../data/processed/mev_full_window/recovered_target_removals.json)。\n')
    add('### 拍卖、库存和仓位的分账结果\n')
    add(f'全窗口 **{au["summary"]["unique_observed_delivery_blocks"]:,}/{au["summary"]["unique_observed_delivery_blocks"]:,}** 个保留的 relay 交付金额与链上 proposer 实际收款相等；关联 {au["summary"]["units_with_observed_delivery"]:,} 个操作单元、{au["summary"]["delivery_blocks_linked_to_strategy_units"]:,} 个区块。另逐块列 fee recipient 原生流入、流出、priority、自己支付的 Gas 和原生余额变化代理。Searcher→builder→proposer 是同一价值的后续分配，不能相加成新损失。[全窗口拍卖与实际付款](全窗口拍卖与实际付款.csv)。\n')
    add(f'{pos["summary"]["position_or_NFT_units"]} 个仓位／债务／NFT 单元另列现金、本金、债务及流动性变化，解码 {pos["summary"]["decoded_events"]:,} 个事件、{pos["summary"]["loan_collateral_rows"]} 条借贷／抵押本金账及 {pos["summary"]["liquidity_position_rows"]} 条流动性仓位账。借入是负债，Withdraw／Redeem 是释放旧本金，Mint／Burn 的流动性数量不是利润。跨交易开放库存保留完整窗口的收支，未将当前卖出收入伪装成历史成本利润。[本金与仓位明细](../../data/processed/mev_full_window/position_principal_ledger.json)。\n')
    add(f'普通池 **{pool["historical_asset_identities_verified"]}/{pool["pools"]}** 已取得历史资产身份依据，其中 {pool["factory_matches"]} 个历史 factory 目录匹配，余下一个通过历史 EIP-1967 implementation 和 `underlyingTokens()` 核实为 Ammalgam 的 USDC/WETH 借贷池；它的借贷风险单独标出。Algebra 自定义池查询完整 allPairs 目录；动态费率池用 tick spacing，未再套用错误的固定 fee 身份参数。\n')
    add('### 价格不足与转账金额不足是两回事\n')
    add(f'补充确切合约的历史二级报价和已认证币种的 Binance spot 后，**{price["fully_priced_units"]:,}/{price["verified_disjoint_cycle_units"]:,}** 个资金闭合单元可完整估值，参考净额 **${Decimal(price["priced_reference_net_USD"]):,.2f}**，保留 {price["nonpositive_after_cost_units"]} 个扣费后非正单元。其余单元的资产合约和 raw 数量仍全部可查，缺少的是可靠美元标价，并非转账未找到。\n')
    add(f'四种 Few 包装资产已核对历史 `token()`、小数位、准备金及 **{len(few["observed_conversions"])} 次实际 Wrap/Unwrap**，每次同时匹配原币转账和包装币 mint/burn，数量均为 1:1。然而核实源码还允许授权 minter 不交原币直接 mint，24 个快照的直接准备金也低于 totalSupply。实证支持已发生兑换的数量，不能据此宣称全部发行量始终按原币价格兑现。九笔订单中六笔的这些储备数量因此保留原币单位，独立于已经精确算出的 maker 交付和 filler 权益。[历史兑换与准备金](../../data/processed/few_wrapper_backing.json)。\n')
    add('### Bitquery 比较新增的同口径敏感度\n')
    comparison=read('named_pool_edge_comparison.json');add('稳定币改按 $1，同时分别使用前分钟和同分钟 Coinbase，再用实际取回的 Hyperliquid 15 分钟高低价给出条件范围。目标日期的 Hyperliquid 1 分钟请求返回空数组；官方接口只保留最近 5,000 根对应周期 K 线，因此没有冒充取回精确分钟数据。下面是各地址参与的全部 ETH/USDT、USDC **卖出池腿价差**，未扣重复路径和整笔成本，不称为实际最终利润。\n\n| 地址 | 卖出腿价差：同分钟 Coinbase、稳定币 $1 | 唯一交易数 |\n|---|---:|---:|')
    for r in comparison['summary']:
        if r['scope']=='all_ETH_stable_pool_legs' and r['phase']=='sell_ETH':add(f'| `{r["address"]}` | ${Decimal(r["same_minute_Coinbase_stable_1_margin_USD"]):,.2f} | {r["unique_transactions"]} |')
    add('\n例如 `0xa127…3fa6` 的卖出腿约 $0.73M，接近来源约 $0.72M，但其原 gas 地址＋入口边界不留这些资产。完整真实收支表另外列出实际原币提供者、收款人和协议仓位，不能把中间卖出腿全写成该 EOA 的净所得。`0x58a4…e836` 的同口径卖出腿约 $1.265M，整笔操作参考净额约 $0.581M，差异体现成本及路径范围。比较结果支持部分价差数量级，未证明 Bitquery 所有行的交易筛选或整篇全链总数。[逐池比较及行情范围](../../data/processed/mev_full_window/named_pool_edge_comparison.json)。\n')
    return '\n'.join(rows)
