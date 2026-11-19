"""Whole-window, all-counterparty transaction journals with integer conservation.
No fixed list of profitable bots, no +/-5-block cutoff, no valuation during extraction.
"""
import json,gzip
from collections import defaultdict,Counter
from src.event_allocation.config import ROOT,OUT,START,END,setup
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.accounting import native_flows,DEPOSIT,WITHDRAWAL
from src.arbitrage.complete_surplus_ledger import claim_event,MANAGER,ZERO
from src.arbitrage.v4_keys import decode_key
from src.arbitrage.transfer_audit import receipt_movements
from src.anomaly.screen import POSITION_TOPICS
from src.decoding.events import transfer,integer,WETH,signed_word

AAVE={'0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2','0xc13e21b648a5ee794902342038ff3adab66be987'}
COMET={'0xa17581a9e3356d9a858b789d68b4d866e593ae94','0xc3d688b66703497daa19211eedff47f25384cdc3'}

def normalize(asset):return 'native:eth' if asset in [WETH,'0x'+'0'*40] else asset

def position_adjustments(receipt,comet_case):
    changes=defaultdict(lambda:defaultdict(int));events=[];actors=set();risks=[]
    def position(owner,protocol,asset,amount):
        asset=normalize(asset);changes[owner][asset]+=amount;changes[protocol][asset]-=amount
    for l in receipt.get('logs',[]):
        ts=l.get('topics',[]);event=POSITION_TOPICS.get(ts[0].lower()) if ts else None
        if not event:continue
        protocol=l['address'].lower();words=[l['data'][i:i+64] for i in range(2,len(l['data']),64)];addr=lambda i:'0x'+ts[i][-40:].lower();record={'emitter':protocol,'event':event,'log_index':integer(l['logIndex'])}
        if protocol in AAVE and event.startswith(('Supply(','Withdraw(','Borrow(','Repay(')):
            assert len(ts)==4;kind=event.split('(')[0];asset=addr(1);owner=addr(2);amount=int(words[1] if kind in ['Supply','Borrow'] else words[0],16);signed=amount if kind in ['Supply','Repay'] else -amount;position(owner,protocol,asset,signed)
            if kind=='Repay' and len(words)>1 and int(words[1],16):position(addr(3),protocol,asset,-amount);record['repayment_with_aTokens']=True
            record.update(owner=owner,asset=asset,principal_raw=str(amount),equity_principal_adjustment_raw=str(signed))
        elif protocol in AAVE and event.startswith('LiquidationCall('):
            collateral,debt,user=addr(1),addr(2),addr(3);repaid=int(words[0],16);seized=int(words[1],16);liquidator='0x'+words[2][-40:];position(user,protocol,debt,repaid);position(user,protocol,collateral,-seized)
            if int(words[3],16):position(liquidator,protocol,collateral,seized)
            record.update(owner=user,liquidator=liquidator,debt_asset=debt,repaid_raw=str(repaid),collateral_asset=collateral,seized_raw=str(seized))
        elif event.startswith(('Mint(','Burn(','Collect(','ModifyLiquidity(')):
            if len(ts)>1:actors.add(addr(1))
            record['liquidity_principal_not_profit']=True
        else:risks.append(record)
        events.append(record)
    if receipt['transactionHash']==comet_case['tx_hash']:
        for asset,raw in comet_case['position_equity_change_raw'].items():position(comet_case['position_owner'],comet_case['comet'],asset,int(raw))
        events.append({'emitter':comet_case['comet'],'event':'Exact historical Comet collateral/debt state change','evidence':'data/processed/mev_full_window/comet_resolver_equity.json'})
    return changes,events,actors,risks

