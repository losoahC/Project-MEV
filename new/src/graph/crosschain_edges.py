"""Verified cross-chain companion edges; matched conversions are not fabricated transfer edges."""
import json
from decimal import Decimal
from datetime import datetime,timezone
import pandas as pd
from src.visualization.common import ROOT
from src.ingestion.evidence import read_json


def extend(primary):
    path=ROOT/'data/processed/thorchain_paths.json'
    if not path.exists():return primary,{}
    cases=read_json(path);extra=[];entities={}
    for c in cases:
        entities[c['router']]='verified_THORChain_service'
        for link in c['funding_path']:
            tx=read_json(ROOT/link['evidence'][0])['response']['result']
            extra.append({'tx_hash':link['tx_hash'],'sender':link['sender'],'recipient':link['recipient'],'amount_raw':link['amount_wei'],'token':'native:eth','symbol':'ETH','decimals':18,'amount':str(Decimal(link['amount_wei'])/10**18),'timestamp':link['timestamp'],'timestamp_utc':link['timestamp_utc'],'block_number':int(tx['blockNumber'],16),'block_hash':tx['blockHash'],'transaction_index':int(tx['transactionIndex'],16),'chain':'ethereum','event_location':'call:[]','evidence_path':link['evidence'][0],'usd_value':None,'valuation_status':'missing_funding_timestamp_price_not_zero','confidence':'observed_ordinary_RPC_transfer; common control unresolved','tx_url':'https://etherscan.io/tx/'+link['tx_hash'],'crosschain_case':c['case_id']})
        tx=read_json(ROOT/c['evidence']['ethereum'][0])['response']['result']
        extra.append({'tx_hash':c['ethereum_deposit'],'sender':c['source_address'],'recipient':c['router'],'amount_raw':str(int(tx['value'],16)),'token':'native:eth','symbol':'ETH','decimals':18,'amount':c['input_ETH'],'timestamp':c['deposit_timestamp'],'timestamp_utc':c['deposit_utc'],'block_number':c['source_block'],'block_hash':tx['blockHash'],'transaction_index':int(tx['transactionIndex'],16),'chain':'ethereum','event_location':'call:[]','evidence_path':c['evidence']['ethereum'][0],'usd_value':c['input_reference_USD'],'valuation_status':'estimated_deposit_prior_completed_minute','reference_price_usd':c['reference']['ETH_USD'],'price_bar_start':int(pd.Timestamp(c['reference']['minute_utc']).timestamp()),'price_source':c['reference']['evidence']['ETH'],'confidence':'observed THORChain deposit; fund-flow association only','tx_url':'https://etherscan.io/tx/'+c['ethereum_deposit'],'crosschain_case':c['case_id']})
        btc=read_json(ROOT/c['evidence']['bitcoin'])['response'];senders={v['prevout'].get('scriptpubkey_address') for v in btc['vin']}
        assert len(senders)==1 and None not in senders,'Multi-source UTXO attribution requires a distinct input-bundle representation'
        sender=next(iter(senders));entities[sender]='verified_THORChain_service'
        for o in c['bitcoin_outputs']:
            extra.append({'tx_hash':c['bitcoin_txid'],'sender':sender,'recipient':c['destination_address'],'amount_raw':str(o['value_sats']),'token':'native:btc','symbol':'BTC','decimals':8,'amount':str(Decimal(o['value_sats'])/10**8),'timestamp':btc['status']['block_time'],'timestamp_utc':datetime.fromtimestamp(btc['status']['block_time'],timezone.utc).isoformat(),'block_number':btc['status']['block_height'],'block_hash':btc['status']['block_hash'],'transaction_index':None,'chain':'bitcoin','event_location':f"vout:{o['index']}",'evidence_path':c['evidence']['bitcoin'],'usd_value':str(Decimal(o['value_sats'])/10**8*Decimal(c['reference']['BTC_USD'])),'valuation_status':'estimated_at_matched_ETH_deposit_reference_not_BTC_inclusion_time','reference_price_usd':c['reference']['BTC_USD'],'price_bar_start':int(pd.Timestamp(c['reference']['minute_utc']).timestamp()),'price_source':c['reference']['evidence']['BTC'],'confidence':'observed confirmed BTC recipient output, inbound hash linked by OUT memo','tx_url':'https://blockstream.info/tx/'+c['bitcoin_txid'],'crosschain_case':c['case_id']})
    seen={(r['chain'],r['tx_hash'],r['token'],r['sender'],r['recipient'],r['amount_raw']) for r in primary.to_dict('records')}
    distinct=[]
    for r in extra:
        key=(r['chain'],r['tx_hash'],r['token'],r['sender'],r['recipient'],r['amount_raw'])
        if key in seen:continue
        seen.add(key);r['edge_id']=f"{r['chain']}:{r['tx_hash']}:{r['event_location']}";distinct.append(r)
    from collections import defaultdict
    case_ids=defaultdict(set)
    for r in extra:
        key=(r['chain'],r['tx_hash'],r['token'],r['sender'],r['recipient'],r['amount_raw'])
        case_ids[key].add(r['crosschain_case'])
    output=pd.concat([primary,pd.DataFrame(distinct)],ignore_index=True)
    output['crosschain_case']=[', '.join(sorted(case_ids[(r['chain'],r['tx_hash'],r['token'],r['sender'],r['recipient'],r['amount_raw'])])) or None for r in output.to_dict('records')]
    output.to_parquet(ROOT/'data/processed/fund_flow_graph_edges.parquet',index=False)
    (ROOT/'data/processed/crosschain_graph_entities.json').write_text(json.dumps(entities,indent=2))
    return output,entities
