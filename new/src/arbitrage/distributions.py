"""Resolve pool-surplus gaps into NET external address settlements, not outgoing sums.
Flash principal in/out cancels; native direct fee-recipient payment is kept separate.
"""
import json
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows,DEPOSIT,WITHDRAWAL
from src.decoding.events import transfer,integer,WETH
getcontext().prec=90
E=Decimal(10)**18

def run():
    p=ROOT/'data/processed/mev_full_window';allrows=json.loads((p/'strategy_accounts_v4.json').read_text());units=[r for r in allrows if r['status']=='pool_closed_cycle_distribution_or_cost_gap'];engine=Reconstruction(ROOT.parent/'research',False);blocks=defaultdict(list);acc={}
    for u in units:
        uid=u['unit_id'];acc[uid]={'unit':u,'net':defaultdict(int),'flows':[]}
        for tx in u['transaction_evidence']:blocks[tx['block']].append((uid,tx['tx_hash']))
    for n,items in sorted(blocks.items()):
        head,rs,tr,paths=engine.block(n);fee=head['miner'].lower()
        for uid,h in items:
            s=acc[uid];u=s['unit'];boundary=set(u['boundary']);pools={k.split(':')[0] for k in u['distinct_pool_keys']};r=rs[h];wrap=[];fee_log_indices={f['log_index'] for ip in u.get('indirect_fee_paths',[]) if ip['tx_hash']==h for f in ip['transfer_logs']}
            for l in r['logs']:
                ts=l.get('topics',[])
                if l['address'].lower()==WETH and len(ts)==2 and ts[0].lower() in [DEPOSIT,WITHDRAWAL]:wrap.append((ts[0].lower(),'0x'+ts[1][-40:].lower(),integer(l['data'])))
                f=transfer(l)
                if not f or f['token']!=WETH or f['log_index'] in fee_log_indices:continue
                if (f['sender'] in boundary)==(f['recipient'] in boundary):continue
                outgoing=f['sender'] in boundary;outside=f['recipient'] if outgoing else f['sender']
                if outside in pools:continue
                amount=int(f['amount_raw'])*(1 if outgoing else -1);s['net'][outside]+=amount;s['flows'].append({'tx_hash':h,'asset':'WETH','counterparty':outside,'direction':'out' if outgoing else 'in','amount_raw':f['amount_raw'],'event_location':'log:'+str(f['log_index']),'fee_recipient_match':outside==fee,'evidence':paths['receipts']})
            for f in native_flows(tr[h]):
                if (f['sender'] in boundary)==(f['recipient'] in boundary):continue
                outgoing=f['sender'] in boundary;outside=f['recipient'] if outgoing else f['sender'];inside=f['sender'] if outgoing else f['recipient'];amount=int(f['amount_raw'])
                if outside in pools:continue
                if outgoing and outside==fee:continue  # Already in separately observed native direct payment.
                if outside==WETH and (DEPOSIT if outgoing else WITHDRAWAL,inside,amount) in wrap:continue
                s['net'][outside]+=amount*(1 if outgoing else -1);s['flows'].append({'tx_hash':h,'asset':'ETH','counterparty':outside,'direction':'out' if outgoing else 'in','amount_raw':str(amount),'event_location':'trace:'+str(f['trace_address']),'fee_recipient_match':outside==fee,'evidence':paths['traces']})
        engine.cache.clear()
    results=[]
    for s in acc.values():
        u=s['unit'];net=sum(s['net'].values());gap=Decimal(u['pool_surplus_minus_operational_gross_ETH']);difference=gap-Decimal(net)/E;results.append({'unit_id':u['unit_id'],'sender':u['sender'],'included_transactions':u['included_transactions'],'target_hashes':u['target_hashes'],'pool_WETH_surplus_ETH':u['pool_WETH_surplus_ETH'],'net_retained_operational_ETH':u['net_joint_boundary_ETH'],'gas_ETH':u['gas_ETH'],'native_direct_fee_recipient_ETH':u['direct_fee_recipient_ETH'],'indirect_or_WETH_fee_recipient_ETH':u.get('indirect_fee_recipient_ETH','0'),'surplus_gap_ETH':str(gap),'observed_net_external_settlements_ETH':str(Decimal(net)/E),'unexplained_difference_ETH':str(difference),'all_gap_reconciled':difference==0,'address_net_settlements_ETH':{a:str(Decimal(v)/E) for a,v in s['net'].items() if v},'flows':s['flows'],'interpretation':'Actual address settlements, not automatic tips, common ownership, or all-in beneficiary profits. Negative counterparty amounts are net financing/incoming flows. Native direct fee recipient is separately counted once; WETH fee-recipient transfers remain explicit.'})
    (p/'external_distributions.json').write_text(json.dumps(results,indent=2));summary={'units_audited':len(results),'exact_gap_reconciliations':sum(r['all_gap_reconciled'] for r in results),'unresolved_units':sum(not r['all_gap_reconciled'] for r in results),'largest_reconciled_gaps_ETH':sorted([r['surplus_gap_ETH'] for r in results if r['all_gap_reconciled']],key=Decimal,reverse=True)[:5]};(p/'distribution_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
