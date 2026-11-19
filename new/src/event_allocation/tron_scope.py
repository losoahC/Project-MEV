"""Paginate all events at every target-touched TRON pool, not just four bots."""
import json,time,argparse
from collections import Counter
from urllib.parse import urlparse
from src.event_allocation.config import ROOT,OUT,START,END,setup
from src.ingestion.public_evidence import PublicEvidence

def run():
    setup();targets=json.loads((ROOT/'data/processed/mev_tron/target_owner_accounting.json').read_text());pools=sorted({e['pool_address'] for r in targets for e in r['swap_events'] if START<=r['timestamp']<END});api=PublicEvidence(ROOT,True);all_events={};coverage=[]
    for pool in pools:
        url=f'https://api.trongrid.io/v1/contracts/{pool}/events?only_confirmed=true&min_timestamp={START*1000}&max_timestamp={END*1000-1}&order_by=block_timestamp,asc&limit=200';seen=set();pages=[];events={};failure=None
        while url:
            if url in seen or urlparse(url).netloc!='api.trongrid.io':raise ValueError('Invalid pagination successor')
            seen.add(url);doc,path=api.get(url);data=doc.get('response') or {}
            if doc.get('http_status')!=200 or data.get('success') is not True:failure={'evidence':path,'http_status':doc.get('http_status'),'response':data,'error':doc.get('error')};break
            pages.append(path)
            for e in data.get('data',[]):
                assert e['contract_address']==pool and START*1000<=e['block_timestamp']<END*1000
                key=(e['transaction_id'],int(e['event_index']))
                if key in events:assert events[key]['event']==e
                else:events[key]={'event':e,'evidence':path}
            url=data.get('meta',{}).get('links',{}).get('next');time.sleep(.30)
            if len(pages)%10==0:print(pool,'pages',len(pages),'events',len(events),flush=True)
        record={'pool':pool,'pages':pages,'events':len(events),'transaction_count':len({k[0] for k in events}),'all_pages_complete':not url and failure is None,'failure':failure,'event_names':dict(Counter(r['event']['event_name'] for r in events.values()))};coverage.append(record)
        for (h,i),r in events.items():
            key=(h,pool,i);all_events[key]=r
        (OUT/('tron_events_'+pool+'.json')).write_text(json.dumps({'coverage':record,'rows':list(events.values())},indent=2));print('TRON event census',pool,record['events'],'complete',record['all_pages_complete'],flush=True)
    doc={'time_start':START,'time_end_exclusive':END,'pools':coverage,'unique_transactions':len({k[0] for k in all_events}),'unique_events':len(all_events),'all_pools_paginated':all(r['all_pages_complete'] for r in coverage),'scope':'Every confirmed indexed event at every target-touched TRON pool in the common window, including all senders. V4 manager index is shared; PoolId membership is applied before economic attribution. Index completeness is separate from receipt/hash verification.'};(OUT/'tron_event_census.json').write_text(json.dumps(doc,indent=2));print(json.dumps(doc,indent=2))
if __name__=='__main__':run()
