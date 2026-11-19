"""Nonfungible position rights, separate from underlying cash and loan principal."""
import json,gzip,csv
from collections import defaultdict,Counter
from src.event_allocation.config import ROOT,OUT,REPORT
from src.ingestion.evidence import read_json
from src.arbitrage.transfer_audit import receipt_movements

def run():
    jobs=defaultdict(set);paths={};counts=Counter();seen=set()
    with gzip.open(OUT/'ethereum_journal.jsonl.gz','rt') as f:
        for line in f:r=json.loads(line);jobs[r['block']].add(r['tx_hash']);paths[r['block']]=r['evidence']['receipts']
    fields=['chain','tx_hash','block','asset','sender','recipient','amount_raw','event_type','reference','evidence'];rows=[]
    for i,(n,hashes) in enumerate(jobs.items(),1):
        receipts=read_json(ROOT/paths[n])
        for r in receipts:
            if r['transactionHash'] not in hashes:continue
            for movement in receipt_movements(r,None):
                if not movement['asset'].startswith(('erc721:','erc1155:')):continue
                k=('ethereum',r['transactionHash'],movement['reference'],movement['asset']);assert k not in seen;seen.add(k);rows.append({'chain':'ethereum','tx_hash':r['transactionHash'],'block':n,**{k:movement[k] for k in ['asset','sender','recipient','amount_raw','event_type','reference']},'evidence':paths[n]});counts[movement['event_type']]+=1
        if i%500==0:print('Position rights receipt blocks',i,'/',len(jobs),'movements',len(rows),flush=True)
    with gzip.open(REPORT/'nonfungible_position_rights.csv.gz','wt') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    (OUT/'nonfungible_position_rights_summary.json').write_text(json.dumps({'ethereum_receipt_blocks':len(jobs),'audited_transactions':sum(map(len,jobs.values())),'unique_position_right_movements':len(rows),'counts':dict(counts),'priced_as_extra_profit':False,'interpretation':'ERC721/1155 ownership or balance changes are recorded separately. Underlying LP cash flows already occur in the financial journal. No arbitrary NFT price, individual LP ownership share or extra cash profit is imputed.'},indent=2))
if __name__=='__main__':run()
