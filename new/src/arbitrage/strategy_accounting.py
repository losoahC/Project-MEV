"""Recompute constant-boundary ledgers for disjoint units from original receipts/traces.
Pool-side surplus is checked independently; public routers/managers stay outside.
"""
import json,argparse
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow,native_flows
from src.decoding.events import transfer,integer,WETH
from src.decoding.extended_events import extended_swap
from src.arbitrage.indirect_payments import fee_paths
getcontext().prec=90
E=Decimal(10)**18

def run(include_v4=False):
    p=ROOT/'data/processed/mev_full_window';units=json.loads((p/'strategy_units.json').read_text());byid={u['unit_id']:u for u in units};byblock=defaultdict(list);metapath=p/'pool_metadata_full.json';metas={m['pool']:m for m in json.loads(metapath.read_text())};state={};v4keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']} if include_v4 else {}
    for u in units:
        for tx in u['txs']:byblock[tx['block']].append((u['unit_id'],tx['tx_hash']))
        state[u['unit_id']]={'net':Decimal(0),'gross':Decimal(0),'gas':0,'priority':0,'burn':0,'fee_payment':0,'indirect_fee':0,'indirect_paths':[],'tokens':defaultdict(int),'poolnet':defaultdict(int),'pools':set(),'protocols':Counter(),'unknown_pools':set(),'payouts':[],'tx_evidence':[],'errors':[],'has_v4':False,'unresolved_v4':set(),'v4_hooks':set()}
    engine=Reconstruction(ROOT.parent/'research',False)
    for i,(n,items) in enumerate(sorted(byblock.items()),1):
        head,rs,tr,paths=engine.block(n);base=integer(head['baseFeePerGas'])
        for uid,h in items:
            u=byid[uid];s=state[uid];r=rs[h];boundary=set(u['boundary'])
            try:
                cf=cashflow(r,tr[h],boundary,head['miner']);s['net']+=Decimal(cf['net_after_gas_and_builder_ETH']);s['gross']+=Decimal(cf['gross_after_pool_fees_before_gas_and_builder_ETH']);s['gas']+=int(cf['gas_wei']);s['burn']+=integer(r['gasUsed'])*base;s['priority']+=int(cf['gas_wei'])-integer(r['gasUsed'])*base;s['fee_payment']+=int(cf['identified_builder_payment_wei'])
                for t,v in cf['token_net_raw'].items():s['tokens'][t]+=int(v)
                evs=[e for l in r['logs'] if (e:=extended_swap(l))];pooladdrs={e['pool'] for e in evs if not e['protocol'].startswith('V4')}
                ipaths=fee_paths(r,tr[h],boundary,head['miner'],{e['pool'] for e in evs});indirect=sum(int(x['amount_wei']) for x in ipaths);s['indirect_fee']+=indirect;s['gross']+=Decimal(indirect)/E;s['indirect_paths'].extend({'tx_hash':h,**x} for x in ipaths)
                for e in evs:
                    s['pools'].add(e['pool_key']);s['protocols'][e['protocol']]+=1
                    if e['protocol'].startswith('V4'):
                        s['has_v4']=True;key=v4keys.get(e['pool_key'])
                        if not key or e['pool']!='0x000000000004444c5dc75cb358380d2e3de08a90':s['unresolved_v4'].add(e['pool_key'])
                        else:
                            if int(key['hooks'],16):s['v4_hooks'].add(key['hooks'])
                            for side in [0,1]:
                                token=key[f'currency{side}'];token='native:eth' if int(token,16)==0 else token
                                s['poolnet'][token]+=int(e[f'amount{side}_raw'])
                    elif not (metas.get(e['pool'],{}).get('factory_lookup_matches_pool') or metas.get(e['pool'],{}).get('historical_asset_identity_verified')):s['unknown_pools'].add(e['pool'])
                for l in r['logs']:
                    f=transfer(l)
                    if not f:continue
                    if f['sender'] in pooladdrs:s['poolnet'][f['token']]+=int(f['amount_raw'])
                    if f['recipient'] in pooladdrs:s['poolnet'][f['token']]-=int(f['amount_raw'])
                    if f['sender'] in boundary and f['recipient'] not in boundary and f['recipient'] not in pooladdrs:s['payouts'].append({'tx_hash':h,'asset_kind':'ERC20',**f})
                for f in native_flows(tr[h]):
                    if f['sender'] in boundary and f['recipient'] not in boundary:s['payouts'].append({'tx_hash':h,'asset_kind':'native',**f})
                s['tx_evidence'].append({'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'evidence':paths,'gas_wei':cf['gas_wei'],'net_ETH':cf['net_after_gas_and_builder_ETH'],'other_token_residual_raw':cf['other_token_residual_raw']})
            except Exception as ex:s['errors'].append({'tx_hash':h,'error':str(ex)})
        engine.cache.clear()
        if i%200==0:print('strategy blocks',i,'/',len(byblock),flush=True)
    results=[]
    for u in units:
        s=state[u['unit_id']];other={t:str(v) for t,v in s['tokens'].items() if t!=WETH and v};poolother={t:str(v) for t,v in s['poolnet'].items() if t not in [WETH,'native:eth'] and v};poolprofit=Decimal(s['poolnet'].get(WETH,0)+s['poolnet'].get('native:eth',0))/E
        lending_pools=sorted(p for p in s['pools'] if metas.get(p,{}).get('protocol_risk'))
        clean=not s['errors'] and not u['positions'] and not u['nft_transfers'] and not lending_pools;mechanical=clean and not other and not poolother and (not s['has_v4'] or include_v4 and not s['unresolved_v4'] and not s['v4_hooks']) and not s['unknown_pools'] and len(s['pools'])>=2 and poolprofit>0
        exact_pool_bridge=mechanical and poolprofit==s['gross']
        if exact_pool_bridge and s['net']>0:status='verified_cashflow_and_pool_closed_positive_cycle'
        elif mechanical:status='pool_closed_cycle_distribution_or_cost_gap'
        elif u['positions'] or u['nft_transfers'] or lending_pools:status='position_debt_or_NFT_requires_separate_accounting'
        elif s['has_v4'] and (not include_v4 or s['unresolved_v4'] or s['v4_hooks']):status='V4_settlement_requires_poolId_level_reconstruction'
        elif s['unknown_pools']:status='pool_identity_or_metadata_incomplete'
        elif other:status='open_inventory_requires_valuation_and_history'
        else:status='no_verified_positive_closed_cycle'
        results.append({'unit_id':u['unit_id'],'kind':u['kind'],'sender':u['sender'],'boundary':u['boundary'],'boundary_ownership_verified':False,'excluded_public_entrypoints':u['excluded_public_entrypoints'],'candidate_hashes':u['candidate_hashes'],'included_transactions':[t['tx_hash'] for t in u['txs']],'target_hashes':u['target_hashes'],'status':status,'net_joint_boundary_ETH':str(s['net']),'gross_before_gas_direct_fee_recipient_ETH':str(s['gross']),'indirect_fee_recipient_ETH':str(Decimal(s['indirect_fee'])/E),'indirect_fee_paths':s['indirect_paths'],'gross_field_note':'gross_before_gas_direct_fee_recipient_ETH now also adds strictly verified WETH-to-coinbase helper payments; direct native field stays separate.','gas_ETH':str(Decimal(s['gas'])/E),'priority_ETH':str(Decimal(s['priority'])/E),'burn_ETH':str(Decimal(s['burn'])/E),'direct_fee_recipient_ETH':str(Decimal(s['fee_payment'])/E),'other_token_residual_raw':other,'pool_inventory_residual_nonWETH_raw':poolother,'pool_WETH_surplus_ETH':str(poolprofit) if not s['has_v4'] or include_v4 and not s['unresolved_v4'] else None,'pool_surplus_minus_operational_gross_ETH':str(poolprofit-s['gross']) if not s['has_v4'] or include_v4 and not s['unresolved_v4'] else None,'v4_keys_resolved':not s['unresolved_v4'],'v4_nonzero_hooks':sorted(s['v4_hooks']),'unresolved_v4':sorted(s['unresolved_v4']),'distinct_pool_keys':sorted(s['pools']),'protocol_counts':dict(s['protocols']),'unknown_pools':sorted(s['unknown_pools']),'position_events':u['positions'],'external_payouts':s['payouts'],'errors':s['errors'],'transaction_evidence':s['tx_evidence'],'limit':'Observed constant operational-address boundary, not verified beneficial ownership or global strategy economics. Joint assets can remain in executors; outside-window funding/hedges unresolved. Target association is not causal attribution.'})
    assert sum(len(x['candidate_hashes']) for x in results)==12841
    (p/('strategy_accounts_v4.json' if include_v4 else 'strategy_accounts.json')).write_text(json.dumps(results,indent=2));verified=[r for r in results if r['status']=='verified_cashflow_and_pool_closed_positive_cycle'];summary={'units':len(results),'statuses':dict(Counter(r['status'] for r in results)),'candidate_transactions_covered_once':12841,'verified_positive_cycle_units':len(verified),'verified_cycle_operational_net_ETH':str(sum((Decimal(r['net_joint_boundary_ETH']) for r in verified),Decimal(0))),'interpretation':'Transaction-disjoint, inventory-closed pool bridges only; bounded operational cashflow, not whole-event MEV or ultimate owner profit. Other classes remain fully listed.','whole_event_profit_established':False}
    (p/('strategy_accounting_v4_summary.json' if include_v4 else 'strategy_accounting_summary.json')).write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--v4',action='store_true');a=ap.parse_args();run(a.v4)
