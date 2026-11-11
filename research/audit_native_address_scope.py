import json,gzip
from pathlib import Path
from collections import defaultdict
from rawtrace_native import parse
R=Path(__file__).resolve().parent
def main():
 leads={r['address'].lower() for r in json.loads((R/'address_leads.json').read_text())['wallets']};fbi=set(json.loads((R/'fbi_eth_addresses.json').read_text())['addresses']);fbi={a.lower() for a in fbi};extra=fbi-leads;known={r['hash'] for f in ['window_ledger.json','extension_ledger.json'] for r in json.loads((R/f).read_text())['rows']};rows=[];errors=[]
 for n in range(26300640,26303951):
  ts=json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result'];hits=set()
  for t in ts:
   a=t.get('action',{});addresses={a.get(k,'').lower() for k in ['from','to','address','refundAddress']}|{(t.get('result') or {}).get('address','').lower()}
   if addresses&(leads|extra) and t.get('transactionHash'):hits.add(t['transactionHash'])
  groups=defaultdict(list)
  for t in ts:
   if t.get('transactionHash') in hits:groups[t['transactionHash']].append(t)
  for h,trs in groups.items():
   try:
    nr=parse(h,trs);l={a:v for a,v in nr['native_net_wei'].items() if a in leads};e={a:v for a,v in nr['native_net_wei'].items() if a in extra}
    if l or e:rows.append({'hash':h,'block':n,'lead_net_wei':l,'additional_FBI_net_wei':e,'already_in_token_or_root_ledger':h in known})
   except Exception as e:errors.append({'hash':h,'error':str(e)})
  if (n-26300639)%700==0:print('native scope',n,'hits',len(rows),flush=True)
 out={'method':'All 3311 continuous-window traces checked including internal CALL/CREATE/SELFDESTRUCT. Reverted branches excluded. Amounts are native transfers, exclude gas/withdrawals. No claim same beneficial ownership for FBI-associated addresses. Later time period and other chains not covered here.','summary':{'blocks':3311,'lead_addresses':len(leads),'additional_FBI_addresses':len(extra),'native_flow_transactions':len(rows),'additional_FBI_native_flow_transactions':sum(bool(r['additional_FBI_net_wei']) for r in rows),'lead_native_transactions_missing_old_ledger':sum(bool(r['lead_net_wei']) and not r['already_in_token_or_root_ledger'] for r in rows)},'rows':rows,'errors':errors}
 (R/'native_address_scope_audit.json').write_text(json.dumps(out,indent=2));print(out['summary'],'errors',len(errors),flush=True)
if __name__=='__main__':main()
