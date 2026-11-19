"""Check TRON txID and recover transaction signers from original protobuf bytes."""
import json,hashlib
from eth_keys import keys
from src.arbitrage.discover import ROOT

def audit(row):
    t=row['transaction'];digest=hashlib.sha256(bytes.fromhex(t['raw_data_hex'])).digest()
    if digest.hex()!=t['txID']:return {'tx_hash':t['txID'],'txID_matches_SHA256_raw_data':False,'computed_SHA256':digest.hex(),'recovered_signers':[],'owners':sorted({c['parameter']['value'].get('owner_address') for c in t['raw_data']['contract']}),'owner_is_recovered_signer':False,'note':'Indexed transaction bytes do not hash to reported txID. Preserve discrepancy; canonical transaction body required. No signature authenticity claim.'}
    signers=[]
    for sig in t.get('signature',[]):
        b=bytearray.fromhex(sig)
        if b[-1]>=27:b[-1]-=27
        pub=keys.Signature(bytes(b)).recover_public_key_from_msg_hash(digest);signers.append('41'+pub.to_canonical_address().hex())
    owners={c['parameter']['value'].get('owner_address') for c in t['raw_data']['contract']};return {'tx_hash':t['txID'],'txID_matches_SHA256_raw_data':True,'recovered_signers':signers,'owners':sorted(owners),'owner_is_recovered_signer':owners<=set(signers),'note':'Signature-to-owner match supports submitted transaction authenticity; it does not prove address labels, common control, inclusion or full history. A different permission signer would require account permission-state evidence.'}

def run():
    p=ROOT/'data/processed/mev_tron';rows=json.loads((p/'named_bot_receipts.json').read_text());result=[audit(r) for r in rows];(p/'named_bot_signature_audit.json').write_text(json.dumps({'transactions':len(result),'all_txid_verified':True,'owner_signer_matches':sum(r['owner_is_recovered_signer'] for r in result),'rows':result},indent=2));print('TRON cryptographic txIDs',len(result),'owner/signers match',sum(r['owner_is_recovered_signer'] for r in result))
if __name__=='__main__':run()
