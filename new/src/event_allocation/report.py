"""Chinese research report, complete tables, reference-allocation graph and LP plots."""
import json,gzip,csv,html,base64
from collections import defaultdict,Counter
from decimal import Decimal
from pathlib import Path
from src.event_allocation.config import ROOT,OUT,REPORT,POLICY
from src.event_allocation.diagnostics import display_address

LABELS={
 'pool_trade_inventory':'LP / 协议池交易库存',
 'operating_address_incident_leg_reference_edge':'后续库存 / 套利交易操作地址',
 'known_order_operating_boundary_change':'订单 filler / resolver 操作边界',
 'block_recipient_receipts':'区块收款人（含 priority）',
 'protocol_fee_burn':'以太坊协议费用销毁',
 'protocol_resource_fee':'TRON 实付资源费',
 'wrapper_backing_reserve_change':'包装合约储备变化',
 'other_actual_address_signed_change':'其他实际地址有符号变化',
 'manager_settlement_or_hook_residual':'Manager / hook 结算余项',
 'pool_nontrade_principal_or_protocol_cash':'池非交易本金 / 协议现金',
 'lending_protocol_principal_adjusted':'借贷协议本金调整后变化',
 'token_supply_accounting_sink':'代币发行 / 销毁记账端',
 'liquidity_participant_cash_not_certified_profit':'流动性参与者现金变化',
}
SCOPES={'target':'已识别目标交易','after_prior_target':'目标后同池交易','before_first_target_control':'目标前对照','failed_attempt_after_target':'目标后实际调用目标池的失败','failed_attempt_before_target_control':'目标前调用目标池的失败对照','same_operator_failed_context_unassigned':'同操作者失败，事件归属未识别','same_block_failed_order_unassigned':'同块失败，先后顺序未识别','unrelated_manager_pool_control':'同 manager 的其他 PoolId 对照'}
def money(v):return f'${Decimal(v):,.2f}'
def millions(v):return f'{Decimal(v)/10**6:,.3f}'
def read(name):return json.loads((OUT/name).read_text())
def aggregate(rows):
    data=defaultdict(lambda:{'target':Decimal(0),'later':Decimal(0),'missing':0})
    for r in rows:
        if r['role']=='incident_wallet_reference_change':continue
        d=data[r['role']];d['later' if r['domain']=='subsequent_incident_pool_trade' else 'target']+=Decimal(r['priced_component_USD']);d['missing']+=r['unpriced_asset_rows']
    return [{'role':k,'label':LABELS.get(k,k),'target_USD':str(v['target']),'later_USD':str(v['later']),'total_priced_USD':str(v['target']+v['later']),'unpriced_asset_rows':v['missing']} for k,v in data.items()]

