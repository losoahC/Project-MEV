import json,gzip
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from fetch_expanded_scope_details import call
from audit_active_wallet_history import receipt_block
from rawtrace_native import parse
from screen_expanded import net_for,swaps
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
ws={x['address'] for x in load('exploiter_1_16_and_bot_audit.json')['wallets']}
def traces(n):
 p=R/'drpc_trace_raw'/f'{n}.json.gz'
 return json.loads(gzip.decompress(p.read_bytes()))['result'] if p.exists() else call(n,'trace')
def one(x):
 n=x['block'];h=x['hash'];ts=[t for t in traces(n) if t.get('transactionHash')==h];native=parse(h,ts);r=next(r for r in receipt_block(n) if r['transactionHash']==h)
 addresses=set();calls=[]
 for t in ts:
  a=t.get('action',{});addresses.update(a[k] for k in ['from','to'] if a.get(k));calls.append({'type':t['type'],'path':t['traceAddress'],'from':a.get('from'),'to':a.get('to'),'value':a.get('value'),'selector':a.get('input','')[:10],'error':t.get('error')})
 return {**x,'native':native,'wallet_net_token_raw':net_for(r,ws),'calls':calls,'receipt_logs':r['logs'],'pool_events':swaps(r),'interpretation':'contract_creation' if r['to'] is None else 'no_logs_native_movement' if not r['logs'] and native['native_net_wei'] else 'requires_protocol_semantics'}
def main():
 xs=[x for x in load('wallet_active_history_audit.json')['rows'] if x['category']=='other_contract_call' and (not x['method'] or x['method'].startswith('0x'))]
 with ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(one,xs))
 # Reconstruct the missed ETH sale pool neighborhood, including predecessor.
 target=load('wallet_active_history_audit.json')['new_pool_activity'][0];n=target['block'];pools={p['pool'] for p in target['pool_events']};neighbors=[]
 for b in range(n,n+6):
  for r in receipt_block(b):
   ev=[e for e in swaps(r) if e['pool'] in pools]
   if ev:neighbors.append({'hash':r['transactionHash'],'block':b,'index':int(r['transactionIndex'],16),'from':r['from'],'to':r['to'],'events':ev})
 out={'unknown_calls':rows,'missed_ETH_sale':target,'sale_pool_neighborhood':neighbors,'internal_outflow_reconciliation':load('wallet_internal_followup.json'),'limits':'No unknown-call semantics inferred from selector alone. Pool event compatibility does not verify factory. Indexed history may omit events.'}
 (R/'history_edge_cases_verified.json').write_text(json.dumps(out,indent=2));print('unknown calls',len(rows),'neighbor tx',len(neighbors));print([(r['hash'],r['interpretation'],len(r['receipt_logs'])) for r in rows])
if __name__=='__main__':main()
