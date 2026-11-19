"""Scan all raw blocks for named-address activity, including other gas senders."""
import json
from collections import Counter
from src.arbitrage.discover import ROOT
from src.arbitrage.inventory_profiles import NAMED
from src.arbitrage.full_window import FIRST,LAST
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,native_flows,cashflow
from src.decoding.events import integer,TRANSFER
from src.anomaly.screen import POSITION_TOPICS

def run():
    engine=Reconstruction(ROOT.parent/'research',False);out=ROOT/'data/processed/mev_full_window';named=set(NAMED);public=set(json.loads((out/'public_boundary_exclusions.json').read_text())['addresses']);counts=Counter()
    with (out/'named_full_window_ledger.jsonl').open('w') as f:
        for n in range(FIRST,LAST+1):
            h,rs,ts,paths=engine.block(n)
            for tx,rc in rs.items():
                sender=rc['from'].lower();hits=({sender,(rc.get('to') or '').lower()}&named)
                for l in rc['logs']:
                    hits|={l['address'].lower()}&named
                    for topic in l.get('topics',[])[1:3]:hits|={'0x'+topic[-40:].lower()}&named
                for tr in ts[tx]:
                    a=tr.get('action',{});hits|={a.get(k,'').lower() for k in ['from','to','address','refundAddress']}&named
                if not hits:continue
                flows=native_flows(ts[tx]);deltas={};gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);priority=integer(rc['gasUsed'])*(integer(rc['effectiveGasPrice'])-integer(h['baseFeePerGas']))
                for a in hits:
                    tokens=token_net(rc,{a});native=sum(int(v['amount_raw'])*((v['recipient']==a)-(v['sender']==a)) for v in flows)
                    # Priority income from this tx is actual additional address cashflow.
                    if a==h['miner'].lower():native+=priority
                    deltas[a]={'token_net_raw':{t:str(v) for t,v in tokens.items()},'native_net_before_gas_wei':str(native),'gas_wei':str(gas if a==sender else 0)}
                executor=(rc.get('to') or '').lower();joint_boundary={sender,executor}-public-{''};joint=cashflow(rc,ts[tx],joint_boundary,h['miner']) if sender in joint_boundary and ({sender,executor}&named) else None
                row={'root_to':executor,'joint_operation_boundary':sorted(joint_boundary) if joint else [],'joint_operation_cashflow':joint,'tx_hash':tx,'block':n,'index':integer(rc['transactionIndex']),'timestamp':integer(h['timestamp']),'sender':sender,'single_address_asset_deltas':deltas,'position_or_debt_events':[{'emitter':l['address'],'log_index':integer(l['logIndex']),'event':POSITION_TOPICS[l['topics'][0].lower()]} for l in rc['logs'] if l.get('topics') and l['topics'][0].lower() in POSITION_TOPICS],'recognized_erc721_transfer_events':sum(len(l.get('topics',[]))==4 and l['topics'][0].lower()==TRANSFER for l in rc['logs']),'evidence':paths};f.write(json.dumps(row,separators=(',',':'))+'\n');counts['unique_transactions']+=1
                for a in hits:counts[a]+=1
            engine.cache.clear();counts['blocks']+=1
            if counts['blocks']%500==0:print('named raw blocks',counts['blocks'],'transactions',counts['unique_transactions'],flush=True)
    (out/'named_full_window_summary.json').write_text(json.dumps(dict(counts),indent=2));print(json.dumps(dict(counts),indent=2))
if __name__=='__main__':run()
