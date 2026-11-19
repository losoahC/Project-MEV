"""Plot ETH/WETH cycle surplus partition and actual fee-recipient addresses.
This is an accounting diagram, not invented hacker-to-bot fund tracing.
"""
import json
from collections import defaultdict
from decimal import Decimal,getcontext
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotly.offline import plot
import plotly.graph_objects as go
from src.arbitrage.discover import ROOT
getcontext().prec=90
E=Decimal(10)**18

def run():
    p=ROOT/'data/processed/mev_full_window';out=ROOT/'reports/mev_expansion';cycles=[r for r in json.loads((p/'strategy_accounts_v4.json').read_text()) if r['status']=='verified_cashflow_and_pool_closed_positive_cycle'];txmap={h:r for r in cycles for h in r['included_transactions']};assert len(txmap)==sum(len(r['included_transactions']) for r in cycles);fee={};priority={};refund=[]
    with (p/'all_sender_accounting.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['tx_hash'] in txmap:
                fee[r['tx_hash']]=r['fee_recipient'];priority[r['tx_hash']]=Decimal(r['priority_fee_wei'])/E
                if r['fee_recipient'] in txmap[r['tx_hash']]['boundary']:refund.append(r['tx_hash'])
    if refund:raise ValueError('Handle own fee-recipient priority refunds explicitly before plotting: '+str(refund))
    totals={k:sum((Decimal(r[field]) for r in cycles),Decimal(0)) for k,field in [('gross','gross_before_gas_direct_fee_recipient_ETH'),('burn','burn_ETH'),('priority','priority_ETH'),('direct','direct_fee_recipient_ETH'),('indirect','indirect_fee_recipient_ETH'),('retained','net_joint_boundary_ETH')]};assert totals['gross']==sum(totals[k] for k in ['burn','priority','direct','indirect','retained'])
    recipients=defaultdict(lambda:{'priority':Decimal(0),'direct':Decimal(0),'indirect':Decimal(0)});senders=defaultdict(lambda:{'units':0,'net_ETH':Decimal(0),'executors':set()})
    for r in cycles:
        a=senders[r['sender']];a['units']+=1;a['net_ETH']+=Decimal(r['net_joint_boundary_ETH']);a['executors'].update(set(r['boundary'])-{r['sender']})
        for h in r['included_transactions']:recipients[fee[h]]['priority']+=priority[h]
        for f in r['external_payouts']:
            if f['asset_kind']=='native' and f['recipient']==fee[f['tx_hash']]:recipients[f['recipient']]['direct']+=Decimal(f['amount_raw'])/E
        for f in r.get('indirect_fee_paths',[]):recipients[f['fee_recipient']]['indirect']+=Decimal(f['amount_wei'])/E
    assert sum(a['indirect'] for a in recipients.values())==totals['indirect']
    assert sum(a['priority'] for a in recipients.values())==totals['priority'];assert sum(a['direct'] for a in recipients.values())==totals['direct']
    rrows=[{'address':a,'priority_ETH':str(v['priority']),'direct_native_ETH':str(v['direct']),'indirect_or_WETH_ETH':str(v['indirect']),'total_ETH':str(v['priority']+v['direct']+v['indirect']),'role':'Block fee recipient; neither builder brand nor final proposer inferred.'} for a,v in recipients.items()];rrows.sort(key=lambda r:Decimal(r['total_ETH']),reverse=True)
    srows=[{'sender':a,'units':v['units'],'joint_boundary_net_ETH':str(v['net_ETH']),'execution_addresses':sorted(v['executors']),'role':'Operational sender and execution addresses, not final beneficial-owner attribution.'} for a,v in senders.items()];srows.sort(key=lambda r:Decimal(r['joint_boundary_net_ETH']),reverse=True)
    record={'covered_units':len(cycles),'totals_ETH':{k:str(v) for k,v in totals.items()},'fee_recipients':rrows,'operational_senders':srows,'unit_ids':[r['unit_id'] for r in cycles],'scope_note':'Disjoint fully bridged single ETH/WETH-surplus cycles only. Includes gas, direct native and authenticated WETH/unwrap fee-recipient payments once; does not include open inventories or all incident MEV. Subsequent proposer payments must not be added again.'};(p/'covered_surplus_distribution.json').write_text(json.dumps(record,indent=2))
    labels=['Base-fee burn','Priority fees','Direct native fee-recipient payments','WETH / unwrap-helper payments','Retained in operating addresses'];colors=['#9AA9BC','#E2A34B','#227C9D','#8759B5','#17988A'];vals=[totals[k] for k in ['burn','priority','direct','indirect','retained']]
    fig,ax=plt.subplots(figsize=(14,6));left=0
    for label,color,v in zip(labels,colors,vals):
        ax.barh(0,float(v),left=left,height=.4,color=color,label=f'{label}: {v:,.6f} ETH')
        if float(v)/float(totals['gross'])>.07:ax.text(left+float(v)/2,0,f'{v:,.2f} ETH',ha='center',va='center',color='white',fontsize=13,fontweight='bold')
        left+=float(v)
    ax.set_xlim(0,float(totals['gross'])*1.02);ax.set_ylim(-.9,.9);ax.set_yticks([]);ax.set_xlabel('ETH / WETH accounting units');ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);fig.suptitle('Where the verified cycle surplus went',x=.08,ha='left',fontsize=23,fontweight='bold');ax.set_title(f"{len(cycles):,} disjoint covered cycle units | Gross surplus {totals['gross']:,.6f} ETH",loc='left',fontsize=12,pad=20);fig.legend(*ax.get_legend_handles_labels(),loc='lower left',bbox_to_anchor=(.08,.10),frameon=False,ncol=2,fontsize=10);fig.text(.08,.015,'Source: original receipts, native traces and poolId-verified V4 events. Covered-cycle accounting, not whole-event MEV or causal hacker loss.\nBurn is not a wallet receipt. Fee recipients are actual block addresses; their later proposer payouts are a separate distribution layer.',fontsize=10,color='#526377');fig.subplots_adjust(left=.08,right=.98,top=.77,bottom=.38)
    for ext in ['png','svg']:fig.savefig(out/f'covered_surplus_distribution.{ext}',dpi=160)
    plt.close(fig)
    fig=go.Figure(go.Sankey(node={'label':['Verified pool surplus']+labels,'color':['#102a43']+colors},link={'source':[0]*5,'target':[1,2,3,4,5],'value':[float(v) for v in vals]}));fig.update_layout(title=f'Covered-cycle surplus partition: {len(cycles):,} units; all values ETH',font_size=15)
    plot(fig,filename=str(out/'covered_surplus_distribution.html'),auto_open=False,include_plotlyjs=True)
    text='# 已核对闭合循环的收益与去向\n\n本页是有界样本的收益分配账，不是全事件 MEV 总额，也不是 hacker 到 bot 的直接转账图。所有单位为 ETH/WETH 等值数量，包装兑换按明确 1:1 处理。\n\n'
    text+=f"{len(cycles)} 个交易互不重复、池侧剩余与账户账完全衔接的 ETH/WETH 循环，毛剩余 **{totals['gross']} ETH**，分为：\n\n"
    for label,key in [('Base fee 燃烧','burn'),('Priority fee 到区块 fee recipient','priority'),('直接 native 付款到区块 fee recipient','direct'),('WETH 直接付款或经解包合约到区块 fee recipient','indirect'),('留在明确操作边界中的净额','retained')]:text+=f'- {label}：**{totals[key]} ETH**。\n'
    text+='\n[交互分配图](covered_surplus_distribution.html) · [静态图](covered_surplus_distribution.png)\n\n## 实际费用接收地址\n\nfee recipient 取每笔所在区块的 header，不按标签猜 builder 身份。它之后付给 proposer 的金额属于二次分配，不再加到本账。\n\n| 地址 | Priority ETH | 直接 native ETH | WETH／解包中转 ETH | 合计 ETH |\n|---|---:|---:|---:|---:|\n'
    for r in rrows:text+=f"| `{r['address']}` | {Decimal(r['priority_ETH']):.9f} | {Decimal(r['direct_native_ETH']):.9f} | {Decimal(r['indirect_or_WETH_ETH']):.9f} | {Decimal(r['total_ETH']):.9f} |\n"
    text+='\n## 操作发送者与执行地址\n\n此表按实际 sender 汇总，不将不同 gas 钱包归并成同一家机构。净额属于列明的联合操作地址边界；还需检查边界外收益分配及最终受益人。它不是每个 sender 钱包单独收到的金额。\n\n| sender | 执行地址 | 单元数 | 联合边界净 ETH |\n|---|---|---:|---:|\n'
    for r in srows:text+=f"| `{r['sender']}` | {'; '.join('`'+a+'`' for a in r['execution_addresses'])} | {r['units']} | {Decimal(r['joint_boundary_net_ETH']):.9f} |\n"
    text+='\n全部 unitId、精确值和接收地址见 data/processed/mev_full_window/covered_surplus_distribution.json；多币种循环及开放库存不在此图中，不能据本图推断全部盈利者。\n';(out/'收益与费用去向.md').write_text(text);print(json.dumps({'units':len(cycles),'totals':record['totals_ETH'],'fee_recipient_addresses':len(rrows),'operational_senders':len(srows)},indent=2))
if __name__=='__main__':run()
