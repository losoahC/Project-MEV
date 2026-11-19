"""Exact one-order reference-shortfall partition, including a third-party settlement fee.
This is an accounting identity, NOT MEV incremental victim-loss attribution.
"""
import json
from decimal import Decimal
from src.arbitrage.comet_resolver import BLOCK,TX,RESOLVER
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows,token_net
from src.arbitrage.value_candidates import book_from_archive
from src.decoding.events import USDT,WETH,integer
MAKER='0x9749292d74fd460982d0912ea9515ea24736c762'

def run():
    p=ROOT/'data/processed/mev_full_window';c=json.loads((p/'comet_resolver_equity.json').read_text());engine=Reconstruction(ROOT.parent/'research',False);head,rs,tr,paths=engine.block(BLOCK);flows=native_flows(tr[TX]);makerflow=[f for f in flows if f['recipient']==MAKER];assert len(makerflow)==1;carrier=makerflow[0]['sender'];third=[f for f in flows if f['sender']==carrier and f['recipient']!=MAKER];assert len(third)==1;book=book_from_archive();price=book.price('ETH',integer(head['timestamp']))[0];tokens=token_net(rs[TX],{MAKER});nat=sum(int(f['amount_raw'])*((f['recipient']==MAKER)-(f['sender']==MAKER)) for f in flows);loss=-sum((Decimal(book.value(t,v,integer(head['timestamp']))['USD']) for t,v in tokens.items()),Decimal(0))-Decimal(nat)/10**18*price
    cf=c['actual_cashflow'];parts={'resolver_marked_equity_gain_USD':Decimal(c['reference_equity_gain_after_gas_USD']),'direct_block_fee_recipient_payment_USD':Decimal(cf['identified_builder_payment_wei'])/10**18*price,'third_party_settlement_payment_USD':Decimal(third[0]['amount_raw'])/10**18*price,'actual_gas_USD':Decimal(cf['gas_wei'])/10**18*price};assert sum(parts.values(),Decimal(0))==loss
    doc={'tx_hash':TX,'block':BLOCK,'maker':MAKER,'resolver':RESOLVER,'gas_payer':rs[TX]['from'].lower(),'fee_recipient':head['miner'].lower(),'settlement_carrier':carrier,'third_party_receiver':third[0]['recipient'],'maker_net_USDT_raw':str(tokens[USDT]),'maker_native_ETH_in':str(Decimal(nat)/10**18),'third_party_native_ETH_in':str(Decimal(third[0]['amount_raw'])/10**18),'reference_ETH_USD':str(price),'maker_reference_shortfall_USD':str(loss),'partition_USD':{k:str(v) for k,v in parts.items()},'partition_reconciles_exactly':True,'MEV_incremental_loss_proven':False,'third_party_beneficial_owner_proven':False,'actual_native_flows':flows,'position_equity_evidence':'data/processed/mev_full_window/comet_resolver_equity.json','evidence':paths,'interpretation':'Same-transaction reference-price accounting identity, using maker asset deltas and resolver collateral-minus-debt equity. Unknown third-party recipient is retained by address, not labelled as protocol firm revenue. Not all-event, equilibrium or ordering-caused MEV loss.'};(p/'order_reference_shortfall_partition.json').write_text(json.dumps(doc,indent=2));print(json.dumps({'loss_USD':str(loss),'partition_USD':doc['partition_USD'],'third_party_receiver':doc['third_party_receiver'],'third_party_ETH':doc['third_party_native_ETH_in']},indent=2))
if __name__=='__main__':run()
