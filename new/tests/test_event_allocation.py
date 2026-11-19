"""Economic counterexamples and accounting/scope invariants of the event budget."""
from decimal import Decimal
from types import SimpleNamespace
from src.event_allocation.allocate import Pools,subsequent_allocation,target_allocation
from src.event_allocation.quotes import Quotes
from src.event_allocation.tron_journal import journal,W,ZERO

def fake_pools():
    p=Pools.__new__(Pools);p.meta={'pool':{'token0':'native:eth','token1':'usd'}};p.keys={};p.tron={};p.tk={};p.first={('ethereum','pool'):(10,2)};p.hackers={'ethereum':{'maker'}};return p

def trade(pool='pool',log=1):return {'pool':pool,'pool_key':pool,'log_index':log,'protocol':'V3-compatible','amount0_raw':'-100','amount1_raw':'200'}

def transaction():return {'chain':'ethereum','tx_hash':'tx','block':11,'index':0,'sender':'trader','fee_recipient':'builder','gas_raw':'15','priority_raw':'5','base_burn_raw':'10','blob_burn_raw':'0','entries':[{'address':'builder','asset':'native:eth','raw':'12','component':'cash'}],'swap_events':[trade()],'association':'after_prior_target','position_events':[],'liquidity_actors':[]}

def totals(rows):
    d={}
    for _,_,v in rows:
        for a,r in v.items():d[a]=d.get(a,0)+int(r)
    return d

def test_direct_tip_priority_burn_are_not_double_charged_across_pools():
    p=fake_pools();p.meta['second']=p.meta['pool'];p.first['ethereum','second']=(10,2);r=transaction();r['swap_events'].append(trade('second',2));rows,errors,ids=subsequent_allocation(r,p)
    assert not errors and len(ids)==2 and not any(totals(rows).values())
    assert sum(v.get('native:eth',0) for role,_,v in rows if role=='block_recipient_receipts')==12
    # Priority 5 + direct tip 7 + burn 10 = total cost 22, not 27 or 44.
    assert next(v for role,_,v in rows if role=='operating_address_incident_leg_reference_edge')['native:eth']==178

def test_before_first_target_and_other_pool_are_controls_even_in_same_transaction():
    p=fake_pools();r=transaction();r['block']=10;r['index']=1
    assert subsequent_allocation(r,p)[0]==[]
    r['block']=11;r['swap_events']=[trade('unrelated')]
    assert subsequent_allocation(r,p)[0]==[]

def test_failed_attempt_cost_stays_negative_without_fictitious_swap_gain():
    p=fake_pools();r=transaction();r['association']='failed_attempt_after_target';r['swap_events']=[];r['entries'][0]['raw']='5';rows,_,ids=subsequent_allocation(r,p)
    assert not ids and not any(totals(rows).values())
    assert next(v for role,_,v in rows if role=='operating_address_incident_leg_reference_edge')['native:eth']==-15

def test_priority_paid_back_to_the_same_sender_is_internal():
    p=fake_pools();r=transaction();r['fee_recipient']=r['sender'];rows,_,_=subsequent_allocation(r,p)
    assert not any(totals(rows).values())
    assert next(v for role,_,v in rows if role=='operating_address_incident_leg_reference_edge')['native:eth']==90
    assert not next(v for role,_,v in rows if role=='block_recipient_receipts')

def test_v4_event_is_trader_delta_and_claim_liability_is_not_lp_profit():
    p=fake_pools();p.keys['manager:id']={'currency0':'native:eth','currency1':'usd'};e=trade('manager:id');e['protocol']='V4-compatible'
    assert dict(p.leg('ethereum',e))=={'native:eth':100,'usd':-200}

def test_loan_principal_is_not_invented_receiver_income():
    p=fake_pools();r=transaction();r['swap_events']=[];r['entries']=[{'address':a,'asset':'native:eth','raw':str(n),'component':c} for a,n,c in [('borrower',100,'cash'),('lender',-100,'cash'),('borrower',-100,'position_principal'),('lender',100,'position_principal')]];r['position_events']=[{'emitter':'lender','owner':'borrower'}]
    rows,_=target_allocation(r,p);assert all(not any(v.values()) for _,_,v in rows)

