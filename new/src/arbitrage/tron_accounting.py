"""Rebuild TRON bot token/native ledgers and two-pool cycles from solidified receipts."""
import json
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_collect import decode_addr,encode_addr
from src.arbitrage.accounting import DEPOSIT,WITHDRAWAL
from src.decoding.events import TRANSFER,signed_word
from src.decoding.extended_events import extended_swap
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction
getcontext().prec=90
U=decode_addr('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t');W=decode_addr('TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR');PUBLIC={decode_addr(a) for a in ['TNJVzGqKBWkJxJB5XYSqGAwUTV15U24pPq','TQAvWQpT9H916GckwWDJNhYZvQMkuRL7PN','TXF1xDbVGdxFGbovmmmXvBGu8ZiE3Lq4mR','TKzxdSv2FZKQrEqkKVgp5DcwEXBEKMg2Ax','TCFNp179Lg46D16zKoumd4Poa2WFFdtqYj','TJ4NNy8xZEqsowCBhLvZ45LCqPdGjkET5j','TFVisXFaijZfeyeSjCEVkHfex7HGdTxzF9','TVjuTE3V5bMVdpfNhid8kD2v35T2k1u1Br','TTJxU3P8rHycAyFY4kVtGNfmnMH4ezcuM9']};ZERO='41'+'0'*40
PUBLIC.update({U,W,decode_addr('TE2RzoSV3wFK99w6J9UnnZ4vLfXYoxvRwP'),decode_addr('TXJgMdjVX5dKiQaUi9QobwNxtSQaFqccvd')})

