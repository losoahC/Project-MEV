import json,gzip,subprocess,time
from pathlib import Path
from Crypto.Hash import keccak
from audit_target_v2_fees import call
R=Path(__file__).resolve().parent;C=R/'wallet_nonce_raw'
def rlp(v):
 if isinstance(v,int):v=v.to_bytes((v.bit_length()+7)//8,'big')
 if isinstance(v,list):
  z=b''.join(rlp(x) for x in v);return bytes([192+len(z)])+z if len(z)<56 else bytes([247+(len(z).bit_length()+7)//8])+len(z).to_bytes((len(z).bit_length()+7)//8,'big')+z
 if len(v)==1 and v[0]<128:return v
 return bytes([128+len(v)])+v

def rpc(method,a,n):
 p=C/f'{a}_{method}_{n}.json'
 if p.exists():return json.loads(p.read_text())['response']['result']
 q={'jsonrpc':'2.0','id':1,'method':method,'params':[a,hex(n)]};z=subprocess.run(['curl','--fail','--silent','--show-error','--max-time','30','-H','Content-Type: application/json','--data',json.dumps(q),'https://eth.drpc.org'],capture_output=True,check=True);d={'request':q,'response':json.loads(z.stdout)};assert 'result' in d['response'];p.write_text(json.dumps(d));time.sleep(.2);return d['response']['result']
def main():
 initial=json.loads((R/'wallet_nonce_coverage_validation.json').read_text());active=json.loads((R/'wallet_active_history.json').read_text())['rows'];rows=[]
 for w in initial['rows']:
  proofs=[]
  for missing in w['missing_nonces']:
   possible=[x for x in active if x['from']['hash'].lower()==w['address'] and x['type']==4 and x['nonce']==missing-1];assert len(possible)==1
   x=possible[0];n=x['block_number'];b=json.loads(gzip.decompress((R/'window_raw'/f'{n}_block.json.gz').read_bytes()));b=b.get('result',b);t=next(t for t in b['transactions'] if t['hash']==x['hash']);auth=next(a for a in t['authorizationList'] if int(a['nonce'],16)==missing)
   digest=keccak.new(digest_bits=256,data=b'\x05'+rlp([int(auth['chainId'],16),bytes.fromhex(auth['address'][2:]),missing])).digest();inp='0x'+digest.hex()+hex(27+int(auth['yParity'],16))[2:].zfill(64)+auth['r'][2:].zfill(64)+auth['s'][2:].zfill(64)
   recovered='0x'+call('nonce_auth_'+x['hash'],'0x0000000000000000000000000000000000000001',inp,n)[-40:];before=int(rpc('eth_getTransactionCount',w['address'],n-1),16);after=int(rpc('eth_getTransactionCount',w['address'],n),16);code=rpc('eth_getCode',w['address'],n)
   ok=recovered==w['address'] and before==missing-1 and after==missing+1 and code=='0xef0100'+auth['address'][2:];assert ok
   proofs.append({'transaction':x['hash'],'block':n,'authorization':auth,'signing_hash':'0x'+digest.hex(),'recovered_authority':recovered,'nonce_before_block':before,'nonce_after_block':after,'code_after_block':code,'explained_nonce':missing,'verified':ok})
  rows.append({**w,'authorization_nonce_proofs':proofs,'unexplained_nonces':sorted(set(w['missing_nonces'])-{p['explained_nonce'] for p in proofs}),'outgoing_nonce_accounting_complete':not w['duplicate_nonce_count'] and not w['out_of_range_nonces'] and len(proofs)==len(w['missing_nonces'])})
 out={'specification':'https://eips.ethereum.org/EIPS/eip-7702','method':'Historical account nonce reconciled to indexed outgoing nonces plus verified self-sponsored 7702 authority increments. Auth signatures recovered by Ethereum ecrecover precompile; before/after nonce and delegation code checked at historical blocks. Does not prove inbound histories complete.','rows':rows,'all_wallets_reconciled':all(r['outgoing_nonce_accounting_complete'] for r in rows),'outgoing_transactions':sum(r['indexed_outgoing_transactions'] for r in rows),'authorization_increments':sum(len(r['authorization_nonce_proofs']) for r in rows)};(R/'wallet_nonce_authorization_reconciliation.json').write_text(json.dumps(out,indent=2));print(out['all_wallets_reconciled'],out['outgoing_transactions'],out['authorization_increments'])
if __name__=='__main__':main()
