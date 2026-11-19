"""Full-window census of canonical V4 ERC-6909 value claims, including non-swap txs."""
import json
from collections import defaultdict
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.complete_surplus_ledger import claim_event,MANAGER,ZERO
from src.arbitrage.full_window import FIRST,LAST
from src.decoding.events import integer

def run():
    engine=Reconstruction(ROOT.parent/'research',False);p=ROOT/'data/processed/mev_full_window';events=[];balances=defaultdict(lambda:defaultdict(int));transactions=0
    for n in range(FIRST,LAST+1):
        head,rs,tr,paths=engine.block(n)
        for h,r in rs.items():
            seen=False
            for l in r['logs']:
                if l['address'].lower()!=MANAGER:continue
                c=claim_event(l)
                if not c:continue
                seen=True;events.append({'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'timestamp':integer(head['timestamp']),'root_sender':r['from'].lower(),**c,'evidence':paths})
                value=int(c['amount_raw'])
                if c['sender']!=ZERO:balances[c['sender']][c['currency']]-=value
                if c['recipient']!=ZERO:balances[c['recipient']][c['currency']]+=value
            transactions+=seen
        engine.cache.clear()
        if (n-FIRST+1)%500==0:print('claim census blocks',n-FIRST+1,'events',len(events),flush=True)
    doc={'blocks':LAST-FIRST+1,'claim_event_transactions':transactions,'claim_events':len(events),'events':events,'address_claim_changes_raw':{a:{t:str(v) for t,v in ts.items() if v} for a,ts in balances.items()},'source':'https://raw.githubusercontent.com/Uniswap/v4-core/main/src/ERC6909.sol','meaning':'Asset claim changes, not native cash. Address-level receipt is verified; common beneficial ownership is not inferred.'};(p/'v4_claim_census.json').write_text(json.dumps(doc,indent=2));print('claim census done',len(events),transactions,'transactions',len(balances),'addresses')
if __name__=='__main__':run()