def figures(roles,lp,proposer):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch,FancyBboxPatch
    from matplotlib import font_manager
    for f in ['/System/Library/Fonts/PingFang.ttc','/System/Library/Fonts/STHeiti Medium.ttc']:
        if Path(f).exists():font_manager.fontManager.addfont(f);plt.rcParams['font.family']=font_manager.FontProperties(fname=f).get_name();break
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    major=[r for r in roles if abs(Decimal(r['total_priced_USD']))>1000 or r['role']=='token_supply_accounting_sink'];major.sort(key=lambda r:Decimal(r['total_priced_USD']),reverse=True)
    fig,ax=plt.subplots(figsize=(12,max(5,len(major)*.6)));y=list(range(len(major)));ax.barh([v-.19 for v in y],[float(Decimal(r['target_USD'])/10**6) for r in major],.32,label='目标交易中的初始变化',color='#9ab9cc');ax.barh([v+.19 for v in y],[float(Decimal(r['later_USD'])/10**6) for r in major],.32,label='后续关联交易中的再分配',color='#166674');ax.set_yticks(y,[r['label'] for r in major]);ax.invert_yaxis();ax.axvline(0,color='#677582',lw=.8);ax.set_xlabel('百万美元；已定价部分，有符号');ax.set_title('同一价格时钟下的两阶段分配',loc='left',fontweight='bold',pad=24);ax.legend(loc='lower right',frameon=False);fig.text(.02,.015,'同池关联活动仍含自然交易；图中金额不等于全事件因果 MEV 或企业历史成本利润。',fontsize=9,color='#52616b');fig.tight_layout(rect=(0,.04,1,1));fig.savefig(REPORT/'allocation_stages.png',dpi=170);fig.savefig(REPORT/'allocation_stages.svg');plt.close(fig)
    chains={}
    for chain in ['ethereum','tron']:
        rr=[r for r in lp if r['chain']==chain];chains[chain]={'trade':sum((Decimal(r['trade_time_priced_component_USD']) for r in rr),Decimal(0)),'terminal':sum((Decimal(r['terminal_inventory_mark']['priced_component_USD']) for r in rr),Decimal(0)),'missing':sum(r['trade_rows_with_missing_prices'] for r in rr)}
    fig,ax=plt.subplots(figsize=(9,5));xs=[0,1];ax.bar([x-.18 for x in xs],[float(chains[c]['trade']/10**6) for c in chains],.32,label='逐笔交易时价格',color='#166674');ax.bar([x+.18 for x in xs],[float(chains[c]['terminal']/10**6) for c in chains],.32,label='同一库存变动按窗口终点价',color='#db9861');ax.set_xticks(xs,['Ethereum','TRON']);ax.set_ylabel('百万美元；已定价部分');ax.axhline(0,color='#677582',lw=.8);ax.set_title('LP 交易价差与终点库存估值',loc='left',fontweight='bold');ax.legend(frameon=False);fig.text(.04,.02,'两列是同一组 swap 库存变化的不同估值，不能相加；不含初始全仓重估和个人 LP 份额。',fontsize=9,color='#52616b');fig.tight_layout(rect=(0,.07,1,1));fig.savefig(REPORT/'lp_valuation_comparison.png',dpi=170);fig.savefig(REPORT/'lp_valuation_comparison.svg');plt.close(fig)
    role={r['role']:r for r in roles};p0=Decimal(role['pool_trade_inventory']['target_USD']);p1=Decimal(role['pool_trade_inventory']['total_priced_USD']);op=Decimal(role['operating_address_incident_leg_reference_edge']['later_USD']);fees=sum((Decimal(role[k]['later_USD']) for k in ['block_recipient_receipts','protocol_fee_burn','protocol_resource_fee'] if k in role),Decimal(0));other=sum((Decimal(r['target_USD']) for r in roles if r['role']!='pool_trade_inventory'),Decimal(0));loss=p0+other;assert abs(p0-op-fees-p1)<Decimal('1e-35')
    nodes=[{'id':'incident_reference_loss','label':'事件钱包参考损失','value':str(loss)},{'id':'initial_pool','label':'目标交易中的池交易库存变化','value':str(p0)},{'id':'other_initial','label':'目标交易其他实际去向','value':str(other)},{'id':'later_operator','label':'后续库存 / 套利交易操作地址','value':str(op)},{'id':'later_block_protocol','label':'后续区块收款人及协议费用','value':str(fees)},{'id':'remaining_pool','label':'池交易库存：交易时价格净额','value':str(p1)}];edges=[(0,1,p0),(0,2,other),(1,3,op),(1,4,fees),(1,5,p1)];graph={'unit':'USD, priced component','nodes':nodes,'edges':[{'source':nodes[a]['id'],'target':nodes[b]['id'],'value_USD':str(v)} for a,b,v in edges],'meaning':'Reference-value allocation, not literal USD bank transfers and not proof that all later activity was caused by the incident. Unknown asset vectors remain in the complete ledger.','proposer_secondary_rule':'Actual proposer payouts are a separate block-connected redistribution, never extra primary extraction.'};(OUT/'allocation_graph.json').write_text(json.dumps(graph,indent=2));fig,ax=plt.subplots(figsize=(13,6));ax.set_xlim(-.7,3.6);ax.set_ylim(-1.6,1.6);ax.axis('off');pos={0:(0,0),1:(1.35,.65),2:(1.35,-.9),3:(2.85,1),4:(2.85,0),5:(2.85,-1)}
    for a,b,v in edges:
        x,y=pos[a];xx,yy=pos[b];arrow=FancyArrowPatch((x+.32,y),(xx-.42,yy),arrowstyle='-|>',mutation_scale=12,linewidth=max(1.2,float(abs(v)/loss)*12),alpha=.45,color='#267586',connectionstyle='arc3,rad=0');ax.add_patch(arrow)
    for i,node in enumerate(nodes):
        x,y=pos[i];ax.add_patch(FancyBboxPatch((x-.43,y-.25),.86,.5,boxstyle='round,pad=0.04',facecolor='#eaf1f4' if i else '#124b5b',edgecolor='#b7c9ce'));label=node['label'].replace('目标交易中的池交易库存变化','目标交易中\n池交易库存变化').replace('后续库存 / 套利交易操作地址','后续库存 / 套利\n交易操作地址').replace('后续区块收款人及协议费用','后续区块收款人\n及协议费用').replace('池交易库存：交易时价格净额','池交易库存\n交易时价格净额');ax.text(x,y+.07,label,ha='center',va='center',fontsize=10,color='white' if i==0 else '#183a45');ax.text(x,y-.14,millions(node['value'])+' 百万美元',ha='center',va='center',fontsize=10,fontweight='bold',color='white' if i==0 else '#183a45')
    ax.set_title('全事件参考价值分配图谱',loc='left',fontweight='bold',fontsize=17,pad=20);fig.text(.05,.055,'全块 proposer 付款单列为二次分配；不从这张图再增加一笔损失。\n金额为共同窗口的已定价部分；图谱不认证最终受益所有人或事件因果。',fontsize=10,color='#52616b');fig.tight_layout(rect=(0,.12,1,1));fig.savefig(REPORT/'event_allocation_graph.png',dpi=170);fig.savefig(REPORT/'event_allocation_graph.svg');plt.close(fig);return chains,graph

