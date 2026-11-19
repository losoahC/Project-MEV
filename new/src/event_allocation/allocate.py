"""Disjoint full-frame allocation and a separate actual address audit.

Target transactions use the complete signed journal. Subsequent transactions use
only incident-pool swap legs, charging the observed transaction cost once. This
is a marked market-transfer budget, not historical inventory cost-basis PnL.
"""
import json,gzip,csv,argparse
from collections import defaultdict,Counter
from decimal import Decimal,getcontext
from src.event_allocation.config import ROOT,OUT,REPORT,START,END,POLICY,setup
from src.event_allocation.quotes import Quotes
from src.event_allocation.ethereum_journal import normalize
from src.event_allocation.tron_journal import norm as tron_norm,MANAGER as TM
from src.arbitrage.complete_surplus_ledger import MANAGER,ZERO
from src.arbitrage.tron_accounting import ZERO as TZERO
getcontext().prec=90
D=Decimal
def vector():return defaultdict(int)
def add(dst,src,mult=1):
    for a,v in src.items():dst[a]+=int(v)*mult
def clean(v):return {a:str(r) for a,r in v.items() if r}

class Pools:
    def __init__(self):
        p=ROOT/'data/processed/mev_full_window';self.meta={r['pool']:r for r in json.loads((p/'pool_metadata_full.json').read_text())};self.keys={r['pool_key']:r for r in json.loads((p/'v4_pool_keys.json').read_text())['rows']}
        self.keys.update({r['pool_key']:r for r in json.loads((OUT/'additional_v4_pool_keys.json').read_text())})
        self.order_boundaries={a for r in json.loads((p/'order_filler_equity.json').read_text())['rows'] for a in r['boundary']};self.wrappers={r['wrapper'] for r in json.loads((ROOT/'data/processed/few_wrapper_identities.json').read_text())};self.lending_protocols={'0xa17581a9e3356d9a858b789d68b4d866e593ae94','0xc3d688b66703497daa19211eedff47f25384cdc3','0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2','0xc13e21b648a5ee794902342038ff3adab66be987'}
        self.tron={r['pool_hex']:r for r in json.loads((ROOT/'data/processed/mev_tron/pool_metadata_current.json').read_text())};self.tk={r['manager_hex']+':'+r['pool_id']:r for r in json.loads((ROOT/'data/processed/mev_tron/sun_v4_pool_keys.json').read_text())};self.first={};self.target={};self.hackers=defaultdict(set)
        for r in json.loads((p/'targets.json').read_text()):
            if not START<=r['timestamp']<END:continue
            self.target['ethereum',r['tx_hash']]=r
            for w in r['wallets']:self.hackers['ethereum'].add(w['address'])
            for e in r['pool_events']:
                key=('ethereum',e['pool_key']);at=(r['block'],r['index']);self.first[key]=min(self.first.get(key,at),at)
        metadata=json.loads((OUT/'tron_root_transactions.json').read_text())['rows']
        for r in json.loads((ROOT/'data/processed/mev_tron/target_owner_accounting.json').read_text()):
            if not START<=r['timestamp']<END or not r['swap_events']:continue
            from src.arbitrage.tron_collect import decode_addr
            self.target['tron',r['tx_hash']]=r;self.hackers['tron'].add(decode_addr(r['owner']))
            for e in r['swap_events']:
                k=e.get('pool_key',e['pool_hex']);k=k.replace('0x','41',1) if k.startswith('0x') else k;key=('tron',k);at=(r['block'],int(metadata[r['tx_hash']]['transaction']['transactionIndex'],16));self.first[key]=min(self.first.get(key,at),at)

    def leg(self,chain,e):
        k=e['pool_key'];isv4='V4' in e['protocol'];meta=(self.keys if chain=='ethereum' else self.tk).get(k) if isv4 else (self.meta if chain=='ethereum' else self.tron).get(k)
        if not meta:raise ValueError('Missing authenticated pool currencies: '+chain+' '+k)
        norm=normalize if chain=='ethereum' else tron_norm;out=vector()
        for side in [0,1]:
            a=meta['currency'+str(side)+('_hex' if chain=='tron' else '')] if isv4 else meta.get('fields',meta)['token'+str(side)]
            out[norm(a)]+=int(e['amount'+str(side)+'_raw'])*(-1 if isv4 else 1)
        return out

    def domain(self,row):
        if row['chain']=='tron':return 'TRON'
        t=self.target.get((row['chain'],row['tx_hash']))
        if t and t['order_events']:return 'order_fills'
        if t:
            v=vector()
            for w in t['wallets']:
                add(v,{normalize(a):r for a,r in w['token_net_raw'].items()});v['native:eth']+=int(w['native_net_wei'] or 0)
            stable={'0xdac17f958d2ee523a2206206994597c13d831ec7','0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'}
            if v['native:eth']>0 and any(v[a]<0 for a in stable):return 'ETH_purchase'
        return 'token_disposal_or_mixed'