def test_nonfuture_contract_quote_and_explicit_missing_never_zero():
    q=Quotes.__new__(Quotes);q.mode='primary';q.book=SimpleNamespace(registry={});q.decimals={'coin':{'decimals':6}};q.receipts={};q.tron_metadata={};q.stables=set();q.cache={};q.records={};q.secondary={'coin':[(599,{'quote':{'price':2,'confidence':.99},'evidence':'past'}),(601,{'quote':{'price':999,'confidence':.99},'evidence':'future'})]}
    assert q.value('coin',10**6,610)==Decimal(2)
    assert q.quote('coin',659)==q.quote('coin',610)
    assert q.value('coin',10**6,1800) is None
    assert q.vector({'unknown':123},610)['unpriced_raw']=={'unknown':'123'}

def test_tron_wrapping_does_not_double_count_backing_or_estimate_staked_energy_fee():
    owner='41'+'1'*40;wrapper=W;h='ab'*32;meta={'transaction':{'hash':'0x'+h,'blockNumber':'0x64','transactionIndex':'0x1','from':'0x'+owner[2:],'to':'0x'+wrapper[2:],'value':hex(100),'gasPrice':'0x64'},'evidence':'source','batch_id':1}
    from src.arbitrage.accounting import DEPOSIT
    receipt={'id':h,'blockNumber':100,'blockTimeStamp':1793306000000,'fee':7,'receipt':{'energy_usage_total':100000},'log':[{'address':wrapper[2:],'topics':[DEPOSIT[2:],'0'*24+owner[2:]],'data':hex(100)[2:].rjust(64,'0')}]}
    r=journal(meta,receipt,{}, {},'receipt');assert r['gas_raw']=='7'
    sums={}
    for e in r['entries']:sums[e['address']]=sums.get(e['address'],0)+int(e['raw'])
    assert sums[owner]==-7 and sums.get(wrapper,0)==0 and sums['protocol:tron_resource_fee']==7

def test_explicit_log_only_rights_extraction_keeps_empty_trace_validation():
    import pytest
    from src.arbitrage.transfer_audit import receipt_movements
    r={'logs':[{'address':'0x'+'3'*40,'topics':['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef','0x'+'0'*64,'0x'+'0'*24+'1'*40,'0x'+hex(123)[2:].rjust(64,'0')],'data':'0x','logIndex':'0x0'}]}
    movements=list(receipt_movements(r,None));assert len(movements)==1 and movements[0]['asset'].endswith(':123')
    with pytest.raises(ValueError):list(receipt_movements(r,[]))

def test_failed_tron_receipt_with_zero_paid_sun_does_not_invent_gas_cost():
    owner='41'+'1'*40;h='ef'*32;meta={'transaction':{'hash':'0x'+h,'blockNumber':'0x64','transactionIndex':'0x1','from':'0x'+owner[2:],'to':'0x'+'2'*40,'value':'0x64'},'evidence':'source','batch_id':1};receipt={'id':h,'blockNumber':100,'blockTimeStamp':1793306000000,'receipt':{'result':'REVERT','energy_usage_total':120000}}
    r=journal(meta,receipt,{}, {},'receipt');assert r['gas_raw']=='0' and r['entries']==[] and r['success'] is False

def test_indexed_proto3_zero_recovery_matches_independent_canonical_node_fixture():
    import json
    from src.event_allocation.config import ROOT,OUT
    from src.event_allocation.tron_encoding import recover
    from src.arbitrage.tron_collect import encode_addr
    fixture=next(r for r in json.loads((ROOT/'data/processed/mev_tron/canonical_transaction_overrides.json').read_text()) if r['canonical_hash_verified']);canonical=fixture['canonical_transaction'];owner=canonical['raw_data']['contract'][0]['parameter']['value']['owner_address'];history=json.loads((OUT/'tron_operator_history'/(encode_addr(owner)+'.json')).read_text());indexed=history['rows'][canonical['txID']]['transaction'];raw,inserted,method=recover(indexed)
    assert raw.hex()==canonical['raw_data_hex'] and method=='explicit_zero_wire_reconstruction_hash_match' and inserted
