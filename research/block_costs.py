import json,gzip
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict
from decimal import Decimal
from enrich_window import block,R
def main():
 ledger=json.loads((R/'window_ledger.json').read_text());out=[];errors=[]
 with ThreadPoolExecutor(max_workers=5) as ex:
  fs={ex.submit(block,n):n for n in range(ledger['first_block'],ledger['last_block']+1)}
  for i,f in enumerate(as_completed(fs),1):
   n=fs[f]
   try:b=f.result()
   except Exception as e:errors.append({'block':n,'error':str(e)});continue
   rs=json.loads(gzip.decompress((R/'window_raw'/f'{n}.json.gz').read_bytes()));txs={t['hash']:t for t in b['transactions']}
   assert len(txs)==len(rs)
   assert all(r['blockHash']==b['hash'] for r in rs)
   base=int(b['baseFeePerGas'],16);burn=sum(int(r['gasUsed'],16)*base for r in rs);fee=sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in rs)
   failed=[r for r in rs if int(r['status'],16)==0]
   transfers=[{'hash':t['hash'],'to':t['to'],'value_wei':str(int(t['value'],16))} for t in txs.values() if t['from']==b['miner'] and int(t['value'],16)>0 and any(r['transactionHash']==t['hash'] and int(r['status'],16)==1 for r in rs)]
   out.append({'block':n,'timestamp':int(b['timestamp'],16),'miner':b['miner'],'transactions':len(rs),'gas_fee_wei':str(fee),'base_burn_wei':str(burn),'priority_fee_wei':str(fee-burn),'failed_count':len(failed),'failed_gas_fee_wei':str(sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in failed)),'miner_origin_value_transfers':transfers})
   if i%200==0:print('cost blocks',i,len(fs),'errors',len(errors),flush=True)
 out.sort(key=lambda x:x['block'])
 (R/'window_block_costs.json').write_text(json.dumps({'note':'Whole-window observed fees; not all caused by hacker. Miner-origin transfers are payment leads, not verified validator income; do not add to builder receipts','errors':errors,'rows':out},indent=2));print('DONE',len(out),len(errors),flush=True)
if __name__=='__main__':main()
