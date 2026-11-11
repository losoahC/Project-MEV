import json
from pathlib import Path
R=Path(__file__).resolve().parent
load=lambda n:json.loads((R/n).read_text())
def main():
 checks=[]
 def check(name,x):checks.append({'name':name,'passed':bool(x)})
 nonce=load('wallet_nonce_authorization_reconciliation.json');headers=load('wallet_nonce_header_crosscheck.json');native=load('wallet_native_balance_reconciliation.json');tokens=load('wallet_token_balance_reconciliation.json');aave=load('aave_token_balance_residual_proof.json');cov=load('wallet_history_coverage.json')
 check('48 indexed endpoint scans exhausted',len(cov['rows'])==48 and all(r['pagination_exhausted'] and not r['error'] for r in cov['rows']))
 check('1024 indexed outgoing transactions match RPC',headers['expected']==headers['checked']==1024 and not headers['mismatches'] and not headers['errors'] and all(r['verified'] for r in headers['rows']))
 check('all 16 nonce totals reconcile including three verified authorization increments',len(nonce['rows'])==16 and sum(len(r['authorization_nonce_proofs']) for r in nonce['rows'])==3 and all(r['chain_nonce']==r['indexed_outgoing_transactions']+len(r['authorization_nonce_proofs']) and not r['unexplained_nonces'] for r in nonce['rows']))
 check('16 native balances independently conserve wei',len(native['rows'])==16 and not native['errors'] and all(int(r['start_balance_wei'])+sum(int(e['native_net_wei'])-int(e.get('gas_wei','0')) for e in r['entries'])==int(r['end_balance_wei']) for r in native['rows']))
 check('WETH synthetic records replaced exactly once',len({(e['wallet'],e['hash'],e['log_index']) for e in tokens['indexed_WETH_synthetic_events_replaced']})==len(tokens['indexed_WETH_synthetic_events_replaced']) and all(r['residual_raw']=='0' for r in tokens['rows'] if r['token']=='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'))
 proofs={r['token']:r for r in aave['rows']};valid=0
 for r in tokens['rows']:
  residual=int(r['end_balance_raw'])-int(r['start_balance_raw'])-int(r['indexed_transfer_net_raw'])-int(r['WETH_wrap_net_raw']);assert residual==int(r['residual_raw'])
  if residual==0:valid+=1;continue
  p=proofs[r['token']];ss=p['states'];ok=ss[0]['scaled_balance_raw']==ss[1]['scaled_balance_raw'] and all((int(s['scaled_balance_raw'])*int(s['normalized_index_ray'])+10**27//2)//10**27==int(s['balance_raw']) for s in ss) and int(ss[0]['balance_raw'])==int(r['indexed_transfer_net_raw']) and int(ss[1]['balance_raw'])==int(r['end_balance_raw']) and int(ss[1]['balance_raw'])-int(ss[0]['balance_raw'])==residual
  valid+=bool(ok)
 check('106 token-wallet balances reconcile including independently recomputed Aave interest',valid==len(tokens['rows'])==106 and not tokens['errors'])
 check('coverage boundaries explicit',bool(tokens['excluded_contracts']) and all(r['cutoff_block']==26349764 for r in native['rows']+tokens['rows']))
 out={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'scope':'Conservation and nonce coverage evidence, not proof no omitted offsetting transactions or unknown-token events.'};(R/'wallet_history_accounting_validation.json').write_text(json.dumps(out,indent=2));print(out);assert out['failed']==0
if __name__=='__main__':main()
