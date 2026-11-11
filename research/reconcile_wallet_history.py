import json,gzip
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent
coverage=json.loads((R/'wallet_history_coverage.json').read_text());targets={r['hash'] for r in json.loads((R/'全部兑换时间线.json').read_text())['rows']};allrows={};cutoff=26349764
for scan in coverage['rows']:
 for p in scan['pages']:
  for x in json.loads(gzip.decompress((R/p).read_bytes()))['items']:
   h=x.get('hash') if scan['endpoint']=='transactions' else x.get('transaction_hash')
   if not h:continue
   r=allrows.setdefault(h,{'hash':h,'wallets':set(),'endpoints':set(),'block':x.get('block_number'),'known_exchange':h in targets});r['wallets'].add(scan['wallet']);r['endpoints'].add(scan['endpoint'])
   if r['block'] is None:r['block']=x.get('block_number')
rows=[{**r,'wallets':sorted(r['wallets']),'endpoints':sorted(r['endpoints'])} for r in allrows.values()]
summary={'endpoint_scans':len(coverage['rows']),'exhausted':sum(r['pagination_exhausted'] for r in coverage['rows']),'distinct_transaction_hashes':len(rows),'at_or_before_cutoff':sum(r['block'] is not None and r['block']<=cutoff for r in rows),'unclassified_at_or_before_cutoff':sum(r['block'] is not None and r['block']<=cutoff and not r['known_exchange'] for r in rows)}
(R/'wallet_history_reconciliation.json').write_text(json.dumps({'summary':summary,'warning':'Unclassified includes ordinary transfers, spam, lending and other non-exchange activity; not all are missing MEV. Indexer pagination exhaustion is not independent chain completeness.','rows':rows},indent=2));print(summary)
