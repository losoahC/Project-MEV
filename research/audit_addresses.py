import json,gzip,argparse
from pathlib import Path
from collections import defaultdict
from screen_expanded import swaps,net_for
from identify_mev import TRANSFER
R=Path(__file__).resolve().parent
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--extension',action='store_true');args=parser.parse_args()
 fbi=set(json.loads((R/'fbi_eth_addresses.json').read_text())['addresses']);lead={w['address'].lower() for w in json.loads((R/'address_leads.json').read_text())['wallets']};extra=fbi-lead
 old={r['hash'] for r in json.loads((R/('extension_ledger.json' if args.extension else 'window_ledger.json')).read_text())['rows']};rows=[];active=set()
 for p in sorted((R/('extension_raw' if args.extension else 'window_raw')).glob('[0-9]*.json.gz')):
  if '_block' in p.name:continue
  for r in json.loads(gzip.decompress(p.read_bytes())):
   hit={a for a in [r['from'],r.get('to')] if a in extra}
   for l in r['logs']:
    t=l['topics']
    if len(t)==3 and t[0]==TRANSFER:
     hit.update(a for a in ['0x'+t[1][-40:],'0x'+t[2][-40:]] if a in extra)
   if not hit:continue
   active.update(hit);net=net_for(r,extra);ss=swaps(r)
   rows.append({'hash':r['transactionHash'],'block':int(r['blockNumber'],16),'extra_addresses':sorted(hit),'already_in_tracker_ledger':r['transactionHash'] in old,'net_token_raw':net,'swap_event_count':len(ss),'status':int(r['status'],16)})
 out={'fbi_addresses':len(fbi),'tracker_addresses':len(lead),'overlap':len(fbi&lead),'union':len(fbi|lead),'additional_active_addresses':len(active),'rows':rows,'caution':'FBI list says operated by OR closely connected; do not assume every address belongs to one owner'}
 (R/('extension_address_audit.json' if args.extension else 'address_scope_audit.json')).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'});print('transactions',len(rows),'novel',sum(not r['already_in_tracker_ledger'] for r in rows),'novel_swap_outflow',sum(not r['already_in_tracker_ledger'] and r['swap_event_count']>0 and any(int(v)<0 for v in r['net_token_raw'].values()) for r in rows))
if __name__=='__main__':main()
