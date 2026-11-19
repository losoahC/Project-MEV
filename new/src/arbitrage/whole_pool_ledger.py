"""Value every covered affected-pool counterparty over the whole original window.
Inventory/reference trading margins remain separate from closed arbitrage profits.
"""
import json
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import token_net,native_flows
from src.arbitrage.full_valuations import FullWindowBook
from src.arbitrage.value_candidates import book_from_archive,mark
from src.decoding.events import integer
from src.anomaly.screen import POSITION_TOPICS
getcontext().prec=90
E=Decimal(10)**18
# Explicit risk flags, not an ownership or protocol-profit label.
COMET={'0xa17581a9e3356d9a858b789d68b4d866e593ae94','0xc3d688b66703497daa19211eedff47f25384cdc3'}

def run():
    p=ROOT/'data/processed/mev_full_window';byblock=defaultdict(list)
    with (p/'affected_pool_scope.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['scope_category']!='target':byblock[r['block']].append(r)
    public=set(json.loads((p/'public_boundary_exclusions.json').read_text())['addresses']);scope=json.loads((p/'address_scope.json').read_text());incident=set(scope['original_leads'])|{scope['additional_order_swapper']};book=book_from_archive();book.__class__=FullWindowBook;book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('USDC',('2026-10-29','2026-10-30'));engine=book.engine;counts=Counter();actors=defaultdict(lambda:{'transactions':0,'priced':0,'position_or_debt':0,'net_USD':Decimal(0),'gas_USD':Decimal(0),'tx_hashes':[]})
    with (p/'whole_pool_counterparty_ledger.jsonl').open('w') as out:
        for i,(n,items) in enumerate(sorted(byblock.items()),1):
            head,rs,tr,paths=engine.block(n);timestamp=integer(head['timestamp']);eth=book.price('ETH',timestamp)
            for candidate in items:
                h=candidate['tx_hash'];r=rs[h];sender=r['from'].lower();entry=(r.get('to') or '').lower();boundary={sender}|({entry} if entry and entry not in public else set());flows=native_flows(tr[h]);tok=token_net(r,boundary);native=sum(int(f['amount_raw'])*((f['recipient'] in boundary)-(f['sender'] in boundary)) for f in flows);gas=integer(r['gasUsed'])*integer(r['effectiveGasPrice']);priority=integer(r['gasUsed'])*(integer(r['effectiveGasPrice'])-integer(head['baseFeePerGas']));credit=priority if head['miner'].lower() in boundary else 0;raw={t:str(v) for t,v in tok.items()};raw['native:eth']=str(native-gas+credit);v=mark(book,raw,timestamp);position=[{'emitter':l['address'],'event':POSITION_TOPICS[l['topics'][0].lower()]} for l in r['logs'] if l.get('topics') and l['topics'][0].lower() in POSITION_TOPICS];comet=sorted({t.get('action',{}).get('to','').lower() for t in tr[h]}&COMET);nft=sum(len(l.get('topics',[]))==4 and l['topics'][0].lower()=='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' for l in r['logs']);eligible=not position and not comet and not nft and sender not in incident
                row={'tx_hash':h,'block':n,'index':integer(r['transactionIndex']),'timestamp':timestamp,'sender':sender,'entrypoint':entry,'boundary':sorted(boundary),'public_entrypoint_excluded':entry in public,'scope_category':candidate['scope_category'],'last_prior_targets':candidate['last_prior_targets'],'affected_pool_keys':candidate['affected_pool_keys'],'pool_events':candidate['events'],'pre_gas_native_net_wei':str(native),'token_net_raw':{t:str(q) for t,q in tok.items()},'gas_wei':str(gas),'priority_credit_to_own_boundary_wei':str(credit),'gas_USD':str(Decimal(gas-credit)/E*eth[0]) if eth else None,'reference_valuation':v,'reference_after_cost_USD':v['marked_net_USD'],'position_or_debt_events':position,'Comet_interactions':comet,'NFT_transfers':nft,'incident_sender_context':sender in incident,'eligible_reference_trade_margin':eligible,'evidence':paths,'meaning':'Independent reference-marked operational asset change, after gas and observed payments. Not all-in inventory cost-basis profit, common ownership, or causal MEV. Whole-window affected-pool scope deliberately includes ordinary and pre-event trades.'}
                out.write(json.dumps(row,separators=(',',':'))+'\n');counts['transactions']+=1;counts['fully_priced']+=v['marked_net_USD'] is not None;counts['eligible_no_known_positions']+=eligible;counts['own_priority_refund_transactions']+=credit>0
                key=(sender,entry,candidate['scope_category']);a=actors[key];a['transactions']+=1;a['position_or_debt']+=not eligible;a['tx_hashes'].append(h)
                if eligible and v['marked_net_USD'] is not None:a['priced']+=1;a['net_USD']+=Decimal(v['marked_net_USD']);a['gas_USD']+=Decimal(row['gas_USD']) if row['gas_USD'] is not None else 0
            engine.cache.clear()
            if i%300==0:print('whole pool ledger blocks',i,'tx',counts['transactions'],flush=True)
    ranks=[{'sender':s,'entrypoint':e,'scope_category':c,**{k:str(v) if isinstance(v,Decimal) else v for k,v in a.items()},'status':'Reference trade margins only; different entrypoints are not clustered as firms.'} for (s,e,c),a in actors.items()];ranks.sort(key=lambda r:Decimal(r['net_USD']),reverse=True);(p/'whole_pool_counterparty_rankings.json').write_text(json.dumps(ranks,indent=2));(p/'whole_pool_ledger_summary.json').write_text(json.dumps({**counts,'blocks':len(byblock),'global_profit_established':False},indent=2));print(json.dumps(dict(counts),indent=2))
if __name__=='__main__':run()
