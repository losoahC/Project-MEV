"""All-address TRON cash/claims/principal journal from actual solidified receipts."""
import json,gzip,argparse
from collections import defaultdict,Counter
from web3 import Web3
from src.event_allocation.config import ROOT,OUT,START,END,setup
from src.ingestion.evidence import read_json
from src.arbitrage.tron_accounting import U,W,ZERO
from src.arbitrage.tron_collect import decode_addr,encode_addr
from src.arbitrage.justlend_positions import MARKETS
from src.arbitrage.accounting import DEPOSIT,WITHDRAWAL
from src.arbitrage.complete_surplus_ledger import CLAIM
from src.decoding.events import TRANSFER,signed_word
from src.decoding.extended_events import extended_swap
MANAGER=decode_addr('TVjuTE3V5bMVdpfNhid8kD2v35T2k1u1Br')
V4='04206ad2b7c0f463bff3dd4f33c5735b0f2957a351e4f79763a4fa9e775dd237'
def norm(a):return 'native:trx' if a in [W,ZERO] else a.lower()
def address(a):return '41'+a.removeprefix('0x')[-40:].lower()

def position_abis():
    rows=json.loads((ROOT/'data/processed/mev_tron/justlend_current_ABI.json').read_text())
    return {decode_addr(r['contract']):{Web3.keccak(text=e['name']+'('+','.join(i['type'] for i in e.get('inputs',[]))+')').hex().removeprefix('0x'):e for e in r['events']} for r in rows}

