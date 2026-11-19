"""Unique-transaction, full-window accounting for every candidate sender.
Includes non-associated and negative legs; single-address balances are separate.
No global profit total or automatic ownership clustering.
"""
import json,bisect
from collections import Counter,defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import cashflow,token_net,native_flows
from src.decoding.events import integer,transfer
from src.anomaly.screen import POSITION_TOPICS
from src.arbitrage.full_window import FIRST,LAST

def run():
    out=ROOT/'data/processed/mev_full_window';cands=json.loads((out/'candidates.json').read_text());ch={x['tx_hash'] for x in cands};senders={x['sender'] for x in cands};engine=Reconstruction(ROOT.parent/'research',False);counts=Counter();failures=[];actors=defaultdict(lambda:Counter());dest=out/'all_sender_accounting.jsonl'
    with dest.open('w') as stream:
        for n in range(FIRST,LAST+1):
            head,rs,ts,paths=engine.block(n);base=integer(head['baseFeePerGas']);pri=sorted(integer(r['effectiveGasPrice'])-base for r in rs.values());knownsendercount=Counter(r['from'].lower() for r in rs.values());callers=defaultdict(set)
            for r in rs.values():callers[(r.get('to') or '').lower()].add(r['from'].lower())
            for h,r in sorted(rs.items(),key=lambda x:integer(x[1]['transactionIndex'])):
                sender=r['from'].lower()
                if sender not in senders:continue
                executor=(r.get('to') or '').lower();accounts={sender,executor}-{''};counts['transactions']+=1;is_candidate=h in ch;counts['candidate_transactions']+=is_candidate;counts['other_same_sender_transactions']+=not is_candidate
                row={'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'timestamp':integer(head['timestamp']),'status':integer(r['status']),'sender':sender,'executor':executor,'is_discovery_candidate':is_candidate,'accounting_boundary':sorted(accounts),'entrypoint_senders_in_block':len(callers[executor]),'sender_transactions_in_block':knownsendercount[sender],'evidence':paths}
                try:
                    cf=cashflow(r,ts[h],accounts,head['miner']);flows=native_flows(ts[h]);gasused=integer(r['gasUsed']);effective=integer(r['effectiveGasPrice']);priority=effective-base;assert priority>=0
                    row.update(cf);row.update(gas_used=gasused,effective_gas_price_wei=str(effective),base_fee_burn_wei=str(gasused*base),priority_fee_wei=str(gasused*priority),priority_fee_per_gas_wei=str(priority),same_block_priority_fee_median_wei=str(pri[len(pri)//2]),same_block_priority_fee_fraction_at_or_below=bisect.bisect_right(pri,priority)/len(pri),fee_recipient=head['miner'].lower())
                    row['single_address_asset_deltas']={}
                    for a in accounts:
                        toks=token_net(r,{a});native=sum(int(f['amount_raw'])*((f['recipient']==a)-(f['sender']==a)) for f in flows)
                        row['single_address_asset_deltas'][a]={'token_net_raw':{t:str(v) for t,v in toks.items()},'native_net_before_gas_wei':str(native),'gas_wei':cf['gas_wei'] if a==sender else '0'}
                    row['external_native_payouts']=[f for f in flows if f['sender'] in accounts and f['recipient'] not in accounts];row['external_token_payouts']=[f for l in r['logs'] if (f:=transfer(l)) and f['sender'] in accounts and f['recipient'] not in accounts]
                    row['position_or_debt_events']=[{'emitter':l['address'],'log_index':integer(l['logIndex']),'event':POSITION_TOPICS[l['topics'][0].lower()]} for l in r['logs'] if l.get('topics') and l['topics'][0].lower() in POSITION_TOPICS]
                    row['recognized_erc721_transfer_events']=sum(len(l.get('topics',[]))==4 and l['topics'][0].lower()=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' for l in r['logs'])
                    row['boundary_verified']=False;row['MEV_classified_from_gas']=False;row['profit_status']='raw operational asset deltas only; LP principal, debt, shared entrypoint and strategy inventory unresolved'
                    counts['accounting_complete']+=1;counts['position_or_debt_transactions']+=bool(row['position_or_debt_events']);a=actors[(sender,executor)];a['transactions']+=1;a['candidate_transactions']+=is_candidate;a['failed_transactions']+=integer(r['status'])==0
                except Exception as ex:row['accounting_error']=str(ex);failures.append({'tx_hash':h,'block':n,'error':str(ex)})
                stream.write(json.dumps(row,separators=(',',':'))+'\n')
            engine.cache.clear();counts['blocks']+=1
            if counts['blocks']%200==0:print('full accounting',counts['blocks'],'tx',counts['transactions'],'candidates',counts['candidate_transactions'],flush=True)
    assert counts['candidate_transactions']==len(cands)
    (out/'sender_accounting_failures.json').write_text(json.dumps(failures,indent=2));(out/'sender_executor_census.json').write_text(json.dumps([{'sender':s,'executor':e,**a} for (s,e),a in sorted(actors.items())],indent=2))
    summary={**counts,'candidate_senders':len(senders),'failures':len(failures),'unique_transaction_stream':str(dest.relative_to(ROOT)),'global_profit_established':False,'warning':'Complete available-window transactions for selected senders, not all beneficiary/control addresses or whole-history strategies. Gas includes base burn plus priority; direct fee-recipient payment remains separate. Shared entrypoints not clustered.'}
    (out/'sender_accounting_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