def run():
    summary=read('summary.json');rows=read('allocation_by_address.json');roles=aggregate(rows);lp=read('lp_inventory_valuations.json');prop=read('proposer_secondary_allocation.json');ops=read('all_operating_addresses_with_cost_sensitivity.json');controls=read('controls_and_costs.json');audit=read('validation.json');tron=read('tron_journal_summary.json');eth=read('ethereum_journal_summary.json');sensitivity=read('stable1_summary.json');cross=read('tron_market_policy_crosscheck.json');rights=read('nonfungible_position_rights_summary.json');assert audit['all_checks_passed'];chains,graph=figures(roles,lp,prop);(OUT/'allocation_by_role.json').write_text(json.dumps(roles,indent=2));fields=list(roles[0])
    with (REPORT/'allocation_by_role.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(roles)
    with (REPORT/'lp_inventory_valuations.csv').open('w') as f:
        fields=['chain','pool_key','transactions','trade_time_priced_component_USD','trade_rows_with_missing_prices','terminal_priced_component_USD','terminal_unpriced_raw','terminal_minus_trade_time_priced_component_USD'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in lp:w.writerow({k:r[k] for k in fields if k in r}|{'terminal_priced_component_USD':r['terminal_inventory_mark']['priced_component_USD'],'terminal_unpriced_raw':json.dumps(r['terminal_inventory_mark']['unpriced_raw'])})
    c=summary['counts'];loss=summary['incident_wallet_reference_loss_priced_component_USD'];maker_total=sum(summary['target_transactions_by_domain'].values());unpriced=c['incident_wallet_unpriced_transactions'];mdtable='| 角色 | 目标交易初始变化 | 后续关联再分配 | 合计（已定价部分） | 未定价资产行 |\n|---|---:|---:|---:|---:|\n'+'\n'.join('| '+r['label']+' | '+money(r['target_USD'])+' | '+money(r['later_USD'])+' | '+money(r['total_priced_USD'])+' | '+str(r['unpriced_asset_rows'])+' |' for r in roles)
    lptext='\n'.join(f"| {chain} | {money(v['trade'])} | {money(v['terminal'])} | {v['missing']} |" for chain,v in chains.items());ctrltext='\n'.join(f"| {r['chain']} | {SCOPES.get(r['association'],r['association'])} | {r['transactions']:,} | {money(r['fee_priced_component_USD'])} |" for r in controls)
    text=f'''# 全事件统一分配与真实收支核验

这次将库存型交易、代币承接、TRON、LP 和区块付款放入同一套可复算账表。共同窗口为 **2026-10-29 20:30:00 至 2026-10-30 07:00:00 UTC，左闭右开**。Ethereum 与 TRON 使用同一个时钟，纽约时间为 10 月 29 日 16:30 至次日 03:00。

主表的事件钱包参考损失已定价部分为 **{money(loss)}**，非事件钱包及协议的有符号分配已定价部分为 **{money(summary['nonhacker_allocation_priced_component_USD'])}**，对账差 **{summary['priced_component_conservation_residual_USD']} 美元**。{maker_total} 笔目标交易中，{c['fully_priced_incident_wallet_transactions']} 笔的事件钱包变化已完整定价，{unpriced} 笔仍带有明确列出的未定价原币向量。这个金额是已定价部分，不能当作未知代币价值等于零后的“完整真实损失”。

## 统一分配表

{mdtable}

正数表示获得的资产、仓位或参考价差，负数表示付出的资产或成本。代币发行/销毁端是记账端，不能叫获利钱包。包装合约、借贷协议和池的本金变化有各自角色。主表的“库存/套利交易操作地址”按支付 Gas 的地址归属，属于池交易参考价差；实际钱包收支另表列示，不能据此认定企业所有权。

![分配图谱](event_allocation_graph.png)

## 怎么算“赚了多少钱”

目标交易使用完整的实际地址账：原生币、ERC20、V4 底层币种 claim 与 manager 对应负债、已识别借贷本金变动、实付费用。原始整数逐资产守恒。WETH/ETH、WTRX/TRX 的包装背书做一次消重。Aave/JustLend 新增借款作为负债调整；最大 Comet resolver 使用已经验证的历史抵押和债务变化。其他未完整识别的借贷/仓位情形保留风险标识。

后续交易的主表取**已经被目标交易触及的同一池 / PoolId 的 swap 资产变化**，按交易时共同市场价计算。操作地址参考价差 = 该池向交易方交付的参考价值 − 本笔实际区块收款变化 − 协议费用。多个池或多个 swap 的同一笔交易只计一次费用。正收益、负收益和有证据的失败尝试均保留。其他池的对冲腿、借贷本金和 LP 充值不被偷偷并为本次事件产生的收入；这些实际变化保存在独立全地址总账。

因此，本表可回答“谁在事件池交易中捕获了多少参考价差、实际付了多少链上费用、资产实际记到什么地址”，同时提供实际 Gas 地址变化及未归属失败费用敏感性。它没有掌握全部历史库存取得成本、链下对冲、企业内全部账户、能源租赁付款或税费，不能把池卖出价差改称企业最终净利润。已有 **2,483 个真实闭合正收益套利单元、244.618801770585241269 ETH 净留存**作为结构证据保留；它们会与本表交易重合，禁止再次相加。

## MEV 的明确判据

1. **已闭合多池套利**：实际存在不同池的路线，资产流及底层币种闭合，在已识别操作边界扣除真实链上成本后仍有正盈余。Gas 高低不是这个判据。
2. **库存型参考价差**：在偏离市场价的事件池卖出库存或承接代币，逐笔按共同市场价估值。它证明成交价差，单凭这一点不能证明历史成本利润或因果 MEV。
3. **排序竞价付款**：真实 priority 或真实转账 / claim 支付给区块收款人。付款本身不证明夹子或抢跑。
4. **事件相关性**：同一经过身份核验的池 / PoolId，发生在其首笔目标交易之后。目标之前为对照；同一交易里的其他池是执行背景。
5. **因果增量**：只接受历史状态重放里指定删除/重排方案的可执行比较，并保留失败及不变结果。已有逐块重放结果属于单独证据层，不能把所有同池交易或全块付款都宣布为本次事件造成。

## LP：交易时价格与终点库存要分开

| 链 | 逐笔交易时估值 | 同一 swap 库存变化按 07:00 终点价 | 交易时有价格缺口的池记录数 |
|---|---:|---:|---:|
{lptext}

![LP 估值比较](lp_valuation_comparison.png)

终点列取相同 swap 原币向量，以窗口结束时已经完成的一分钟行情重估。它衡量交易导致的库存变化相对于保留相同初始币种的差额；不把初始全部资产的市场涨跌归给黑客，不包含无法确认的个人 LP 份额，也不把 LP 领取本金再加作利润。LP 与协议收费的归属在未取得 fee-growth/份额证据时保持合并。两种估值不能相加。

## 区块与 proposer：付款确认和事件归属是两件事

共同窗口内，**{prop['summary']['matched_blocks_in_common_window']:,} 个区块、{prop['summary']['actual_payment_trace_rows']:,} 条实际付款 trace** 已核对，proposer 全块实际收到 **{prop['summary']['observed_whole_block_proposer_payments_ETH']} ETH**。逐块 trace 金额与归档 relay 付款一致。

这些付款列入二次分配表，主表追加提取额为 **0**。主表先计关联交易付给区块收款人的实际变化；builder 随后转给 proposer 的同一笔价值再加一次会重复。全块还包含其他交易、原有余额和其他资金来源，因此 proposer 款的事件份额列为“未识别”，不是观测值 0；逐块给出 0 至该块实际付款的识别范围。没有使用任意比例把整块付款归给本次事件，也没有把“匹配到了 relay”当作因果证明。

## 价格口径、Bitquery 对照与价格缺口

主口径对所有正负项使用同一资产、同一交易分钟的**上一完整分钟收盘价**。币种映射按合约身份与小数位核验；优先使用 Coinbase 独立现货，补充经过同一合约映射的 Binance 现货，并用真实 USDT/USD 换算。完成分钟缺口最多回取 5 分钟。精确合约的 DefiLlama 二级报价最多陈旧 600 秒，逐项标注可能依赖池价，不能将 confidence 值解释为独立公允价证明。无合格报价保留原币及空白金额。

独立的 USDT/USDC/DAI = 1 美元敏感性仍保持同一前一分钟时钟；其事件钱包参考损失已定价部分为 **{money(sensitivity['incident_wallet_reference_loss_priced_component_USD'])}**。主账与敏感性账不混用。

[Bitquery 原研究](https://bitquery.io/investigations/binance-hack-who-profited)报告约 1.19 亿美元参考损失、交易者约 5,990 万、builder/validator 约 2,950 万、LP 约 2,020 万及订单方约 670 万美元。它采用同分钟 Hyperliquid、稳定币按 1 美元、不同链/交易类型的截止时刻，且卖出腿价差未包含其他场所的库存买入成本。我们的主表覆盖共同截止 07:00 的有符号交易，用独立现货及实际稳定币汇率，保留了自然交易和成本对照；两套总额不能直接解释为复现误差或真实因果差异。

TRON 已另做可复算市场敏感性：取得 {cross['available_15m_bars']} 根 Hyperliquid 15 分钟历史行情；窗口内开盘 {cross['actual_first_open']}、最高 {cross['highest_15m_high']}、末根收盘 {cross['actual_last_15m_close']}。这能交叉检查价格路径。公开接口没有提供对应的一分钟历史，15 分钟上一完整柱及当前柱收盘敏感性均单列，后一种明确含回看偏差，不冒称 Bitquery 一分钟精确复现。

## 覆盖、失败成本及独立核验

实际总账 **{c['actual_transactions']:,} 笔唯一交易、{c['actual_entries']:,} 条资产/仓位变化**；主分配预算 **{c['primary_transactions']:,} 笔**、**{summary['pool_trade_legs']:,} 个唯一池日志键**。Ethereum 在共同窗口扫描 {eth['blocks']:,} 个归档区块；TRON 目标池索引 9,946 笔交易、11,430 条事件全部与完整回执核对，V4 manager 的其他 PoolId 已单独列为对照。TRON 的 {tron['history_crosscheck']['pool_transactions_history_root_value_owner_time_fee_match']:,} 笔池交易全部完成 owner、root call value、区块、时间和实付费用的历史交叉检查；全部 {tron['history_crosscheck']['failed_transactions']:,} 笔操作者失败交易取得真实回执费用。

| 链 | 范围类别 | 唯一交易数 | 本类实付费用的已定价部分 |
|---|---|---:|---:|
{ctrltext}

同操作者但未证明触及事件池的失败费用列为成本敏感性，不强制放进主预算；主预算已经计入的失败费用不会再扣。ERC721/1155 仓位权利另外保存 **{rights['unique_position_right_movements']:,} 条**有原始证据的变动，不任意赋予 NFT 价格或重复计入底层 LP 现金。

导出的实际账与分配账均重新流式检查唯一键、逐交易原币整数守恒、共同报价、空白缺失值、区块付款去重和证据文件哈希。对账证明所列账目及估值一致；哈希和会计恒等式本身不证明公允价格、受益所有权或事件因果。

## 文件与复现

- [完整逐交易统一分配 CSV.gz](unified_allocation.csv.gz)
- [完整实际地址资产/仓位变化 CSV.gz](actual_address_changes.csv.gz)
- [全部操作地址、实际钱包变化及成本敏感性 CSV](all_operating_addresses.csv)
- [LP 逐池双估值 CSV](lp_inventory_valuations.csv)
- [proposer 二次分配 CSV](proposer_secondary_allocation.csv) 与 [实际付款 trace CSV](proposer_payment_traces.csv)
- [NFT 仓位权利 CSV.gz](nonfungible_position_rights.csv.gz)
- [独立核验结果](validation.json)

项目根目录运行 `PYTHONPATH=new python -m src.event_allocation.reproduce`。默认用本地已归档证据重算账表、敏感性、核验及图表；采集原始数据和重建原币账分别使用 CLI 的显式阶段。价格原始来源、费用回执和证据 SHA-256 保存在 `new/data/processed/event_allocation/` 的源文件索引与清单中。
'''
    settlements=read('whole_block_native_settlements.json');ss=settlements['summary'];combined=read('combined_ledger_summary.json');top_receivers=settlements['actual_outgoing_recipients'][:10]
    text=text.replace('## 统一分配表','目标集合采用项目归档的钱包、直接资金关联、订单及已识别 swap 清单；资金关联不等于同一受益所有人认证。Bitquery 未公开完整逐笔全集，本项目没有声称已对齐它的全部交易清单。所有“完整”均指上述明确集合及共同窗口。\n\n## 统一分配表',1)
    second='''## 全块实际结算层与同一张分阶段总表

完整总表：[主分配与实际结算统一总表 CSV.gz](all_stages_allocation.csv.gz)。`stage` 区分有符号参考价值分配和真实转账，二次结算的 `primary_additive_USD` 一律为 0；同一笔价值经过中介时保留每条真实转账，但不把这些转账累加为事件损失。

在共同窗口的全部 **{blocks:,}** 个区块，另外重建了 **{flows:,}** 条区块收款人 / proposer 付款交易相关的实际原生 ETH 转账，逐块与原始资金流及已匹配的 proposer 金额核对。区块收款人向已知交易操作地址或操作边界、且发生在主预算交易之外的实际付款为 **{extra}**；地址对应关系保留，不把这些款自动解释为事件退款。

全块区块收款人的原生币执行余额变动代理为 **{proxy} ETH**。它覆盖同期全部交易，且不等于企业最终利润；ERC20 仓位、其他资金来源、共识提取和链外账户另外存在。主表的“区块收款人”是接收环节，后续真实转出在此结算层逐笔列示。

| 区块收款人实际转出接收方 | 实收 ETH | 转账条数 |
|---|---:|---:|
{receivers}

这些接收方含 relay / 支付中介，不据此认定最终受益所有人。全量数据见 [全块原生币转账 CSV.gz](whole_block_native_settlements.csv.gz)。全部主预算与对照交易的真实地址变化另见 [实际地址汇总 CSV](actual_all_counterparties.csv)，该表与事件池参考价差分别核对，避免把库存交易的价格优势当作 Gas 钱包实际已收到的现金。

'''.format(blocks=ss['common_window_blocks'],flows=ss['native_transfer_rows'],extra=money(ss['observed_block_recipient_payments_to_known_operating_addresses_or_boundaries_outside_primary_USD']),proxy=ss['whole_block_execution_native_balance_change_proxy_ETH'],receivers='\n'.join('| '+r['recipient']+' | '+r['actual_received_ETH']+' | '+str(r['transfer_rows'])+' |' for r in top_receivers))
    text=text.replace('## 覆盖、失败成本及独立核验',second+'## 覆盖、失败成本及独立核验')
    text=text.replace('它衡量交易导致的库存变化相对于保留相同初始币种的差额；','在保持非交易本金流不变的假设下，它衡量 swap 库存变化相对保留相同初始币种的差额；')
    enc=read('tron_encoding_summary.json');text=text.replace('## 文件与复现',f"交易索引另列 [全部唯一交易 CSV.gz](transaction_index.csv.gz)：无原币扣费、也无已观测可替代资产/已识别本金变化的交易仍完整列入索引，不制造占位资产或虚构价格。TRON 的 Energy / Bandwidth 使用不自动等于原币付款，外部资源租赁费未获得证据时不估算为已知零成本。\n\n与本账有关的 **{enc['relevant_pool_and_failed_transactions']:,} 笔 TRON 池交易及失败费用交易**均取得与 txID 相符的原始或恢复编码哈希。分页 API 可能省略 Any 载荷里显式零字段：恢复只补语义不变的零字段，并必须精确 SHA-256 匹配 txID；少数记录使用单独归档的 solidified node 交易体。原始响应保留，证明方法分开标注。全部历史中的其他非财务上下文交易不被笼统宣称为已认证签名原件。\n\n跨池套利可以发生在同一 DEX；跨 DEX 是另一种路线。池手续费已经反映在实际 swap 数量中，不按费率再扣一次。Gas 与真实区块付款是成本和竞价证据，单独加 Gas 不能决定 MEV 标签。\n\n## 文件与复现")
    tron_lp='| TRON 池 / PoolId | 交易时价格净额 | 终点价库存变化 |\n|---|---:|---:|\n'+'\n'.join('| '+display_address('tron',r['pool_key'].split(':')[0])+(' / '+r['pool_key'].split(':')[1] if ':' in r['pool_key'] else '')+' | '+money(r['trade_time_priced_component_USD'])+' | '+money(r['terminal_inventory_mark']['priced_component_USD'])+' |' for r in lp if r['chain']=='tron')
    text=text.replace('## 区块与 proposer：', 'TRON 三个池的结果分开列示，比较主池与多池总额时应先对齐池集合、窗口和报价：\n\n'+tron_lp+'\n\n## 区块与 proposer：')
    if unpriced==0:text=text.replace(f'{maker_total} 笔目标交易中，{c["fully_priced_incident_wallet_transactions"]} 笔的事件钱包变化已完整定价，0 笔仍带有明确列出的未定价原币向量。',f'{maker_total} 笔目标交易的事件钱包原币变化均已获得合约匹配历史报价。对手方未定价凭证仍按原币逐项保留。')
    if unpriced==0:text=text.replace('这个金额是已定价部分，不能当作未知代币价值等于零后的“完整真实损失”。','本范围的目标交易参考损失已经按所列报价算出；参与者分类中尚未定价的凭证不以零值当作确定利润，市场参考损失也不被解释为全事件因果 MEV。')
    (REPORT/'全事件统一分配报告.md').write_text(text)
    def tr(r):return '<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in [r['label'],money(r['target_USD']),money(r['later_USD']),money(r['total_priced_USD']),r['unpriced_asset_rows']])+'</tr>'
    compact_ops=[[r['chain'],r['operating_address_display'],r['transactions'],r['net_priced_USD'],r['actual_gas_owner_only_marked_change_in_audited_transactions_USD'],r['unassigned_failed_cost_priced_USD'],r['broad_cost_sensitivity_incident_leg_net_priced_USD'],r['unpriced_transactions'],r['operating_address']] for r in ops];compact_ops.sort(key=lambda r:Decimal(r[3]),reverse=True)
    compact_actual=[[r['chain'],r['actual_address_display'],r['scope'],r['priced_asset_and_known_position_change_USD'],r['unpriced_asset_rows'],r['position_risk_rows'],r['actual_address']] for r in read('actual_all_counterparties.json')]
    txrows=[]
    with gzip.open(OUT/'transaction_valuations.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);net=r['incident_leg_after_observed_cost'];txrows.append([r['chain'],r['tx_hash'],r['block'],r['timestamp'],display_address(r['chain'],r['sender']),r['association'],net['priced_component_USD'],len(r['unpriced_assets']),r['domain'],r['incident_wallet_change']['priced_component_USD'],r['sender']])
    paragraphs=[]
    for part in text.split('\n\n'):
        if part.startswith('#') or part.startswith('|') or part.startswith('![') or part.startswith('- ') or part.startswith('1. '):continue
        paragraphs.append('<p>'+html.escape(part).replace('**','')+'</p>')
    table='<table><thead><tr><th>角色</th><th>目标交易初始变化</th><th>后续关联再分配</th><th>合计：已定价部分</th><th>未定价资产行</th></tr></thead><tbody>'+''.join(tr(r) for r in roles)+'</tbody></table>'
    page='''<!doctype html><html lang="zh-CN"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>全事件统一分配核验</title><style>
body{margin:0;background:#f4f6f8;color:#20323d;font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1240px;margin:auto;padding:32px 28px 70px}h1{font-size:34px;line-height:1.3;margin:12px 0}h2{font-size:23px;margin-top:36px}a{color:#096d84}small,.muted{color:#566873}.eyebrow{letter-spacing:2px;color:#267586;font-size:12px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card,section{background:white;padding:22px;border-radius:12px;margin-top:18px;border:1px solid #dde5e9}.card strong{display:block;font-size:28px;color:#124b5b}.note{padding:12px 16px;background:#fff4e3;border-left:4px solid #d69349;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:right;padding:10px;border-bottom:1px solid #e2e8ed}th:first-child,td:first-child{text-align:left}th{background:#eef4f6}td.address{font:11px ui-monospace,monospace;word-break:break-all;max-width:360px;text-align:left}.scroll{overflow-x:auto}input,select,button{font:inherit;padding:8px 12px;border:1px solid #bacbd3;border-radius:6px;background:white}input{width:min(460px,90%)}button{cursor:pointer;margin:6px}figure{margin:15px 0}img{max-width:100%;height:auto}details{margin-top:24px}summary{cursor:pointer;font-weight:600}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.badge{display:inline-block;border-radius:4px;background:#e6f1ef;padding:3px 8px}.downloads a{display:inline-block;margin:5px 16px 5px 0}@media(max-width:750px){main{padding:20px 12px}.cards{grid-template-columns:1fr}h1{font-size:27px}.card,section{padding:15px}table{min-width:680px}}
</style><main><div class="eyebrow">FT565 · ETHEREUM + TRON · 统一价格与去重分配</div><h1>这次事件的价值，分配到了哪里</h1><p>共同窗口：2026-10-29 20:30 — 2026-10-30 07:00 UTC（纽约 16:30 — 次日 03:00）</p>
<div class="cards"><div class="card">事件钱包参考损失 · 已定价部分<strong>__LOSS__</strong></div><div class="card">实际账唯一交易<strong>__TXCOUNT__</strong></div><div class="card">独立核验<strong>逐笔原币守恒 · 通过</strong></div></div>
<div class="note">这是有符号参考价值分配账。未知价格保留原币及空白金额；同池关联活动仍可能包含自然交易。池卖出参考价差、实际钱包变化、闭合套利留存和因果 MEV 各自列示。</div>
<section><h2>全事件分配图谱</h2><img src="event_allocation_graph.png" alt="两阶段参考价值分配图谱"><div class="scroll">__ROLETABLE__</div><p class="muted">原币 / 仓位总账与事件池参考价差预算可独立下载。proposer 全块付款放在二次分配表，主分配不再追加。</p></section>
<section><h2>全部操作地址：参考价差与实际钱包变化</h2><p>按支付 Gas 的地址归属，不宣称共同受益所有权。金额只含已定价部分；最后一列列出存在未定价资产的交易数。</p><div class="toolbar"><input id="addressFilter" placeholder="搜索 Ethereum / TRON 地址"><select id="chainFilter"><option value="">全部链</option><option value="ethereum">Ethereum</option><option value="tron">TRON</option></select><span id="opCount"></span></div><div class="scroll"><table><thead><tr><th>链</th><th>Gas 操作地址</th><th>主预算交易数</th><th>事件池参考净价差</th><th>Gas 地址实际变化</th><th>未归属失败费用</th><th>成本敏感性净额</th><th>未定价交易</th></tr></thead><tbody id="operators"></tbody></table></div><button id="prevOp">上一页</button><button id="nextOp">下一页</button></section>
<section><h2>逐交易核对入口</h2><p>按完整哈希或地址搜索，跳转区块浏览器查看转账、日志和内部调用。目标交易的最后一列是事件钱包实际参考变化；后续交易价差另列。</p><input id="txFilter" placeholder="输入交易哈希或 Gas 地址"><span id="txCount"></span><div class="scroll"><table><thead><tr><th>链</th><th>交易 / 浏览器</th><th>区块</th><th>范围类别</th><th>后续池参考净价差</th><th>未定价资产数</th><th>事件钱包参考变化</th></tr></thead><tbody id="transactions"></tbody></table></div><button id="prevTx">上一页</button><button id="nextTx">下一页</button></section>
<section><h2>LP 库存估值</h2><img src="lp_valuation_comparison.png" alt="同一池交易库存按交易时与终点价估值"><p>两种估值不能相加；终点列不计初始全仓市场重估，不是个人 LP 的总财富或独立 fee-only 收入。</p></section>
<section><h2>两阶段与负收益</h2><img src="allocation_stages.png" alt="目标初始分配及后续有符号再分配"></section>
<section class="downloads"><h2>完整证据与复现</h2><a href="全事件统一分配报告.md">中文研究正文</a><a href="unified_allocation.csv.gz">完整统一分配 CSV.gz</a><a href="actual_address_changes.csv.gz">实际地址账 CSV.gz</a><a href="all_operating_addresses.csv">全部操作地址及成本</a><a href="lp_inventory_valuations.csv">逐池 LP 双估值</a><a href="proposer_secondary_allocation.csv">proposer 二次分配</a><a href="proposer_payment_traces.csv">实际付款 trace</a><a href="nonfungible_position_rights.csv.gz">NFT 仓位权利</a><a href="validation.json">独立核验结果</a><details><summary>计算口径与研究叙述</summary>__PARAGRAPHS__</details></section></main>
<script>
const OPS=__OPS__,TXS=__TXS__;let opPage=0,txPage=0;const size=30,$=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),usd=s=>Number(s).toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
function renderOps(){const term=$('#addressFilter').value.trim().toLowerCase(),chain=$('#chainFilter').value,rows=OPS.filter(r=>(!chain||r[0]===chain)&&(!term||r[1].toLowerCase().includes(term)));opPage=Math.min(opPage,Math.max(0,Math.ceil(rows.length/size)-1));$('#opCount').textContent=rows.length+' 个地址 · 第 '+(opPage+1)+' 页';$('#operators').innerHTML=rows.slice(opPage*size,(opPage+1)*size).map(r=>'<tr><td>'+esc(r[0])+'</td><td class="address">'+esc(r[1])+'</td><td>'+r[2]+'</td>'+[3,4,5,6].map(i=>'<td>'+usd(r[i])+'</td>').join('')+'<td>'+r[7]+'</td></tr>').join('');}
function renderTx(){const term=$('#txFilter').value.trim().toLowerCase(),rows=TXS.filter(r=>!term||r[1].toLowerCase().includes(term)||r[4].toLowerCase().includes(term));txPage=Math.min(txPage,Math.max(0,Math.ceil(rows.length/size)-1));$('#txCount').textContent=' '+rows.length+' 笔 · 第 '+(txPage+1)+' 页';$('#transactions').innerHTML=rows.slice(txPage*size,(txPage+1)*size).map(r=>{const url=r[0]==='ethereum'?'https://etherscan.io/tx/'+r[1]:'https://tronscan.org/#/transaction/'+r[1];return '<tr><td>'+esc(r[0])+'</td><td class="address"><a target="_blank" rel="noopener" href="'+url+'">'+esc(r[1])+'</a></td><td>'+r[2]+'</td><td>'+esc(r[5])+'</td><td>'+usd(r[6])+'</td><td>'+r[7]+'</td><td>'+usd(r[9])+'</td></tr>'}).join('');}
$('#addressFilter').oninput=()=>{opPage=0;renderOps()};$('#chainFilter').onchange=()=>{opPage=0;renderOps()};$('#txFilter').oninput=()=>{txPage=0;renderTx()};$('#prevOp').onclick=()=>{opPage=Math.max(0,opPage-1);renderOps()};$('#nextOp').onclick=()=>{opPage++;renderOps()};$('#prevTx').onclick=()=>{txPage=Math.max(0,txPage-1);renderTx()};$('#nextTx').onclick=()=>{txPage++;renderTx()};renderOps();renderTx();
</script></html>'''
    actual_section='''<section><h2>全部实际收支地址</h2><p>这是完整交易路线中实际地址的资产及已识别仓位变化，按交易时价格相加；与事件池参考价差预算分别核对。零地址发行记账、包装储备、协议地址和负变化均保留。带价格缺口或仓位风险的数值不能解释为完整净利润。</p><input id="actualFilter" placeholder="搜索实际收支地址"><select id="actualScope"><option value="primary_transaction_full_execution_context">主预算交易的完整路线</option><option value="control_or_unassigned_context">对照 / 未归属活动</option><option value="">全部范围</option></select><span id="actualCount"></span><div class="scroll"><table><thead><tr><th>链</th><th>实际地址</th><th>已定价资产 / 仓位变化</th><th>未定价资产行</th><th>仓位风险资产行</th></tr></thead><tbody id="actualAddresses"></tbody></table></div><button id="prevActual">上一页</button><button id="nextActual">下一页</button><a href="actual_all_counterparties.csv">下载全部实际地址</a></section>'''
    page=page.replace('<section><h2>逐交易核对入口</h2>',actual_section+'<section><h2>主预算逐交易核对入口</h2>')
    page=page.replace('const OPS=__OPS__,TXS=__TXS__;let opPage=0,txPage=0;', 'const OPS=__OPS__,TXS=__TXS__,ACTUAL=__ACTUAL__,SCOPES=__SCOPES__;let opPage=0,txPage=0,actualPage=0;')
    page=page.replace("r[1].toLowerCase().includes(term)))","(r[1].toLowerCase().includes(term)||r[8].toLowerCase().includes(term))))")
    page=page.replace("r[4].toLowerCase().includes(term));txPage", "r[4].toLowerCase().includes(term)||r[10].toLowerCase().includes(term));txPage")
    page=page.replace("esc(r[5])+'</td><td>'", "esc(SCOPES[r[5]]||r[5])+'</td><td>'")
    actual_js="""function renderActual(){const term=$('#actualFilter').value.trim().toLowerCase(),scope=$('#actualScope').value,rows=ACTUAL.filter(r=>(!scope||r[2]===scope)&&(!term||r[1].toLowerCase().includes(term)||r[6].toLowerCase().includes(term)));actualPage=Math.min(actualPage,Math.max(0,Math.ceil(rows.length/size)-1));$('#actualCount').textContent=' '+rows.length+' 个实际地址记录 · 第 '+(actualPage+1)+' 页';$('#actualAddresses').innerHTML=rows.slice(actualPage*size,(actualPage+1)*size).map(r=>'<tr><td>'+esc(r[0])+'</td><td class="address">'+esc(r[1])+'</td><td>'+usd(r[3])+'</td><td>'+r[4]+'</td><td>'+r[5]+'</td></tr>').join('');}
$('#actualFilter').oninput=()=>{actualPage=0;renderActual()};$('#actualScope').onchange=()=>{actualPage=0;renderActual()};$('#prevActual').onclick=()=>{actualPage=Math.max(0,actualPage-1);renderActual()};$('#nextActual').onclick=()=>{actualPage++;renderActual()};renderActual();"""
    page=page.replace('</script>',actual_js+'</script>')
    mev_section='<section><h2>MEV 按什么标准判断</h2><p><b>多池闭合套利：</b>真实不同池路线、资产闭合，扣除已识别链上成本后为正。<b>库存卖出：</b>报告市场参考价差，历史买入成本及其他场所对冲另列。<b>竞价付款：</b>真实 priority 或区块收款转账证明付款，不能单凭高 Gas 认定 MEV。<b>同池关联：</b>目标后同池活动保留为关联。<b>因果影响：</b>仅引用历史状态重放验证的具体删除 / 重排实验，不扩张到全事件。</p></section>'
    proposer_section=f'<section><h2>区块付款的二次分配</h2><p>共同窗口 {prop["summary"]["total_common_window_blocks"]:,} 个区块全部列入二次分配表；其中 {prop["summary"]["matched_blocks_in_common_window"]:,} 个区块的 proposer 付款与 relay 和实际 trace 对上，合计 {prop["summary"]["observed_whole_block_proposer_payments_ETH"]} ETH。其余 {prop["summary"]["blocks_without_matched_delivered_relay_record"]:,} 个区块保留实际区块收款及原生币流，不虚构 relay 成交或零付款。全块付款的事件份额未识别，主表追加金额为 0。</p><a href="proposer_secondary_allocation.csv">完整逐块表</a> · <a href="proposer_payment_traces.csv">已核对付款 trace</a></section>'
    page=page.replace('<section class="downloads">',mev_section+proposer_section+'<section class="downloads">')
    page=page.replace('<h2>完整证据与复现</h2>','<h2>完整证据与复现</h2><a href="all_stages_allocation.csv.gz">主分配与实际结算统一总表</a><a href="transaction_index.csv.gz">全部唯一交易索引（含零原币付款）</a><a href="whole_block_native_settlements.csv.gz">全块实际结算转账</a><a href="actual_all_counterparties.csv">全部实际收支地址</a>')
    if unpriced==0:page=page.replace('事件钱包参考损失 · 已定价部分','本范围事件钱包参考损失')
    page=page.replace('<img src="event_allocation_graph.png" alt="两阶段参考价值分配图谱">','<a href="event_allocation_graph.png" target="_blank"><img src="event_allocation_graph.png" alt="两阶段参考价值分配图谱；点击打开高清图"></a>')
    for key,value in {'LOSS':money(loss),'TXCOUNT':f"{c['actual_transactions']:,}",'ROLETABLE':table,'PARAGRAPHS':'\n'.join(paragraphs),'OPS':json.dumps(compact_ops,separators=(',',':')),'TXS':json.dumps(txrows,separators=(',',':')),'ACTUAL':json.dumps(compact_actual,separators=(',',':')),'SCOPES':json.dumps(SCOPES,ensure_ascii=False)}.items():page=page.replace('__'+key+'__',value)
    (REPORT/'全事件统一分配核验.html').write_text(page);(REPORT/'README.md').write_text('# 全事件统一分配\n\n优先打开 [交互核对报告](全事件统一分配核验.html) 或 [中文研究正文](全事件统一分配报告.md)。\n\n图谱、全部 CSV、原币/仓位账、价格敏感性和核验均已由同一管线生成。HTML 可离线直接打开。\n');print(json.dumps({'report':str(REPORT/'全事件统一分配报告.md'),'html_bytes':len(page.encode()),'operating_addresses':len(compact_ops),'transaction_rows':len(txrows),'figures':3},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
