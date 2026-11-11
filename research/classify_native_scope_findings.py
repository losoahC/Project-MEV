import json,gzip
from collections import defaultdict,Counter
from decimal import Decimal as D,getcontext
from pathlib import Path
from screen_expanded import net_for,swaps
R=Path(__file__).resolve().parent;getcontext().prec=60
def main():
 data=json.loads((R/'native_address_scope_audit.json').read_text());leads={r['address'].lower() for r in json.loads((R/'address_leads.json').read_text())['wallets']};fbi=set(json.loads((R/'fbi_eth_addresses.json').read_text())['addresses'])-leads;targets={r['hash'] for r in json.loads((R/'unified_target_valuation.json').read_text())['rows'] if r['eligible_exchange_candidate']};byblock=defaultdict(list)
 for r in data['rows']:
  if r['additional_FBI_net_wei'] or not r['already_in_token_or_root_ledger']:byblock[r['block']].append(r)
 rows=[];aggregate=defaultdict(int)
 for n,items in byblock.items():
  folder='window_raw' if n<=26301940 else 'extension_raw';rs={r['transactionHash']:r for r in json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()))};ts=defaultdict(list)
  for t in json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result']:
   if t.get('transactionHash'):ts[t['transactionHash']].append(t)
  for r in items:
   rec=rs[r['hash']];row={**r,'from':rec['from'],'to':rec['to'],'status':int(rec['status'],16),'lead_token_net':net_for(rec,leads),'additional_FBI_token_net':net_for(rec,fbi),'pool_swap_event_count':len(swaps(rec)),'overlaps_exchange_sample':r['hash'] in targets,'direct_native_paths_to_extra_FBI':[]}
   for t in ts[r['hash']]:
    a=t['action']
    if t['type']=='call' and a.get('callType')=='call' and a.get('to') in r['additional_FBI_net_wei'] and int(a.get('value','0x0'),16)>0:row['direct_native_paths_to_extra_FBI'].append({'from':a['from'],'to':a['to'],'value_wei':str(int(a['value'],16)),'trace_address':t['traceAddress'],'local_error':t.get('error')})
   for a,v in r['additional_FBI_net_wei'].items():aggregate[a]+=int(v)
   rows.append(row)
 out={'method':'Read-only classification of previously omitted native-only address activity. Additional FBI association is not proof of common ownership. Trace paths shown for context; authoritative net flow excludes reverted ancestors in native_address_scope_audit.','summary':{'reviewed_transactions':len(rows),'additional_FBI_addresses_with_native_net':len(aggregate),'additional_FBI_net_ETH':str(D(sum(aggregate.values()))/10**18),'additional_FBI_transactions_with_token_net':sum(bool(r['additional_FBI_token_net']) for r in rows),'additional_FBI_transactions_overlapping_exchange_sample':sum(bool(r['additional_FBI_net_wei']) and r['overlaps_exchange_sample'] for r in rows),'missing_old_ledger_lead_transactions_with_token_net':sum(not r['already_in_token_or_root_ledger'] and bool(r['lead_token_net']) for r in rows),'missing_old_ledger_lead_native_net_ETH':str(sum((D(sum(map(int,r['lead_net_wei'].values())))/10**18 for r in rows if not r['already_in_token_or_root_ledger']),D(0)))},'additional_FBI_address_native_net_wei':{a:str(v) for a,v in aggregate.items()},'rows':rows};(R/'native_scope_findings_classification.json').write_text(json.dumps(out,indent=2));print(out['summary'],flush=True)
if __name__=='__main__':main()
