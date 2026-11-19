"""Account for the complete observable pool surplus distribution, without ownership merges.
Includes callbacks, native/WETH conversions, gas, and canonical V4 ERC-6909 claims.
"""
import json,csv
from collections import defaultdict
from decimal import Decimal
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows,DEPOSIT,WITHDRAWAL
from src.decoding.events import transfer,integer,WETH
from src.decoding.extended_events import extended_swap
MANAGER='0x000000000004444c5dc75cb358380d2e3de08a90'
ZERO='0x'+'0'*40
CLAIM='0x'+Web3.keccak(text='Transfer(address,address,address,uint256,uint256)').hex().removeprefix('0x')
E=Decimal(10)**18

def claim_event(log):
    ts=log.get('topics',[])
    if log['address'].lower()!=MANAGER or len(ts)!=4 or ts[0].lower()!=CLAIM or len(log['data'])!=130:return None
    w=[log['data'][i:i+64] for i in [2,66]];cid=int(ts[3],16);assert cid<2**160
    return {'manager':MANAGER,'caller':'0x'+w[0][-40:].lower(),'sender':'0x'+ts[1][-40:].lower(),'recipient':'0x'+ts[2][-40:].lower(),'currency':'native:eth' if cid==0 else '0x'+hex(cid)[2:].rjust(40,'0'),'amount_raw':str(int(w[1],16)),'log_index':integer(log['logIndex'])}

def transaction_ledger(head,receipt,traces,keys):
    cash=defaultdict(int);claims=defaultdict(int);events=[];liability=0;normal=set();v4delta=0;details=[]
    for l in receipt['logs']:
        f=transfer(l)
        if f and f['token']==WETH:cash[f['sender']]-=int(f['amount_raw']);cash[f['recipient']]+=int(f['amount_raw'])
        ts=l.get('topics',[])
        if l['address'].lower()==WETH and len(ts)==2 and ts[0].lower() in [DEPOSIT,WITHDRAWAL]:cash['0x'+ts[1][-40:].lower()]+=integer(l['data'])*(1 if ts[0].lower()==DEPOSIT else -1)
        ev=extended_swap(l)
        if ev:
            if ev['protocol'].startswith('V4'):
                if ev['pool']!=MANAGER or ev['pool_key'] not in keys:raise ValueError('Unknown V4 settlement')
                k=keys[ev['pool_key']]
                for side in [0,1]:
                    if k[f'currency{side}'] in [ZERO,WETH]:v4delta+=int(ev[f'amount{side}_raw'])
            else:normal.add(ev['pool'])
        c=claim_event(l)
        if c:
            events.append(c)
            if c['currency'] in ['native:eth',WETH]:
                amount=int(c['amount_raw'])
                if c['sender']!=ZERO:claims[c['sender']]-=amount
                else:liability+=amount
                if c['recipient']!=ZERO:claims[c['recipient']]+=amount
                else:liability-=amount
    for f in native_flows(traces):cash[f['sender']]-=int(f['amount_raw']);cash[f['recipient']]+=int(f['amount_raw']);details.append(f)
    # The wrapper reserve backs WETH claims; counting both doubles mint/burn backing.
    cash.pop(WETH,None);resource=-sum(cash.pop(pool,0) for pool in normal)+v4delta
    # Manager backing of claims is a liability, not an extra receiver profit.
    cash[MANAGER]+=v4delta-liability
    gas=integer(receipt['gasUsed'])*integer(receipt['effectiveGasPrice']);burn=integer(receipt['gasUsed'])*integer(head['baseFeePerGas']);priority=gas-burn;sender=receipt['from'].lower();fee=head['miner'].lower();cash[sender]-=gas;cash[fee]+=priority
    assert sum(cash.values())+sum(claims.values())+burn==resource
    return {'cash':dict(cash),'claims':dict(claims),'resource':resource,'burn':burn,'priority':priority,'gas':gas,'fee_recipient':fee,'normal_pools':sorted(normal),'claim_events':events,'native_flows':details,'v4_trader_delta_raw':str(v4delta),'v4_claim_backing_liability_delta_raw':str(liability)}

