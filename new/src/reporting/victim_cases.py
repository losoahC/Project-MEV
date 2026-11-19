"""Link fresh victim interventions to actual operator cashflows and payout addresses."""
import json
from collections import defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow
from src.decoding.events import integer

def run():
    p=ROOT/'data/processed/mev_full_window';out=ROOT/'reports/mev_expansion';folder=out/'victim_cases';folder.mkdir(exist_ok=True)
    replays=json.loads((p/'victim_replays.json').read_text())['rows'];locals=json.loads((p/'local_victim_effects.json').read_text())['rows'];lookup={(x['target'],x.get('front')):x for x in locals};engine=Reconstruction(ROOT.parent/'research',False);results=[]
    for r in replays:
        if r['status']!='verified_fixed_call_victim_intervention':continue
        local=lookup[(r['target'],r['removed_front'])];n=r['block'];head,rs,tr,paths=engine.block(n);front=r['removed_front'];sender=rs[front]['from'].lower();back=min(local['back_transactions'],key=lambda h:integer(rs[h]['transactionIndex']));lo=integer(rs[front]['transactionIndex']);hi=integer(rs[back]['transactionIndex'])
        hs=[h for h,rec in rs.items() if rec['from'].lower()==sender and lo<=integer(rec['transactionIndex'])<=hi];hs.sort(key=lambda h:integer(rs[h]['transactionIndex']));boundary={sender}|{(rs[h].get('to') or '').lower() for h in hs};boundary.discard('');net=Decimal(0);gross=Decimal(0);gas=0;payment=0;residual=defaultdict(int);payouts=[];legs=[]
        from src.arbitrage.accounting import native_flows
        for h in hs:
            f=cashflow(rs[h],tr[h],boundary,head['miner']);net+=Decimal(f['net_after_gas_and_builder_ETH']);gross+=Decimal(f['gross_after_pool_fees_before_gas_and_builder_ETH']);gas+=int(f['gas_wei']);payment+=int(f['identified_builder_payment_wei'])
            for t,v in f['other_token_residual_raw'].items():residual[t]+=int(v)
            for v in native_flows(tr[h]):
                if v['sender'] in boundary and v['recipient'] not in boundary:payouts.append({'tx_hash':h,**v})
            legs.append({'tx_hash':h,'index':integer(rs[h]['transactionIndex']),'sender':sender,'entrypoint':rs[h]['to'],**f})
        residual={t:str(v) for t,v in residual.items() if v};rec={'block':n,'target':r['target'],'front':front,'back':back,'operator_sender':sender,'operational_boundary':sorted(boundary),'boundary_verified':False,'included_sender_interval_transactions':hs,'gross_ETH':str(gross),'gas_ETH':str(Decimal(gas)/Decimal(10)**18),'direct_fee_recipient_payment_ETH':str(Decimal(payment)/Decimal(10)**18),'net_operational_cashflow_ETH':str(net),'non_WETH_residual_raw':residual,'external_native_payouts':payouts,'legs':legs,'victim_intervention':r,'total_strategy_profit_established':False};results.append(rec)
        text=f"# 排序干预案例：区块 {n}\n\n## 判定标准\n\n前腿与 hacker 在同池同方向；同一发送者存在目标之后的反向交易。以最早相关后腿为退出端，核算该发送者区间内全部交易。前后入口可不同，不能仅按相同 to 地址配对。执行入口及外部收款人的共同控制仍未证明。\n\n- 前腿：[{front}](https://etherscan.io/tx/{front})\n- hacker：[{r['target']}](https://etherscan.io/tx/{r['target']})\n- 后腿：[{back}](https://etherscan.io/tx/{back})\n- 操作发送者：`{sender}`\n- 执行入口边界：`{sorted(boundary)}`\n\n## Hacker 在指定干预下少收到多少\n\n实际前缀 {r['actual_prefix_transactions_reproduced']} 笔交易的状态、gas、日志均复现。删除指定前腿，保持其他调用参数不变，两种情景下目标均成功执行。\n\n"
        for v in r['victim_effects']:
            text+=f"地址 `{v['address']}`：投入是否不变：{v['inputs_unchanged']}；无前腿情景比实际多收到的原始资产整数为 `{v['without_front_minus_actual_asset_raw']}`，同一历史时点估值差额为 **USD {v['marked_output_improvement_USD']}**，不含 gas 差异。\n\n"
        text+='该结果是固定原调用干预下的收款差异，不是优化交易政策或全市场均衡损失，不能自动等同 bot 净赚。\n\n## Bot 操作边界的实际账\n\n'
        for name,key in [('毛现金流（池费已在成交中）','gross_ETH'),('Gas','gas_ETH'),('向区块 fee recipient 直接付款','direct_fee_recipient_payment_ETH'),('净操作现金流','net_operational_cashflow_ETH')]:text+=f"- {name}：{rec[key]} ETH\n"
        text+=f"\n非 WETH 残差：`{residual}`。账不含未认证边界外的利润接收人、跨区块建仓和场外对冲；即使残差为零，也不因此确认最终受益人利润。区间存在其他策略时还需进一步拆分。\n\n## 钱实际转到哪些地址\n\n"
        for f in payouts:text+=f"- `{f['sender']}` → `{f['recipient']}`：{Decimal(f['amount_raw'])/Decimal(10)**18} ETH，调用路径 `{f['trace_address']}`，交易 `{f['tx_hash']}`。\n"
        if not payouts:text+='该边界未识别对外 native 付款；ERC20 对外转账保存在完整逐交易账中。\n'
        text+='\n完整代币收付款、base fee、priority fee、单地址余额变化及付款接收人见 `data/processed/mev_full_window/all_sender_accounting.jsonl` 对应交易；DEX 与池路径后续与全窗口路径清单统一。\n\n原始执行、回执、轨迹与估值来源均在 `data/processed/mev_full_window/victim_case_accounts.json`，包括返回字节 SHA256 和 UTC 采集时间。\n'
        (folder/(r['target']+'.md')).write_text(text);engine.cache.clear()
    (p/'victim_case_accounts.json').write_text(json.dumps(results,indent=2));lines=['# Hacker 收款差异与 bot 现金流：历史执行干预','','所有金额逐案报告，不构成全事件可加总损失。bot 列为尚待边界核验的操作现金流。','','| 区块 | hacker 无前腿多收到的估值 USD（不含 gas） | bot 操作净现金流 ETH | 证据 |','|---|---:|---:|---|']
    for r in sorted(results,key=lambda x:Decimal(x['victim_intervention']['victim_effects'][0]['marked_output_improvement_USD'] or '0'),reverse=True):
        usd=r['victim_intervention']['victim_effects'][0]['marked_output_improvement_USD'];lines.append(f"| {r['block']} | {Decimal(usd):,.2f} | {Decimal(r['net_operational_cashflow_ETH']):.9f} | [逐案](victim_cases/{r['target']}.md) |")
    (out/'victim_intervention_index.md').write_text('\n'.join(lines)+'\n');print('Linked victim intervention records',len(results))
if __name__=='__main__':run()