def journal(meta,receipt,keys,abis,evidence):
    tx=meta['transaction'];h=tx['hash'].removeprefix('0x');assert receipt['id']==h and receipt['blockNumber']==int(tx['blockNumber'],16)
    owner=address(tx['from']);entry=address(tx['to']);success=receipt.get('receipt',{}).get('result','SUCCESS')=='SUCCESS';cash=defaultdict(lambda:defaultdict(int));claims=defaultdict(lambda:defaultdict(int));positions=defaultdict(lambda:defaultdict(int));liability=defaultdict(int);minted=0;wrap=[];flows=[];swaps=[];pe=[]
    def move(a,b,asset,raw):cash[a][asset]-=raw;cash[b][asset]+=raw
    if success:
        move(owner,entry,'native:trx',int(tx['value'],16))
        for i,t in enumerate(receipt.get('internal_transactions',[])):
            if t.get('rejected'):continue
            note=bytes.fromhex(t.get('note','')).decode(errors='replace')
            if note not in ['call','create','suicide']:continue
            raw=sum(int(v.get('callValue',0)) for v in t.get('callValueInfo',[]) if not v.get('tokenId'))
            if raw:move(address(t['caller_address']),address(t['transferTo_address']),'native:trx',raw)
        for i,l in enumerate(receipt.get('log',[])):
            ts=l.get('topics',[]);emitter=address(l['address']);data=l.get('data','');words=[data[j:j+64] for j in range(0,len(data),64)]
            if len(ts)==3 and ts[0].lower()==TRANSFER[2:] and len(data)==64:
                a,b=address(ts[1]),address(ts[2]);raw=int(data,16);asset=norm(emitter);flows.append((emitter,a,b,raw))
                if emitter==W and ZERO in [a,b]:
                    if a!=ZERO:cash[a][asset]-=raw;minted-=raw
                    if b!=ZERO:cash[b][asset]+=raw;minted+=raw
                else:move(a,b,asset,raw)
            if emitter==W and len(ts)==2 and len(data)==64 and ts[0].lower() in [DEPOSIT[2:],WITHDRAWAL[2:]]:wrap.append((ts[0].lower(),address(ts[1]),int(data,16)))
            e=extended_swap({'address':'0x'+emitter[2:],'topics':['0x'+v for v in ts],'data':'0x'+data,'logIndex':i})
            if e:
                e.update(pool=emitter,pool_key=emitter if not e['protocol'].startswith('V4') else emitter+':'+e['pool_id'].removeprefix('0x'));swaps.append(e)
            elif emitter==MANAGER and ts and ts[0]==V4 and len(ts)==3 and len(words)==7:
                swaps.append({'protocol':'SunSwap V4-compatible','pool':emitter,'pool_key':emitter+':'+ts[1],'pool_id':ts[1],'amount0_raw':str(signed_word(words[0])),'amount1_raw':str(signed_word(words[1])),'log_index':i,'amount_sign_convention':'trader delta'})
            if emitter==MANAGER and len(ts)==4 and ts[0]==CLAIM[2:] and len(words)==2:
                cid=int(ts[3],16);assert cid<2**160;asset=norm('41'+hex(cid)[2:].rjust(40,'0'));raw=int(words[1],16);a,b=address(ts[1]),address(ts[2])
                if a!=ZERO:claims[a][asset]-=raw
                else:liability[asset]+=raw
                if b!=ZERO:claims[b][asset]+=raw
                else:liability[asset]-=raw
            if emitter in abis and ts and ts[0] in abis[emitter]:
                abi=abis[emitter][ts[0]];kind=abi['name']
                if kind not in ['Mint','Redeem','Borrow','RepayBorrow']:continue
                assert len(ts)==1 and len(words)==len(abi['inputs']);d={f['name']:address(w) if f['type']=='address' else int(w,16) for f,w in zip(abi['inputs'],words)};asset=norm(MARKETS[emitter])
                if kind=='Mint':a=d['minter'];raw=d['mintAmount']
                elif kind=='Redeem':a=d['redeemer'];raw=-d['redeemAmount']
                elif kind=='Borrow':a=d['borrower'];raw=-d['borrowAmount']
                else:a=d['borrower'];raw=d['repayAmount']
                positions[a][asset]+=raw;positions[emitter][asset]-=raw;pe.append({'event':kind,'emitter':emitter,'owner':a,'asset':asset,'principal_raw':str(raw),'log_index':i,'decoded':{k:str(v) for k,v in d.items()}})
        for topic,a,raw in wrap:
            deposit=topic==DEPOSIT[2:];already=any(t==W and v==raw and ((s==ZERO and r==a) if deposit else (s==a and r==ZERO)) for t,s,r,v in flows)
            if not already:signed=raw*(1 if deposit else -1);cash[a]['native:trx']+=signed;minted+=signed
        cash[W]['native:trx']-=minted
    fee=int(receipt.get('fee',0));move(owner,'protocol:tron_resource_fee','native:trx',fee)
    entries=[]
    for component,by in [('cash',cash),('V4_claim',claims),('position_principal',positions)]:
        for a,v in by.items():
            for asset,raw in v.items():
                if raw:entries.append({'address':a,'asset':asset,'raw':str(raw),'component':component})
    for asset,raw in liability.items():
        if raw:entries.append({'address':MANAGER,'asset':asset,'raw':str(-raw),'component':'V4_claim_backing_liability'})
    totals=defaultdict(int)
    for e in entries:totals[e['asset']]+=int(e['raw'])
    assert not {a:v for a,v in totals.items() if v},(h,dict(totals))
    return {'chain':'tron','tx_hash':h,'block':receipt['blockNumber'],'index':int(tx['transactionIndex'],16),'timestamp':int(receipt['blockTimeStamp'])//1000,'sender':owner,'entrypoint':entry,'fee_recipient':'protocol:tron_resource_fee','gas_raw':str(fee),'base_burn_raw':'0','priority_raw':'0','blob_burn_raw':'0','entries':entries,'swap_events':swaps,'position_events':pe,'position_risks':[],'liquidity_actors':[],'evidence':{'transaction':meta['evidence'],'transaction_batch_id':meta['batch_id'],'receipt':evidence},'raw_conservation_verified':True,'success':success}

def run(partial=False):
    setup();idx=json.loads((OUT/'tron_receipt_index.json').read_text())
    if not partial:assert idx['finished'] and idx['completed']==idx['requested'] and not idx['failures'], 'Receipt acquisition must finish first.'
    metadata=json.loads((OUT/'tron_root_transactions.json').read_text())['rows'];keys={r['manager_hex']+':'+r['pool_id']:r for r in json.loads((ROOT/'data/processed/mev_tron/sun_v4_pool_keys.json').read_text())};abis=position_abis();targets={r['tx_hash']:r for r in json.loads((ROOT/'data/processed/mev_tron/target_owner_accounting.json').read_text()) if START<=r['timestamp']<END and r['swap_events']};first={};indexed=defaultdict(list)
    for f in OUT.glob('tron_events_*.json'):
        for r in json.loads(f.read_text())['rows']:indexed[r['event']['transaction_id']].append(r)
    for h,t in targets.items():
        at=(t['block'],int(metadata[h]['transaction']['transactionIndex'],16))
        for e in t['swap_events']:
            k=e.get('pool_key',e['pool_hex']);k=k.replace('0x','41',1) if k.startswith('0x') else k
            first[k]=min(first.get(k,at),at)
    counts=Counter();failures=[];assets=Counter();name='tron_journal.partial' if partial else 'tron_pool_journal';seen=set()
    with gzip.open(OUT/(name+'.jsonl.gz'),'wt') as output:
        for h,path in idx['rows'].items():
            try:
                d=read_json(ROOT/path);r=journal(metadata[h],d.get('response',d),keys,abis,path);assert h not in seen;seen.add(h);assert START<=r['timestamp']<END
                for x in indexed[h]:
                    e=x['event'];assert e['block_number']==r['block'] and e['block_timestamp']//1000==r['timestamp'];i=e['event_index'];l=d.get('response',d)['log'][i];assert address(l['address'])==decode_addr(e['contract_address'])
                    if e['event_name']=='Swap':
                        ev=next(ev for ev in r['swap_events'] if ev['log_index']==i);result=e['result']
                        for side in [0,1]:
                            key='amount'+str(side)
                            if key in result:assert int(result[key])==int(ev[key+'_raw'])
                poolkeys={e['pool_key'] for e in r['swap_events']};affected=poolkeys&set(first);post={k for k in affected if first[k]<(r['block'],r['index'])};r['affected_pool_keys']=sorted(affected);r['last_prior_targets']=sorted(post);r['association']='target' if h in targets else 'after_prior_target' if post else 'before_first_target_control' if affected else 'unrelated_manager_pool_control';r['indexed_events_verified_against_receipt']=len(indexed[h]);output.write(json.dumps(r,separators=(',',':'))+'\n');counts['transactions']+=1;counts[r['association']]+=1;counts['entries']+=len(r['entries']);counts['verified_indexed_events']+=len(indexed[h])
                for e in r['entries']:assets[e['asset']]+=1
            except Exception as ex:failures.append({'tx_hash':h,'error':repr(ex)})
    summary={**counts,'first_target_by_pool':{k:list(v) for k,v in first.items()},'asset_frequency':dict(assets),'failures':failures,'receipts_complete':idx['finished'],'all_rows_raw_conserve':not failures};(OUT/(name+'_summary.json')).write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['asset_frequency','first_target_by_pool']},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');a=p.parse_args();run(a.partial)
