"""Principal-adjusted TRON lending conversions from actual Mint/Redeem/Borrow events.
No current exchange rate is applied to a historical position.
"""
import json
from collections import defaultdict
from decimal import Decimal
from web3 import Web3
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_more import BOTS
from src.arbitrage.tron_accounting import U,W
from src.arbitrage.tron_collect import decode_addr
from src.arbitrage.value_candidates import book_from_archive
from src.arbitrage.reconstruct import Reconstruction
MARKETS={'412c7c9963111905d29eb8da37d28b0f53a7bb5c28':'native:trx','41ea09611b57e89d67fbb33a516eb90508ca95a3e5':U}

def adjust(raw,account):
    boundary={decode_addr(a) for a in account['boundary']};p=ROOT/'data/processed/mev_tron';abis=json.loads((p/'justlend_current_ABI.json').read_text());by={decode_addr(r['contract']):{Web3.keccak(text=e['name']+'('+','.join(i['type'] for i in e.get('inputs',[]))+')').hex().removeprefix('0x'):e for e in r['events']} for r in abis};shares=defaultdict(int);underlying=defaultdict(int);events=[]
    for i,l in enumerate(raw['receipt'].get('log',[])):
        market='41'+l['address'][-40:];ts=l.get('topics',[])
        if market not in by or not ts or ts[0] not in by[market]:continue
        abi=by[market][ts[0]];name=abi['name']
        if name not in ['Mint','Redeem','Borrow','RepayBorrow']:continue
        if len(ts)!=1:raise ValueError('Unexpected indexed event layout')
        words=[l['data'][j:j+64] for j in range(0,len(l['data']),64)];assert len(words)==len(abi['inputs']);decoded={f['name']:('41'+w[-40:] if f['type']=='address' else int(w,16)) for f,w in zip(abi['inputs'],words)};asset=MARKETS[market];effect=0
        if name=='Mint' and decoded['minter'] in boundary:shares[market]+=decoded['mintTokens'];effect=decoded['mintAmount']
        elif name=='Redeem' and decoded['redeemer'] in boundary:shares[market]-=decoded['redeemTokens'];effect=-decoded['redeemAmount']
        elif name=='Borrow' and decoded['borrower'] in boundary:effect=-decoded['borrowAmount']
        elif name=='RepayBorrow' and decoded['borrower'] in boundary:effect=decoded['repayAmount']
        else:continue
        underlying[asset]+=effect;events.append({'market':market,'underlying':asset,'name':name,'decoded':{k:str(v) for k,v in decoded.items()},'underlying_principal_equity_delta_raw':str(effect),'log_index':i})
    if not events:return None
    actual={t:int(v) for t,v in account['token_net_raw'].items()};unmatched={m:str(actual.get(m,0)-shares.get(m,0)) for m in MARKETS if actual.get(m,0)!=shares.get(m,0)};other={t:str(v) for t,v in actual.items() if t not in [W,U,*MARKETS] and v};assets={'native:trx':int(Decimal(account['combined_TRX_WTRX_before_fee'])*10**6)+underlying.get('native:trx',0),U:actual.get(U,0)+underlying.get(U,0)}
    return {'tx_hash':raw['tx_hash'],'bot':account['owner'],'boundary':account['boundary'],'decoded_position_events':events,'actual_jtoken_delta_raw':{m:str(actual.get(m,0)) for m in MARKETS if actual.get(m,0)},'event_share_delta_raw':{m:str(v) for m,v in shares.items() if v},'unmatched_jtoken_transfers_raw':unmatched,'unresolved_other_tokens_raw':other,'equity_principal_adjustment_raw':{t:str(v) for t,v in underlying.items() if v},'principal_adjusted_asset_vector_raw':{t:str(v) for t,v in assets.items() if v},'complete_for_principal_conversion':not unmatched and not other,'evidence':account['evidence'],'limit':'Actual historical conversion amounts, not present-day jToken prices. Includes new loan principal as liability. Excludes revaluation/interest on previously held positions and ultimate-owner/offchain costs. Not a proved MEV increment.'}

def run():
    p=ROOT/'data/processed/mev_tron';accounts=json.loads((p/'all_named_bot_accounting.json').read_text());raw=json.loads((p/'named_bot_receipts.json').read_text())
    for bot in BOTS:
        path=p/bot/'receipts.json'
        if path.exists():raw+=json.loads(path.read_text())
    by={r['tx_hash']:r for r in raw};book=book_from_archive();book.engine=Reconstruction(ROOT.parent/'research',False);book.binance_spot('TRX',('2026-10-29','2026-10-30'));book.loaded.add('TRX');rows=[]
    for a in accounts['rows']:
        if not a['success']:continue
        r=adjust(by[a['tx_hash']],a)
        if r is None:continue
        st=book.price('USDT',a['timestamp']);tr=book.price('TRX',a['timestamp'],venue='Binance');v=r['principal_adjusted_asset_vector_raw'];usd=(Decimal(v.get(U,'0'))*st[0]+Decimal(v.get('native:trx','0'))*tr[0])/10**6-Decimal(a['fee_USD']) if r['complete_for_principal_conversion'] and st and tr and a['fee_USD'] is not None else None
        r.update(principal_adjusted_reference_edge_after_fee_USD=str(usd) if usd is not None else None,timestamp=a['timestamp'],signature_txid_matches=a['signature_txid_matches'],signature_owner_matches=a['signature_owner_match'],overlaps_simple_swap_edge=a['marked_swap_reference_edge_after_fee_USD'] is not None,price_evidence=a['price_evidence']);rows.append(r)
    summaries=[]
    for s in accounts['summary_by_bot']:
        rr=[r for r in rows if r['bot']==s['bot']];extra=[r for r in rr if not r['overlaps_simple_swap_edge'] and r['principal_adjusted_reference_edge_after_fee_USD'] is not None];summaries.append({'bot':s['bot'],'lending_transactions':len(rr),'principal_conversions_priced':sum(r['principal_adjusted_reference_edge_after_fee_USD'] is not None for r in rr),'additional_disjoint_lending_reference_edge_USD':str(sum((Decimal(r['principal_adjusted_reference_edge_after_fee_USD']) for r in extra),Decimal(0))),'simple_and_lending_reference_edge_USD':str(Decimal(s['priced_swap_reference_edge_after_trade_fees_USD'])+sum((Decimal(r['principal_adjusted_reference_edge_after_fee_USD']) for r in extra),Decimal(0))),'interpretation':'Priced trade edges including actual principal conversions; not all-in equity mark, historical cost-basis PnL or whole-event MEV.'})
    (p/'justlend_position_adjustments.json').write_text(json.dumps({'rows':rows,'summary_by_bot':summaries,'source':'https://docs.justlend.org/developers/contracts_overview/','event_abi_source':'Current node getcontract ABIs archived; layouts checked against actual historical event topics/lengths.'},indent=2));print(json.dumps(summaries,indent=2))
if __name__=='__main__':run()
