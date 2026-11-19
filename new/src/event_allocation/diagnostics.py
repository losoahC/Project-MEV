"""Controls, disjoint unassigned costs and evidence-based MEV classifications."""
import json,gzip,csv
from collections import defaultdict,Counter
from decimal import Decimal
from src.event_allocation.config import ROOT,OUT,REPORT,START,END
from src.event_allocation.quotes import Quotes
from src.event_allocation.allocate import Pools
from src.arbitrage.tron_collect import encode_addr

def display_address(chain,address):return encode_addr(address) if chain=='tron' and address.startswith('41') and len(address)==42 else address

def run():
    q=Quotes();pools=Pools();costs=[];by=defaultdict(lambda:{'cost':Decimal(0),'transactions':0,'missing':0});control=defaultdict(lambda:{'transactions':0,'fee_priced_component_USD':Decimal(0)});actual_sender=defaultdict(lambda:{'raw':defaultdict(int),'priced_USD':Decimal(0),'unpriced_rows':0});actual_addresses=defaultdict(lambda:{'raw':defaultdict(int),'priced_USD':Decimal(0),'unpriced_rows':0,'asset_rows':0,'position_risk_rows':0});source=json.loads((OUT/'tron_failed_costs.json').read_text());route={r['tx_hash']:r['same_entrypoint_as_successful_pool_trade'] for r in source};counts=Counter()
    for chain in ['ethereum','tron']:
        with gzip.open(OUT/(chain+'_journal.jsonl.gz'),'rt') as f:
            for line in f:
                r=json.loads(line);native='native:eth' if chain=='ethereum' else 'native:trx';gross_raw=int(r['gas_raw'])+int(r['blob_burn_raw']);fee=q.value(native,gross_raw,r['timestamp']);cat=r['association'];k=(chain,cat);control[k]['transactions']+=1;control[k]['fee_priced_component_USD']+=fee or 0
                a=actual_sender[chain,r['sender']]
                for e in r['entries']:
                    v=q.value(e['asset'],e['raw'],r['timestamp']);phase='primary_transaction_full_execution_context' if cat in ['target','after_prior_target','failed_attempt_after_target'] else 'control_or_unassigned_context';aa=actual_addresses[chain,e['address'],phase];aa['raw'][e['asset']]+=int(e['raw']);aa['asset_rows']+=1;aa['position_risk_rows']+=bool(r['position_risks'])
                    if v is not None:aa['priced_USD']+=v
                    else:aa['unpriced_rows']+=1
                    if e['address']==r['sender']:
                        a['raw'][e['asset']]+=int(e['raw'])
                        if v is not None:a['priced_USD']+=v
                        else:a['unpriced_rows']+=1
                if cat not in ['same_operator_failed_context_unassigned','same_block_failed_order_unassigned']:continue
                net_raw=gross_raw-(int(r['priority_raw']) if chain=='ethereum' and r['sender']==r['fee_recipient'] else 0);net_fee=q.value(native,net_raw,r['timestamp']);eligible=chain=='ethereum' or route.get(r['tx_hash'],False);costs.append({'chain':chain,'tx_hash':r['tx_hash'],'operating_address':r['sender'],'timestamp':r['timestamp'],'association':cat,'same_entrypoint_cost_sensitivity_eligible':eligible,'actual_receipt_gross_fee_raw':str(gross_raw),'actual_net_external_fee_raw':str(net_raw),'actual_fee_USD':str(net_fee) if net_fee is not None else None,'included_in_primary_budget':False,'reason':'Same-operator route context, or same-block ordering unknown; not charged as proven incident cost. Broad cost sensitivity only. Priority received by the same sender is internal.','evidence':r['evidence']})
                if eligible:b=by[chain,r['sender']];b['transactions']+=1;b['cost']+=net_fee or 0;b['missing']+=net_fee is None
    ops=json.loads((OUT/'all_operating_addresses.json').read_text());opkeys={(r['chain'],r['operating_address']) for r in ops}
    for key,b in by.items():
        if key not in opkeys:ops.append({'chain':key[0],'operating_address':key[1],'transactions':0,'gross_priced_USD':'0','net_priced_USD':'0','fee_priced_USD':'0','unpriced_transactions':0,'fully_priced_positive':0,'fully_priced_negative':0})
    for r in ops:
        r['operating_address_display']=display_address(r['chain'],r['operating_address'])
        b=by[r['chain'],r['operating_address']];a=actual_sender[r['chain'],r['operating_address']];r.update(unassigned_same_entrypoint_failed_transactions=b['transactions'],unassigned_failed_cost_priced_USD=str(b['cost']),broad_cost_sensitivity_incident_leg_net_priced_USD=str(Decimal(r['net_priced_USD'])-b['cost']),actual_gas_owner_only_marked_change_in_audited_transactions_USD=str(a['priced_USD']),actual_gas_owner_unpriced_asset_rows=a['unpriced_rows'],actual_gas_owner_asset_vector_raw={k:str(v) for k,v in a['raw'].items() if v},interpretation='Incident-pool leg margin minus onchain costs, using gas-paying address convention. Actual gas-owner change is separate. Neither column is full historical inventory/firm profit. Unassigned failed costs are sensitivity only; not charged twice to primary.')
    (OUT/'all_operating_addresses_with_cost_sensitivity.json').write_text(json.dumps(ops,indent=2));fields=[k for k,v in ops[0].items() if not isinstance(v,(dict,list))]
    with (REPORT/'all_operating_addresses.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(ops)
    (OUT/'unassigned_failed_costs.json').write_text(json.dumps(costs,indent=2));controls=[{'chain':k[0],'association':k[1],**{f:str(v) if isinstance(v,Decimal) else v for f,v in r.items()}} for k,r in control.items()];(OUT/'controls_and_costs.json').write_text(json.dumps(controls,indent=2))
    address_rows=[{'chain':key[0],'actual_address':key[1],'actual_address_display':display_address(key[0],key[1]),'scope':key[2],'priced_asset_and_known_position_change_USD':str(v['priced_USD']),'unpriced_asset_rows':v['unpriced_rows'],'asset_rows':v['asset_rows'],'position_risk_rows':v['position_risk_rows'],'raw_net_vector':{a:str(raw) for a,raw in v['raw'].items() if raw},'interpretation':'Actual signed address changes across complete transaction routes, not the incident-leg reference budget. Includes all visible counterparties and identified principal adjustments. No assertion of historical cost, beneficial ownership or causal profit.'} for key,v in actual_addresses.items()];address_rows.sort(key=lambda r:Decimal(r['priced_asset_and_known_position_change_USD']),reverse=True);(OUT/'actual_all_counterparties.json').write_text(json.dumps(address_rows,indent=2))
    with (REPORT/'actual_all_counterparties.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(address_rows[0]));w.writeheader()
        for r in address_rows:w.writerow(r|{'raw_net_vector':json.dumps(r['raw_net_vector'],separators=(',',':'))})
    units=json.loads((ROOT/'data/processed/mev_full_window/strategy_accounts_v4.json').read_text());closed=[u for u in units if u['status']=='verified_cashflow_and_pool_closed_positive_cycle'];included=[];unique_txs=set()
    for u in closed:
        txs=[r for r in u['transaction_evidence'] if START<=r['timestamp']<END] if u['transaction_evidence'] and 'timestamp' in u['transaction_evidence'][0] else u['transaction_evidence'];hashes=[r['tx_hash'] for r in txs];unique_txs.update(hashes);included.append({'unit_id':u['unit_id'],'sender':u['sender'],'transactions':hashes,'net_ETH_WETH':u['net_joint_boundary_ETH'],'criterion':'Actual multi-pool asset closure, matched underlying asset cashflow and positive joint boundary after gas/direct identified block fees. Association with a target is separate from causal MEV.','evidence':'data/processed/mev_full_window/strategy_accounts_v4.json'})
    mev={'criteria':[{'label':'verified_closed_multi_pool_arbitrage','criterion':'Actual distinct-pool route plus matched positive closed assets after observed onchain costs. High gas is not the criterion.','can_claim':'Observed arbitrage surplus on the stated operational boundary; no common-beneficial-owner assertion.'},{'label':'inventory_sale_reference_edge','criterion':'Signed incident-pool swap delta marked at frozen market prices, less observed cost once.','can_claim':'Reference execution margin only; no historical acquisition/hedge cost or causal MEV certification.'},{'label':'priority_or_direct_block_payment','criterion':'Actual gas priority or actual trace/claim payment to block recipient.','can_claim':'Ordering/auction payment evidence; a payment alone does not prove arbitrage, frontrunning or sandwiching.'},{'label':'target_association','criterion':'Same authenticated pool/PoolId, after first monitored target, within the common window. Before-target activity stays control.','can_claim':'Association only; organic trading can remain.'},{'label':'causal_execution_effect','criterion':'Historical-state replay comparing actual execution with removal/reordering of specified front legs; report feasibility, failures and unique targets.','can_claim':'Only the tested replay increment under its assumptions; not whole-event MEV.'}],'existing_closed_units_for_separate_evidence':len(closed),'overlap_rule':'Existing closed-cycle and replay catalogues are annotations, not extra rows added to the unified budget.','closed_cycle_units':included,'all_event_market_margin_is_causal_MEV':False}
    (OUT/'mev_criteria_and_evidence.json').write_text(json.dumps(mev,indent=2));print(json.dumps({'control_rows':len(controls),'unassigned_failed_cost_transactions':len(costs),'cost_sensitive_operating_addresses':len(ops),'existing_verified_closed_units':len(closed)},indent=2))
if __name__=='__main__':run()
