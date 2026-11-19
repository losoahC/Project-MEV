"""A single staged export with an explicit non-additive secondary amount column."""
import csv,gzip,json
from decimal import Decimal
from collections import Counter
from src.event_allocation.config import ROOT,OUT,REPORT

def run():
    fields=['stage','chain','tx_hash','block','timestamp','record_id','basis','role','account_address','actual_sender','actual_recipient','asset','raw','USD','primary_additive_USD','overlaps_primary_transaction','quote_id','evidence_reference'];counts=Counter();seen=set();primary_sum=Decimal(0);path=REPORT/'all_stages_allocation.csv.gz'
    with gzip.open(path,'wt') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        with gzip.open(REPORT/'unified_allocation.csv.gz','rt') as src:
            for r in csv.DictReader(src):
                key=('primary',r['chain'],r['tx_hash'],r['allocation_record_index'],r['asset']);assert key not in seen;seen.add(key);counts['primary_asset_rows']+=1
                if r['USD']:primary_sum+=Decimal(r['USD'])
                w.writerow({'stage':'primary_reference_allocation','chain':r['chain'],'tx_hash':r['tx_hash'],'block':r['block'],'timestamp':r['timestamp'],'record_id':r['allocation_record_index']+':'+r['asset'],'basis':r['basis'],'role':r['role'],'account_address':r['address'],'actual_sender':'','actual_recipient':'','asset':r['asset'],'raw':r['raw'],'USD':r['USD'],'primary_additive_USD':r['USD'],'overlaps_primary_transaction':True,'quote_id':r['quote_id'],'evidence_reference':'data/processed/event_allocation/'+r['chain']+'_journal.jsonl.gz; locate tx_hash'})
        with gzip.open(REPORT/'whole_block_native_settlements.csv.gz','rt') as src:
            for r in csv.DictReader(src):
                key=('secondary','ethereum',r['tx_hash'],r['trace_address']);assert key not in seen;seen.add(key);counts['secondary_actual_native_transfer_rows']+=1
                w.writerow({'stage':'secondary_observed_whole_block_settlement','chain':'ethereum','tx_hash':r['tx_hash'],'block':r['block'],'timestamp':r['timestamp'],'record_id':r['trace_address'],'basis':'Actual native transfer; whole-block funding and event share are not inferred.','role':r['category'],'account_address':'','actual_sender':r['sender'],'actual_recipient':r['recipient'],'asset':'native:eth','raw':r['amount_raw'],'USD':r['USD'],'primary_additive_USD':'0','overlaps_primary_transaction':r['in_primary_transaction'],'quote_id':'native:eth@'+str(int(r['timestamp'])//60*60),'evidence_reference':r['evidence']})
    assert abs(primary_sum)<Decimal('1e-40');result={'rows':dict(counts),'all_stages_export':str(path.relative_to(ROOT)),'primary_signed_sum_USD':str(primary_sum),'secondary_additive_amount_USD':'0','unique_stage_record_keys':True,'interpretation':'Primary rows are signed reference-allocation entries. Secondary rows are directed observed native transfers. Never sum the mixed USD column as incident extraction; secondary primary_additive_USD is explicitly zero. The overlap flag prevents mistaking a second observation of an already-included transaction for new extraction.'};(OUT/'combined_ledger_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':run()