def cash_fee(row):
    """Observed net receipts at the block recipient, including priority once."""
    native='native:eth' if row['chain']=='ethereum' else 'native:trx';v=vector()
    if row['chain']=='tron':v[native]=int(row['gas_raw']);return v
    if row['fee_recipient']==row['sender']:
        # The payer receives its own priority fee: it is an internal address
        # transfer, not another extraction or an external operating cost.
        return v
    for e in row['entries']:
        if e['address']==row['fee_recipient'] and e['component'] in ['cash','V4_claim']:v[e['asset']]+=int(e['raw'])
    return v

def target_allocation(row,pools):
    by=defaultdict(vector);chain=row['chain'];manager=MANAGER if chain=='ethereum' else TM;unresolved=[]
    for e in row['entries']:by[e['address']][e['asset']]+=int(e['raw'])
    legs=defaultdict(vector)
    for e in row['swap_events']:
        try:add(legs[e['pool_key']],pools.leg(chain,e))
        except ValueError as ex:unresolved.append(str(ex))
    out=[]
    for k,v in legs.items():
        emitter=k.split(':')[0];add(by[emitter],v,-1);out.append(('pool_trade_inventory',k,v))
    position_protocols={e['emitter'] for e in row['position_events'] if e.get('emitter')}
    for a,v in by.items():
        if a in pools.hackers[chain]:role='incident_wallet_reference_change'
        elif a.startswith('protocol:'):role='protocol_resource_fee' if chain=='tron' else 'protocol_fee_burn'
        elif a==row['fee_recipient']:role='block_recipient_receipts'
        elif a in getattr(pools,'order_boundaries',set()):role='known_order_operating_boundary_change'
        elif a in getattr(pools,'wrappers',set()):role='wrapper_backing_reserve_change'
        elif a==manager:role='manager_settlement_or_hook_residual'
        elif a in pools.meta or a in pools.tron:role='pool_nontrade_principal_or_protocol_cash'
        elif a in position_protocols or a in getattr(pools,'lending_protocols',set()):role='lending_protocol_principal_adjusted'
        elif a in [ZERO,TZERO]:role='token_supply_accounting_sink'
        elif a in row['liquidity_actors']:role='liquidity_participant_cash_not_certified_profit'
        else:role='other_actual_address_signed_change'
        out.append((role,a,v))
    return out,unresolved

def subsequent_allocation(row,pools):
    chain=row['chain'];out=[];total=vector();errors=[];leg_ids=[]
    for e in row['swap_events']:
        first=pools.first.get((chain,e['pool_key']))
        if not first or (row['block'],row['index'])<=first:continue
        try:
            v=pools.leg(chain,e);add(total,v);out.append(('pool_trade_inventory',e['pool_key'],v));leg_ids.append((e['pool_key'],e['log_index']))
        except ValueError as ex:errors.append(str(ex))
    if not leg_ids and row['association']!='failed_attempt_after_target':return [],errors,leg_ids
    # Deduct transaction-level costs once even if multiple incident pools occur.
    fee=cash_fee(row);burn=vector();native='native:eth' if chain=='ethereum' else 'native:trx';burn[native]=int(row['base_burn_raw'])+int(row['blob_burn_raw']);trader=vector();add(trader,total,-1);add(trader,fee,-1);add(trader,burn,-1)
    out.extend([('operating_address_incident_leg_reference_edge',row['sender'],trader),('block_recipient_receipts' if chain=='ethereum' else 'protocol_resource_fee',row['fee_recipient'],fee),('protocol_fee_burn','protocol:fee_burn',burn)])
    return out,errors,leg_ids

