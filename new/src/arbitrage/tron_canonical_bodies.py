"""Resolve indexed raw-byte/txID discrepancies against solidified transaction bodies."""
import json,hashlib
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_more import fetch

def run():
    p=ROOT/'data/processed/mev_tron';rows=[r for path in p.glob('*/receipts.json') for r in json.loads(path.read_text())];bad=[r for r in rows if hashlib.sha256(bytes.fromhex(r['transaction']['raw_data_hex'])).hexdigest()!=r['tx_hash']];result=[]
    for row in bad:
        h=row['tx_hash'];d,path=fetch('https://api.trongrid.io/walletsolidity/gettransactionbyid',{'value':h});t=d.get('response',{});verified=t.get('txID')==h and hashlib.sha256(bytes.fromhex(t.get('raw_data_hex',''))).hexdigest()==h;result.append({'tx_hash':h,'indexed_transaction_evidence':row['transaction_evidence'],'canonical_evidence':path,'canonical_hash_verified':verified,'canonical_transaction':t if verified else None,'error':None if verified else d.get('response',d.get('error'))})
    (p/'canonical_transaction_overrides.json').write_text(json.dumps(result,indent=2));print('Indexed hash discrepancies',len(bad),'canonical corrected',sum(r['canonical_hash_verified'] for r in result))
if __name__=='__main__':run()