def run():
    p=ROOT/'data/processed/mev_full_window';units=[r for r in json.loads((p/'strategy_accounts_v4.json').read_text()) if r['status']=='pool_closed_cycle_distribution_or_cost_gap'];keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']};engine=Reconstruction(ROOT.parent/'research',False);byblock=defaultdict(list);state={u['unit_id']:{'cash':defaultdict(int),'claims':defaultdict(int),'resource':0,'burn':0,'gas':0,'priority':0,'receivers':set(),'txs':[],'errors':[]} for u in units}
    for u in units:
        for tx in u['transaction_evidence']:byblock[tx['block']].append((u,tx['tx_hash']))
    for n,jobs in sorted(byblock.items()):
        head,rs,tr,paths=engine.block(n)
        for u,h in jobs:
            s=state[u['unit_id']]
            try:
                x=transaction_ledger(head,rs[h],tr[h],keys)
                for k in ['cash','claims']:
                    for a,v in x[k].items():s[k][a]+=v
                for k in ['resource','burn','gas','priority']:s[k]+=x[k]
                s['receivers'].add(x['fee_recipient']);s['txs'].append({'tx_hash':h,'block':n,'evidence':paths,'claim_events':x['claim_events'],'native_flows':x['native_flows'],'v4_trader_delta_raw':x['v4_trader_delta_raw'],'v4_claim_backing_liability_delta_raw':x['v4_claim_backing_liability_delta_raw']})
            except Exception as ex:s['errors'].append({'tx_hash':h,'error':repr(ex)})
        engine.cache.clear()
    results=[];flat=[]
    for u in units:
        s=state[u['unit_id']];addresses=[]
        for a in sorted(set(s['cash'])|set(s['claims'])):
            cash=s['cash'].get(a,0);claim=s['claims'].get(a,0)
            if not cash and not claim:continue
            role='original operational boundary' if a in u['boundary'] else 'actual block fee recipient' if a in s['receivers'] else 'V4 manager non-swap reserve/hook component' if a==MANAGER else 'actual external receiver or financier; beneficial owner unassigned'
            row={'unit_id':u['unit_id'],'address':a,'role':role,'cash_ETH_WETH_delta':str(Decimal(cash)/E),'V4_underlying_ETH_WETH_claim_delta':str(Decimal(claim)/E),'combined_ETH_WETH_delta_after_gas':str(Decimal(cash+claim)/E),'in_original_boundary':a in u['boundary'],'is_actual_fee_recipient':a in s['receivers']};addresses.append(row);flat.append(row)
        expected=Decimal(u['pool_WETH_surplus_ETH']);computed=Decimal(s['resource'])/E;total=(sum(s['cash'].values())+sum(s['claims'].values())+s['burn']);ok=not s['errors'] and total==s['resource'] and computed==expected;results.append({'unit_id':u['unit_id'],'included_transactions':u['included_transactions'],'target_hashes':u['target_hashes'],'original_boundary':u['boundary'],'pool_surplus_ETH':str(expected),'recomputed_resource_ETH':str(computed),'pool_resource_difference_ETH':str(expected-computed),'burn_ETH':str(Decimal(s['burn'])/E),'gas_ETH':str(Decimal(s['gas'])/E),'priority_ETH':str(Decimal(s['priority'])/E),'all_observable_ETH_WETH_distribution_reconciled':ok,'address_changes':addresses,'transactions':s['txs'],'errors':s['errors'],'interpretation':'Complete signed observed ETH/WETH/6909-claim redistribution of pool surplus. Negative financing and operating costs remain signed. No receiver is silently merged into bot ownership; a claim is not native cash and a public reserve change is not a named LP wallet profit.'})
    summary={'previous_gap_units':len(results),'fully_reconciled':sum(r['all_observable_ETH_WETH_distribution_reconciled'] for r in results),'still_not_reconciled':sum(not r['all_observable_ETH_WETH_distribution_reconciled'] for r in results),'units_with_6909_claims':sum(any(t['claim_events'] for t in r['transactions']) for r in results),'actual_receiver_rows':len(flat),'original_boundaries_not_expanded':True};(p/'complete_pool_surplus_distributions.json').write_text(json.dumps({'summary':summary,'rows':results,'source':'https://raw.githubusercontent.com/Uniswap/v4-core/main/src/ERC6909.sol'},indent=2))
    with (ROOT/'reports/mev_expansion/完整池收益逐地址分配.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print(json.dumps(summary,indent=2));print([(r['unit_id'],r['pool_resource_difference_ETH'],r['errors']) for r in results if not r['all_observable_ETH_WETH_distribution_reconciled']][:10])
if __name__=='__main__':run()
