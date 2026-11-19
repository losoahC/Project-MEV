"""Full 12841-candidate event paths, per-unit standards, and flat review tables."""
import json,csv
from collections import defaultdict,Counter
from decimal import Decimal
from src.arbitrage.discover import ROOT

def run():
    p=ROOT/'data/processed/mev_full_window';out=ROOT/'reports/mev_expansion';candidates=json.loads((p/'candidates.json').read_text());meta={r['pool']:r for r in json.loads((p/'pool_metadata_full.json').read_text())};keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']};registry=json.loads((ROOT/'data/processed/historical_pricebook.json').read_text())['registry'];units=json.loads((p/'strategy_accounts_v4.json').read_text());profits={r['unit_id']:r for r in json.loads((p/'terminal_cycle_profits.json').read_text())};txunit={h:r['unit_id'] for r in units for h in r['included_transactions']};routes={};flat=[]
    def asset(t,n):
        m=registry.get(t,{});d=18 if t=='native:eth' else m.get('decimals');return {'address':t,'raw':str(n),'symbol':'ETH' if t=='native:eth' else m.get('symbol'),'decimals':d,'quantity':str(Decimal(n)/Decimal(10)**d) if d is not None else None,'metadata_basis':m.get('decimal_basis')}
    for c in candidates:
        steps=[]
        for ev in sorted(c['events'],key=lambda x:x['log_index']):
            isv4=ev['protocol'].startswith('V4');m=keys.get(ev['pool_key'],{}) if isv4 else meta.get(ev['pool'],{});identity=bool(m) if isv4 else bool(m.get('factory_lookup_matches_pool'));dex='Uniswap V4' if isv4 and ev['pool']=='0x000000000004444c5dc75cb358380d2e3de08a90' else m.get('dex_name');inputs=[];outputs=[]
            for side in [0,1]:
                t=m.get(('currency' if isv4 else 'token')+str(side));raw=int(ev[f'amount{side}_raw']);raw=-raw if isv4 else raw
                if t and int(t,16)==0:t='native:eth'
                if t and raw:(inputs if raw>0 else outputs).append(asset(t,abs(raw)))
            step={'number':len(steps)+1,'log_index':ev['log_index'],'pool':ev['pool'],'pool_key':ev['pool_key'],'DEX':dex,'identity_verified':identity,'factory':m.get('factory'),'fee_pips':m.get('fee_pips',m.get('fee')),'hooks':m.get('hooks'),'protocol_event':ev['protocol'],'inputs':inputs,'outputs':outputs,'original_event':ev,'metadata_evidence':m.get('sources',m.get('evidence'))};steps.append(step)
            flat.append({'tx_hash':c['tx_hash'],'unit_id':txunit[c['tx_hash']],'block':c['block'],'step':step['number'],'log_index':step['log_index'],'DEX':dex or 'unnamed','pool_key':step['pool_key'],'identity_verified':identity,'input_assets':json.dumps(inputs,separators=(',',':')),'output_assets':json.dumps(outputs,separators=(',',':'))})
        rounds=[];start=0
        while start<len(steps):
            initial=steps[start];found=False
            if len(initial['inputs'])==len(initial['outputs'])==1:
                path=[initial['inputs'][0]['address']];net=defaultdict(int)
                for end in range(start,len(steps)):
                    step=steps[end]
                    if len(step['inputs'])!=1 or len(step['outputs'])!=1 or step['inputs'][0]['address']!=path[-1]:break
                    for a in step['inputs']:net[a['address']]-=int(a['raw'])
                    for a in step['outputs']:net[a['address']]+=int(a['raw'])
                    path.append(step['outputs'][0]['address'])
                    if path[-1]==path[0]:rounds.append({'first_swap':start+1,'last_swap':end+1,'token_path':path,'pool_net_raw':{t:str(v) for t,v in net.items() if v},'meaning':'Contiguous token-path closure in log order. Not proof of isolated funding, profit or absence of split execution.'});start=end+1;found=True;break
            if not found:start+=1
        routes[c['tx_hash']]={'tx_hash':c['tx_hash'],'unit_id':txunit[c['tx_hash']],'block':c['block'],'index':c['index'],'sender':c['sender'],'executor':c['executor'],'swap_event_count':len(steps),'distinct_pool_keys':len({e['pool_key'] for e in c['events']}),'ordered_swaps':steps,'contiguous_token_path_rounds':rounds,'associations':c['associations'],'classification_from_gas':False,'order_note':'Receipt log order; callbacks may make swap emission order differ from call initiation. Split paths are not forced into one route.'}
    (p/'full_ordered_routes.json').write_text(json.dumps(list(routes.values()),indent=2))
    with (out/'全部候选池路径.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    target_values=json.loads((p/'target_reference_valuations.json').read_text());bytarget=defaultdict(list)
    for value in target_values:bytarget[value['tx_hash']].append({'address':value['address'],'reference_shortfall_USD':value['signed_reference_shortfall_USD'],'complete':value['valuation_complete'],'meaning':'Reference execution shortfall, not MEV causal loss'})
    interventions=json.loads((p/'victim_replays.json').read_text())['rows'];unitrows=[]
    for u in units:
        local=[routes[h] for h in u['candidate_hashes']];links=[a for r in local for a in r['associations']];pr=profits.get(u['unit_id']);standard='跨池正剩余闭合且与边界资金完全衔接' if pr else '未通过完整闭合收益核验，见 status';sameblock=any(a['block_distance']==0 and a['relative_order']=='after' and a['opposite_direction'] for a in links)
        effects=[{'target':r['target'],'removed_front':r['removed_front'],'effects':r['victim_effects'],'meaning':'Conditional fixed-call output effect, not global/equilibrium loss'} for r in interventions if r['removed_front'] in u['included_transactions']]
        mechanism='同sender前后包围结构候选' if u['kind']=='same_sender_bracketing_interval' else '单笔多池闭合套利机制' if pr and len(u['included_transactions'])==1 else '跨交易闭合策略' if pr else '开放库存／仓位／未闭合关联，见status'
        unitrows.append({'mechanism_type':mechanism,'same_pool_before_target_after_structure':u['kind']=='same_sender_bracketing_interval','conditional_front_effect_experiments':len(effects),'unit_id':u['unit_id'],'sender':u['sender'],'boundary':';'.join(u['boundary']),'transactions':';'.join(u['included_transactions']),'target_hashes':';'.join(u['target_hashes']),'status':u['status'],'mechanism_standard':standard,'same_block_after_opposite_target':sameblock,'MEV_causal_attribution':'尚未由此筛选证明；另见逐案执行干预','gas_is_classification_standard':False,'swap_event_count_in_candidate_txs':sum(r['swap_event_count'] for r in local),'distinct_pool_keys':len(u['distinct_pool_keys']),'contiguous_token_path_rounds_in_candidate_txs':sum(len(r['contiguous_token_path_rounds']) for r in local),'net_joint_ETH':u['net_joint_boundary_ETH'],'net_reference_USD':pr['net_reference_USD'] if pr else None,'gas_ETH':u['gas_ETH'],'burn_ETH':u['burn_ETH'],'priority_ETH':u['priority_ETH'],'direct_fee_recipient_ETH':u['direct_fee_recipient_ETH'],'indirect_WETH_fee_recipient_ETH':u.get('indirect_fee_recipient_ETH','0'),'target_reference_shortfalls_not_causal':json.dumps({h:bytarget[h] for h in u['target_hashes']},separators=(',',':')),'conditional_front_removal_effects_not_additive':json.dumps(effects,separators=(',',':')),'all_terminal_asset_raw':json.dumps(pr['terminal_pool_surplus_raw'],separators=(',',':')) if pr else None,'ownership_verified':False})
    with (out/'全部操作单元与判据.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(unitrows[0]));writer.writeheader();writer.writerows(unitrows)
    summary={'candidate_transactions':len(routes),'unit_rows':len(unitrows),'swap_event_rows':len(flat),'all_12249_units_have_explicit_mechanism_standard':True,'gas_used_as_sufficient_MEV_test':False,'unresolved_pool_identity_swap_events':sum(not r['identity_verified'] for r in flat),'protocol_event_counts':dict(Counter(s['protocol_event'] for r in routes.values() for s in r['ordered_swaps'])),'not_all_associations_are_MEV':True};(p/'full_route_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
