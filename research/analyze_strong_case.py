import json,gzip
from pathlib import Path
from decimal import Decimal as D,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent
def main():
 h='0xf3935c9604416f38ea2942652ea8c652bc2ea0cfac2ad0316181031bdcd607c2';target='0x625e674d10c864a1d98d8ba9b5c05ed2f325d74cca62b8b67cd6268edbd8f051';n=26301609;pool='0xa43fe16908251ee70ef74718545e4fe6c5ccec9f';sync='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1';swap='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
 rs=json.loads(gzip.decompress((R/'window_raw'/f'{n}.json.gz').read_bytes()));byh={r['transactionHash']:r for r in rs};case=next(r for r in json.loads((R/'candidate_classification.json').read_text())['rows'] if r['hash']==h)
 words=lambda data:[int(data[i:i+64],16) for i in range(2,len(data),64)]
 tl=[l for l in byh[target]['logs'] if l['address']==pool];sw=[l for l in tl if l['topics'][0]==swap];assert len(sw)==1
 after=next(words(l['data']) for l in reversed(tl) if l['topics'][0]==sync);amounts=words(sw[0]['data']);before=[after[0]-amounts[0]+amounts[2],after[1]-amounts[1]+amounts[3]]
 between=[l for r in rs if int(byh[target]['transactionIndex'],16)<int(r['transactionIndex'],16)<int(byh[h]['transactionIndex'],16) for l in r['logs'] if l['address']==pool];assert not between
 edge=next(e for e in case['token_cycle'] if e['pool']==pool);amount_in=int(edge['input_raw']);actual=int(edge['output_raw'])
 quote=lambda rin,rout:amount_in*997*rout//(rin*1000+amount_in*997)
 expected=quote(after[1],after[0]);assert expected==actual
 baseline=quote(before[1],before[0]);assert actual>baseline
 output=int(next(e for e in case['token_cycle'] if e['pool']!=pool)['output_raw']);gross=D(output-amount_in)/D(10)**18;gas=D(case['gas_ETH']);net=D(case['operational_cashflow_ETH']);other_cost=gross-gas-net
 block=json.loads(gzip.decompress((R/'window_raw'/f'{n}_block.json.gz').read_bytes()));miner=block['miner'];tr=[t for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result'] if t.get('transactionHash')==h];bad={tuple(t['traceAddress']) for t in tr if t.get('error')};paid=0
 for t in tr:
  path=tuple(t['traceAddress']);a=t['action']
  if any(path[:i] in bad for i in range(len(path)+1)):continue
  if t['type']=='call' and a.get('callType')=='call' and a.get('from') in case['operational_boundary'] and a.get('to')==miner:paid+=int(a['value'],16)
 assert D(paid)/D(10)**18==other_cost
 out={'hash':h,'target':target,'block':n,'target_index':int(byh[target]['transactionIndex'],16),'candidate_index':int(byh[h]['transactionIndex'],16),'route':'WETH -> PEPE in Uniswap V2; PEPE -> WETH in Uniswap V3','input_WETH':str(D(amount_in)/D(10)**18),'intermediate_PEPE':str(D(actual)/D(10)**18),'output_WETH':str(D(output)/D(10)**18),'gross_spread_WETH':str(gross),'direct_fee_recipient_payment_ETH':str(other_cost),'fee_recipient':miner,'gas_ETH':str(gas),'operational_net_ETH':str(net),'v2_reserves_before_target_raw':list(map(str,before)),'v2_reserves_after_target_raw':list(map(str,after)),'actual_first_leg_output_matches_v2_formula':expected==actual,'same_input_before_target_PEPE':str(D(baseline)/D(10)**18),'actual_to_before_target_output_ratio':str(D(actual)/D(baseline)),'no_intervening_pool_logs':not between,'interpretation':'Strong observed atomic cross-pool cycle; exact economic owner unresolved. Removing only target reserve change in first-leg formula reduces output, holding input fixed. This is a local mechanical sensitivity, NOT a complete second-leg/whole-block counterfactual or proof all net gain is target-caused.'}
 (R/'strong_case_analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