def journal(head,rc,traces,scope,known_keys,comet_case):
    cash=defaultdict(lambda:defaultdict(int));claims=defaultdict(lambda:defaultdict(int));liability=defaultdict(int);tokens=set();minted=0
    for f in native_flows(traces):cash[f['sender']]['native:eth']-=int(f['amount_raw']);cash[f['recipient']]['native:eth']+=int(f['amount_raw'])
    nft=[]
    for l in rc['logs']:
        f=transfer(l)
        if f:
            t=normalize(f['token']);raw=int(f['amount_raw']);tokens.add(f['token']);cash[f['sender']][t]-=raw;cash[f['recipient']][t]+=raw
        ts=l.get('topics',[])
        if l['address'].lower()==WETH and len(ts)==2 and ts[0].lower() in [DEPOSIT,WITHDRAWAL]:
            raw=integer(l['data'])*(1 if ts[0].lower()==DEPOSIT else -1);cash['0x'+ts[1][-40:].lower()]['native:eth']+=raw;minted+=raw
        c=claim_event(l)
        if c:
            t=normalize(c['currency']);raw=int(c['amount_raw'])
            if c['sender']!=ZERO:claims[c['sender']][t]-=raw
            else:liability[t]+=raw
            if c['recipient']!=ZERO:claims[c['recipient']][t]+=raw
            else:liability[t]-=raw
    # Remove only wrapper backing created by the same issuance, not forced ETH
    # donations or unrelated ERC20 balances at the wrapper address.
    cash[WETH]['native:eth']-=minted
    gas=integer(rc['gasUsed'])*integer(rc['effectiveGasPrice']);burn=integer(rc['gasUsed'])*integer(head['baseFeePerGas']);blob=integer(rc.get('blobGasUsed',0))*integer(rc.get('blobGasPrice',0));priority=gas-burn;sender=rc['from'].lower();fee=head['miner'].lower();cash[sender]['native:eth']-=gas+blob;cash[fee]['native:eth']+=priority;cash['protocol:base_fee_burn']['native:eth']+=burn;cash['protocol:blob_fee_burn']['native:eth']+=blob
    positions,events,lp_actors,risks=position_adjustments(rc,comet_case)
    if any(t.get('action',{}).get('to','').lower() in COMET for t in traces) and rc['transactionHash']!=comet_case['tx_hash']:risks.append({'event':'Other Compound interaction: cash-only amount is not certified net position PnL'})
    swaps=scope.get('events',[]);new_keys=[]
    for e in swaps:
        if e['protocol'].startswith('V4') and e['pool_key'] not in known_keys:
            for tr in traces:
                a=tr.get('action',{});key=decode_key(a.get('input','')) if a.get('to','').lower()==e['pool'] else None
                if key and key['pool_id']==e['pool_id']:
                    row={'pool_key':e['pool_key'],'manager':e['pool'],**key,'evidence':scope['evidence']['traces'],'tx_hash':rc['transactionHash'],'trace_address':tr['traceAddress']};known_keys[e['pool_key']]=row;new_keys.append(row);break
    entries=[]
    for component,byaddress in [('cash',cash),('V4_claim',claims),('position_principal',positions)]:
        for address,assets in byaddress.items():
            for asset,raw in assets.items():
                if raw:entries.append({'address':address,'asset':asset,'raw':str(raw),'component':component})
    for asset,raw in liability.items():
        if raw:entries.append({'address':MANAGER,'asset':asset,'raw':str(-raw),'component':'V4_claim_backing_liability'})
    # Fungible integer conservation is independent of all USD price assumptions.
    totals=defaultdict(int)
    for r in entries:totals[r['asset']]+=int(r['raw'])
    assert not {t:v for t,v in totals.items() if v},(rc['transactionHash'],{t:v for t,v in totals.items() if v})
    return {'chain':'ethereum','tx_hash':rc['transactionHash'],'block':integer(rc['blockNumber']),'index':integer(rc['transactionIndex']),'timestamp':integer(head['timestamp']),'sender':sender,'entrypoint':(rc.get('to') or '').lower(),'fee_recipient':fee,'gas_raw':str(gas),'base_burn_raw':str(burn),'priority_raw':str(priority),'blob_burn_raw':str(blob),'entries':entries,'swap_events':swaps,'affected_pool_keys':scope.get('affected_pool_keys',[]),'association':scope['scope_category'],'last_prior_targets':scope.get('last_prior_targets',[]),'position_events':events,'liquidity_actors':sorted(lp_actors),'position_risks':risks,'token_contracts':sorted(tokens),'evidence':scope['evidence'],'raw_conservation_verified':True},new_keys

