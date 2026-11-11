"""Complete the unknown-price row symbolically without inventing a fair price."""
import json
from decimal import Decimal as D,getcontext
from pathlib import Path
getcontext().prec=80
R=Path(__file__).resolve().parent
def main():
 d=json.loads((R/'DAR_execution_decomposition.json').read_text());v=json.loads((R/'wallet_purchase_price_completion.json').read_text());row=next(r for r in v['rows'] if r['hash']==d['hash']);ethprice=D(row['scenarios']['strict']['ETH_price']);received=D(d['ETH_actual_received'])*ethprice;amount=D(d['DAR_input']);breakeven=received/amount
 # Recompute directly from integer reserve/input units, independently of the formatted decomposition.
 reserve_token,reserve_weth=map(int,d['pretrade_reserves']);raw=int(amount*10**6);out=raw*997*reserve_weth//(reserve_token*1000+raw*997);assert out==int(D(d['ETH_actual_received'])*10**18)
 localprice=D(reserve_weth)/10**18/(D(reserve_token)/10**6)*ethprice;spotloss=amount*localprice-received
 result={'hash':d['hash'],'wallet':row['wallet'],'DAR_units':str(amount),'ETH_received':d['ETH_actual_received'],'ETH_reference_USD':str(ethprice),'ETH_price_evidence':row['scenarios']['strict']['ETH_price_evidence'],'received_reference_value_USD':str(received),'unidentified_DAR_fair_price_symbol':'p_USD_per_old_DAR','execution_shortfall_formula':'DAR_units * p_USD_per_old_DAR - received_reference_value_USD; gas excluded','break_even_DAR_price_USD':str(breakeven),'conditional_bound_if_p_nonnegative':{'shortfall_USD_lower':str(-received),'shortfall_USD_upper':None,'upper_bound_reason':'No independently justified finite upper bound on p supplied by this evidence.'},'separate_local_pool_spot_sensitivity':{'spot_price_USD_per_DAR':str(localprice),'shortfall_USD_at_local_spot':str(spotloss),'actual_integer_output_reproduced':True,'not_external_fair_price':True,'not_added_to_market_shortfall_total':True},'resolution':'Row is fully cashflow-reconciled and actual AMM execution reproduced; fair price remains unidentified. Symbolic shortfall and break-even threshold replace an invented zero, migration parity, or new-token price. This is execution shortfall, never an MEV lower bound.'};(R/'DAR_price_identification_bounds.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()
