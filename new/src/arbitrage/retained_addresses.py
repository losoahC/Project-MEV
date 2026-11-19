"""Decompose covered-cycle retained asset changes into actual individual addresses."""
import json,csv
from collections import defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,native_flows
from src.decoding.events import WETH,integer

def run():
    p=ROOT/'data/processed/mev_full_window';units=json.loads((p/'terminal_cycle_profits.json').read_text());byblock=defaultdict(list);state={}
    for u in units:
        state[u['unit_id']]={a:{'native':0,'tokens':defaultdict(int),'gas':0} for a in u['boundary']}
        for t in u['transaction_evidence']:byblock[t['block']].append((u,t['tx_hash']))
    engine=Reconstruction(ROOT.parent/'research',False)
    for n,jobs in sorted(byblock.items()):
        head,rs,tr,paths=engine.block(n)
        for u,h in jobs:
            r=rs[h];flows=native_flows(tr[h]);gas=integer(r['gasUsed'])*integer(r['effectiveGasPrice'])
            for a,s in state[u['unit_id']].items():
                for t,v in token_net(r,{a}).items():s['tokens'][t]+=v
                s['native']+=sum(int(f['amount_raw'])*((f['recipient']==a)-(f['sender']==a)) for f in flows);s['gas']+=gas if r['from'].lower()==a else 0
                if a==head['miner'].lower():raise ValueError('Explicitly account own priority credit before decomposing')
        engine.cache.clear()
    rows=[]
    for u in units:
        check=0;checktokens=defaultdict(int)
        for a,s in state[u['unit_id']].items():
            combined=s['native']+s['tokens'].get(WETH,0)-s['gas'];check+=combined
            for t,v in s['tokens'].items():
                if t!=WETH:checktokens[t]+=v
            rows.append({'unit_id':u['unit_id'],'address':a,'is_sender':a==u['sender'],'native_change_before_gas_wei':str(s['native']),'WETH_change_raw':str(s['tokens'].get(WETH,0)),'own_gas_wei':str(s['gas']),'net_ETH_WETH_change_after_own_gas':str(Decimal(combined)/10**18),'other_token_change_raw':{t:str(v) for t,v in s['tokens'].items() if t!=WETH and v},'unit_transactions':u['included_transactions'],'meaning':'Actual address net asset changes over this included unit, not ending balance or common beneficial ownership.'})
        assert Decimal(check)/10**18==Decimal(u['net_joint_boundary_ETH']);assert {t:str(v) for t,v in checktokens.items() if v}==u['other_token_residual_raw']
    (p/'covered_cycle_address_changes.json').write_text(json.dumps({'units':len(units),'rows':rows,'all_joint_boundaries_reconciled':True,'not_terminal_balance_or_ultimate_owner':True},indent=2))
    with (ROOT/'reports/mev_expansion/闭合循环逐地址净变化.csv').open('w') as f:
        flat=[{**r,'other_token_change_raw':json.dumps(r['other_token_change_raw'],separators=(',',':')),'unit_transactions':';'.join(r['unit_transactions'])} for r in rows];w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('Reconciled individual-address changes',len(units),'units',len(rows),'address rows')
if __name__=='__main__':run()
