"""Publish the evidence-backed research deliverable; no invented global MEV total."""
import json
from pathlib import Path
from decimal import Decimal as D,getcontext
from datetime import datetime,timezone
from collections import defaultdict
getcontext().prec=70
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
fmt=lambda x:f'{D(x):,.2f}'
utc=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def main():
 native_findings=load('native_scope_findings_classification.json');old=load('unified_target_valuation.json');new=load('expanded_scope_valuation.json');oracle=load('oracle_assisted_scenarios.json');late=load('late_candidate_completion.json');pan=load('pancake_coverage_completion.json');inv=load('inventory_valued_ledger.json');allocation=load('target_settlement_allocation.json');fee=load('full_fee_distribution.json');gas=load('gas_baseline_comparison.json');native=load('native_address_scope_audit.json');precision=load('priced_token_precision_validation.json');aave=load('aave_borrower_accounting.json');liq=aave['liquidations'][0];cf=load('v2_local_counterfactuals.json');lp=load('v3_position_valuation.json');v2=load('target_v2_fee_accounting.json');tron=load('tron_valuation.json');recipients=load('recipient_distribution_ledger.json');cutoff=load('scope_latest_cutoff.json')['result'];heads={r['block']:r for r in load('full_window_evidence.json')['rows']}
 allinv=load('all_scope_strategy_valuation.json');allgroups=load('all_scope_sandwich_groups.json');allallocation=load('all_scope_settlement_allocation.json');incremental=load('incremental_candidate_classification.json')
 oldrows=[r for r in old['rows'] if r['eligible_exchange_candidate']];newrows=[r for r in new['rows'] if r['category']=='pool_swap_compatible'];oldhs={r['hash'] for r in oldrows};newhs={r['hash'] for r in newrows};checks=[]
 def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
 check('原窗口1172与后续180兑换哈希唯一且不重叠',len(oldhs)==1172 and len(newhs)==180 and not oldhs&newhs)
 check('全部兑换存在资产流出及对价流入',all(any(int(x)<0 for x in r['lead_net_token_raw'].values()) and (D(r['lead_native_ETH'])>0 or any(int(x)>0 for x in r['lead_net_token_raw'].values())) for r in oldrows) and all(any(int(x)<0 for x in r['net_token_raw'].values()) and (int(r['lead_native_wei'])>0 or any(int(x)>0 for x in r['net_token_raw'].values())) for r in newrows))
 for label,data,rows,modes in [('original',old,oldrows,['strict','five_minute']),('later',new,newrows,['strict','five_minute','fifteen_minute_sensitivity'])]:
  for mode in modes:
   priced=[r for r in rows if r[mode]['USD'] is not None]
   check(label+' '+mode+' 汇总与逐笔金额相等',len(priced)==data['summary'][mode]['count'] and -sum((D(r[mode]['USD']) for r in priced),D(0))==D(data['summary'][mode]['execution_shortfall_USD']))
   check(label+' '+mode+' 缺失价格未记零',all((r[mode]['USD'] is None)==bool(r[mode]['missing_assets'] or r[mode]['ETH_cashflow_USD'] is None) for r in rows))
 check('原窗口全部1172笔混合基准估值',oracle['summary']['target']['count']==1172 and {r['id'] for r in oracle['rows'] if r['kind']=='target' and r['eligible'] and r['USD'] is not None}==oldhs)
 check('新增候选完整且无重复',not late['errors'] and len({r['hash'] for r in late['rows']})==2633 and all(r['trace_complete'] for r in late['rows']))
 union={r['hash'] for r in load('full_candidates.json')['rows']}|{r['hash'] for r in pan['candidates']}|{r['hash'] for r in late['rows']}
 check('扩展候选集16491笔去重',len(union)==16491 and late['summary']['union_candidate_transactions']==len(union))
 check('新增候选均有同块或后五块关联目标',all(any(0<=r['block']-p['block']<=5 and p['hash'] in newhs for p in r['prior_targets']) for r in late['rows']))
 check('新增候选逐资产估值算术',all(D(r[m]['USD'])==D(r[m]['ETH_cashflow_USD'])+sum((D(a['USD']) for a in r[m]['assets']),D(0)) for r in late['rows'] for m in ['strict','five_minute'] if r[m]['USD'] is not None))
 check('1172笔结算资产对账逐笔守恒',len(allocation['rows'])==1172 and all(abs(D(r['conservation_residual_USD']))<D('1e-30') for r in allocation['rows']) and abs(D(allocation['summary']['sum_roles_USD']))<D('1e-25'))
 check('145个已估值合约历史精度核验',len(precision['rows'])==145 and not precision['errors'] and not precision['mismatches'])
 check('FUN行情合约与代号一致',load('verified_fun_market_prices.json')['contract']=='0x419d0d8bdd9af5e606ae2232ed285aff190e711b' and load('verified_fun_market_prices.json')['exchange_symbol']=='FUNTOKEN' and all('FUNTOKEN_USDT' in b['source'] for b in load('verified_fun_market_prices.json')['bars'].values()))
 check('清算抵押物本金等式',int(liq['total_collateral_removed_underlying_raw'])==int(liq['collateral_received_raw'])+int(liq['protocol_fee_aUSDT_raw']))
 check('清算损失等于毛价差加协议费',D(liq['gross_borrower_liquidation_asset_loss_USD'])==D(liq['gross_liquidation_spread_USD'])+D(liq['protocol_fee_underlying_valuation']['USD']))
 check('原生币地址范围复核无解析错误',not native['errors'] and native['summary']['blocks']==3311)
 check('窗口与对照Gas均等于销毁加优先费',all(D(gas[k]['gas_ETH'])==D(gas[k]['burn_ETH'])+D(gas[k]['priority_ETH']) for k in ['event','baseline']))
 check('失败交易比率与计数相符',all(abs(D(gas[k]['failed_fraction'])-D(gas[k]['failed_transactions'])/gas[k]['transactions'])<D('1e-27') for k in ['event','baseline']))
 check('已有14项缺口检查及19项收益检查全部通过',all(c['passed'] for c in load('candidate_gap_validation.json')['checks']) and load('revenue_ledger_validation.json')['failed']==0)
 check('新增2868候选完成经济分类且无重复',len(incremental['rows'])==2868 and len({r['hash'] for r in incremental['rows']})==2868)
 ah=[h for r in allinv['rows'] for h in r['transaction_hashes']]
 check('全范围策略核算交易哈希去重',len(ah)==len(set(ah)))
 check('全部16491候选纳入全范围策略账',union<=set(ah) and allinv['candidate_hashes']==16491)
 check('564组结构覆盖1128个不重复策略腿',len(allgroups['groups'])==564 and len({r['hash'] for g in allgroups['groups'] for r in g['legs']})==1128)
 check('全范围配对现金流等于各腿合计',all(D(g['net_cashflow_ETH'])==sum((D(l['cashflow_ETH']) for l in g['legs']),D(0)) for g in allgroups['groups']))
 check('1351笔结算逐笔与汇总守恒',len(allallocation['rows'])==1351 and all(abs(D(r['conservation_residual_USD']))<D('1e-30') for r in allallocation['rows']) and abs(D(allallocation['summary']['sum_roles_USD']))<D('1e-25'))
 oldsettle={r['hash']:r['lead_change_including_own_gas_USD'] for r in allocation['rows']}
 check('扩展结算不改变原1172笔的定价',all(D(r['lead_change_including_own_gas_USD'])==D(oldsettle[r['hash']]) for r in allallocation['rows'] if r['hash'] in oldsettle))
 check('全范围策略估值缺失项仍未记零',all((r[m]['USD'] is None)==bool(r[m]['missing_assets'] or r[m]['ETH_cashflow_USD'] is None) for r in allinv['rows'] for m in ['strict','five_minute']))
 validation={'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks)};(R/'event_completion_validation.json').write_text(json.dumps(validation,indent=2));assert not validation['failed'],validation
 combined={m:{'count':old['summary'][m]['count']+new['summary'][m]['count'],'shortfall_USD':str(D(old['summary'][m]['execution_shortfall_USD'])+D(new['summary'][m]['execution_shortfall_USD']))} for m in ['strict','five_minute']}
 mixed=-D(oracle['summary']['target']['sum_marked_change_USD'])+D(new['summary']['fifteen_minute_sensitivity']['execution_shortfall_USD']);lastswap=max(r['timestamp'] for r in newrows);roles=allocation['summary']['role_priced_asset_changes_USD'];lpfee=[x for x in lp['rows'] if x.get('credited_fee_USD_at_last_event') is not None];lpclosed=[x for x in lp['rows'] if x.get('closed_position_marked_cashflow_before_gas_USD') is not None]
 findings={'version_date':'2026-11-05','cutoff_UTC':utc(int(cutoff['timestamp'],16)),'exchange_candidates':len(oldhs|newhs),'candidate_transactions':len(union),'market_only':combined,'mixed_sensitivity':{'count':1351,'shortfall_USD':str(mixed),'not_global_MEV':True},'last_observed_later_swap_UTC':utc(lastswap),'validation':validation}
 (R/'event_completion_summary.json').write_text(json.dumps(findings,indent=2))
 lines=[
 '# Binance 资金急迫兑换、MEV 与收益归属：提交版研究报告','',
 f'更新：2026-11-05。所有时间为 UTC。后续地址日志扫描截至 **{utc(int(cutoff["timestamp"],16))}**，区块 {int(cutoff["number"],16)}。本稿替代旧报告中的覆盖数与汇总金额；旧文件保留为历史证据。','',
 '## 研究结论','',
 f'在有来源的关联地址集合内，本研究识别 **1,352 笔 Ethereum 兑换候选**，取得兑换回执及内部原生币收支，并将附近潜在套利交易扩展至 **16,491 笔**。采用统一的交易前已完成分钟行情，{combined["strict"]["count"]} 笔可完整估值，成交资产差额合计 **${fmt(combined["strict"]["shortfall_USD"])}**；行情允许额外陈旧五分钟时覆盖 {combined["five_minute"]["count"]} 笔，差额 **${fmt(combined["five_minute"]["shortfall_USD"])}**。这两组样本不同，不能解释为同一总额的上下界。','',
 f'另外给出覆盖更广、假设更强的敏感性口径：原窗口缺价资产使用前一区块 Aave 预言机，后续低流动性 FUNToken 行情放宽至额外十五分钟，**1,351 笔差额为 ${fmt(mixed)}**。剩余一笔 DAR 兑换保留原始数量和 ETH 收入，没有把缺价资产记成零。该口径不能替代主要市场行情结果。','',
 '**上述金额是基准价格下的成交差额，不是“全事件被 MEV 拿走的精确金额”。** 它同时包含交易冲击、池费、报价差异、市场变动和排序影响。现有证据可以独立给出可复核的部分排序影响、地址现金流、费用转付及借贷清算结果；无法从这些相互重叠的量唯一推出全事件因果 MEV 总额。本研究不以第三方数字填补这一步。','',
 '## 1. 老师的问题及研究口径','',
 '核心问题是：被盗资金在赶时间兑换稳定币和 ETH 时，是否因价格冲击和交易排序损失价值；损失有多少被套利者、LP、订单成交方、构建者和验证者取得；为何 Gas 激增。截图中的“DEX 约 3000、市场约 2200”是待检验的特定成交现象，不是可直接套用到全部被盗资产的比例。','',
 '本研究区分三项量：','',
 '1. **执行差额**：对关联地址集合的每种资产净变化按交易前价格估值，取负值。内部地址互转抵消；Gas 另列。保留负差额，即有利成交，不只挑损失交易。','2. **观察到的收支与费用**：按原生币和 ERC-20 逐资产记账，区分本金、债务、手续费、Gas 销毁及后续转付。地址收到钱并不必然代表最终赚到同样多的钱。','3. **局部排序影响**：在可精确复现的池状态下固定输入，仅移除指定前置交易，比较目标输出。这是有条件的局部反事实，不能推广为全事件行为反事实。','',
 '## 2. 时间线与覆盖','',
 '| 时点/范围 | 事件与证据 |','|---|---|',
 '| 10-29 19:58:23—10-30 07:02:47 | 连续核查 Ethereum 26300640–26303950，共 3,311 块、751,258 笔交易；回执、区块及完整调用轨迹齐备。 |',
 '| 原窗口内 | 识别 1,172 笔兑换候选；补识别此前遗漏的 Pancake V3 事件格式、UniswapX 及 1inch 订单事件。 |',
 f'| 10-30 07:06:59—{utc(lastswap)} | 发现另外 180 笔含兼容兑换事件、资产流出和对价流入的交易；逐笔取得完整回执与轨迹。不是这一整段时间的全链连续扫描。 |',
 '| 11-03 官方通报 | Binance 报告受影响约 63.4 亿美元，冻结或拦截约 28.5 亿美元。与老师截图中的早期 63/20/43 亿口径分开保留。 |',
 f'| {utc(next(r["timestamp"] for r in new["rows"] if r["hash"]==liq["hash"]))} | 关联 Aave 仓位被部分清算，另行核算抵押物、负债和费用。 |',
 f'| {utc(int(cutoff["timestamp"],16))} | 本轮后续已知地址 ERC-20 日志扫描截止。截止不是事件结束的证明。 |','',
 '[Binance 官方通报](https://www.binance.bh/en/blog/community/3229153443759566763)给出官方损失与冻结时点；[FBI 通报](https://www.fbi.gov/investigate/cyber/alerts/2026/north-korea-responsible-for-6-billion-binance-attack)提供关联地址线索。FBI 的“运营或密切关联”不等于共同所有权。','',
 f'地址集合来自追踪清单的 55 个 Ethereum 地址，以及 FBI 的 608 个地址，合并 653 个。原连续窗口已追加检查全部内部原生币调用：额外 598 个 FBI 地址涉及原生币净流的交易为 **{native["summary"]["additional_FBI_native_flow_transactions"]}**；55 地址存在原生币净流、但未列入旧根交易/代币日志账的交易为 **{native["summary"]["lead_native_transactions_missing_old_ledger"]}**。详见 `native_address_scope_audit.json`。此结果不外推到后续全部区块。','',
 f'补查中发现 37 个额外 FBI 关联地址通过 42 笔交易净流入 {native_findings["summary"]["additional_FBI_net_ETH"]} ETH；另外，55 地址有 108 笔旧账未捕捉的纯原生币净流入，合计 {native_findings["summary"]["missing_old_ledger_lead_native_net_ETH"]} ETH。上述两类交易均无对应集合的代币净流，额外 FBI 交易也没有与 1,172 笔兑换样本重叠。因此补入资金流附表，不能直接作为新增兑换损失或套利利润。', '',
 '后续扫描仅针对 55 个地址双向 ERC-20 Transfer：1,072 次范围查询无下载错误；6 条格式不符合标准的日志隔离，取得 183 笔已知代币净流出详细记录，其中 180 笔列入兑换候选、3 笔为其他流出。未知地址、仅原生币活动、其他链及截止后的活动仍可能遗漏。','',
 '## 3. 兑换损失的统一核算','',
 '| 价格口径 | 原连续窗口 | 后续新增 | 合计（美元） |','|---|---:|---:|---:|',
 f'| 前一已完成分钟 | {old["summary"]["strict"]["count"]} 笔 / {fmt(old["summary"]["strict"]["execution_shortfall_USD"])} | {new["summary"]["strict"]["count"]} 笔 / {fmt(new["summary"]["strict"]["execution_shortfall_USD"])} | {fmt(combined["strict"]["shortfall_USD"])} |',
 f'| 额外陈旧 ≤5 分钟 | {old["summary"]["five_minute"]["count"]} 笔 / {fmt(old["summary"]["five_minute"]["execution_shortfall_USD"])} | {new["summary"]["five_minute"]["count"]} 笔 / {fmt(new["summary"]["five_minute"]["execution_shortfall_USD"])} | {fmt(combined["five_minute"]["shortfall_USD"])} |',
 f'| 独立混合敏感性 | 1,172 笔 / {fmt(-D(oracle["summary"]["target"]["sum_marked_change_USD"]))} | 179 笔 / {fmt(new["summary"]["fifteen_minute_sensitivity"]["execution_shortfall_USD"])} | {fmt(mixed)} |','',
 '混合敏感性在原窗口补入 8 笔 USDe、4 笔 DAI、2 笔 USDS 的预言机估值；不是把稳定币一律按 1 美元。预言机可能含赎回比例、价格上限和旧报价，未核验每个底层 feed 更新时间。后续十五分钟口径加入 15 笔在五分钟内没有有效成交报价的 FUNToken 交易。','',
 '已纠正同名代币风险：Ethereum FUNToken 的 Gate 市场代号是 **FUNTOKEN_USDT**；Gate/KuCoin 的 FUN 是另一条链的 Sport.fun，不可用于本研究。已撤除错误映射，正确合约为 `0x419d0d8bdd9af5e606ae2232ed285aff190e711b`。所有纳入本轮精度抽查的 145 个已估值合约，其历史 decimals() 与采用的小数位一致。其他未独立验证的交易所同名映射仍在逐资产证据中明示。','',
 '唯一在混合扩展口径仍未完整估值的后续兑换是 DAR：交易 `0x230b5d9ec55aa34e0de8342c1b0f5ef8ca46d11d9f13dfaeadd2dff3351b5272` 转出 **3,530,547.65 DAR（6 位小数）**，收到 **0.163436357213440460 ETH**。DAR 发生过代币迁移，不能直接以新代币同名价格替代旧合约，也不能把转出价值置零。','',
 f'TRON 独立附表覆盖首日 46 个地址的交易历史及其发起调用，16 笔大额兑换将 234,000,000 USDT 换成 638,172,758.693694 TRX，选定基准差额 **${fmt(tron["summary"]["shortfall_usd"])}**。该表有 0–240 秒报价陈旧、地址方向和时段限制，未完成与 Ethereum 同等的所有套利者策略核算。因此不将它与上表合成“全事件 MEV”。','',
 '老师提到的高价买 ETH 有直接成交证据。例如区块 26300992 的交易 [0x2a1979…](https://etherscan.io/tx/0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6) 支出 30,000,000 USDT，净收到 9,551.900920261967562557 ETH，等效成本约 **3,140.74 USDT/ETH**；前一已完成分钟的市场 ETH/USD 为 **2,260.00**。这是地址净收付的平均执行成本，不是池内瞬时现货价格；USDT/USD 偏差在实际差额估值中另有转换。', '',
 '## 4. 损失在兑换完成时首先体现在哪里','',
 '对原窗口全部 1,172 笔兑换，按混合基准、在同一交易结算时点为所有触及账户记账。每种资产的转入与转出守恒，Gas 拆为销毁和优先费；WETH 铸造/销毁单设储备对应项，避免重复算 ETH 和 WETH。1,163 笔交易的所有对手方资产可以完整估值；其余 9 笔保留未估值的凭证或负债类资产。下表是**可估值资产部分**，不是全部主体净财富。','',
 '| 账户角色 | 资产净变化（美元） | 解释 |','|---|---:|---|',
 f'| 关联地址集合 | {fmt(roles["lead_set"])} | 包含本集合自己支付的 Gas。 |',
 f'| 池库存 | {fmt(roles["pool_inventory"])} | 后续套利前留在池内的价值，不等于 LP 最终利润。 |',
 f'| 借贷协议资产 | {fmt(roles["lending_protocol_assets_excluding_liabilities"])} | 尚未抵消债权/负债变化，不是协议利润。 |',
 f'| 其他地址 | {fmt(roles["other_addresses"])} | 包含路由及未完成主体归属的账户。 |',
 f'| 当块费用收款地址 | {fmt(roles["block_fee_recipient"])} | 后续可能转付；不可再把转付全额相加。 |',
 f'| 已识别 UniswapX filler 地址 | {fmt(roles["identified_UniswapX_filler"])} | 结算时资产变化，不是全部订单成交方利润。 |',
 f'| 基础费销毁 | {fmt(roles["base_fee_burn"])} | 被销毁，任何人都未收入。 |',
 f'| 铸销及包装对应项 | {fmt(roles["token_issuance_or_wrap_bookkeeping"])} | 非人物账户收益；保留转换/计价差。 |',
 f'| 总和 | {fmt(roles and allocation["summary"]["sum_roles_USD"])} | 不同角色在本结算口径下相互抵消。 |','',
 '结算时池库存增加，并不意味着套利者尚未拿走或最终一定拿走同样金额。后续交易会在池与参与者之间重新分配价值。因此不能把本表与后面的套利现金流、LP 手续费、提议者付款相加。逐地址原始金额见 `target_settlement_allocation.json`。','',
 '## 5. 谁获得了可观察的收入','',
 f'**套利候选。** 原来的 12,934 笔原生币缺口已归零。修复 Pancake V3 事件格式后，原窗口候选由 13,623 扩为 13,858；后续针对 180 笔兑换读取 866 个相关区块回执，新增 2,633 笔，合计 16,491。新增候选所在 484 个区块的完整轨迹与区块/回执根交易集合一致。所有这些仍只是同块或后五块池重合候选，不自动认定套利。','',
 f'原窗口 449 组前后手结构按交易哈希去重。严格行情下 {inv["summary"]["paired_strategy:strict"]["fully_priced_without_recognized_position_events"]} 组可完整估值且没有已识别仓位/债务事件，合计净现金流 **${fmt(inv["summary"]["paired_strategy:strict"]["marked_net_cashflow_USD"])}**；五分钟口径 {inv["summary"]["paired_strategy:five_minute"]["fully_priced_without_recognized_position_events"]} 组为 **${fmt(inv["summary"]["paired_strategy:five_minute"]["marked_net_cashflow_USD"])}**。Gas 和原生币付款已经扣除，但共享路由器、窗口外头寸及对冲仍限制受益人利润解释。后续候选采用更窄的交易发起者加入口地址边界，未冒充同等完整策略利润。','',
 f'**LP。** 141 个 V3 仓位本金/记账手续费全部对平，139 个在窗口内完整开平。{len(lpfee)} 个可估值手续费项合计 **${fmt(sum((D(x["credited_fee_USD_at_last_event"]) for x in lpfee),D(0)))}**；{len(lpclosed)} 个可估值完整开平仓位的领取减投入为 **${fmt(sum((D(x["closed_position_marked_cashflow_before_gas_USD"]) for x in lpclosed),D(0)))}**，未扣完整策略成本，不是因果 MEV。另有 527 次 V2 兑换通过官方 factory 与整数输出公式核验，其中 {v2["summary"]["priced_fee_swaps"]} 次毛池费可估值，共 **${fmt(v2["summary"]["marked_gross_pool_fees_USD"])}**。这些不是全体 LP 的净利润。','',
 f'**订单成交方。** 识别 4 个 UniswapX Fill 与 5 个 1inch 兼容订单事件。9 笔交易中，8 笔在排除已识别借贷并允许预言机补价后，边界内净资产变化合计 **${fmt(oracle["summary"]["filler"]["sum_marked_change_USD"])}**；另 1 笔含 Compound 市场交互，不能直接算利润。Fill 指定地址有直接事件依据，但扩展调用边界不构成共同所有权证明。','',
 f'**构建者与验证者。** 连续窗口全部交易 Gas 为 **{fmt(D(fee["summary"]["gas_wei"])/10**18)} ETH**，其中销毁 {fmt(D(fee["summary"]["burn_wei"])/10**18)} ETH、优先费 {fmt(D(fee["summary"]["priority_wei"])/10**18)} ETH。88 个当块费用收款地址、473 个公开记录覆盖的提议者收款地址已分别列账。公开 relay 覆盖 {fee["relay_record_blocks"]} 块，{fee["relay_matched_blocks"]} 块匹配实际单笔或转付路径，合计 **{fmt(D(fee["matched_proposer_payout_wei"])/10**18)} ETH**。这是窗口实际付款，不是全部由本事件创造的 MEV。','',
 '可观察收款地址示例（按已匹配提议者付款排序；没有推定真实人物身份）：','',
 '| 提议者收款地址 | 已匹配付款 ETH |','|---|---:|']
 for a,d in sorted(recipients['proposer_recipients'].items(),key=lambda x:D(x[1].get('matched_payment_wei','0')),reverse=True)[:5]:lines.append(f'| [{a}](https://etherscan.io/address/{a}) | {fmt(D(d.get("matched_payment_wei","0"))/10**18)} |')
 lines += ['', '完整地址表及对应口径见 `收款地址分配账.csv` 与 `recipient_distribution_ledger.json`。验证者转付与费用收款地址的流出重叠；不能把两个表头金额加成新的收益。','',
 '## 6. 能直接复核的排序影响','',
 f'217 个 V2 前手—目标链接中，70 个不同目标通过官方池身份核验、前手与目标实际输出的整数复现、储备连续性检查。固定目标输入，仅撤掉紧邻前手，目标理论上多收到的资产估值共 **${fmt(cf["summary"]["marked_target_output_reduction_USD"])}**。其余 147 个按复杂路径或池身份等原因排除，没有强行拟合。','',
 '这个值是局部模型下的目标输出减少，不是套利者实得金额，也不是全事件 MEV 下限。它没有允许其他套利者重排、交易撤回、跨池路径重新选择或滑点约束重新决定执行。','',
 '双池案例进一步展示为何要合并前后手：后手单看增加 567.6797 ETH，前手减少 555.5996 ETH，合并后只有 **12.0800 ETH**。固定路线和输入、移除目标交易的另一局部实验差值为 **23.8284 ETH**。这两个反事实移除的交易不同，不可混用。原始交易与公式见 `strong_case_verified.json`、`v2_local_counterfactuals.json`。','',
 '## 7. 借贷、冻结与 11 月 4 日清算','',
 f'关联借款地址为 [{aave["user"]}](https://etherscan.io/address/{aave["user"]})。窗口内两次存入合计 **60,000,000 USDT**，两次借出本金合计 **19,762.412971223783227507 WETH**。借出的 ETH 同时对应负债，不是凭空增加同额财富；抵押物、借款和冻结额不可重复计数。','',
 f'[后续清算交易](https://etherscan.io/tx/{liq["hash"]})实际偿还 **{D(liq["debt_covered_raw"])/10**18} WETH**，清算执行合约 `{liq["liquidator"]}` 收到 **{fmt(D(liq["collateral_received_raw"])/10**6)} USDT**；协议另收 **{fmt(D(liq["protocol_fee_aUSDT_raw"])/10**6)} aUSDT**，收款地址 `{liq["protocol_fee_recipient"]}`。','',
 f'按交易前市场价、把协议 aUSDT 费用按底层 USDT 标记，借款人的抵押物减少减去债务减少为 **${fmt(liq["gross_borrower_liquidation_asset_loss_USD"])}**。其中清算执行的毛价差为 **${fmt(liq["gross_liquidation_spread_USD"])}**，协议费约 **${fmt(liq["protocol_fee_underlying_valuation"]["USD"])}**。毛价差不等于执行者最终利润。该交易当块费用地址 `{liq["block_fee_recipient"]}` 净收到 **{D(liq["block_fee_recipient_net_native_ETH"]):.8f} ETH**，约 **${fmt(liq["block_fee_recipient_net_native_USD"])}**；这已属于同一笔清算价值流，不再加到清算损失上。','',
 '核算使用 LiquidationCall 的真实偿债量，而不是直接使用债务代币净 Transfer：利息累积会使两者不同。aUSDT 的净转移同样受利息结晶影响。前一区块健康因子大于 1 不等于清算调用前的块内健康因子大于 1。截止区块仍有抵押物和负债；被冻结的抵押物不一定能够赎回。因此本表不是全事件最终可收回财富表。清算与前面兑换表交易哈希不同，但仍不把二者一并称为 MEV。','',
 '## 8. Gas 激增是否成立','',
 '以前一天相同 UTC 时段为描述性对照，仅对应最初 1,301 块的约 4 小时 21 分钟事件窗口；不是全部 11 小时窗口。已完整取得对照 1,303 块回执。','',
 '| 指标 | 事件窗口 | 前一天同时段 |','|---|---:|---:|',
 f'| 交易数 | {gas["event"]["transactions"]:,} | {gas["baseline"]["transactions"]:,} |',
 f'| 失败率 | {D(gas["event"]["failed_fraction"])*100:.4f}% | {D(gas["baseline"]["failed_fraction"])*100:.4f}% |',
 f'| 每笔平均 Gas 成本 ETH | {D(gas["event"]["mean_gas_fee_ETH_per_transaction"]):.9f} | {D(gas["baseline"]["mean_gas_fee_ETH_per_transaction"]):.9f} |',
 f'| 基础费中位数 gwei | {D(gas["event"]["median_base_fee_gwei"]):.6f} | {D(gas["baseline"]["median_base_fee_gwei"]):.6f} |',
 f'| 优先费 ETH | {fmt(gas["event"]["priority_ETH"])} | {fmt(gas["baseline"]["priority_ETH"])} |',
 f'| 失败交易 Gas ETH | {fmt(gas["event"]["failed_gas_ETH"])} | {fmt(gas["baseline"]["failed_gas_ETH"])} |','',
 f'每笔平均 Gas 成本为对照的 **{D(gas["ratios"]["mean_gas_fee_ETH_per_transaction"]):.2f} 倍**，失败率为 **{D(gas["ratios"]["failed_fraction"]):.2f} 倍**。这支持拥堵和竞争显著上升，但单日同期比较没有控制全部市场活动，不能把全部增量因果归于此次盗币或 MEV。','',
 '## 9. 与第三方总额的关系及未识别部分','',
 '[Bitquery 研究](https://bitquery.io/investigations/binance-hack-who-profited)给出约 1.19 亿美元差额，并列交易者 5,990 万、构建者/验证者 2,950 万、LP 2,020 万、成交方 670 万美元。列出的四项合计为 1.163 亿，并不直接等于 1.19 亿；不能自行补一个残差来宣称复现。','',
 '本研究采用的地址集合、截止日期、成交价格和覆盖链不同。新的 Ethereum 扩展结果也不能拿去与旧的局部 TRON 表简单相加后声称证明或推翻第三方总额。需要对方逐笔范围和价格规则才能严格调和。','',
 '仍未被数据唯一识别的是：所有相关主体及未知地址、其他链和窗口外交易的完整经济账；共享路由与真实受益人的区分；全体 LP/借贷和跨市场对冲成本；以及允许全市场重新行动后的统一因果反事实。原 12,934 笔缺内部转账已不是障碍；剩余问题主要是范围和经济归因，而非把候选现金流再加一遍。','',
 '## 10. 可复核交付与完成状态','',
 f'本次新增 **{validation["passed"]} 项检查全部通过**；原 14 项候选缺口核验、19 项收益账核验仍通过；另有 30 次历史余额独立对比及 145 个历史代币精度检查。检查证明相应实现和账目自洽，不证明所有身份、估值或因果假设。','',
 '| 老师要求 | 本次交付 | 状态 |','|---|---|',
 '| 独立建立事件时间线 | 官方时点、连续主窗口、后续兑换与清算时间线 | 已交付，覆盖边界明确 |',
 '| 量化兑换造成的价值差额 | 1,352 笔候选，严格/五分钟/混合三套逐笔估值 | 已交付；最后一种仍有 1 笔缺价 |',
 '| 查清原 12,934 笔候选收支 | 原缺口为 0，候选扩到 16,491 且原生币可核对 | 已完成对应数据任务 |',
 '| 判断是否存在套利与排序影响 | 分类、449 组结构、70 笔局部反事实与双池案例 | 已交付限定因果证据 |',
 '| 解释收益流向 | 1,172 笔结算对账、地址分配、LP 本金/费、订单方、清算 | 已交付可观察分配；非全体最终净利润 |',
 '| 验证 Gas 与失败率上升 | 完整前日同期对照 | 已完成描述性检验 |',
 '| 全事件精确 MEV 及完整受益人分配 | 不能由当前证据唯一识别；未用差额冒充 | 仍未达到这一最强要求 |','',
 '主要复核文件：`event_completion_summary.json`、`event_completion_validation.json`、`unified_target_valuation.json`、`expanded_scope_valuation.json`、`oracle_assisted_scenarios.json`、`late_candidate_completion.json`、`pancake_coverage_completion.json`、`target_settlement_allocation.json`、`native_address_scope_audit.json`、`aave_borrower_accounting.json`、`gas_baseline_comparison.json`。原始回执、完整调用树、历史状态、市场价格及哈希清单均保留在 research 目录。','',
 '方法和合约身份的公开来源包括 [UniswapX 部署](https://developers.uniswap.org/docs/liquidity/uniswapx/deployments)、[UniswapX Fill 事件定义](https://raw.githubusercontent.com/Uniswap/UniswapX/main/src/base/ReactorEvents.sol)、[Pancake V3 Swap 定义](https://raw.githubusercontent.com/pancakeswap/pancake-v3-contracts/main/projects/v3-core/contracts/interfaces/pool/IPancakeV3PoolEvents.sol)、[Aave Oracle 文档](https://www.aave.com/docs/aave-v3/smart-contracts/oracles)、[Aave Pool 接口](https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/interfaces/IPool.sol)、[Coinbase 资产合约清单](https://api.exchange.coinbase.com/currencies)、[Gate 币种及网络合约清单](https://api.gateio.ws/api/v4/spot/currencies)。金额来自保存的链上与行情原始响应，而非仅依赖文章叙述。','']
 # Add the extended accounting next to its original-window counterpart.
 fullroles=allallocation['summary']['role_priced_asset_changes_USD'];rolelabels={'lead_set':'关联地址集合（含自身 Gas）','pool_inventory':'池库存','other_addresses':'其他地址','block_fee_recipient':'当块费用收款地址','identified_UniswapX_filler':'已识别 UniswapX filler','lending_protocol_assets_excluding_liabilities':'借贷协议资产，不含抵消债权','base_fee_burn':'基础费销毁','token_issuance_or_wrap_bookkeeping':'铸销及包装对应项'}
 addition=['### 后续资金去向已补入','',f'扩展后共 **{allallocation["summary"]["transactions"]} 笔**结算逐笔对平，沿用上文独立混合敏感性价格；其中 **{allallocation["summary"]["fully_priced_all_accounts"]} 笔**的全部对手方资产可估值，19 笔仍保留未估值资产。原窗口 1,172 笔的定价与结果保持不变。以下为扩展后的合计，已包含前表，不能再与前表相加。','', '| 角色 | 全部已估值资产净变化（美元） |','|---|---:|']
 for role,label in rolelabels.items():addition.append(f'| {label} | {fmt(fullroles[role])} |')
 addition+=['| 合计 | 0.00 |','','这里仍是兑换结算时的资产分配，不是最终 MEV 利润分配。19 笔未估值资产不能因为已估值部分相抵就视为已解决。逐笔见 `all_scope_settlement_allocation.json`。','']
 at=lines.index('## 5. 谁获得了可观察的收入');lines[at:at]=addition
 addition=['### 全范围策略核算更新','',f'全部 **16,491 笔候选**已纳入统一经济分类与去重核算。新增 2,868 笔中，69 笔包含 LP 仓位操作、15 笔包含借贷或清算、1,818 笔仍有其他代币库存、436 笔存在外部资金或未解释协议事件，均不能仅凭 ETH 收款认定利润；108 笔具备闭合跨池循环和正现金流结构，合计 53.624114967927574043 ETH，但仍不是全事件因果收益。剩余分类保留在逐笔文件。','',f'合并全部已发现池事件后，识别 **564 组**前后手结构、**1,128 个策略腿**，涉及 648 笔目标兑换；共享交易只计一次。严格行情下，{allinv["summary"]["paired_strategy:strict"]["fully_priced_without_recognized_position_events"]} 组可完整估值且无已识别仓位/债务事件，合计标记净现金流 **${fmt(allinv["summary"]["paired_strategy:strict"]["marked_net_cashflow_USD"])}**；五分钟行情覆盖 {allinv["summary"]["paired_strategy:five_minute"]["fully_priced_without_recognized_position_events"]} 组，合计 **${fmt(allinv["summary"]["paired_strategy:five_minute"]["marked_net_cashflow_USD"])}**。另有 112 组其他 ERC-20 库存闭合且无已识别仓位事件，合计 81.011840776198967932 ETH；此子集与前两项重叠，不能相加。','',f'全表共 {allinv["accounting_units"]:,} 个不重叠核算单元，包含候选及前置交易共 {allinv["unique_transaction_hashes_including_fronts"]:,} 个唯一交易哈希。未配对候选不是完整策略，不以其总现金流宣称利润。详见 `all_scope_strategy_valuation.json`、`all_scope_sandwich_groups.json`、`incremental_candidate_classification.json`。以下原窗口结果保留作范围对照，不再代表扩展后的全部组合。','']
 at=next(i for i,x in enumerate(lines) if x.startswith('原窗口 449 组'));lines[at:at]=addition
 senderrows=load('全范围策略发起者分配.json')['rows']
 senderlines=['严格行情下可完整估值的配对结构，按交易发起地址汇总前五如下。金额来自包含调用辅助地址的核算边界，不能推定发起地址本人的最终净利润。','', '| 策略交易发起地址 | 组合数 | 标记净现金流（美元） |','|---|---:|---:|']
 for r in senderrows[:5]:
  label='; '.join(f'[{a}](https://etherscan.io/address/{a})' for a in r['sender_addresses']);senderlines.append(f'| {label} | {r["strict"]["groups"]} | {fmt(r["strict"]["USD"])} |')
 senderlines+=['','完整逐组关联见 `全范围策略发起者分配.json`；该表与配对结构总额是同一批数据，不重复累计。','']
 at=next(i for i,x in enumerate(lines) if x.startswith('**LP。**'));lines[at:at]=senderlines
 lines=[x.replace('分类、449 组结构、70 笔局部反事实与双池案例','全部候选分类、564 组结构、70 笔局部反事实与双池案例').replace('1,172 笔结算对账、地址分配、LP 本金/费、订单方、清算','1,351 笔结算对账、地址分配、LP 本金/费、订单方、清算') for x in lines]
 (R/'研究结论_提交版.md').write_text('\n'.join(lines))
 checklist=['# 老师任务完成度审查（最终更新）','',f'更新时间：2026-11-05。优先阅读[研究结论提交版](研究结论_提交版.md)。本文件覆盖旧的 836 笔/1.14076 亿美元及 13,623 候选汇总，不再把它们作为当前全范围结果。','']+lines[lines.index('| 老师要求 | 本次交付 | 状态 |'):lines.index('主要复核文件：`event_completion_summary.json`、`event_completion_validation.json`、`unified_target_valuation.json`、`expanded_scope_valuation.json`、`oracle_assisted_scenarios.json`、`late_candidate_completion.json`、`pancake_coverage_completion.json`、`target_settlement_allocation.json`、`native_address_scope_audit.json`、`aave_borrower_accounting.json`、`gas_baseline_comparison.json`。原始回执、完整调用树、历史状态、市场价格及哈希清单均保留在 research 目录。')]
 checklist += ['已关闭的缺口：原候选内部转账、Pancake 事件遗漏、前日完整 Gas/失败率对照、141 个 V3 仓位本金手续费对账、已知 Aave 仓位与后续清算、原窗口全部兑换的混合基准估值、后续候选筛查。','', '仍存在的实质限制：全事件未知地址与其他链覆盖、所有经济主体和跨市场持仓、剩余 DAR 可靠行情、全部 LP 与订单方净利润、全事件一致反事实。数据下载完成不等于这些识别条件自动成立。','']
 (R/'任务完成度审查.md').write_text('\n'.join(checklist))
 banner='<!-- event-completion-update -->\n> **最新提交稿：** 已扩展至 1,352 笔 Ethereum 兑换候选、16,491 笔潜在套利交易，补入后续清算及前日 Gas 对照。请以[研究结论提交版](研究结论_提交版.md)为当前统一结论；本文件保留其指定窗口的历史分析。\n<!-- event-completion-update-end -->\n\n'
 for name in ['研究报告_综合版.md','收益与分配总账报告.md','套利判定报告.md','后续时段补充报告.md']:
  p=R/name;s=p.read_text()
  if '<!-- event-completion-update -->' in s:s=s.split('<!-- event-completion-update-end -->',1)[1].lstrip()
  p.write_text(banner+s)
 print('published',findings)
if __name__=='__main__':main()
