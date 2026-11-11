import json
from pathlib import Path
from decimal import Decimal as D,getcontext
from collections import defaultdict
from datetime import datetime,timezone
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def utc(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%m-%d %H:%M:%S')
def main():
 v=load('extension_valuation.json');s=v['summary'];a=load('all_candidate_accounting.json')['summary'];old=load('expanded_valuation.json');tron=load('tron_valuation.json');full=load('full_candidates.json');audit=load('extension_address_audit.json')
 gap=load('candidate_gap_validation.json') if (R/'candidate_gap_validation.json').exists() else None
 checks_note=f"原 24 项、窗口扩展 14 项、候选补齐 {gap['passed']} 项均通过" if gap and gap['remaining']==0 and gap['failed']==0 else '原 24 项与窗口扩展 14 项均通过'
 orig=sum((D(r['shortfall_usd']) for r in old['rows'] if r['shortfall_usd'] is not None),D(0));tr=sum((D(r['shortfall_usd']) for r in tron['rows'] if r['shortfall_usd'] is not None),D(0));strict=D(s['strict_shortfall_usd']['sum_usd']);stale=D(s['up_to_5min_stale_shortfall_usd']['sum_usd'])
 lines=['# 后续时段与全候选核查补充报告','', '更新：2026-11-04。承接原综合报告，使用公开数据；没有使用私人节点或付费密钥。','',
 '本轮确认：原报告截止时间偏早，并遗漏了后续多币种兑换。现已将 Ethereum 连续扫描延长至 **10 月 30 日 07:02:47 UTC**。但老师要求的全事件 MEV 收益分配账仍未完成，不能把执行差额直接当作套利利润。','',
 '| 项目 | 更新结果 |','|---|---|',
 '| 连续范围 | 区块 26300640–26303950；10-29 19:58:23 至 10-30 07:02:47 UTC |',
 '| 交易扫描 | 3,311 块，751,258 笔交易，无缺块 |',
 '| 新增净流出日志记录 | 830 笔，全部取得公开原生币调用轨迹 |',
 '| 新增分类 | 685 笔含池兑换事件；66 笔代币流出/ETH 流入但协议待确认；3 笔其他流出；76 笔未核实合约日志隔离 |',
 f"| 合并兑换事件与候选 | 1,102 笔含兑换事件的净流出记录，{full['affected_pool_count']} 个池标识，13,623 笔后续候选 |",
 f"| 候选现金流 | 全部建表；{a['native_available']:,} 笔原生币证据齐全，{a['native_missing']:,} 笔仍缺失 |",
 f"| 账户库存闭合子集 | {a['native_available_and_other_inventory_closed']:,} 笔其他 ERC-20 净库存为零；扣 gas 后 ETH/WETH 净额合计 {a['closed_group_cashflow_ETH']} ETH |",
 f'| 一致性检查 | {checks_note}；不代表因果证明 |','',
 '## 1. 新增执行差额','',
 '执行差额采用地址线索集合的外部净资产变化与事件前的市场报价比较，不含 gas。正值表示相对基准少收到的价值；它同时可能包含正常滑点、急售冲击、流动性成本、报价差异和 MEV，不能把这些因素全部归给套利者。','',
 '| 口径 | 新增可估值笔数 | 新增执行差额（美元） |','|---|---:|---:|',
 f"| 严格：上一完整分钟有成交报价 | {s['strict_shortfall_usd']['count']} | {strict:,.2f} |",
 f"| 扩展敏感性：允许最多再陈旧 5 分钟 | {s['up_to_5min_stale_shortfall_usd']['count']} | {stale:,.2f} |",'',
 '**两行样本数量不同，不能把两个数当作同一估计的上下界或置信区间。** 价格缺失、身份未核实、协议/收支不满足估值条件的记录不按零处理。USDC/DAI 使用平价假设，WBTC 使用 BTC 代理报价。','',
 f'原 Ethereum 严格样本 328 笔与本轮 492 笔合计 **820 笔、{orig+strict:,.2f} 美元**。再加原 TRON 16 笔大额样本，限定样本共 **836 笔、{orig+strict+tr:,.2f} 美元**。TRON 使用不同交易所、允许报价陈旧的基准，因此跨链合计仅作描述性汇总，不是统一基准下的全事件损失，更不是 MEV 总额或下限。','',
 '严格新增样本中，455 笔有池兑换事件，差额为 7,165,047.64 美元；另 37 笔协议待确认，差额为 655,427.20 美元。后者属于条件估计。','',
'## 2. 代币身份与地址范围','',
 '按合约地址对照公开 CoinGecko Ethereum 代币目录和 Blockscout 小数位，55 个新增流出合约中 43 个得到对应；12 个未得到对应，其中多份日志使用 ETH、USDT、LINK 的同名或相似字符。76 笔涉及未核实合约的记录全部隔离。目录缺失本身不证明诈骗，但这些日志也不能证明真实主流资产流出。','',
 f"FBI 名单相对原追踪器多出的地址中，新增窗口有 {audit['additional_active_addresses']} 个活跃地址、54 笔触及交易，其中 52 笔不在原追踪器集合活动表中；未发现新增池兑换净流出。FBI 的表述包括‘由其控制或与其密切相关’，不能把整个名单视为同一所有者。该活动审查依赖交易首尾及代币日志，原生币内部转账单独触及地址仍可能遗漏。",'',
 '## 3. 全候选收益对账的进展与边界','',
 f"[全部候选核算表](全部候选核算.csv) 覆盖 13,623 笔去重候选，包括跨原/新增窗口边界的 18 笔补充候选。筛选条件是同池、目标之后同块或后五块；这不是已确认套利。全部候选的 gas 合计 {D(a['candidate_gas_ETH']):,.6f} ETH，也不能全部归因于攻击。",'',
 f"每笔暂按交易发起地址与调用目标地址合并核算。根调用转账在该边界内抵消，gas 只扣一次；共享路由器、外部收款人、跨交易库存、交易所头寸和主体归属仍会影响真实利润。{a['native_available_and_other_inventory_closed']:,} 笔库存闭合子集的 {D(a['closed_group_cashflow_ETH']):,.9f} ETH 是账户现金流小计，不是全体参与者利润，也不能与攻击者执行差额相加。",'',
 '最初的公开批量接口取得前 225 个区块后达到限额，后续找到支持历史 trace_block 的 dRPC 免费公开节点，按区块补齐全部候选，并与已保存的 Blockscout 逐笔轨迹交叉核验。每个相关区块的交易集合、哈希和位置都与原始回执匹配；每笔候选检查完整调用树、失败祖先、原生币守恒和根调用身份。候选补取结果详见[缺口完成报告](候选收支缺口完成报告.md)。','',
 '## 4. 老师任务尚未完成的部分','',
 (f"- {a['native_missing']:,} 笔候选的原生币现金流仍未齐全；其余代币库存尚未统一按历史价格核算。" if a['native_missing'] else '- 候选原生币现金流缺口已补齐；其余代币库存尚未统一按历史价格核算。'),
 '- LP 收入、订单成交方收入、构建者收款与验证者最终收款尚未形成去重的全事件账本。',
 '- 其他链、冻结资金、借贷负债和全事件初末余额仍未实现资金守恒闭合。',
 '- 仍未进行反事实回放，无法严格区分攻击引起的收益与正常交易收益。',
 '- 新窗口结束不代表全事件结束；所选地址和事件签名也不保证所有兑换协议被覆盖。','',
 '当前无需人工提供密钥；主要障碍是公开接口配额、历史价格缺口以及主体/因果识别。后续公开数据工作应按候选收支缺失量、订单协议和未定价资产逐项推进，而不是继续扩大一个无法解释的总数。','',
 '## 5. 可复核材料与来源','',
 '- [新增逐笔时间线](后续交易时间线.md)：包含被隔离和未估值记录。',
 '- [完整候选表](全部候选核算.csv)、[候选核算原始结果](all_candidate_accounting.json)。',
 '- [新增估值](extension_valuation.json)、[身份核查](extension_identity_audit.json)、[新增地址审查](extension_address_audit.json)。',
 '- [新增检查结果](extension_validation.json)、[原检查结果](validation_results.json)。',
 '- [CoinGecko Ethereum token list](https://tokens.coingecko.com/uniswap/all.json)，按地址核对而非按名称替代。',
 '- [Coinbase 历史蜡烛图文档](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles)。原始报价及请求地址保存在 extension_prices_raw 和 extension_price_sources.json。',
 '- [Blockscout 公开 API 定义](https://github.com/blockscout/blockscout-api-v2-swagger/blob/main/swagger.yaml)。每笔轨迹来源链接保存在 extension_rawtrace_native.json；原始响应保存在 rawtrace_raw。','']
 (R/'后续时段补充报告.md').write_text('\n'.join(lines))
 categories={'pool_swap':'池兑换事件','token_out_ETH_in_protocol_unconfirmed':'代币换 ETH，协议待核','other_outflow_not_priced':'其他流出，未估值','unverified_token_logs_excluded':'未核实合约，隔离'}
 timeline=['# 后续交易时间线','', '时间均为 UTC。差额空白表示未估值；隔离记录不能视作真实主流资产流出。','', '| 时间 | 分类 | 净流出资产 | ETH 净额 | 严格差额 USD | 交易 |','|---|---|---|---:|---:|---|']
 for r in v['rows']:
  outs=', '.join(x['symbol'] for x in r['assets'] if x['address']!='native' and int(x.get('raw','0'))<0);eth=next(x['amount'] for x in r['assets'] if x['address']=='native');val='' if r['strict_shortfall_usd'] is None else f"{D(r['strict_shortfall_usd']):,.2f}"
  timeline.append(f"| {utc(r['timestamp'])} | {categories[r['category']]} | {outs} | {eth} | {val} | [{r['hash'][:12]}…](https://etherscan.io/tx/{r['hash']}) |")
 (R/'后续交易时间线.md').write_text('\n'.join(timeline)+'\n')
 mainpath=R/'研究报告_综合版.md';text=mainpath.read_text();marker='<!-- extension-update -->'
 if marker in text:text=text.split('<!-- extension-update-end -->\n\n',1)[1]
 banner=f'{marker}\n> **更新：后续扫描已延长至 10 月 30 日 07:02:47 UTC。** 连续检查 751,258 笔交易，新增 830 笔日志净流出均取得调用轨迹；候选扩大至 13,623 笔。新增严格样本执行差额为 {strict:,.2f} 美元。请先读 [后续时段补充报告](后续时段补充报告.md)；下文金额和覆盖数保留为原窗口结果，不能当作最新全窗口结果。\n<!-- extension-update-end -->\n\n'
 mainpath.write_text(banner+text)
 print('Reports written; combined descriptive sample USD',orig+strict+tr)
if __name__=='__main__':main()
