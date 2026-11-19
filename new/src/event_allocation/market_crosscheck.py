"""Observable price sensitivity, without claiming unavailable same-minute replication."""
import json,gzip
from collections import defaultdict
from decimal import Decimal
from src.event_allocation.config import ROOT,OUT,START,END
from src.event_allocation.allocate import Pools,target_allocation,subsequent_allocation
from src.event_allocation.quotes import Quotes
from src.arbitrage.tron_accounting import U

def run():
    source=json.loads((OUT/'hyperliquid_TRX_15m_source.json').read_text());doc=json.loads((ROOT/source['evidence']).read_text());bars=doc['response'];assert all(r['s']=='TRX' and r['i']=='15m' for r in bars);pools=Pools();q=Quotes();q1=Quotes('stable1');modes=['primary','stable1','Hyperliquid_last_completed_15m_stable1','Hyperliquid_current_15m_close_stable1_retrospective'];totals={m:defaultdict(Decimal) for m in modes};inventory=defaultdict(lambda:defaultdict(int));timestamps=[]
    def value(mode,a,raw,ts):
        if mode=='primary':return q.value(a,raw,ts)
        if mode=='stable1':return q1.value(a,raw,ts)
        if a==U:return Decimal(raw)/10**6
        assert a=='native:trx',a;cutoff=ts//60*60*1000
        valid=[b for b in bars if (b['T']<cutoff if 'last_completed' in mode or ts==END else b['t']<=cutoff<b['t']+900000)]
        if not valid:return None
        b=max(valid,key=lambda b:b['t']);return Decimal(raw)*Decimal(b['c'])/10**6
    with gzip.open(OUT/'tron_journal.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);rows,errors=target_allocation(r,pools) if r['association']=='target' else subsequent_allocation(r,pools)[:2];assert not errors
            for role,pool,v in rows:
                if role=='pool_trade_inventory':
                    for a,raw in v.items():inventory[pool][a]+=raw
                for mode in modes:
                    vals=[value(mode,a,raw,r['timestamp']) for a,raw in v.items() if raw]
                    if all(x is not None for x in vals):totals[mode][role]+=sum(vals,Decimal(0))
                    else:totals[mode]['unpriced_role_vectors']+=1
    rows=[]
    for mode,t in totals.items():
        terminal_values=[value(mode,a,raw,END) for v in inventory.values() for a,raw in v.items()];terminal=sum(terminal_values,Decimal(0)) if all(v is not None for v in terminal_values) else None;rows.append({'policy':mode,'incident_wallet_reference_loss_USD':str(-t['incident_wallet_reference_change']),'subsequent_operating_address_net_USD':str(t['operating_address_incident_leg_reference_edge']),'pool_trade_time_inventory_change_USD':str(t['pool_trade_inventory']),'pool_terminal_inventory_change_USD':str(terminal) if terminal is not None else None,'actual_resource_fee_mark_USD':str(t['protocol_resource_fee']),'unpriced_role_vectors':int(t['unpriced_role_vectors']),'same_minute_Bitquery_reproduction':False,'lookahead_warning':'Uses a later close within the current 15-minute candle; retrospective sensitivity only. Terminal price still uses the last candle completed by window end.' if 'retrospective' in mode else None})
    inwindow=[b for b in bars if START*1000<=b['t']<END*1000];result={'hyperliquid_evidence':source['evidence'],'available_15m_bars':len(bars),'actual_first_open':inwindow[0]['o'],'actual_last_15m_close':inwindow[-1]['c'],'highest_15m_high':str(max(Decimal(r['h']) for r in inwindow)),'comparisons':rows,'identification':'One-minute Hyperliquid history was unavailable under the public retention window. A 15-minute sensitivity cannot certify Bitquery same-minute values. The terminal inventory column values swap changes relative to holding the same initial coins under fixed-inventory assumptions; it is not individual LP total wealth or an extra extraction amount.'};(OUT/'tron_market_policy_crosscheck.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':run()
