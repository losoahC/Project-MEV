"""Compare Bitquery trade-leg margins with full address cashflows.
Exact observed pool transfers are retained; sale proceeds are never called profit.
"""
import json
from collections import defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.inventory_profiles import NAMED
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.accounting import native_flows
from src.decoding.events import transfer,integer,WETH,USDT,USDC
from src.decoding.extended_events import extended_swap

def run():
    p=ROOT/'data/processed/mev_full_window';named=set(NAMED[:8]);jobs=defaultdict(list)
    for line in (p/'named_full_window_ledger.jsonl').open():
        r=json.loads(line)
        if set(r['single_address_asset_deltas'])&named:jobs[r['block']].append(r)
    engine=Reconstruction(ROOT.parent/'research',False);book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']};rows=[]
    hyper=json.loads((ROOT/'data/raw/public_http/hyperliquid-bd527d70fa19394323bbf19f9c8994e7ff67d605916faaf2bc02337467d5fcef.json').read_text());hb={r['t']//1000:r for r in hyper['response']};main={'0x4e68ccd3e89f51c3074ca5072bbac773960dfa36','0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'}
    for n,leads in sorted(jobs.items()):
        head,rs,tr,paths=engine.block(n);ts=integer(head['timestamp']);ep=book.price('ETH',ts);same=book.bars.get(('Coinbase','ETH',ts//60*60));hbar=hb.get(ts//900*900)
        for lead in leads:
            h=lead['tx_hash'];rc=rs[h];ev=[e for l in rc['logs'] if (e:=extended_swap(l))];pools={e['pool'] for e in ev if not e['protocol'].startswith('V4')};net=defaultdict(lambda:defaultdict(int));flows=[f for l in rc['logs'] if (f:=transfer(l))]+native_flows(tr[h])
            for f in flows:
                if f['sender'] in pools:net[f['sender']][f['token']]+=int(f['amount_raw'])
                if f['recipient'] in pools:net[f['recipient']][f['token']]-=int(f['amount_raw'])
            for e in ev:
                if e['protocol'].startswith('V4') and e['pool_key'] in keys:
                    k=keys[e['pool_key']]
                    for i in [0,1]:
                        token=k[f'currency{i}'];token='native:eth' if int(token,16)==0 else token;net[e['pool_key']][token]+=int(e[f'amount{i}_raw'])
            for pool,raw in net.items():
                eth=raw.get(WETH,0)+raw.get('native:eth',0);stable={t:v for t,v in raw.items() if t in [USDT,USDC] and v};other={t:v for t,v in raw.items() if v and t not in [WETH,'native:eth',USDT,USDC]}
                if not eth or not stable or other:continue
                stable_face=sum((Decimal(v)/10**6 for v in stable.values()),Decimal(0));eq=Decimal(eth)/10**18;prior=stable_face+eq*ep[0] if ep else None;current=stable_face+eq*Decimal(same['close']) if same and not same['conflicting'] else None;low=stable_face+eq*Decimal(hbar['h' if eq<0 else 'l']) if hbar else None;high=stable_face+eq*Decimal(hbar['l' if eq<0 else 'h']) if hbar else None
                rows.append({'tx_hash':h,'etherscan':'https://etherscan.io/tx/'+h,'block':n,'timestamp':ts,'named_addresses':sorted(set(lead['single_address_asset_deltas'])&named),'root_sender':lead['sender'],'pool_key':pool,'main_UniV3_ETH_stable_pool':pool in main,'direction':'sell_ETH' if eth<0 and stable_face>0 else 'buy_ETH' if eth>0 and stable_face<0 else 'mixed','pool_to_trader_net_raw':{t:str(v) for t,v in raw.items() if v},'ETH_quantity_delta':str(eq),'stablecoin_face_quantity_delta':str(stable_face),'trade_leg_margin_prior_Coinbase_stable_at_1_USD':str(prior) if prior is not None else None,'trade_leg_margin_same_minute_Coinbase_stable_at_1_USD':str(current) if current is not None else None,'same_15minute_Hyperliquid_low_margin_USD':str(low) if low is not None else None,'same_15minute_Hyperliquid_high_margin_USD':str(high) if high is not None else None,'swap_event_count_same_pool':sum(e['pool_key']==pool for e in ev),'actual_gas_ETH':str(Decimal(integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']))/10**18),'actual_fee_recipient':head['miner'].lower(),'evidence':paths,'meaning':'Pool-leg reference margin only. Costs apply once per transaction, not once per pool. Hyperliquid 15m high/low sensitivity contains possible minute marks; it is not exact historical 1m replication. Named address involvement does not assign this entire leg to address profit.'})
        engine.cache.clear()
    summary=[]
    for a in NAMED[:8]:
        for scope in ['all_ETH_stable_pool_legs','main_two_pools']:
            for phase in ['all_directions','sell_ETH','buy_ETH']:
                rr=[r for r in rows if a in r['named_addresses'] and (scope=='all_ETH_stable_pool_legs' or r['main_UniV3_ETH_stable_pool']) and (phase=='all_directions' or r['direction']==phase)]
                total=lambda field:str(sum((Decimal(r[field]) for r in rr if r[field] is not None),Decimal(0))) if all(r[field] is not None for r in rr) else None
                summary.append({'address':a,'scope':scope,'phase':phase,'unique_transactions':len({r['tx_hash'] for r in rr}),'pool_legs':len(rr),'swap_events':sum(r['swap_event_count_same_pool'] for r in rr),'prior_Coinbase_stable_1_margin_USD':total('trade_leg_margin_prior_Coinbase_stable_at_1_USD'),'same_minute_Coinbase_stable_1_margin_USD':total('trade_leg_margin_same_minute_Coinbase_stable_at_1_USD'),'Hyperliquid_15m_low_bound_USD':total('same_15minute_Hyperliquid_low_margin_USD'),'Hyperliquid_15m_high_bound_USD':total('same_15minute_Hyperliquid_high_margin_USD')})
    result={'rows':rows,'summary':summary,'Hyperliquid_1minute_request_result':[],'Hyperliquid_15minute_evidence':'data/raw/public_http/hyperliquid-bd527d70fa19394323bbf19f9c8994e7ff67d605916faaf2bc02337467d5fcef.json','exact_Bitquery_reproduction':False};(p/'named_pool_edge_comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps([r for r in summary if r['scope']=='main_two_pools' and r['phase']=='sell_ETH'],indent=2))
if __name__=='__main__':run()
