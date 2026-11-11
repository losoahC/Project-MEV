import json,gzip
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 evidence=load('full_window_evidence.json');assert len(evidence['rows'])==3311 and not evidence['errors']
 headers={r['block']:r for r in evidence['rows']};targets={r['hash'] for r in load('full_swaps.json')['rows']};candidates={r['hash']:r['category'] for r in load('candidate_classification.json')['rows']};relays=defaultdict(list)
 for source in load('relay_history.json')['rows']:
  for r in source['rows']:
   n=int(r['block_number'])
   if r['block_hash']==headers[n]['hash']:relays[n].append({**r,'relay':source['relay']})
 totals=defaultdict(int);categories=defaultdict(lambda:defaultdict(int));rows=[];selected=[];payments=[]
 for i,(n,b) in enumerate(sorted(headers.items()),1):
  folder='window_raw' if n<=26301940 else 'extension_raw';rs=json.loads(gzip.decompress((R/folder/f'{n}.json.gz').read_bytes()));recs={r['transactionHash']:r for r in rs};miner=b['miner'].lower();base=int(b['base_fee_wei']);cats={h:('target_pool_swap' if h in targets else 'candidate:'+candidates[h] if h in candidates else 'other_transactions') for h in recs}
  br={'block':n,'hash':b['hash'],'fee_recipient':miner,'gas_wei':0,'burn_wei':0,'priority_wei':0,'fee_recipient_paid_gas_wei':0,'direct_inflow_wei':0,'direct_outflow_wei':0}
  for h,r in recs.items():
   gas=int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16);burn=int(r['gasUsed'],16)*base;tip=gas-burn;assert tip>=0
   br['gas_wei']+=gas;br['burn_wei']+=burn;br['priority_wei']+=tip
   if r['from']==miner:br['fee_recipient_paid_gas_wei']+=gas
   cat=cats[h];categories[cat]['transactions']+=1;categories[cat]['gas_wei']+=gas;categories[cat]['burn_wei']+=burn;categories[cat]['priority_wei']+=tip
   if cat!='other_transactions':selected.append({'hash':h,'block':n,'category':cat,'gas_wei':str(gas),'burn_wei':str(burn),'priority_wei':str(tip)})
  tr=json.loads(gzip.decompress((R/'drpc_trace_raw'/f'{n}.json.gz').read_bytes()))['result'];bad=defaultdict(set)
  for t in tr:
   if t.get('transactionHash') and t.get('error'):bad[t['transactionHash']].add(tuple(t['traceAddress']))
  records=[]
  for t in tr:
   h=t.get('transactionHash')
   if not h:continue
   p=tuple(t['traceAddress'])
   if any(p[:j] in bad[h] for j in range(len(p)+1)):continue
   a=t['action'];typ=t['type']
   if typ=='call' and a.get('callType')=='call':src=a['from'];dst=a['to'];value=int(a['value'],16)
   elif typ=='create':src=a['from'];dst=t.get('result',{}).get('address');value=int(a['value'],16)
   elif typ in ['suicide','selfdestruct']:src=a['address'];dst=a['refundAddress'];value=int(a['balance'],16)
   else:continue
   if not value or src==dst:continue
   records.append({'hash':h,'from':src,'to':dst,'value_wei':str(value),'trace_address':t['traceAddress']})
   if dst==miner:br['direct_inflow_wei']+=value;categories[cats[h]]['direct_fee_recipient_inflow_wei']+=value
   if src==miner:br['direct_outflow_wei']+=value;categories[cats[h]]['direct_fee_recipient_outflow_wei']+=value
  br['fee_recipient_observed_execution_ETH_delta_wei']=br['priority_wei']+br['direct_inflow_wei']-br['direct_outflow_wei']-br['fee_recipient_paid_gas_wei']
  delivered=relays[n];variants={(r['proposer_fee_recipient'].lower(),int(r['value'])) for r in delivered};br['relay_count']=len({r['relay'] for r in delivered});br['relay_payment_status']='no_matching_relay_record'
  if len(variants)==1:
   to,value=next(iter(variants));incoming=[r for r in records if r['to']==to];fromminer=[r for r in incoming if r['from']==miner];lastidx=max(int(r['transactionIndex'],16) for r in rs);last=[r for r in incoming if int(recs[r['hash']]['transactionIndex'],16)==lastidx and r['trace_address']==[]]
   propin=sum(int(r['value_wei']) for r in incoming);propout=sum(int(r['value_wei']) for r in records if r['from']==to);propgas=sum(int(r['gasUsed'],16)*int(r['effectiveGasPrice'],16) for r in rs if r['from']==to);proptip=int(br['priority_wei']) if to==miner else 0
   br.update(proposer_native_inflow_wei=str(propin),proposer_native_outflow_wei=str(propout),proposer_paid_gas_wei=str(propgas),proposer_priority_wei=str(proptip),proposer_execution_delta_wei=str(propin-propout-propgas+proptip),relay_value_matches_proposer_execution_delta=propin-propout-propgas+proptip==value)
   br['proposer_inflow_by_transaction_category']={cat:str(sum(int(r['value_wei']) for r in incoming if cats[r['hash']]==cat)) for cat in {cats[r['hash']] for r in incoming}}
   match=fromminer if sum(int(r['value_wei']) for r in fromminer)==value and fromminer else ([r for r in last if int(r['value_wei'])==value][:1])
   if not match:
    # Match the final recipient transfer only, never sum both forwarding hops.
    for r in incoming:
     if int(r['value_wei'])!=value or int(recs[r['hash']]['transactionIndex'],16)!=lastidx:continue
     funding=[z for z in records if z['hash']==r['hash'] and z['trace_address']==[] and z['to']==r['from'] and int(z['value_wei'])==value]
     if funding:match=[r];br['payment_forwarder']=r['from'];break
   br.update(proposer_fee_recipient=to,relay_bid_wei=str(value),relay_payment_status='matched_onchain' if match else 'unmatched_or_direct_coinbase',matched_proposer_payment_wei=str(value) if match else None)
   if match:payments.append({'block':n,'block_hash':b['hash'],'proposer_fee_recipient':to,'value_wei':str(value),'payer_addresses':sorted({recs[r['hash']]['from'] for r in match}),'immediate_transfer_senders':sorted({r['from'] for r in match}),'transfers':match,'relays':sorted({r['relay'] for r in delivered}),'builder_pubkeys':sorted({r['builder_pubkey'] for r in delivered})})
  elif variants:br['relay_payment_status']='relay_values_conflict'
  for field in ['gas_wei','burn_wei','priority_wei','direct_inflow_wei','direct_outflow_wei','fee_recipient_paid_gas_wei','fee_recipient_observed_execution_ETH_delta_wei']:totals[field]+=br[field];br[field]=str(br[field])
  rows.append(br)
  if i%400==0:print('fee blocks',i,'verified proposer payouts',len(payments),flush=True)
 out={'method':'Bounded-window actual fees and fee-recipient native flows, not attack-causal income. Burn+priority=gas. Direct native tips are separate from gas. Matched proposer payments are transfers onward, not extra new revenue; relay bid not added again. Account deltas exclude consensus withdrawals and non-ETH assets.','summary':{k:str(v) for k,v in totals.items()},'relay_matched_blocks':len(payments),'relay_record_blocks':sum(bool(relays[n]) for n in headers),'matched_proposer_payout_wei':str(sum(int(p['value_wei']) for p in payments)),'categories':{k:{a:str(v) for a,v in d.items()} for k,d in categories.items()},'blocks':rows,'selected_transactions':selected,'proposer_payments':payments}
 (R/'full_fee_distribution.json').write_text(json.dumps(out,indent=2));print('DONE',out['summary'],'relay matched',len(payments),flush=True)
if __name__=='__main__':main()
