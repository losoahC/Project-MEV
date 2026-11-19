"""Collect actual independent candles for contract-mapped price gaps; failures stay evidence."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from urllib.parse import urlencode
from src.ingestion.public_evidence import PublicEvidence
from src.ingestion.evidence import read_json
from src.visualization.common import ROOT


def run(online=False):
    public=PublicEvidence(ROOT,online);rows=read_json(ROOT/'data/processed/wallet_swap_valuations.json')
    periods=defaultdict(set)
    for r in rows:
        for a in r['missing_assets']:
            if a.get('symbol'):
                # Additional 15 minutes supports prespecified timing sensitivity.
                periods[a['symbol']].update(range(r['timestamp']//60*60-15*60,r['timestamp']//60*60,60))
    jobs=[]
    for symbol,times in sorted(periods.items()):
        # Small bounded pages; include the closing snapshot minute for common-mark checks.
        times.add(1793343660)
        buckets=defaultdict(list)
        for t in times:buckets[t//(240*60)].append(t)
        for timeset in buckets.values():
            start=min(timeset);end=max(timeset)+60
            fmt=lambda t:datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            url='https://api.exchange.coinbase.com/products/'+symbol+'-USD/candles?'+urlencode({'granularity':60,'start':fmt(start),'end':fmt(end)})
            jobs.append((symbol,url,start,end))
    def fetch(job):
        symbol,url,start,end=job;d,path=public.get(url);response=d.get('response')
        usable=d.get('http_status')==200 and isinstance(response,list) and all(isinstance(r,list) and len(r)==6 for r in response)
        return {'symbol':symbol,'venue':'Coinbase','quote':'USD','url':url,'start':start,'end':end,'evidence_path':path,'http_status':d.get('http_status'),'usable_candles':len(response) if usable else 0,'usable':usable,'error':d.get('error')}
    import time
    results=[]
    for job in jobs:
        result=fetch(job);results.append(result)
        if online and result.get('http_status')==429:
            # A failed immutable URL is retained, not replayed in a tight retry loop.
            time.sleep(15)
        elif online:
            time.sleep(1)
    index=ROOT/'data/processed/fresh_price_sources.json'
    prior=read_json(index) if index.exists() else []
    merged={item['url']:item for item in prior}
    for item in results:merged.setdefault(item['url'],item)
    index.write_text(json.dumps(list(merged.values()),indent=2))
    public.write_index();print('Price gap evidence:',len(results),'queries;',sum(r['usable'] for r in results),'usable;',sum(r['usable_candles'] for r in results),'candles',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');a=p.parse_args();run(a.online)
