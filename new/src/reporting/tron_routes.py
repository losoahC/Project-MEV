"""Per-event TRON paths, with actual amounts and explicitly current pool labels."""
import json,csv
from decimal import Decimal
from src.arbitrage.discover import ROOT
from src.arbitrage.tron_accounting import U,W,ZERO

def run():
    p=ROOT/'data/processed/mev_tron';data=json.loads((p/'all_named_bot_accounting.json').read_text());meta={r['pool_hex']:r for r in json.loads((p/'pool_metadata_current.json').read_text())};tokens={r['token_hex']:r for r in json.loads((p/'token_metadata_current.json').read_text())};flat=[];rows=[]
    def asset(t,v):
        m=tokens.get(t,{});dec=6 if t in [U,W,'native:trx'] else m.get('decimals');return {'token_hex':t,'symbol':'TRX' if t=='native:trx' else m.get('symbol'),'raw':str(v),'quantity':str(Decimal(v)/Decimal(10)**dec) if dec is not None else None,'decimals':dec,'metadata_state':'native denomination / canonical USDT-WTRX, or explicitly current token getter; no price mapped by symbol'}
    for r in data['rows']:
        steps=[]
        for ev in r['swap_events']:
            m=meta.get(ev['pool_hex'],{});fields=m.get('fields',{});delta={};v4=ev['protocol'].startswith('SunSwap V4');v1=ev['protocol'].startswith('SunSwap V1')
            if v4:
                key=ev.get('key_metadata')
                if key and key['verified_pool_key']:
                    for i in [0,1]:
                        t=key[f'currency{i}_hex'];t='native:trx' if t==ZERO else t;delta[t]=-int(ev[f'amount{i}_raw'])
            elif v1 and fields.get('token0'):
                n0,n1=map(int,ev['indexed_amounts_raw']);delta={fields['token0']:n0,'native:trx':-n1} if ev['topic'].startswith('dad9') else {'native:trx':n0,fields['token0']:-n1}
            elif all(k in fields for k in ['token0','token1']):
                delta={fields[f'token{i}']:int(ev[f'amount{i}_raw']) for i in [0,1]}
            inputs=[asset(t,v) for t,v in delta.items() if v>0];outputs=[asset(t,-v) for t,v in delta.items() if v<0];dex='SunSwap V4' if v4 and ev.get('key_metadata',{}).get('official_manager') else m.get('DEX_current_factory');step={'log_index':ev['log_index'],'pool_key':ev['pool_hex']+(':'+ev['pool_id'] if ev.get('pool_id') else ''),'protocol_event':ev['protocol'],'DEX':dex,'DEX_metadata_state':'PoolKey authenticated from historical event hash; manager official current source' if v4 else 'current factory corroboration, not historical state','inputs':inputs,'outputs':outputs,'amounts_resolved':bool(inputs and outputs),'original_event':ev};steps.append(step)
            flat.append({'tx_hash':r['tx_hash'],'block':r['block'],'owner':r['owner'],'entrypoint':r['entrypoint'],'log_index':step['log_index'],'pool_key':step['pool_key'],'DEX':dex or 'unnamed','identity_note':step['DEX_metadata_state'],'input_assets':json.dumps(inputs,separators=(',',':')),'output_assets':json.dumps(outputs,separators=(',',':')),'closed_cycle_at_transaction_boundary':r['mechanically_closed_positive_USDT_cycle'],'reference_trade_edge_USD_not_cost_basis_profit':r['marked_swap_reference_edge_after_fee_USD']})
        rows.append({'tx_hash':r['tx_hash'],'owner':r['owner'],'entrypoint':r['entrypoint'],'swap_event_count':len(steps),'distinct_pool_keys':len({s['pool_key'] for s in steps}),'ordered_swaps':steps,'actual_pool_transfer_legs':r['pool_legs'],'boundary':r['boundary'],'target_pool_chronology':r['target_pool_chronology'],'round_note':'Do not treat distinct pool count or repeated swap count as economic round count. Closed-cycle status applies to the full transaction ledger; callbacks can reverse emission order.','evidence':r['evidence']})
    (p/'all_named_ordered_routes.json').write_text(json.dumps(rows,indent=2));dest=ROOT/'reports/mev_expansion/TRON逐笔池路径.csv'
    with dest.open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    print('TRON path transactions',len(rows),'swap-event rows',len(flat),'resolved',sum(bool(r['input_assets']!='[]' and r['output_assets']!='[]') for r in flat))
if __name__=='__main__':run()
