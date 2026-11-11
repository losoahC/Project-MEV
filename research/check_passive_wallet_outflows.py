import json
from pathlib import Path
from audit_active_wallet_history import receipt_block
from screen_expanded import swaps,net_for
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parent;xs=json.loads((R/'wallet_passive_outflow_followup.json').read_text())['rows'];ws={x['address'] for x in json.loads((R/'exploiter_1_16_and_bot_audit.json').read_text())['wallets']}
def one(x):
 h=x['transaction_hash'];r=next(r for r in receipt_block(x['block_number']) if r['transactionHash']==h);net=net_for(r,ws);return {'hash':h,'block':x['block_number'],'pool_events':swaps(r),'net_token_raw':net,'from':r['from'],'to':r['to'],'net_out':any(int(v)<0 for v in net.values()),'zero_value_indexed_transfer':all(int(v)==0 for v in net.values())}
with ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(one,xs))
(R/'wallet_passive_outflow_audit.json').write_text(json.dumps({'rows':rows},indent=2));print('rows',len(rows),'nonzero out',sum(r['net_out'] for r in rows),'swaps',sum(bool(r['pool_events']) for r in rows));print([(r['hash'],r['net_token_raw']) for r in rows if r['net_out']])
