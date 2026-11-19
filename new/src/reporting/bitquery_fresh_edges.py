import requests,json,datetime,pathlib,pandas as pd
from concurrent.futures import ThreadPoolExecutor
r=pathlib.Path(__file__).resolve().parents[2];e=pd.read_parquet(r/'data/processed/wallet_edges.parquet');w=json.loads((r/'data/processed/wallet_registry.json').read_text());reg={x['address']:x['number'] for x in w};d=e[e.symbol.eq('USDT')].copy();d=d[(d.amount.astype(float)>=50e6)&(d.sender.isin(reg)|d.recipient.isin(reg))].copy()
def check(row):
 h=row['tx_hash'];j=requests.post('https://eth.drpc.org',json={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[h]},timeout=25).json();v=j.get('result');ok=False
 if isinstance(v,dict):
  for l in v.get('logs',[]):
   if int(l['logIndex'],16)==int(row['log_index']):ok=(l['address'].lower()==row['token'] and '0x'+l['topics'][1][-40:]==row['sender'] and '0x'+l['topics'][2][-40:]==row['recipient'] and int(l['data'],16)==int(row['amount_raw']) and v['blockHash']==row['block_hash'] and v['transactionHash']==h)
 return {'edge_id':row['edge_id'],'tx_hash':h,'endpoint':'https://eth.drpc.org','retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'match_exact_receipt_event':ok,'response':j}
with ThreadPoolExecutor(max_workers=4) as ex:res=list(ex.map(check,d.to_dict('records')))
out=r/'reports/bitquery_check';(out/'fresh_edge_receipts.json').write_text(json.dumps(res,indent=2));d.to_parquet(out/'usdt_backbone_edges.parquet',index=False);print('edges',len(d),'exact matches',sum(x['match_exact_receipt_event'] for x in res));print([(x['tx_hash'],x['match_exact_receipt_event']) for x in res])
