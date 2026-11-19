"""Recompute TRON target-owner ledgers from raw history pages and receipts.
Tracker membership is a discovery lead, not verified common ownership.
"""
import json,gzip,hashlib,argparse
from collections import defaultdict
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_accounting import parse,U,W
from src.arbitrage.tron_collect import decode_addr,encode_addr
from src.arbitrage.reconstruct import Reconstruction
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.full_valuations import FullWindowBook

def run(legacy=None):
    engine=Reconstruction(legacy or ROOT.parent/'research',False);tracker=json.loads((ROOT/'data/raw/reference_inputs/tracker_state.json').read_text());leadset={decode_addr(r['address']) for r in tracker['wallets'] if r['chain']=='tron' and r['role'] in tracker['attackerSideRoles']};txs={};receipts={};paths={}
    rawpaths=sorted((engine.legacy/'tron_raw').glob('*.json.gz')) or [engine.source(k) for k in sorted(engine.archive_by_origin) if k.startswith('tron_raw/')]
    for path in rawpaths:
        d=json.loads(gzip.decompress(path.read_bytes()));src=engine.store.archive(path,'Archived public TRON API; original acquisition endpoint/time uncertified','Raw history or transaction-info response') if path.is_relative_to(engine.legacy) else str(path.relative_to(ROOT))
        if d.get('id'):receipts[d['id']]=d;paths[d['id']]=src
        for t in d.get('data',[]):
            if t.get('txID'):txs[t['txID']]=(t,src)
    keys={(r['manager_hex'],r['pool_id']):r for r in json.loads((ROOT/'data/processed/mev_tron/sun_v4_pool_keys.json').read_text())};book=book_from_archive();book.__class__=FullWindowBook;book.engine=engine;book.binance_spot('TRX',('2026-10-29','2026-10-30'));book.loaded.add('TRX');rows=[];missing=[]
    for h,(t,tsource) in sorted(txs.items()):
        contracts=t.get('raw_data',{}).get('contract',[]);owners={c['parameter']['value'].get('owner_address') for c in contracts if c['type']=='TriggerSmartContract'}&leadset
        if not owners:continue
        assert len(owners)==1;owner=next(iter(owners));assert hashlib.sha256(bytes.fromhex(t['raw_data_hex'])).hexdigest()==h
        if h not in receipts:missing.append(h);continue
        row={'tx_hash':h,'transaction':t,'receipt':receipts[h],'bot':encode_addr(owner),'bot_hex':owner,'transaction_evidence':tsource,'receipt_evidence':paths[h]};r=parse(row,keys,{owner});trx=Decimal(r['combined_TRX_WTRX_before_fee']);usdt=Decimal(r['USDT_net']);st=book.price('USDT',r['timestamp']);tr=book.price('TRX',r['timestamp'],venue='Binance');shortfall=-usdt*st[0]-trx*tr[0] if st and tr and not r['other_token_residual_raw'] else None
        r.update(address_scope='Tracker discovery lead only; separate owner accounting, not pooled control.',large_USDT_to_TRX_swap=r['success'] and usdt<=-1000000 and trx>0 and bool(r['swap_events']),reference_shortfall_excluding_gas_USD=str(shortfall) if shortfall is not None else None,MEV_incremental_loss_USD=None,price_evidence={'USDT':st[1] if st else None,'TRX':tr[1] if tr else None});rows.append(r)
    engine.store.save();swaps=[r for r in rows if r['large_USDT_to_TRX_swap']];all_swaps=[r for r in rows if r['success'] and Decimal(r['USDT_net'])<0 and Decimal(r['combined_TRX_WTRX_before_fee'])>0 and r['swap_events']];summary={'raw_history_transactions':len(txs),'tracker_leads_not_verified_control':len(leadset),'owner_origin_contract_transactions':len(rows),'missing_receipts':missing,'large_USDT_to_TRX_swaps':len(swaps),'large_swap_USDT_input':str(-sum((Decimal(r['USDT_net']) for r in swaps),Decimal(0))),'large_swap_TRX_WTRX_output':str(sum((Decimal(r['combined_TRX_WTRX_before_fee']) for r in swaps),Decimal(0))),'large_swap_reference_shortfall_USD':str(sum((Decimal(r['reference_shortfall_excluding_gas_USD']) for r in swaps if r['reference_shortfall_excluding_gas_USD'] is not None),Decimal(0))),'all_positive_TRX_USDT_input_swaps':len(all_swaps),'all_swap_USDT_input':str(-sum((Decimal(r['USDT_net']) for r in all_swaps),Decimal(0))),'all_swap_reference_shortfall_USD':str(sum((Decimal(r['reference_shortfall_excluding_gas_USD']) for r in all_swaps),Decimal(0))) if all(r['reference_shortfall_excluding_gas_USD'] is not None for r in all_swaps) else None,'priced_all_swap_rows':sum(r['reference_shortfall_excluding_gas_USD'] is not None for r in all_swaps),'unpriced_all_swap_hashes':[r['tx_hash'] for r in all_swaps if r['reference_shortfall_excluding_gas_USD'] is None],'all_incident_loss_established':False}
    p=ROOT/'data/processed/mev_tron';(p/'target_owner_accounting.json').write_text(json.dumps(rows,indent=2));(p/'target_owner_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--legacy');args=parser.parse_args();run(args.legacy)
