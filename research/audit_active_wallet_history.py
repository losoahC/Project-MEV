import json,gzip
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
from fetch_expanded_scope_details import call,PCAKE
from screen_expanded import swaps,net_for
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def receipt_block(n):
 for p in [R/'scope_detail_raw'/f'{n}_receipts.json.gz',R/('window_raw' if n<=26301940 else 'extension_raw')/f'{n}.json.gz']:
  if p.exists():
   d=json.loads(gzip.decompress(p.read_bytes()));return d['result'] if isinstance(d,dict) else d
 return call(n,'receipts')
def main():
 xs=load('wallet_active_history.json')['rows'];known={r['hash'] for r in load('全部兑换时间线.json')['rows']};ws={r['address'] for r in load('exploiter_1_16_and_bot_audit.json')['wallets']};cache={};errors=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  fs={pool.submit(receipt_block,n):n for n in {x['block_number'] for x in xs}}
  for f in as_completed(fs):
   try:cache[fs[f]]={r['transactionHash']:r for r in f.result()}
   except Exception as e:errors.append({'block':fs[f],'error':str(e)})
 rows=[]
 for x in xs:
  if x['block_number'] not in cache:continue
  r=cache[x['block_number']][x['hash']];ss=swaps(r);pc=[l['address'] for l in r['logs'] if l['topics'] and l['topics'][0]==PCAKE];net=net_for(r,ws);pool=bool(ss or pc);success=int(r['status'],16)==1
  cat='failed' if not success else 'pool_swap_activity' if pool else 'plain_native_transfer' if x['raw_input']=='0x' else 'other_contract_call'
  rows.append({'hash':x['hash'],'block':x['block_number'],'from':r['from'],'to':r['to'],'category':cat,'known_exchange':x['hash'] in known,'pool_events':ss,'pancake_pools':pc,'wallet_set_token_net_raw':net,'native_value_wei':x['value'],'method':x.get('method'),'gas_wei':str(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16))})
 out={'scope':'All explorer-indexed top-level transactions SENT by the 16 wallets at or before study cutoff. Does not classify passive inbound or internal-only interactions. Receipt-derived categories are triage, not complete protocol semantics.','errors':errors,'summary':dict(Counter(r['category'] for r in rows)),'new_pool_activity':[r for r in rows if r['category']=='pool_swap_activity' and not r['known_exchange']],'rows':rows};(R/'wallet_active_history_audit.json').write_text(json.dumps(out,indent=2));print(out['summary'],'new_pool_activity',len(out['new_pool_activity']),'errors',errors)
if __name__=='__main__':main()
