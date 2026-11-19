"""Recover semantically equivalent explicit-zero Any payloads by exact txID hash.
Indexed JSON can omit proto3 defaults while original Any.value preserves their
wire bytes. Original evidence is immutable; candidates are stored separately.
Schema: tronprotocol/protocol core/contract/smart_contract.proto fields 3,5,6.
"""
import json,gzip,hashlib,itertools
from collections import Counter
from src.event_allocation.config import OUT

def varint(b,i):
    value=shift=0
    while True:
        x=b[i];i+=1;value|=(x&127)<<shift
        if x<128:return value,i
        shift+=7
        if shift>70:raise ValueError('Invalid protobuf integer')

def vint(n):
    out=bytearray()
    while n>127:out.append((n&127)|128);n>>=7
    out.append(n);return bytes(out)

def parse(b):
    rows=[];i=0
    while i<len(b):
        tag,i=varint(b,i);field,wire=tag>>3,tag&7
        if wire==0:value,i=varint(b,i)
        elif wire==2:length,i=varint(b,i);value=b[i:i+length];i+=length
        elif wire in [1,5]:length=8 if wire==1 else 4;value=b[i:i+length];i+=length
        else:raise ValueError('Unsupported protobuf wire type')
        rows.append((field,wire,value))
    assert i==len(b);return rows

def serialize(rows):return b''.join(vint((n<<3)|w)+(vint(v) if w==0 else vint(len(v))+v if w==2 else v) for n,w,v in rows)
def replace(rows,field,value):return [(n,w,value if n==field else v) for n,w,v in rows]

def recover(t):
    original=bytes.fromhex(t['raw_data_hex']);h=t['txID'];digest=hashlib.sha256(original).hexdigest()
    if digest==h:return original,[],'indexed_bytes_hash_match'
    contracts=t['raw_data']['contract']
    if len(contracts)!=1 or contracts[0]['type']!='TriggerSmartContract':return None,[],'unsupported_nontrigger_encoding'
    top=parse(original);contract=parse(next(v for n,w,v in top if n==11));parameter=parse(next(v for n,w,v in contract if n==2));payload=parse(next(v for n,w,v in parameter if n==2));fields={n:(w,v) for n,w,v in payload};p=contracts[0]['parameter']['value'];assert fields[1][1].hex()==p['owner_address'].lower() and fields[2][1].hex()==p['contract_address'].lower();assert fields.get(3,(0,0))[1]==int(p.get('call_value',0));assert fields.get(4,(2,b''))[1].hex()==p.get('data','').lower()
    eligible=[n for n,name in [(3,'call_value'),(5,'call_token_value'),(6,'token_id')] if n not in fields and int(p.get(name,0))==0]
    for flags in itertools.product([False,True],repeat=len(eligible)):
        inserted=[n for n,flag in zip(eligible,flags) if flag]
        if not inserted:continue
        modified=serialize(sorted(payload+[(n,0,0) for n in inserted],key=lambda x:x[0]));candidate=serialize(replace(top,11,serialize(replace(contract,2,serialize(replace(parameter,2,modified))))))
        if hashlib.sha256(candidate).hexdigest()==h:return candidate,inserted,'explicit_zero_wire_reconstruction_hash_match'
    return None,[],'encoding_not_recovered'

def run():
    relevant=set(json.loads((OUT/'tron_root_transactions.json').read_text())['rows'])|set(json.loads((OUT/'tron_failed_receipt_index.json').read_text())['rows']);counts=Counter();unresolved=[];resolved_relevant=0;op=OUT/'tron_encoding_node_overrides.json';overrides=json.loads(op.read_text()) if op.exists() else {}
    with gzip.open(OUT/'tron_encoding_proofs.jsonl.gz','wt') as dst:
        for f in (OUT/'tron_operator_history').glob('*.json'):
            record=json.loads(f.read_text());assert record['complete']
            for h,r in record['rows'].items():
                try:
                    if h in overrides:
                        canonical=overrides[h]['canonical_transaction'];raw=bytes.fromhex(canonical['raw_data_hex']);assert hashlib.sha256(raw).hexdigest()==h;before=r['transaction']['raw_data']['contract'][0]['parameter']['value'];after=canonical['raw_data']['contract'][0]['parameter']['value']
                        for field in ['owner_address','contract_address','data']:assert before.get(field,'')==after.get(field,'')
                        for field in ['call_value','call_token_value','token_id']:assert int(before.get(field,0))==int(after.get(field,0))
                        inserted=[];method='canonical_solidified_node_body_hash_match'
                    else:raw,inserted,method=recover(r['transaction'])
                except Exception as exc:raw=None;inserted=[];method='semantic_or_encoding_check_failed';error=repr(exc)
                counts['transactions']+=1;counts[method]+=1;resolved_relevant+=h in relevant and raw is not None
                if raw is None:unresolved.append({'tx_hash':h,'relevant_to_pool_or_failed_cost':h in relevant,'method':method,'evidence':r['evidence']})
                dst.write(json.dumps({'tx_hash':h,'method':method,'explicit_zero_fields_inserted':inserted,'hash_equals_reported_txid':raw is not None,'reconstructed_raw_data_hex':raw.hex() if raw is not None and inserted else None,'canonical_node_evidence':overrides[h]['evidence'] if h in overrides else None,'original_evidence':r['evidence'],'not_a_fresh_node_read':h not in overrides},separators=(',',':'))+'\n')
    result={'counts':dict(counts),'relevant_pool_and_failed_transactions':len(relevant),'relevant_txid_encodings_verified':resolved_relevant,'all_relevant_txid_encodings_verified':resolved_relevant==len(relevant),'unresolved':unresolved,'schema':'https://github.com/tronprotocol/protocol/blob/master/core/contract/smart_contract.proto','method':'Only semantically default-zero fields are inserted in TriggerSmartContract Any.value; every accepted candidate must SHA256 to the actual txID. Original bytes remain untouched. This proves the recovered encoding hash, not address labels or beneficial ownership.'};(OUT/'tron_encoding_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='unresolved'},indent=2))
def collect_unresolved():
    from src.arbitrage.tron_more import fetch
    from src.event_allocation.tron_evidence import Pace
    run();summary=json.loads((OUT/'tron_encoding_summary.json').read_text());path=OUT/'tron_encoding_node_overrides.json';overrides=json.loads(path.read_text()) if path.exists() else {};pace=Pace(4)
    for r in summary['unresolved']:
        if not r['relevant_to_pool_or_failed_cost']:continue
        h=r['tx_hash'];pace.wait();doc,evidence=fetch('https://tron-rpc.publicnode.com/walletsolidity/gettransactionbyid',{'value':h});t=doc['response'];assert t['txID']==h and hashlib.sha256(bytes.fromhex(t['raw_data_hex'])).hexdigest()==h;overrides[h]={'evidence':evidence,'canonical_transaction':t}
    path.write_text(json.dumps(overrides,indent=2));run()

if __name__=='__main__':run()