def parse(row,v4keys=None,accounts_override=None):
    v4keys=v4keys or {}
    t=row['transaction'];r=row['receipt'];owner=row['bot_hex'];contracts=t['raw_data']['contract'];root=contracts[0];to=root['parameter']['value'].get('contract_address',owner);accounts=set(accounts_override) if accounts_override is not None else {owner}|({to} if root['type']=='TriggerSmartContract' and to not in PUBLIC else set());success=all(x.get('contractRet')=='SUCCESS' for x in t['ret']) and r.get('receipt',{}).get('result','SUCCESS')=='SUCCESS';net=defaultdict(int);flows=[];events=[];wrap=[];native=[];logs=r.get('log',[]) if success else []
    for i,l in enumerate(logs):
        ts=l.get('topics',[]);emitter='41'+l['address'][-40:].lower()
        if len(ts)==3 and ts[0].lower()==TRANSFER[2:] and len(l.get('data',''))==64:
            f={'token':emitter,'sender':'41'+ts[1][-40:].lower(),'recipient':'41'+ts[2][-40:].lower(),'amount_raw':str(int(l.get('data',''),16)),'log_index':i};flows.append(f)
            net[emitter]+=int(f['amount_raw'])*((f['recipient'] in accounts)-(f['sender'] in accounts))
        if emitter==W and len(ts)==2 and len(l.get('data',''))==64 and ts[0].lower() in [DEPOSIT[2:],WITHDRAWAL[2:]]:wrap.append((i,ts[0].lower(),'41'+ts[1][-40:].lower(),int(l.get('data',''),16)))
        e=extended_swap({'address':'0x'+l['address'][-40:],'topics':['0x'+v for v in ts],'data':'0x'+l.get('data',''),'logIndex':i})
        if e:events.append({**e,'pool_hex':'41'+e['pool'][2:],'pool_address':encode_addr(e['pool'][2:])})
        elif ts and ts[0]=='04206ad2b7c0f463bff3dd4f33c5735b0f2957a351e4f79763a4fa9e775dd237' and len(ts)==3 and len(l.get('data',''))==448:
            words=[l['data'][j:j+64] for j in range(0,448,64)];key=v4keys.get((emitter,ts[1]));events.append({'protocol':'SunSwap V4-compatible','pool_hex':emitter,'pool_address':encode_addr(emitter),'pool_key':emitter+':'+ts[1],'pool_id':ts[1],'amount0_raw':str(signed_word(words[0])),'amount1_raw':str(signed_word(words[1])),'log_index':i,'key_verified':bool(key and key['verified_pool_key']),'key_metadata':key})
        elif ts and ts[0] in ['dad9ec5c9b9c82bf6927bf0b64293dcdd1f82c92793aef3c5f26d7b93a4a5306','cd60aa75dea3072fbc07ae6d7d856b5dc5f4eee88854f5b4abf7b680ef8bc50f'] and len(ts)==4 and not l.get('data'):
            events.append({'protocol':'SunSwap V1-compatible (event only)','pool_hex':emitter,'pool_address':encode_addr(emitter),'log_index':i,'topic':ts[0],'indexed_amounts_raw':[str(int(v,16)) for v in ts[2:]],'ABI_source':'https://raw.githubusercontent.com/sun-protocol/transactionAnalysis/master/Events_For_Liquidity_And_Exchange.md'})
    for i,topic,a,v in wrap:
        deposit=topic==DEPOSIT[2:];already=any(f['token']==W and int(f['amount_raw'])==v and ((f['sender']==ZERO and f['recipient']==a) if deposit else (f['sender']==a and f['recipient']==ZERO)) for f in flows)
        if a in accounts and not already:net[W]+=v*(1 if deposit else -1)
    if success:
        for c in contracts:
            p=c['parameter']['value'];v=int(p.get('call_value',0))
            if v:native.append({'sender':p['owner_address'],'recipient':p['contract_address'],'amount_raw':str(v),'trace':'root'})
            if c['type']=='TransferContract' and p.get('amount'):native.append({'sender':p['owner_address'],'recipient':p['to_address'],'amount_raw':str(p['amount']),'trace':'root_transfer'})
        for i,x in enumerate(r.get('internal_transactions',[])):
            if x.get('rejected'):continue
            note=bytes.fromhex(x.get('note','')).decode(errors='replace')
            if note not in ['call','create','suicide']:continue
            v=sum(int(q.get('callValue',0)) for q in x.get('callValueInfo',[]) if not q.get('tokenId'))
            if v:native.append({'sender':x['caller_address'],'recipient':x['transferTo_address'],'amount_raw':str(v),'trace':i,'note':note})
    trx=sum(int(f['amount_raw'])*((f['recipient'] in accounts)-(f['sender'] in accounts)) for f in native);fee=int(r.get('fee',0));pools={e['pool_hex'] for e in events};poolnet=defaultdict(int);legs=[];unresolved_v4=[]
    for pool in sorted(pools):
        if any(e['pool_hex']==pool and e['protocol'].startswith('SunSwap V4') for e in events):continue
        balance=defaultdict(int)
        for f in flows:
            if f['sender']==pool:balance[f['token']]-=int(f['amount_raw'])
            if f['recipient']==pool:balance[f['token']]+=int(f['amount_raw'])
        for f in native:
            if f['sender']==pool:balance['native:trx']-=int(f['amount_raw'])
            if f['recipient']==pool:balance['native:trx']+=int(f['amount_raw'])
        for tok,v in balance.items():poolnet[tok]-=v
        legs.append({'pool_hex':pool,'pool_address':encode_addr(pool),'net_input_raw':{tok:str(v) for tok,v in balance.items() if v>0},'net_output_raw':{tok:str(-v) for tok,v in balance.items() if v<0},'swap_log_indices':[e['log_index'] for e in events if e['pool_hex']==pool],'note':'Actual pool transfer aggregation; event count and repeat visits remain separate. Factory identity not yet independently checked.'})
    for ev in events:
        if not ev['protocol'].startswith('SunSwap V4'):continue
        key=ev['key_metadata']
        if not key or not key['verified_pool_key']:unresolved_v4.append(ev['pool_key']);continue
        delta={}
        for side in [0,1]:
            tok=key[f'currency{side}_hex'];tok='native:trx' if tok==ZERO else tok;value=int(ev[f'amount{side}_raw']);poolnet[tok]+=value;delta[tok]=value
        legs.append({'pool_hex':ev['pool_hex'],'pool_address':ev['pool_address'],'pool_id':ev['pool_id'],'net_input_raw':{t:str(-v) for t,v in delta.items() if v<0},'net_output_raw':{t:str(v) for t,v in delta.items() if v>0},'swap_log_indices':[ev['log_index']],'note':'Historical event amount delta; currency identities authenticated by exact PoolKey hash, no manager-wide token allocation.'})
    other={tok:str(v) for tok,v in net.items() if tok not in [W,U] and v};combined_trx=trx+net.get(W,0);usdt=net.get(U,0);pooltrx=poolnet.get(W,0)+poolnet.get('native:trx',0);poolother={tok:str(v) for tok,v in poolnet.items() if tok not in [U,W,'native:trx'] and v};closed=success and len({e.get('pool_key',e['pool_hex']) for e in events})>=2 and not other and combined_trx>=0 and usdt>=0 and (usdt>0 or combined_trx>0) and not poolother and not unresolved_v4 and poolnet.get(U,0)==usdt and pooltrx==combined_trx
    return {'tx_hash':t['txID'],'block':r['blockNumber'],'timestamp':int(r['blockTimeStamp'])//1000,'success':success,'owner':row['bot'],'entrypoint':encode_addr(to),'boundary':[encode_addr(a) for a in sorted(accounts)],'public_router_excluded':to in PUBLIC,'token_net_raw':{k:str(v) for k,v in net.items() if v},'native_TRX_before_fee':str(Decimal(trx)/10**6),'combined_TRX_WTRX_before_fee':str(Decimal(combined_trx)/10**6),'fee_TRX':str(Decimal(fee)/10**6),'USDT_net':str(Decimal(usdt)/10**6),'other_token_residual_raw':other,'pool_net_to_trader_raw':{tok:str(v) for tok,v in poolnet.items() if v},'swap_events':events,'pool_legs':legs,'mechanically_closed_positive_USDT_cycle':closed,'pool_TRX_WTRX_surplus':str(Decimal(pooltrx)/10**6),'pool_boundary_USDT_gap_raw':str(poolnet.get(U,0)-usdt),'pool_boundary_TRX_gap_raw':str(pooltrx-combined_trx),'unresolved_v4':unresolved_v4,'external_native_payouts':[f for f in native if f['sender'] in accounts and f['recipient'] not in accounts],'external_token_payouts':[f for f in flows if f['sender'] in accounts and f['recipient'] not in accounts and f['recipient'] not in pools],'resource_receipt':r.get('receipt',{}),'evidence':{'receipt':row['receipt_evidence'],'transaction':row['transaction_evidence']},'limit':'Operational owner+nonpublic entry boundary, not proven common beneficial ownership. Internal transfers rely on node saved/rejected flags. Paid TRX fee is observed; delegated-energy rental or offchain costs are not imputed.'}

def run():
    p=ROOT/'data/processed/mev_tron';raw=json.loads((p/'named_bot_receipts.json').read_text());keys={(r['manager_hex'],r['pool_id']):r for r in json.loads((p/'sun_v4_pool_keys.json').read_text())};rows=[parse(r,keys) for r in raw];b=book_from_archive();b.engine=Reconstruction(ROOT.parent/'research',True);b.binance_spot('TRX',('2026-10-29','2026-10-30'));b.loaded.add('TRX')
    for r in rows:
        st=b.price('USDT',r['timestamp']);tr=b.price('TRX',r['timestamp'],venue='Binance');fee=Decimal(r['fee_TRX'])*tr[0] if tr else None
        r['fee_USD']=str(fee) if fee is not None else None;r['marked_USDT_net_USD']=str(Decimal(r['USDT_net'])*st[0]) if st else None;r['price_evidence']={'USDT':st[1] if st else None,'TRX':tr[1] if tr else None}
        r['closed_cycle_after_paid_fee_USD']=str(Decimal(r['USDT_net'])*st[0]+Decimal(r['combined_TRX_WTRX_before_fee'])*tr[0]-fee) if r['mechanically_closed_positive_USDT_cycle'] and st and fee is not None else None
    (p/'named_bot_accounting.json').write_text(json.dumps(rows,indent=2));cycles=[r for r in rows if r['mechanically_closed_positive_USDT_cycle']];priced=[r for r in cycles if r['closed_cycle_after_paid_fee_USD'] is not None];summary={'transactions':len(rows),'success':sum(r['success'] for r in rows),'mechanically_closed_USDT_cycles':len(cycles),'cycle_TRX_WTRX_surplus':str(sum((Decimal(r['combined_TRX_WTRX_before_fee']) for r in cycles),Decimal(0))),'cycle_USDT_surplus':str(sum((Decimal(r['USDT_net']) for r in cycles),Decimal(0))),'priced_cycles':len(priced),'cycles_after_observed_paid_fees_USD':str(sum((Decimal(r['closed_cycle_after_paid_fee_USD']) for r in priced),Decimal(0))) if priced else None,'all_event_profit_established':False};(p/'named_bot_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
