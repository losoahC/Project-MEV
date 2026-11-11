import json,gzip,hashlib
from pathlib import Path
from decimal import Decimal as D,getcontext
getcontext().prec=70
R=Path(__file__).resolve().parent
def load(n):return json.loads((R/n).read_text())
def main():
 checks=[]
 def check(name,ok,detail):
  checks.append({'check':name,'passed':bool(ok),'detail':detail})
 ledger=load('window_ledger.json');cost=load('window_block_costs.json');v=load('expanded_valuation.json');native=load('native_evidence.json');ac=load('candidate_accounting_93.json')['rows'];byh={r['hash']:r for r in v['rows']};byc={r['hash']:r for r in ac}
 check('连续窗口无缺块',not ledger['errors'] and ledger['blocks_successful']==ledger['last_block']-ledger['first_block']+1,ledger['blocks_successful'])
 check('回执与区块已逐块核对',not cost['errors'] and len(cost['rows'])==ledger['blocks_successful'],'block_costs.py verifies block hash and transaction count')
 check('地址活动无重复交易',len({r['hash'] for r in ledger['rows']})==len(ledger['rows']),len(ledger['rows']))
 check('候选无重复交易',len({r['hash'] for r in load('expanded_candidates.json')['rows']})==len(load('expanded_candidates.json')['rows']),len(load('expanded_candidates.json')['rows']))
 check('ETH 内部收支守恒',not native['errors'] and all(D(r['net_conservation_eth'])==0 for r in native['rows']),len(native['rows']))
 check('原四笔跨浏览器一致',all(r['matches'] for r in load('blockscout_native_evidence.json')['crosschecks']) and len(load('blockscout_native_evidence.json')['crosschecks'])==4,4)
 for old in load('swaps_observed.json')['swaps']:
  r=byh[old['tx_hash']];check('旧兑换金额与费用回归 '+old['tx_hash'],D(r['net_assets']['USDT'])==-D(old['input']) and D(r['net_assets']['ETH'])==D(old['output']) and D(r['total_tx_gas_eth'])==D(old['fee']),'token input / native output / gas')
 olds=load('sample_calculated.json');oldhash={r['tx_hash'] for r in olds['swaps']};total=sum(D(r['shortfall_usd']) for r in v['rows'] if r['hash'] in oldhash)
 check('旧样本市场差额回归',abs(total-D(olds['execution_value_shortfall_usd']))<D('.000001'),str(total))
 for old in load('verified_arbitrage.json')['verified_examples']:
  r=byc[old['hash']];check('旧套利账户净额回归 '+old['hash'],D(r['net_ETH_WETH_after_gas'])==D(old['estimated_execution_net_eth']) and D(r['builder_internal_net_eth'])==D(old['builder_payment_eth']),'accounting only, not causal proof')
 check('gas 分项守恒',all(D(r['gas_fee_wei'])==D(r['base_burn_wei'])+D(r['priority_fee_wei']) for r in cost['rows']),len(cost['rows']))
 check('未定价币种未按零损失展示',all(d['shortfall_usd'] is None for d in v['summary'].values() if d['priced_count']==0),'unknown represented by null')
 tron=load('tron_transactions.json');tl=load('tron_ledger.json');tv=load('tron_valuation.json');check('TRON 地址与交易信息下载无错误',not tron['errors'] and not tl['errors'],{'addresses':tron['address_count'],'transactions':len(tron['rows']),'contract_calls':len(tl['rows'])})
 check('TRON 全部交易去重',len({r['txID'] for r in tron['rows']})==len(tron['rows']),len(tron['rows']))
 check('TRON 大额样本无缺价格',tv['summary']['large_swap_count']==tv['summary']['priced_large_swaps'],tv['summary']['priced_large_swaps'])
 check('TRON 大额收支量纲',D(tv['summary']['USDT_input'])==D('234000000') and D(tv['summary']['TRX_received'])>0,'USDT and TRX both six decimals')
 check('引用价格先于交易',all(r['reference_candle_ms']+60000<=r['timestamp_ms']//60000*60000 for r in tv['rows'] if r['shortfall_usd'] is not None),'TRON candle end at/before current minute')
 out={'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'limitations':'Checks validate data consistency and arithmetic, not full coverage, ownership or causal MEV.'};(R/'validation_results.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps(out,ensure_ascii=False,indent=2))
 if out['failed']:raise SystemExit(1)
if __name__=='__main__':main()
