"""Separate observable loan/collateral and liquidity principal from cash profit.
Unrealized shares, interest and ownership are not manufactured from transfer volume.
"""
import json,csv
from collections import defaultdict,Counter
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.decoding.events import integer,signed_word

def decode_position(log,event):
    topics=log['topics'];words=[log['data'][i:i+64] for i in range(2,len(log['data']),64)];topicaddr=lambda i:'0x'+topics[i][-40:].lower();out={'event':event,'emitter':log['address'].lower(),'log_index':integer(log['logIndex']),'topics':topics,'data':log['data'],'kind':'liquidity_or_position_event_raw'}
    if event.startswith(('Supply(','Withdraw(','Borrow(','Repay(')):
        name=event.split('(')[0];assert len(topics)==4;asset=topicaddr(1);owner=topicaddr(2);raw=int(words[1] if name in ['Supply','Borrow'] else words[0],16);out.update(kind='loan_or_collateral_principal',asset=asset,owner=owner,principal_raw=str(raw),collateral_delta_raw=str(raw if name=='Supply' else -raw if name=='Withdraw' else 0),debt_delta_raw=str(raw if name=='Borrow' else -raw if name=='Repay' else 0),note='Event principal only; debt is a liability. Withdrawals release existing assets, not free profit. Interest/index revaluation requires separate position balances.')
    elif event.startswith(('Mint(address,address,int24','Burn(address,int24','Collect(address,address,int24')):
        name=event.split('(')[0];assert len(topics)==4;owner=topicaddr(1);lo=signed_word(topics[2][2:]);hi=signed_word(topics[3][2:]);liq=int(words[1] if name=='Mint' else words[0],16) if name!='Collect' else 0;out.update(kind='concentrated_liquidity_position',owner=owner,tick_lower=lo,tick_upper=hi,liquidity_delta_raw=str(liq if name=='Mint' else -liq if name=='Burn' else 0),note='Liquidity units are distinct from token cashflow. Collect can release prior principal and fees; it is not automatically profit.')
    elif event.startswith('ModifyLiquidity('):
        assert len(topics)==3;out.update(kind='V4_liquidity_position',pool_id=topics[1],owner=topicaddr(2),tick_lower=signed_word(words[0]),tick_upper=signed_word(words[1]),liquidity_delta_raw=str(signed_word(words[2])),salt='0x'+words[3],note='PoolId, owner, range and salt identify liquidity changes. Hook effects are retained in actual transfers and claims.')
    elif event in ['Mint(address,uint256,uint256)','Burn(address,uint256,uint256,address)']:
        out.update(kind='V2_liquidity_principal',amount0_raw=str(int(words[0],16)),amount1_raw=str(int(words[1],16)),note='Underlying liquidity principal; actual LP share mint/burn and token transfers are in the transfer audit. Not trading profit by itself.')
    return out

def run():
    p=ROOT/'data/processed/mev_full_window';units=[r for r in json.loads((p/'strategy_accounts_v4.json').read_text()) if r['status']=='position_debt_or_NFT_requires_separate_accounting'];engine=Reconstruction(ROOT.parent/'research',False);byblock=defaultdict(list);state={r['unit_id']:{'events':[],'principal':defaultdict(lambda:[0,0]),'liquidity':defaultdict(int)} for r in units}
    for u in units:
        txblocks={r['tx_hash']:r['block'] for r in u['transaction_evidence']}
        for e in u['position_events']:byblock[txblocks[e['tx_hash']]].append((u,e))
    for n,jobs in sorted(byblock.items()):
        head,rs,tr,paths=engine.block(n)
        for u,e in jobs:
            log=next(l for l in rs[e['tx_hash']]['logs'] if integer(l['logIndex'])==e['log_index'] and l['address'].lower()==e['emitter'].lower());d=decode_position(log,e['event']);d.update(tx_hash=e['tx_hash'],etherscan='https://etherscan.io/tx/'+e['tx_hash']+'#eventlog',evidence=paths['receipts']);s=state[u['unit_id']];s['events'].append(d)
            if d['kind']=='loan_or_collateral_principal':z=s['principal'][(d['emitter'],d['owner'],d['asset'])];z[0]+=int(d['collateral_delta_raw']);z[1]+=int(d['debt_delta_raw'])
            if d['kind'] in ['concentrated_liquidity_position','V4_liquidity_position']:s['liquidity'][(d['emitter'],d.get('pool_id',''),d['owner'],d['tick_lower'],d['tick_upper'],d.get('salt',''))]+=int(d['liquidity_delta_raw'])
        engine.cache.clear()
    rows=[]
    for u in units:
        s=state[u['unit_id']];rows.append({'unit_id':u['unit_id'],'included_transactions':u['included_transactions'],'boundary':u['boundary'],'native_ETH_WETH_cash_change_after_gas':u['net_joint_boundary_ETH'],'other_observed_asset_change_raw':u['other_token_residual_raw'],'position_events':s['events'],'loan_collateral_principal_changes':[{'protocol':a,'owner':b,'asset':c,'collateral_delta_raw':str(v[0]),'debt_delta_raw':str(v[1]),'net_principal_equity_delta_raw':str(v[0]-v[1])} for (a,b,c),v in s['principal'].items()],'concentrated_liquidity_changes':[{'pool':k[0],'pool_id':k[1],'owner':k[2],'tick_lower':k[3],'tick_upper':k[4],'salt':k[5],'liquidity_delta_raw':str(v)} for k,v in s['liquidity'].items()],'profit_not_inferred_from_principal':True,'historical_all_in_cost_basis_proven':False,'interpretation':'All observable principal and cash movements separated. Existing share holdings, unpaid fee claims, interest and historical acquisition cost remain distinct assets/liabilities; no double addition of aToken shares and their same underlying collateral.'})
    summary={'position_or_NFT_units':len(rows),'units_with_position_events':sum(bool(r['position_events']) for r in rows),'decoded_events':sum(len(r['position_events']) for r in rows),'event_kinds':dict(Counter(e['kind'] for r in rows for e in r['position_events'])),'loan_collateral_rows':sum(len(r['loan_collateral_principal_changes']) for r in rows),'liquidity_position_rows':sum(len(r['concentrated_liquidity_changes']) for r in rows),'principal_does_not_equal_profit':True};(p/'position_principal_ledger.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
