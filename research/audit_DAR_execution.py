import json
from pathlib import Path
from decimal import Decimal as D,getcontext
from audit_target_v2_fees import call,FACTORY
from classify_incremental_candidates import receipts
getcontext().prec=70
R=Path(__file__).resolve().parent;pool='0x4aadb3498f407e4d558589514bb9a4b341475e31';n=26305175;h='0x230b5d9ec55aa34e0de8342c1b0f5ef8ca46d11d9f13dfaeadd2dff3351b5272';meta={}
for field,sel in [('token0','0x0dfe1681'),('token1','0xd21220a7'),('factory','0xc45a0155')]:meta[field]='0x'+call('DAR_'+field,pool,sel,n-1)[-40:]
assert meta['factory']==FACTORY
assert '0x'+call('DAR_pair',FACTORY,'0xe6a43905'+meta['token0'][2:].zfill(64)+meta['token1'][2:].zfill(64),n-1)[-40:]==pool
for k in ['token0','token1']:meta[k+'_decimals']=int(call('DAR_'+k+'_decimals',meta[k],'0x313ce567',n-1),16)
raw=call('DAR_previous_reserves',pool,'0x0902f1ac',n-1);prev=[int(raw[i:i+64],16) for i in range(2,len(raw),64)][:2]
r=next(r for r in receipts(n) if r['transactionHash']==h);logs=[l for l in r['logs'] if l['address']==pool];sync=next(l for l in logs if l['topics'][0]=='0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1');swap=next(l for l in logs if l['topics'][0]=='0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822');w=[int(swap['data'][i:i+64],16) for i in range(2,len(swap['data']),64)];after=[int(sync['data'][i:i+64],16) for i in range(2,len(sync['data']),64)];before=[after[i]-w[i]+w[i+2] for i in [0,1]];assert w[1]==w[2]==0
x=w[0];actual=w[3];model=x*997*before[1]//(1000*before[0]+997*x);assert model==actual
spot=D(x)*D(before[1])/D(before[0]);afterfee=spot*D('0.997');fee=(spot-afterfee)/D(10**18);impact=(afterfee-D(model))/D(10**18)
out={'hash':h,'block':n,'pool':pool,'metadata':meta,'verified_factory':True,'previous_block_reserves':list(map(str,prev)),'pretrade_reserves':list(map(str,before)),'same_as_previous_block':before==prev,'DAR_input':str(D(x)/(D(10)**meta['token0_decimals'])),'ETH_actual_received':str(D(actual)/D(10**18)),'actual_output_formula_exact':True,'input_over_DAR_reserve':str(D(x)/D(before[0])),'local_spot_equivalent_ETH':str(spot/D(10**18)),'fee_component_at_pretrade_spot_ETH':str(fee),'finite_size_price_impact_plus_rounding_ETH':str(impact),'remaining_formula_residual_ETH':'0','method':'Separate local pretrade spot decomposition of deprecated DAR pool, not external fair market value. Spot reference need not be executable for total input and may be economically stale. Actual matches 0.3% Uniswap V2 formula. Do not add to USD market shortfall or call causal MEV.'}
(R/'DAR_execution_decomposition.json').write_text(json.dumps(out,indent=2));print(out)
