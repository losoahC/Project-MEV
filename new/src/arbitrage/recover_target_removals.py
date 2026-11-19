"""Resolve archived failed simulations with explicit nonce-continuity interventions."""
import json,copy,time
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.victim_replay import request
from src.arbitrage.accounting import token_net
from src.arbitrage.replay_audit import NATIVE
from src.decoding.events import integer,WETH
from src.ingestion.evidence import read_json

def run():
    p=ROOT/'data/processed/mev_full_window';old=json.loads((p/'batch_target_removal_audit.json').read_text());engine=Reconstruction(ROOT.parent/'research',False);rows=[]
    for lead in old['rows']:
        if lead['status']!='actual_prefix_verified_counterfactual_response_error':continue
        n=lead['block'];head,rs,tr,paths=engine.block(n);target=lead['removed_target'];sender=rs[target]['from'].lower();h=lead['actor'];doc=read_json(ROOT/lead['evidence']['remove_target']);params=copy.deepcopy(doc['request']['params']);calls=params[0]['blockStateCalls'][0]['calls'];row={'block':n,'actor':h,'removed_target':target,'original_evidence':lead['evidence'],'accounts':lead['accounts'],'boundary_includes_public_service':lead['boundary_includes_public_service'],'nonce_reassigned_sender':sender}
        if any(not c.get('to') for c in calls if c['from'].lower()==sender):row['status']='CREATE_dependency_excluded';rows.append(row);continue
        for c in calls:
            if c['from'].lower()==sender:c.pop('nonce',None)
        fresh,src=request(params);row['fresh_evidence']=src;res=fresh.get('response',{}).get('result')
        if not res:
            error=fresh.get('response',fresh.get('transport_error'));message=str(error)
            row.update(status='verified_intervention_funding_infeasible' if 'insufficient funds for gas * price + value' in message else 'fresh_response_error',error=error)
        else:
            sim=res[0]['calls'][-1];assert len(res[0]['calls'])==len(calls);accounts=set(lead['accounts']);raw=token_net(sim,accounts);eth=raw.pop(WETH,0)+raw.pop(NATIVE,0)-integer(sim['gasUsed'])*integer(rs[h]['effectiveGasPrice']);row.update(status='verified_nonce_continuity_target_removal',actor_counterfactual_status=integer(sim['status']),counterfactual_net_ETH=str(Decimal(eth)/10**18),actual_net_ETH=lead['scenarios']['actual']['net_joint_ETH'],actual_minus_counterfactual_ETH=str(Decimal(lead['scenarios']['actual']['net_joint_ETH'])-Decimal(eth)/10**18),other_counterfactual_asset_raw={t:str(v) for t,v in raw.items() if v},error=sim.get('error'))
        row['meaning']='Original actual prefix already reproduced status/gas/logs. Recovery removes the target and only reassigns remaining sender nonces; signed transactions are not rebroadcast. Not a victim-loss estimate or a continuous event counterfactual.';rows.append(row);engine.cache.clear();time.sleep(1.1);print(n,row['status'],flush=True)
    (p/'recovered_target_removals.json').write_text(json.dumps({'original_response_errors':len(rows),'recovered':sum(r['status']=='verified_nonce_continuity_target_removal' for r in rows),'funding_infeasible_after_target_removal':sum(r['status']=='verified_intervention_funding_infeasible' for r in rows),'unexplained_transport_or_execution_errors':sum(r['status']=='fresh_response_error' for r in rows),'rows':rows},indent=2))
if __name__=='__main__':run()