def run():
    setup();p=ROOT/'data/processed/mev_full_window';targets=json.loads((p/'targets.json').read_text());blocks={r['block']:r['timestamp'] for r in json.loads((p/'blocks.json').read_text())};jobs=defaultdict(dict)
    for line in (p/'affected_pool_scope.jsonl').open():
        r=json.loads(line)
        if START<=blocks[r['block']]<END:jobs[r['block']][r['tx_hash']]=r
    for r in targets:
        if not START<=r['timestamp']<END:continue
        s=jobs[r['block']].setdefault(r['tx_hash'],{'tx_hash':r['tx_hash'],'block':r['block'],'index':r['index'],'events':r['pool_events'],'affected_pool_keys':sorted({e['pool_key'] for e in r['pool_events']}),'evidence':r['evidence']});s['scope_category']='target'
    first={};pairs={(r.get('sender'),r.get('executor')) for items in jobs.values() for r in items.values() if r.get('sender')}
    for t in targets:
        for e in t['pool_events']:
            key=e['pool_key'];at=(t['block'],t['index']);first[key]=min(first.get(key,at),at)
    keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']};comet=json.loads((p/'comet_resolver_equity.json').read_text());engine=Reconstruction(ROOT.parent/'research',False);tokens=Counter();counts=Counter();failures=[];extra=[];allblocks=sorted(n for n,ts in blocks.items() if START<=ts<END);temporary=OUT/'ethereum_journal.partial.jsonl.gz'
    with gzip.open(temporary,'wt') as output:
        for i,n in enumerate(allblocks,1):
            items=jobs.get(n,{})
            h,rs,tr,paths=engine.block(n)
            for tx,rc in rs.items():
                if integer(rc['status'])!=0:continue
                counts['all_window_failed_transactions']+=1;matched=set()
                for trace in tr[tx]:
                    a=trace.get('action',{});to=a.get('to','').lower()
                    if to in first:matched.add(to)
                    if to==MANAGER:
                        k=decode_key(a.get('input',''))
                        if k and MANAGER+':'+k['pool_id'] in first:matched.add(MANAGER+':'+k['pool_id'])
                sender=rc['from'].lower();entry=(rc.get('to') or '').lower();idx=integer(rc['transactionIndex']);post={k for k in matched if first[k]<(n,idx)}
                if matched:
                    category='failed_attempt_after_target' if post else 'failed_attempt_before_target_control';counts['failed_reaches_target_pool']+=1
                elif (sender,entry) in pairs:category='same_operator_failed_context_unassigned';counts['same_operator_failed_context_candidates']+=1
                else:continue
                items[tx]={'tx_hash':tx,'block':n,'index':idx,'events':[],'affected_pool_keys':sorted(matched),'scope_category':category,'last_prior_targets':[{'pool_key':k,'first_target_block':first[k][0]} for k in sorted(post)],'evidence':paths}
            for tx,s in sorted(items.items(),key=lambda x:x[1]['index']):
                s['evidence']=paths
                try:
                    row,kk=journal(h,rs[tx],tr[tx],s,keys,comet);extra.extend(kk);output.write(json.dumps(row,separators=(',',':'))+'\n');counts['transactions']+=1;counts[row['association']]+=1;counts['entries']+=len(row['entries']);counts['position_risk_transactions']+=bool(row['position_risks'])
                    for r in row['entries']:tokens[r['asset']]+=1
                except Exception as ex:failures.append({'tx_hash':tx,'block':n,'error':repr(ex)})
            engine.cache.clear()
            if i%200==0:print('Ethereum journal blocks',i,'/',len(allblocks),'transactions',counts['transactions'],'failures',len(failures),flush=True)
    temporary.replace(OUT/'ethereum_journal.jsonl.gz');summary={**counts,'blocks':len(allblocks),'asset_frequency':dict(tokens),'failures':failures,'all_successful_rows_raw_conserve':True,'common_start':START,'common_end_exclusive':END};(OUT/'ethereum_journal_summary.json').write_text(json.dumps(summary,indent=2));(OUT/'additional_v4_pool_keys.json').write_text(json.dumps(extra,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='asset_frequency'},indent=2))
if __name__=='__main__':run()
