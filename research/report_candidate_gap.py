"""Publish gap closure only after complete, independently rechecked accounting."""
import json,csv
from pathlib import Path
from decimal import Decimal as D,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 a=load('all_candidate_accounting.json');s=a['summary'];validation=load('candidate_gap_validation.json');start=load('candidate_gap_start.json')
 assert validation['remaining']==0 and validation['failed']==0 and s['native_missing']==0,'Cannot report completion with unresolved data'
 closed=[r for r in a['rows'] if r['other_token_inventory_closed']];positive=[r for r in closed if D(r['net_ETH_WETH_after_gas'])>0];negative=[r for r in closed if D(r['net_ETH_WETH_after_gas'])<0];zero=[r for r in closed if D(r['net_ETH_WETH_after_gas'])==0]
 total=lambda rows:sum((D(r['net_ETH_WETH_after_gas']) for r in rows),D(0))
 lines=['# 候选交易原生币收支缺口完成报告','',
 '**原来缺少收支数据的 12,934 笔候选交易已全部补齐，剩余缺口为 0。** 现在 13,623 笔候选均有原生 ETH 收支数据，并已重新计算扣除手续费后的 ETH/WETH 现金流。','',
 '“候选”指在目标兑换之后同一个区块或后五个区块内、交易同一资金池的交易。它们可能包括套利、普通交易和其他策略；补齐数据不等于确认全部是套利。','',
 '| 项目 | 补齐前 | 补齐后 |','|---|---:|---:|',
 f"| 候选总数 | {start['summary_before']['candidates']:,} | {s['candidates']:,} |",
 f"| 原生币收支可用 | {start['summary_before']['native_available']:,} | {s['native_available']:,} |",
 f"| 原生币收支缺失 | {start['summary_before']['native_missing']:,} | {s['native_missing']:,} |",
 f"| 收支可用且其他 ERC-20 净库存为零 | {start['summary_before']['native_available_and_other_inventory_closed']:,} | {len(closed):,} |",'',
 '## 完整核算结果','',
 f"全部候选合计支付 gas **{D(s['candidate_gas_ETH']):,.9f} ETH**。这个金额是所选交易的实际费用，不能全部归因于攻击。",'',
 f"在其他 ERC-20 净库存为零的 **{len(closed):,} 笔**中，按发起地址与调用目标地址合并核算，扣除 gas 后的 ETH/WETH 净现金流合计为 **{total(closed):,.9f} ETH**。",'',
 '| 库存闭合子集的现金流方向 | 笔数 | ETH/WETH 净额（ETH） |','|---|---:|---:|',
 f'| 正值 | {len(positive):,} | {total(positive):,.9f} |',
 f'| 负值 | {len(negative):,} | {total(negative):,.9f} |',
 f'| 零 | {len(zero):,} | 0 |','',
 f"另外 **{len(a['rows'])-len(closed):,} 笔**仍有其他 ERC-20 代币净库存。它们的 ETH/WETH 现金流已经补齐，但尚不能作为完整投资组合利润，仍需对其他资产估值。",'',
 '这里的账户边界不等于已确认的同一经济主体。共享路由器、外部收益接收人、跨交易库存、NFT/其他非 ERC-20 资产及交易所头寸没有因此自动解决。现金流正值不能直接称为套利利润，现金流负值也不能直接称为策略亏损。','',
 '## 如何核验','',
 '- 对照补取前冻结的 12,934 个交易哈希逐笔销账；没有通过删除候选减少缺口。',
 '- 原有 689 笔证据保留；新增记录来自公开调用轨迹，并保存原始响应。',
 '- 检查调用树父子完整、失败调用及失败祖先、根调用发起与目标、回执状态和逐笔原生币守恒。',
 '- 从原始回执重算全部候选的手续费与 ERC-20/WETH 净变化；ETH/WETH 净现金流只扣一次手续费。',
 f"- 本轮 **{validation['passed']} 项检查通过，0 项失败**。检查的是数据与算术一致性，不是攻击因果关系。",'',
 '## 交付文件','',
 '- [候选收支明细（中文）](候选收支明细_中文.csv)：全部 13,623 笔的可读明细。',
 '- [完整核算数据](all_candidate_accounting.json)、[原格式明细](全部候选核算.csv)。',
 '- [缺口销账及验证](candidate_gap_validation.json)、[原始缺口清单](candidate_gap_start.json)。',
 '- [完整区块调用轨迹索引](drpc_candidate_native.json)：含逐笔区块、哈希与原始文件位置；原始响应保存在 drpc_trace_raw。',
 '- [逐笔浏览器交叉证据](candidates_rawtrace_native.json)：保留另一个公开来源的数据，原始响应位于 rawtrace_raw。',
 '- [dRPC trace_block 文档](https://drpc.org/docs/ethereum-api/debugandtrace/trace_block)：使用无需密钥的公开端点 https://eth.drpc.org；这是第三方节点返回的历史轨迹，不是本地独立执行或反事实回放。','',
 '本次完成的是原生币收支数据缺口。全事件 MEV 因果归因、LP 与验证者最终收益分配、其他代币估值仍属于研究的后续问题。','']
 for title,rs in [('现金流正值最大的十笔',sorted(positive,key=lambda r:D(r['net_ETH_WETH_after_gas']),reverse=True)[:10]),('现金流负值最大的十笔',sorted(negative,key=lambda r:D(r['net_ETH_WETH_after_gas']))[:10])]:
  lines+=['## '+title,'','以下只供追查资金路径，不是已确认的套利排行。','','| 区块 | 扣费后 ETH/WETH 净额 | 交易 |','|---|---:|---|']
  for r in rs:lines.append(f"| {r['block']} | {D(r['net_ETH_WETH_after_gas']):,.9f} | [{r['hash'][:14]}…](https://etherscan.io/tx/{r['hash']}) |")
  lines.append('')
 (R/'候选收支缺口完成报告.md').write_text('\n'.join(lines))
 headers=['交易哈希','区块','发起地址','调用目标','原生ETH净变化','WETH净变化','手续费ETH','扣费后ETH及WETH净变化','其他ERC20净库存为零','其他代币原始整数净变化','与目标同一区块','存在反向交易信号','原生币证据来源']
 with (R/'候选收支明细_中文.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(headers)
  for r in a['rows']:w.writerow([r['hash'],r['block'],r['from'],r['to'],r['native_ETH'],r['WETH_delta'],r['gas_ETH'],r['net_ETH_WETH_after_gas'],'是' if r['other_token_inventory_closed'] else '否',json.dumps(r['other_token_net_raw']),'是' if r['same_block_as_target'] else '否','是' if r['opposite_amount0'] else '否',r['native_source']])
 print('Gap completion report and Chinese table written')
if __name__=='__main__':main()
