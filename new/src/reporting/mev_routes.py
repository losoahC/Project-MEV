"""Build ordered, address-resolved route evidence and human-readable case records."""
import json
from decimal import Decimal,getcontext
from collections import defaultdict,Counter
from src.arbitrage.discover import ROOT
getcontext().prec=90

def run():
    p=ROOT/'data/processed/mev_discovery';out=ROOT/'reports/mev_expansion';cases=out/'cases';cases.mkdir(parents=True,exist_ok=True)
    cs=json.loads((p/'candidates.json').read_text());ms={r['pool']:r for r in json.loads((p/'pool_metadata.json').read_text())};book=json.loads((ROOT/'data/processed/historical_pricebook.json').read_text());tokens=book['registry'];vals={r['tx_hash']:r for r in json.loads((p/'candidate_valuations.json').read_text())};classes={r['tx_hash']:r for r in json.loads((p/'classification.json').read_text())};hacker=json.loads((ROOT/'data/processed/wallet_swap_valuations.json').read_text());hv=defaultdict(list)
    for r in hacker:hv[r['tx_hash']].append(r)
    episodes=json.loads((p/'episodes.json').read_text());routes=[]
    prior=json.loads((ROOT/'data/processed/arbitrage_cases.json').read_text());known={(a['block'],pool):meta for a in prior for pool,meta in a['metadata'].items()}
    def asset(t,v):
        m=tokens.get(t,{});d=m.get('decimals');return {'token':t,'symbol':('WETH' if t=='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2' else m.get('symbol')),'amount_raw':str(v),'quantity':str(Decimal(v)/Decimal(10)**d) if d is not None else None,'decimals':d,'decimal_basis':m.get('decimal_basis')}
    bytx={c['tx_hash']:c for c in cs}
    for c in cs:
        ordered=[]
        for l in c['pool_legs']:
            m=dict(ms[l['pool']]);fallback=known.get((c['block'],l['pool']))
            if fallback:
                for key in ['token0','token1','factory','fee_pips']:
                    if key not in m and key in fallback:m[key]=fallback[key];m['sources'][key]=fallback['sources'].get(key,key+' from prior audited case metadata')
            for ev in l['swap_events_in_log_order']:
                ins=[];outs=[]
                for i in [0,1]:
                    t=m.get(f'token{i}');raw=int(ev[f'amount{i}_raw'])
                    if t and raw: (ins if raw>0 else outs).append(asset(t,abs(raw)))
                ordered.append({'pool':l['pool'],'DEX':m['dex_name'],'factory':m.get('factory'),'factory_lookup_matches_pool':m.get('factory_lookup_matches_pool'),'protocol_event':ev['protocol'],'fee_pips':m.get('fee_pips'),'log_index':ev['log_index'],'inputs':ins,'outputs':outs,'amounts_decoded':bool(ins and outs),'signed_event_deltas':{'amount0_raw':ev['amount0_raw'],'amount1_raw':ev['amount1_raw']},'metadata_sources':m['sources']})
        ordered.sort(key=lambda x:x['log_index'])
        cycles=[];start=0
        while start<len(ordered):
            first=ordered[start]
            if len(first['inputs'])!=1 or len(first['outputs'])!=1:start+=1;continue
            initial=first['inputs'][0]['token'];end=start;path=[initial];net=defaultdict(int)
            while end<len(ordered):
                step=ordered[end]
                if len(step['inputs'])!=1 or len(step['outputs'])!=1 or step['inputs'][0]['token']!=path[-1]:break
                for a in step['inputs']:net[a['token']]-=int(a['amount_raw'])
                for a in step['outputs']:net[a['token']]+=int(a['amount_raw'])
                path.append(step['outputs'][0]['token'])
                if path[-1]==initial:
                    cycles.append({'first_swap_number':start+1,'last_swap_number':end+1,'token_path':path,'pool_flow_surplus_raw':{t:str(v) for t,v in net.items() if v},'note':'Contiguous observed token path closes. Actual flash funding and non-pool payments are separately accounted.'});start=end+1;break
                end+=1
            else:start+=1;continue
            if end>=len(ordered) or start<=end:start=max(start,end+1)
        r={'tx_hash':c['tx_hash'],'block':c['block'],'sender':c['sender'],'executor':c['executor'],'swap_event_count':len(ordered),'distinct_pools':len(c['pool_legs']),'ordered_swaps':ordered,'contiguous_token_cycles':cycles,'ordering_note':'Onchain log order, not proof that split branches are a single linear token path.','classification':classes[c['tx_hash']],'target_links':c['associations'],'target_reference_valuations':{h:[{'wallet':r['wallet'],'loss_USD':r.get('loss_USD'),'valuation_complete':r.get('valuation_complete')} for r in hv[h]] for h in sorted({a['target'] for a in c['associations']})},'candidate_marked_cashflow':vals[c['tx_hash']],'native_payouts':c.get('external_native_payouts',[]),'evidence':c['evidence']};routes.append(r)
    (p/'ordered_routes.json').write_text(json.dumps(routes,indent=2));byroute={r['tx_hash']:r for r in routes}
    priority=sorted((e for e in episodes if e['classification'].startswith('closed_positive') and not e['shared_entrypoint_in_block'] and e['transaction_count']==1),key=lambda e:Decimal(e['net_ETH']),reverse=True)
    lines=['# 优先复核的套利交易路径','','以下是候选案例的可读证据，不是最终 MEV 收益排行榜。金额采用明确操作边界；仍需核验 executor 归属及跨区块库存。hacker 参考差额不等于该笔套利造成的损失。','','| 区块 | 净现金流 ETH | swap 事件 / 不同池 | 案例 |','|---|---:|---:|---|']
    for e in priority[:30]:
        h=e['transactions'][0]['tx_hash'];c=bytx[h];r=byroute[h];name=h+'.md';text=f"# 区块 {c['block']}：多池套利候选\n\n交易：[{h}](https://etherscan.io/tx/{h})\n\n发送者：`{c['sender']}`  \n执行入口：`{c['executor']}`  \n核算边界：发送者与执行入口；控制归属仍需验证。\n\n## 为何列为套利 / MEV 候选\n\n池侧非 WETH 库存闭合；操作边界无其他代币残差，扣费用后为正。涉及 {r['swap_event_count']} 个 swap 事件、{r['distinct_pools']} 个不同池。"
        back=r['classification']['criteria']['after_target_same_pool_opposite_direction'];text+=' 与目标同块、同池、后执行且方向相反，符合 backrun 特征。' if back else ' 仅有同池关联，暂未满足后置反向特征。'
        text+='尚未通过删除目标或套利交易的反事实重放证明因果；不以 gas 高低作为 MEV 判据。\n\n## 收益与费用（ETH）\n\n'
        for title,key in [('毛现金流，已含池费','gross_after_pool_fees_before_gas_and_builder_ETH'),('Gas','gas_wei'),('向区块 fee recipient 的直接付款','identified_builder_payment_wei'),('剩余净现金流','net_after_gas_and_builder_ETH')]:
            v=Decimal(c[key])/(Decimal(10)**18 if key.endswith('_wei') else 1);text+=f'- {title}：{v}\n'
        text+=f"\n区块 fee recipient：`{c['fee_recipient']}`。它收到的直接付款不等于该区块最终 proposer 总收款。\n\n## 实际池交易轮次\n\n以下按 logIndex 排序；分支及重复池不能自动拼成一条线性路径。\n\n| 顺序 / logIndex | DEX / 池 | 输入 | 输出 |\n|---|---|---|---|\n"
        def label(a):return f"{a['quantity'] or a['amount_raw']+' raw'} {a['symbol'] or a['token']}"
        for i,step in enumerate(r['ordered_swaps'],1):text+=f"| {i} / {step['log_index']} | {step['DEX'] or 'DEX 未认证'} / `{step['pool']}` | {'; '.join(map(label,step['inputs'])) or 'token0/1 未解析，见原始事件'} | {'; '.join(map(label,step['outputs'])) or '见原始事件'} |\n"
        text+='\n## 可识别的闭合交易轮次\n\n'
        for cycle in r['contiguous_token_cycles']:
            path=' → '.join('WETH' if t=='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2' else tokens.get(t,{}).get('symbol',t) for t in cycle['token_path'])
            text+=f"- swap {cycle['first_swap_number']}–{cycle['last_swap_number']}：{path}；池侧剩余原始整数 `{cycle['pool_flow_surplus_raw']}`。\n"
        text+='\n每轮池侧剩余不是最终净收益；还需合计手续费、借贷／回调成本及运营付款。不能将 log 顺序等同调用发起顺序。\n\n## 相关 hacker 交易与损失口径\n\n' 
        for h2,v in r['target_reference_valuations'].items():
            text+=f'- [{h2}](https://etherscan.io/tx/{h2})：'
            text+='；'.join(f"钱包 {a['wallet']} 的参考成交差额 {a['loss_USD']} USD" if a['valuation_complete'] else f"钱包 {a['wallet']} 缺少完整估值" for a in v) if v else '当前目标估值表未覆盖';text+='。\n'
        text+='\nMEV 增量损失：null。上述参考差额不能重复分给每个关联套利者。\n\n## 资金向外支付\n\n'
        for f in r['native_payouts']:text+=f"- `{f['sender']}` → `{f['recipient']}`：{Decimal(f['amount_raw'])/Decimal(10)**18} ETH，trace 路径 `{f['trace_address']}`。收款人性质未凭转账推断。\n"
        if not r['native_payouts']:text+='未在此边界识别出对外 native 付款；token 付款与余额变化见 candidates.json。\n'
        text+='\n原始证据：\n\n'+''.join(f'- {k}：`{v}`\n' for k,v in c['evidence'].items())
        (cases/name).write_text(text);lines.append(f"| {c['block']} | {Decimal(e['net_ETH']):.9f} | {r['swap_event_count']} / {r['distinct_pools']} | [逐笔路径](cases/{name}) |")
    (out/'route_index.md').write_text('\n'.join(lines)+'\n');print('ordered routes',len(routes),'detailed case files',min(30,len(priority)))
if __name__=='__main__':run()
