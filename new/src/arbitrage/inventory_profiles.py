"""Named Ethereum traders: address-only marks over all available sender context.
ETH/stable trade edges are reference margins, not historical inventory-cost profit.
"""
import json
from collections import defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction
from src.decoding.events import WETH,USDT,USDC
NAMED=['0x0cdd9cbb825212c6cc5b0b36239e94218ee661d8','0xcb02ecb8927434540352e1da27f91c3a194f1d1d','0x65a8f07bd9a8598e1b5b6c0a88f4779dbc077675','0xcaab6ff98989fdd4f47e7db6152e6fb47994ec1e','0xb7c854ed55a7bf36de3217aff276a54d6812dd20','0xa127edc40fea07cdff89f8d812931f612ec13fa6','0x09df642e9001c2020bac1c9f5e0b15ff44b8e86b','0x58a497019644d8c383c8d3764c32ffd43506e836','0x0000000000d3c71f9d0a31e2f2139da1ca37b599','0xbeef02961503351625926ea9a11ae13b29f5c555','0x51c72848c68a965f66fa7a88855f9f7784502a7f','0xae2fc483527b8ef99eb5d9b44875f005ba1fae13','0x45e9b04942176a513b22acc1ced75c34d2fd9215']

def run():
    p=ROOT/'data/processed/mev_full_window';book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('USDC',('2026-10-29','2026-10-30'));poolhash={json.loads(line)['tx_hash'] for line in (p/'pool_census.jsonl').open()};affected={json.loads(line)['tx_hash'] for line in (p/'affected_pool_scope.jsonl').open()};by=defaultdict(list)
    ledger=p/'named_full_window_ledger.jsonl'
    with ledger.open() as f:
        for line in f:
            r=json.loads(line);hits=set(NAMED)&r['single_address_asset_deltas'].keys()
            for a in hits:
                d=r['single_address_asset_deltas'][a];raw={t:int(v) for t,v in d['token_net_raw'].items() if int(v)};raw['native:eth']=int(d['native_net_before_gas_wei']);eth=raw.get(WETH,0)+raw['native:eth'];stable=raw.get(USDT,0)+raw.get(USDC,0);other={t:str(v) for t,v in raw.items() if v and t not in [WETH,USDT,USDC,'native:eth']};simple=r['tx_hash'] in poolhash and not other and not r['position_or_debt_events'] and not r['recognized_erc721_transfer_events'] and eth*stable<0;marks=[book.value(t,v,r['timestamp']) for t,v in raw.items() if v];gas=book.value('native:eth',int(d['gas_wei']),r['timestamp']);gross=sum((Decimal(x['USD']) for x in marks),Decimal(0)) if all(x['USD'] is not None for x in marks) else None;net=gross-Decimal(gas['USD']) if gross is not None and gas['USD'] is not None else None
                joint=r.get('joint_operation_cashflow') if a in {r['sender'],r.get('root_to')} else None; jmarks=[];jnet=None;jeligible=False
                if joint:
                    jraw={t:int(v) for t,v in joint['token_net_raw'].items() if int(v)};jraw['native:eth']=int(joint['native_net_wei'])-int(joint['gas_wei']);jmarks=[book.value(t,v,r['timestamp']) for t,v in jraw.items() if v];jeligible=r['tx_hash'] in poolhash and not r['position_or_debt_events'] and not r['recognized_erc721_transfer_events'];jnet=sum((Decimal(v['USD']) for v in jmarks),Decimal(0)) if jeligible and all(v['USD'] is not None for v in jmarks) else None
                by[a].append({'joint_boundary':r.get('joint_operation_boundary',[]) if joint else [],'joint_reference_trade_edge_USD':str(jnet) if jnet is not None else None,'joint_trade_valuations':jmarks,'tx_hash':r['tx_hash'],'block':r['block'],'index':r['index'],'timestamp':r['timestamp'],'address':a,'root_sender':r['sender'],'has_pool_events':r['tx_hash'] in poolhash,'affected_pool_tx':r['tx_hash'] in affected,'simple_ETH_stable_trade':simple,'direction':'sell_ETH' if simple and eth<0 else 'buy_ETH' if simple else None,'single_address_raw':{t:str(v) for t,v in raw.items() if v},'other_assets_raw':other,'position_or_debt_events':r['position_or_debt_events'],'reference_gross_USD':str(gross) if gross is not None else None,'own_gas_USD':gas['USD'],'reference_net_after_own_gas_USD':str(net) if net is not None else None,'valuation_evidence':marks,'gas_valuation':gas,'evidence':r['evidence']})
    summary=[]
    for a in NAMED:
        rows=by[a];simple=[r for r in rows if r['simple_ETH_stable_trade']];priced=[r for r in simple if r['reference_net_after_own_gas_USD'] is not None];impacted=[r for r in priced if r['affected_pool_tx']];summary.append({'address':a,'context_transactions':len(rows),'joint_priced_pool_trade_rows':sum(r['joint_reference_trade_edge_USD'] is not None for r in rows),'joint_priced_pool_reference_edge_USD':str(sum((Decimal(r['joint_reference_trade_edge_USD']) for r in rows if r['joint_reference_trade_edge_USD'] is not None),Decimal(0))),'simple_ETH_stable_trades':len(simple),'ETH_sells':sum(r['direction']=='sell_ETH' for r in simple),'ETH_buys':sum(r['direction']=='buy_ETH' for r in simple),'priced_simple_trades':len(priced),'simple_reference_gross_USD':str(sum((Decimal(r['reference_gross_USD']) for r in priced),Decimal(0))),'own_gas_USD':str(sum((Decimal(r['own_gas_USD']) for r in priced),Decimal(0))),'simple_reference_net_USD':str(sum((Decimal(r['reference_net_after_own_gas_USD']) for r in priced),Decimal(0))),'affected_pool_priced_trades':len(impacted),'affected_pool_reference_net_USD':str(sum((Decimal(r['reference_net_after_own_gas_USD']) for r in impacted),Decimal(0))),'limit':'All 3311 available raw blocks scanned for this address, including external senders. Reference-price trade edge, not historical cost-basis or offchain-hedged PnL. Token/liquidity/debt contexts remain listed, not silently treated as simple ETH trade profit.'})
    (p/'named_address_profiles.json').write_text(json.dumps({'rows_by_address':by,'summary':summary},indent=2));print(json.dumps(summary[:8],indent=2))
if __name__=='__main__':run()
