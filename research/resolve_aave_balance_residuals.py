import json
from pathlib import Path
from Crypto.Hash import keccak
from audit_target_v2_fees import call
R=Path(__file__).resolve().parent;POOL='0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2';last=26342152;end=26349764;RAY=10**27
sel=lambda s:'0x'+keccak.new(digest_bits=256,data=s.encode()).hexdigest()[:8]
def main():
 audit=json.loads((R/'wallet_token_balance_reconciliation.json').read_text());rows=[]
 for r in audit['rows']:
  if r['reconciled']:continue
  token=r['token'];a=r['address'];assert r['wallet']==3
  underlying='0x'+call('balproof_'+token+'_underlying',token,sel('UNDERLYING_ASSET_ADDRESS()'),end)[-40:]
  name='getReserveNormalizedIncome(address)' if token=='0x23878914efe38d27c4d67ab83ed1b93a74d4086a' else 'getReserveNormalizedVariableDebt(address)';states=[]
  for n in [last,end]:
   scaled=int(call(f'balproof_{token}_{n}_scaled',token,sel('scaledBalanceOf(address)')+a[2:].zfill(64),n),16);index=int(call(f'balproof_{token}_{n}_index',POOL,sel(name)+underlying[2:].zfill(64),n),16);balance=int(call(f'balproof_{token}_{n}_balance',token,'0x70a08231'+a[2:].zfill(64),n),16);pred=(scaled*index+RAY//2)//RAY;assert balance==pred
   states.append({'block':n,'scaled_balance_raw':str(scaled),'normalized_index_ray':str(index),'balance_raw':str(balance),'ray_mul_reproduced':True})
  assert states[0]['scaled_balance_raw']==states[1]['scaled_balance_raw'];interest=int(states[1]['balance_raw'])-int(states[0]['balance_raw']);assert int(states[0]['balance_raw'])==int(r['indexed_transfer_net_raw']);assert interest==int(r['residual_raw'])
  rows.append({'wallet':3,'token':token,'underlying':underlying,'normalization_function':name,'states':states,'interest_since_last_indexed_operation_raw':str(interest),'residual_fully_explained_by_index_growth':True,'debt_not_asset_income':name.startswith('getReserveNormalizedVariableDebt')})
 out={'method':'Constant scaledBalanceOf after last liquidation; historical pool normalized income/debt index reproduces balanceOf via rayMul half-up rounding at last operation and cutoff. Difference equals entire token transfer residual. Claim interest and debt accrual are distinct, not MEV income.','rows':rows,'all_explained':all(r['residual_fully_explained_by_index_growth'] for r in rows)};(R/'aave_token_balance_residual_proof.json').write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