def run(ethereum_only=False,mode='primary'):
    setup();pools=Pools();quotes=Quotes(mode);prefix=('draft_ethereum_' if ethereum_only else '')+('stable1_' if mode=='stable1' else '');counts=Counter();groups={};lp={};operators={};seen=set();leg_seen=set();failures=[];source_paths=set();actual_missing=Counter();budget_missing=Counter();target_loss=D(0);budget_sum=D(0);nonhacker=D(0);max_usd_residual=D(0);total_raw=vector();blockfees=defaultdict(vector);target_domains=Counter();trade_signs=Counter()
    group_fields=['chain','domain','role','address'];actual_fields=['chain','tx_hash','block','timestamp','association','address','component','asset','raw','USD','quote_id'];alloc_fields=['chain','tx_hash','block','timestamp','domain','association','basis','allocation_record_index','role','address','asset','raw','USD','quote_id'];paths=[OUT/'ethereum_journal.jsonl.gz']
    if not ethereum_only:
        s=json.loads((OUT/'tron_journal_summary.json').read_text());assert s['receipts_complete'] and not s['failures'];paths.append(OUT/'tron_journal.jsonl.gz')
    actualpath=REPORT/(prefix+'actual_address_changes.csv.gz');allocationpath=REPORT/(prefix+'unified_allocation.csv.gz')
    with gzip.open(actualpath,'wt') as af,gzip.open(allocationpath,'wt') as bf,gzip.open(OUT/(prefix+'transaction_valuations.jsonl.gz'),'wt') as tf:
        aw=csv.DictWriter(af,fieldnames=actual_fields);aw.writeheader();bw=csv.DictWriter(bf,fieldnames=alloc_fields);bw.writeheader()
        for path in paths:
            with gzip.open(path,'rt') as f:
                for line in f:
                    row=json.loads(line);key=(row['chain'],row['tx_hash']);assert key not in seen;seen.add(key);assert START<=row['timestamp']<END;counts['actual_transactions']+=1;counts[row['chain']+'_actual_transactions']+=1;counts[row['association']]+=1;ts=row['timestamp'];native='native:eth' if row['chain']=='ethereum' else 'native:trx';atotal=D(0);araw=vector()
                    for source in row['evidence'].values():
                        if isinstance(source,str) and source.startswith('data/'):source_paths.add(source)
                    for e in row['entries']:
                        a=e['asset'];v=quotes.value(a,e['raw'],ts);araw[a]+=int(e['raw']);counts['actual_entries']+=1
                        if v is None:actual_missing[a]+=1
                        else:atotal+=v
                        aw.writerow({k:row[k] for k in ['chain','tx_hash','block','timestamp','association']}|e|{'USD':str(v) if v is not None else '', 'quote_id':f'{a}@{ts//60*60}'})
                    assert not any(araw.values());max_usd_residual=max(max_usd_residual,abs(atotal));assert abs(atotal)<D('1e-50')
                    is_target=row['association']=='target';basis='complete_target_journal' if is_target else 'incident_pool_legs_with_transaction_cost_once';domain=pools.domain(row) if is_target else 'subsequent_incident_pool_trade';alloc,errors=(target_allocation(row,pools) if is_target else ([],[]))
                    if not is_target:alloc,errors,ids=subsequent_allocation(row,pools)
                    else:ids=[(e['pool_key'],e['log_index']) for e in row['swap_events']]
                    if errors:failures.append({'chain':row['chain'],'tx_hash':row['tx_hash'],'errors':errors})
                    if not alloc:continue
                    counts['primary_transactions']+=1;counts[row['chain']+'_primary_transactions']+=1
                    if is_target:target_domains[domain]+=1
                    for pid,log in ids:
                        lid=key+(pid,log);assert lid not in leg_seen;leg_seen.add(lid)
                    txraw=vector();txval=D(0);txmissing=Counter();opnet=vector();opgross=vector();allfee=vector();maker=vector();rolevals=defaultdict(Decimal)
                    for allocation_index,(role,address,v) in enumerate(alloc):
                        gkey=(row['chain'],domain,role,address);g=groups.setdefault(gkey,{'raw':vector(),'priced_USD':D(0),'rows':0,'unpriced_asset_rows':0,'secondary_rows':0});add(g['raw'],v);add(txraw,v);add(total_raw,{row['chain']+':'+a:r for a,r in v.items()});g['rows']+=1
                        if role=='pool_trade_inventory':
                            l=lp.setdefault((row['chain'],address),{'raw':vector(),'trade_time_USD':D(0),'missing_trade_rows':0,'transactions':set()});add(l['raw'],v);l['transactions'].add(key);pv=quotes.vector(v,ts);l['trade_time_USD']+=D(pv['priced_component_USD']);l['missing_trade_rows']+=bool(pv['unpriced_raw']);add(opgross,v,-1)
                        if role=='operating_address_incident_leg_reference_edge':add(opnet,v)
                        if role in ['block_recipient_receipts','protocol_fee_burn','protocol_resource_fee']:add(allfee,v)
                        if role=='incident_wallet_reference_change':add(maker,v)
                        if role=='block_recipient_receipts':add(blockfees[row['block']],v)
                        for a,raw in v.items():
                            if not raw:continue
                            val=quotes.value(a,raw,ts);counts['allocation_asset_rows']+=1;quote=quotes.quote(a,ts)
                            if val is None:g['unpriced_asset_rows']+=1;txmissing[a]+=1;budget_missing[a]+=1
                            else:
                                g['priced_USD']+=val;txval+=val;rolevals[role]+=val;budget_sum+=val
                                if role=='incident_wallet_reference_change':target_loss-=val
                                else:nonhacker+=val
                                g['secondary_rows']+=quote['quality'].startswith('exact_contract_DefiLlama')
                            bw.writerow({k:row[k] for k in ['chain','tx_hash','block','timestamp','association']}|{'domain':domain,'basis':basis,'allocation_record_index':allocation_index,'role':role,'address':address,'asset':a,'raw':str(raw),'USD':str(val) if val is not None else '', 'quote_id':f'{a}@{ts//60*60}'})
                    assert not any(txraw.values()),(key,dict(txraw));assert abs(txval)<D('1e-50'),(key,str(txval));counts['fully_priced_primary_transactions']+=not txmissing;counts['secondary_priced_primary_transactions']+=any(quotes.quote(a,ts).get('quality','').startswith('exact_contract_DefiLlama') for _,_,v in alloc for a in v)
                    gross=quotes.vector(opgross,ts);net=quotes.vector(opnet,ts);fees=quotes.vector(allfee,ts);m=quotes.vector(maker,ts)
                    if is_target:counts['fully_priced_incident_wallet_transactions']+=m['fully_priced'];counts['incident_wallet_unpriced_transactions']+=not m['fully_priced']
                    if not is_target:
                        op=operators.setdefault((row['chain'],row['sender']),{'transactions':0,'gross_priced_USD':D(0),'net_priced_USD':D(0),'fee_priced_USD':D(0),'unpriced_transactions':0,'fully_priced_positive':0,'fully_priced_negative':0});op['transactions']+=1;op['gross_priced_USD']+=D(gross['priced_component_USD']);op['net_priced_USD']+=D(net['priced_component_USD']);op['fee_priced_USD']+=D(fees['priced_component_USD']);op['unpriced_transactions']+=not(net['fully_priced'] and gross['fully_priced'])
                        if net['fully_priced']:op['fully_priced_positive']+=D(net['priced_component_USD'])>0;op['fully_priced_negative']+=D(net['priced_component_USD'])<0;trade_signs['positive' if D(net['priced_component_USD'])>0 else 'negative' if D(net['priced_component_USD'])<0 else 'zero']+=1
                    tf.write(json.dumps({'chain':row['chain'],'tx_hash':row['tx_hash'],'block':row['block'],'timestamp':ts,'sender':row['sender'],'association':row['association'],'domain':domain,'basis':basis,'incident_leg_gross':gross,'incident_leg_after_observed_cost':net,'fee_and_burn':fees,'incident_wallet_change':m,'role_priced_USD':{k:str(v) for k,v in rolevals.items()},'unpriced_assets':dict(txmissing),'pool_log_keys':ids,'position_risks':row['position_risks'],'fee_recipient_is_sender':row['fee_recipient']==row['sender'],'scope_limit':'Pool association does not establish causal MEV. Operating address is not beneficial ownership. Other-pool hedge costs and historical inventory acquisition are outside the incident-leg margin. Complete cash/position entries are in the separate actual journal.'},separators=(',',':'))+'\n')
    assert not any(total_raw.values());assert abs(budget_sum)<D('1e-45');assert abs(target_loss-nonhacker)<D('1e-45')
    group_rows=[]
    for key,g in groups.items():group_rows.append(dict(zip(group_fields,key))|{'priced_component_USD':str(g['priced_USD']),'allocation_rows':g['rows'],'unpriced_asset_rows':g['unpriced_asset_rows'],'secondary_price_rows':g['secondary_rows'],'net_asset_vector_raw':clean(g['raw'])})
    (OUT/(prefix+'allocation_by_address.json')).write_text(json.dumps(group_rows,indent=2));lp_rows=[]
    for (chain,pool),r in lp.items():
        terminal=quotes.vector(r['raw'],END);lp_rows.append({'chain':chain,'pool_key':pool,'transactions':len(r['transactions']),'trade_time_priced_component_USD':str(r['trade_time_USD']),'trade_rows_with_missing_prices':r['missing_trade_rows'],'net_swap_inventory_raw':clean(r['raw']),'terminal_inventory_mark':terminal,'terminal_minus_trade_time_priced_component_USD':str(D(terminal['priced_component_USD'])-r['trade_time_USD']),'interpretation':'Swap inventory changes only, including negative signs. Terminal-price mark uses the last completed minute as of the exclusive window end. This is an alternative valuation of the same vector; not additive extraction, total LP wealth, fee-only income or individual LP wallet profit. Non-swap principal is separate.'})
    (OUT/(prefix+'lp_inventory_valuations.json')).write_text(json.dumps(lp_rows,indent=2));ops=[{'chain':k[0],'operating_address':k[1],**{f:str(v) if isinstance(v,D) else v for f,v in r.items()}} for k,r in operators.items()];(OUT/(prefix+'all_operating_addresses.json')).write_text(json.dumps(sorted(ops,key=lambda x:D(x['net_priced_USD']),reverse=True),indent=2))
    quote_path=quotes.dump();summary={'version':POLICY['version'],'draft_ethereum_only':ethereum_only,'price_mode':mode,'window':POLICY['time_window'],'counts':dict(counts),'target_transactions_by_domain':dict(target_domains),'incident_wallet_reference_loss_priced_component_USD':str(target_loss),'nonhacker_allocation_priced_component_USD':str(nonhacker),'priced_component_conservation_residual_USD':str(budget_sum),'maximum_actual_transaction_priced_residual_USD':str(max_usd_residual),'unpriced_actual_asset_rows':dict(actual_missing),'unpriced_primary_asset_rows':dict(budget_missing),'all_raw_vectors_conserve':True,'all_primary_transaction_asset_vectors_conserve':True,'all_price_missing_values_remain_missing':True,'mapping_failures':failures,'pool_trade_legs':len(leg_seen),'operating_addresses':len(operators),'fully_priced_subsequent_transaction_signs':dict(trade_signs),'whole_event_causal_MEV_or_historical_cost_profit_established':False,'policy':POLICY,'quote_schedule':str(quote_path.relative_to(ROOT))};(OUT/(prefix+'summary.json')).write_text(json.dumps(summary,indent=2));(OUT/(prefix+'used_evidence_paths.json')).write_text(json.dumps(sorted(source_paths),indent=2));(OUT/(prefix+'block_primary_fee_vectors.json')).write_text(json.dumps({str(k):clean(v) for k,v in blockfees.items()},indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['policy','unpriced_actual_asset_rows','unpriced_primary_asset_rows']},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ethereum-only',action='store_true');p.add_argument('--mode',choices=['primary','stable1'],default='primary');a=p.parse_args();run(a.ethereum_only,a.mode)
