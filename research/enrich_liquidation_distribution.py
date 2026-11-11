import json,gzip
from pathlib import Path
from decimal import Decimal as D
import value_inventory_ledger as v
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 d=load('aave_borrower_accounting.json');scope={x['hash']:x for x in load('expanded_scope_details.json')['rows']}
 for pr in load('scope_market_prices.json')['rows']:v.PRICES.setdefault(pr['symbol'],{}).update(pr['bars'])
 for e in d['liquidations']:
  t=scope[e['hash']];n=t['block'];b=json.loads(gzip.decompress((R/'scope_detail_raw'/f'{n}_block.json.gz').read_bytes()))['result'];r=next(x for x in json.loads(gzip.decompress((R/'scope_detail_raw'/f'{n}_receipts.json.gz').read_bytes()))['result'] if x['transactionHash']==t['hash']);treasury='0x464c71f6c2f760dda6093dcb91c24c39e5d6e18c';user=d['user'];fee=0
  for l in r['logs']:
   ts=l['topics']
   if l['address']=='0x23878914efe38d27c4d67ab83ed1b93a74d4086a' and len(ts)==3 and ts[0]=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' and '0x'+ts[1][-40:]==user and '0x'+ts[2][-40:]==treasury:fee+=int(l['data'],16)
  feeval=v.token_value(e['collateral_asset'],str(fee),t['timestamp'],5);builder_net=int(t['native']['native_net_wei'].get(b['miner'],'0'));ep=v.price('ETH',t['timestamp'],5)[0];gas=int(t['gas_wei']);tip=gas-int(r['gasUsed'],16)*int(b['baseFeePerGas'],16)
  e.update(protocol_fee_aUSDT_raw=str(fee),protocol_fee_underlying_valuation=feeval,total_collateral_removed_underlying_raw=str(int(e['collateral_received_raw'])+fee),gross_borrower_liquidation_asset_loss_USD=str(D(e['gross_liquidation_spread_USD'])+D(feeval['USD'])) if e['gross_liquidation_spread_USD'] is not None and feeval['USD'] is not None else None,protocol_fee_recipient=treasury,block_fee_recipient=b['miner'],block_fee_recipient_net_native_ETH=str(D(builder_net)/10**18),block_fee_recipient_net_native_USD=str(D(builder_net)/10**18*ep),transaction_priority_ETH=str(D(tip)/10**18),gas_ETH=str(D(gas)/10**18),interpretation='Treasury transfer of aUSDT marked at underlying USDT; redemption/freeze risk excluded. Liability reduction uses LiquidationCall.debtToCover, not net debt-token Transfer, because accrued interest changes emitted values. Previous-block health factor is not the pre-call intra-block health factor.')
 (R/'aave_borrower_accounting.json').write_text(json.dumps(d,indent=2));print([{k:e[k] for k in ['gross_borrower_liquidation_asset_loss_USD','protocol_fee_aUSDT_raw','block_fee_recipient_net_native_ETH','block_fee_recipient_net_native_USD']} for e in d['liquidations']])
if __name__=='__main__':main()
