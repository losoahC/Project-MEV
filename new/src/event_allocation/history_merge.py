"""Crosscheck full operator histories and admit only evidenced failed-pool costs."""
import json,gzip,hashlib
from collections import Counter,defaultdict
from src.event_allocation.config import ROOT,OUT,START,END
from src.ingestion.evidence import read_json
from src.event_allocation.tron_journal import address,MANAGER

def run():
    hs=json.loads((OUT/'tron_operator_history_summary.json').read_text());assert hs['finished'] and hs['operators_completed']==hs['operators_requested'];fi=json.loads((OUT/'tron_failed_receipt_index.json').read_text());assert fi['finished'];hist={};c=Counter()
    for f in (OUT/'tron_operator_history').glob('*.json'):
        d=json.loads(f.read_text());assert d['complete']
        for h,r in d['rows'].items():
            assert h not in hist;assert START*1000<=r['transaction']['block_timestamp']<END*1000;hist[h]=r;c['outgoing_transactions']+=1;c['failed_transactions']+=r['failed'];c['raw_protobuf_matches_txid']+=hashlib.sha256(bytes.fromhex(r['transaction']['raw_data_hex'])).hexdigest()==h
    meta=json.loads((OUT/'tron_root_transactions.json').read_text())['rows'];idx=json.loads((OUT/'tron_receipt_index.json').read_text());assert idx['finished'];cross=[]
    assert set(fi['rows'])=={h for h,r in hist.items() if r['failed']},'Every failed transaction from the completed history must have its own actual receipt.'
    for h,m in meta.items():
        assert h in hist,h;t=hist[h]['transaction'];r=read_json(ROOT/idx['rows'][h]);r=r.get('response',r);params=t['raw_data']['contract'][0]['parameter']['value'];tx=m['transaction'];assert params['owner_address']==address(tx['from']);assert params['contract_address']==address(tx['to']);assert int(params.get('call_value',0))==int(tx['value'],16);assert t['blockNumber']==int(tx['blockNumber'],16)==r['blockNumber'];assert t['block_timestamp']==r['blockTimeStamp'];assert sum(int(x.get('fee',0)) for x in t['ret'])==int(r.get('fee',0));c['pool_transactions_history_root_value_owner_time_fee_match']+=1
    base=json.loads((OUT/'tron_pool_journal_summary.json').read_text());first={k:tuple(v) for k,v in base['first_target_by_pool'].items()};summary=Counter({k:v for k,v in base.items() if isinstance(v,int) and not isinstance(v,bool)});out=OUT/'tron_journal.partial.jsonl.gz';known=set();failed_rows=[];unknown=[]
    with gzip.open(out,'wt') as dst,gzip.open(OUT/'tron_pool_journal.jsonl.gz','rt') as src:
        for line in src:dst.write(line);known.add(json.loads(line)['tx_hash'])
        for h,item in fi['rows'].items():
            assert h not in known;record=hist[h];t=record['transaction'];doc=read_json(ROOT/item['evidence']);r=doc.get('response',doc);assert r.get('receipt',{}).get('result','SUCCESS')!='SUCCESS';assert r['id']==h and r['blockNumber']==t['blockNumber'] and r['blockTimeStamp']==t['block_timestamp'];ts=int(r['blockTimeStamp'])//1000;assert START<=ts<END;contract=t['raw_data']['contract'][0]['parameter']['value'];owner=address(contract['owner_address']);entry_raw=contract.get('contract_address') or r.get('contract_address') or contract.get('to_address');entry=address(entry_raw) if entry_raw else '';matched={entry} & set(first)
            for call in r.get('internal_transactions',[]):
                recipient=address(call['transferTo_address'])
                if recipient in first:matched.add(recipient)
            if entry==MANAGER:
                keys=json.loads((ROOT/'data/processed/mev_tron/sun_v4_pool_keys.json').read_text());data=contract.get('data','')
                for key in keys:
                    k=MANAGER+':'+key['pool_id']
                    if k in first and key['encoded_key'].removeprefix('0x') in data:matched.add(k)
            post={k for k in matched if r['blockNumber']>first[k][0]};same_block={k for k in matched if r['blockNumber']==first[k][0]};category='failed_attempt_after_target' if post else 'same_block_failed_order_unassigned' if same_block else 'failed_attempt_before_target_control' if matched else 'same_operator_failed_context_unassigned';fee=int(r.get('fee',0));entries=[{'address':owner,'asset':'native:trx','raw':str(-fee),'component':'cash'},{'address':'protocol:tron_resource_fee','asset':'native:trx','raw':str(fee),'component':'cash'}] if fee else []
            row={'chain':'tron','tx_hash':h,'block':r['blockNumber'],'index':-1,'timestamp':ts,'sender':owner,'entrypoint':entry,'fee_recipient':'protocol:tron_resource_fee','gas_raw':str(fee),'base_burn_raw':'0','priority_raw':'0','blob_burn_raw':'0','entries':entries,'swap_events':[],'affected_pool_keys':sorted(matched),'last_prior_targets':sorted(post),'association':category,'position_events':[],'liquidity_actors':[],'position_risks':[],'evidence':{'receipt':item['evidence'],'history':record['evidence']},'raw_conservation_verified':True,'success':False,'failed_pool_reach_evidence':'Actual attempted contract call in root/internal receipt. Same-block ordering not inferred. V4 requires exact encoded PoolKey in root calldata.','fee_history_matches_actual_receipt':item['history_fee_matches_actual']};dst.write(json.dumps(row,separators=(',',':'))+'\n');summary['transactions']+=1;summary['entries']+=len(entries);summary[category]+=1;failed_rows.append({'tx_hash':h,'sender':owner,'block':r['blockNumber'],'timestamp':ts,'association':category,'fee_raw':str(fee),'same_entrypoint_as_successful_pool_trade':record['same_operator_entrypoint_as_pool_trade'],'fee_history_matches_actual_receipt':item['history_fee_matches_actual'],'evidence':row['evidence']})
    out.replace(OUT/'tron_journal.jsonl.gz');result={**base,**summary,'receipts_complete':True,'operator_histories_complete':True,'failed_receipts_complete':True,'all_fees_crosschecked':fi['all_fees_crosschecked_against_actual_receipts'],'all_rows_raw_conserve':True,'history_crosscheck':dict(c),'failed_transactions':len(failed_rows),'failed_same_block_order_unknown':summary['same_block_failed_order_unassigned']};(OUT/'tron_journal_summary.json').write_text(json.dumps(result,indent=2));(OUT/'tron_failed_costs.json').write_text(json.dumps(failed_rows,indent=2));(OUT/'tron_history_validation.json').write_text(json.dumps({'counts':dict(c),'all_9946_pool_root_calls_crosschecked_against_confirmed_history':len(meta)==c['pool_transactions_history_root_value_owner_time_fee_match'],'interpretation':'Indexed protobuf hash checks are recorded, not blanket signature certification. Pool-root owner/value/block/time/actual fee crosscheck is separate from signature authenticity.'},indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['first_target_by_pool','asset_frequency','failures']},indent=2))
if __name__=='__main__':run()
