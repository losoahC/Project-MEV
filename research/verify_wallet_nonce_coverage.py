"""Independent historical nonce check of indexed outgoing transaction coverage."""
import json,gzip,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;C=R/'wallet_nonce_raw';C.mkdir(exist_ok=True);cutoff=26349764
load=lambda n:json.loads((R/n).read_text())
def main():
 wallets=load('exploiter_1_16_and_bot_audit.json')['wallets'];coverage=load('wallet_history_coverage.json')['rows'];rows=[]
 for w in wallets:
  a=w['address'];path=C/(a+'.json')
  if path.exists():d=json.loads(path.read_text())
  else:
   q={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionCount','params':[a,hex(cutoff)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':q,'response':json.loads(z.stdout)};assert 'result' in d['response'],d;path.write_text(json.dumps(d));time.sleep(.25)
  nonce=int(d['response']['result'],16);out={}
  for s in coverage:
   if s['wallet']!=w['number'] or s['endpoint']!='transactions':continue
   for p in s['pages']:
    for x in json.loads(gzip.decompress((R/p).read_bytes()))['items']:
     if x.get('block_number') is not None and x['block_number']<=cutoff and (x.get('from') or {}).get('hash','').lower()==a:out[x['hash']]=x
  ns=[int(x['nonce']) for x in out.values()];missing=sorted(set(range(nonce))-set(ns));duplicate=len(ns)-len(set(ns));extra=sorted(set(ns)-set(range(nonce)))
  rows.append({'wallet':w['number'],'address':a,'cutoff_block':cutoff,'chain_nonce':nonce,'indexed_outgoing_transactions':len(out),'distinct_nonces':len(set(ns)),'missing_nonces':missing,'duplicate_nonce_count':duplicate,'out_of_range_nonces':extra,'complete_outgoing_nonce_sequence':not missing and not duplicate and not extra and len(out)==nonce})
 out={'method':'Compare historical Ethereum account nonce to all indexed top-level outgoing transaction nonces at same cutoff, including failed transactions. Complete 0..nonce-1 proves indexed nonce sequence coverage under normal EOA nonce semantics; EIP-7702 authorizations/other nonce-changing behavior require separate audit if gaps appear. Does not prove inbound/internal/token history completeness.','rows':rows,'all_passed':all(r['complete_outgoing_nonce_sequence'] for r in rows)};(R/'wallet_nonce_coverage_validation.json').write_text(json.dumps(out,indent=2));print([(r['wallet'],r['chain_nonce'],r['indexed_outgoing_transactions'],r['complete_outgoing_nonce_sequence']) for r in rows])
if __name__=='__main__':main()
