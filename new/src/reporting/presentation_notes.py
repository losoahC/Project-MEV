"""Authoritative slide-by-slide research content, exact values and source notes."""
from decimal import Decimal
import json
import xml.etree.ElementTree as ET
from src.visualization.common import ROOT


def read(p):return json.loads((ROOT/p).read_text())
def build():
    arb=read('data/processed/arbitrage_cases.json');auction=read('data/processed/auction_outcomes.json');anomaly=read('data/processed/anomaly_case_studies.json');thor=read('data/processed/thorchain_paths.json');rec=read('data/processed/loss_reconciliation.json');inv=read('data/processed/asset_inventory.json')
    xml=ET.parse(ROOT/'reports/pytest-results.xml');test_count=sum(int(x.get('tests',0)) for x in xml.getroot().iter('testsuite'))
    titles=['Binance Incident, DEX Arbitrage and MEV Auctions','Research scope','Wallets and data','Measuring dislocation','Actual arbitrage A1','Three arbitrage cases','A complete sandwich episode','Auction results and proposer payments','Auction coverage and sensitivity','Largest abnormal swaps','Slippage protection and intent','Three matched THORChain paths','Snapshot reconciliation','Conclusions and limits']
    bodies=[
    'Group12 · FT565. Evidence from Ethereum execution, relay records and matched cross-chain conversions. Research snapshot18Nov2026.',
    'Ethereum blocks26,300,640–26,303,950. Transfer observations29Oct20:24:23–30Oct07:02:47UTC. Observed transactions; estimated reference shortfalls; unresolved intent, causal MEV and ownership. November THOR paths are separate.',
    '16 historical address leads,15 independently source-corroborated.1,640 transactions;57,042 core transfer edges;1,155 compatible Swap events. Wallet13 unverified;wallet9 source concerns Arbitrum. All16 fresh numbered-label pages returned403. Receiving funds does not prove common control.',
    'Execution price=input reference USD/output ETH quantity. N1:USD29,961,300 input,9,551.900920ETH output,USD3,136.68 effective price versusUSD2,260 reference. Estimated shortfallUSD8,374,003.92,gas excluded.210 observed price points in Figure2; no full no-MEV counterfactual.',
    'A1,block26,300,992:14 aggregated pool legs; non-WETH inventory closes.12.137824ETH gross after pool fees−1.139064ETHgas−8.252948ETHbuilder=2.745812ETH retained net. The target’sUSD8.374M shortfall is a different quantity.',
    'A1/A2/A3 retained net:2.745812,0.000065,0.002184ETH. Selected total gross12.147692ETH; net2.748062ETH. Display rounded to6decimals; exact amounts below. These are selected cases, not event-wide MEV.',
    'Block26,301,609; indices9/10/11. Front≈−555.599628ETH; back≈+567.679662ETH. Full episode net12.080033775421395622ETH. Back-leg proceeds are not episode profit. No causal incremental victim loss established.',
    'A1/A2/A3 proposer payments36.437514095553389525,3.120166160586952436,0.578802351165718120ETH. All3 exactly reconcile. SELFDESTRUCT forwarding matters; A3 payer differs from fee recipient. Whole-block payments are not solely one searcher’s cost.',
    '2,939 delivered blocks/3,311; baseline109/130,event2,830/3,181.7,958 retained submissions;3slots,4relays. Revisions/late bids may appear. Drop Ultrasound:3,129 records,1/3retained relay outcome support,3/3independent onchain payments. No decision cutoff known.',
    'N1–N5 shortfalls≈USD8.374M,6.047M,4.279M,3.257M,2.001M.810two-sided rows;621complete valuations;241qualify(input>USD100k and loss>5%).Five aboveUSD1M,two aboveUSD5M. No deliberate loss proven.',
    'All5 have zero intermediate minima AND nonzero final unwrap minima. Zero-bound counts18/17/17/16/16. N3/N4 internal execute calls decoded despite unsupported root selector. Classification:insufficient_evidence. Adjacent profits and later incoming transfers are not compensating-profit proof.',
    '17Nov2026:T1 36ETH→1.00484202BTC;T2 61ETH→1.68897154BTC;T3 40ETH→1.10797406BTC. Estimated deposit-time shortfallsUSD316.17/754.33/429.72. Every path matches ETHreceipt,THORNode,Midgard and confirmed BTCvout/OUTmemo. Prior funding association is not exclusive taint/control.',
    'Fixed closing reference30Oct07:02:47UTC:four-asset balancesUSD2.646601359B,includingUSD2.026000812B blacklisted stablecoins andUSD0.620600547B other lead balances.64/64four-asset accounts reconcile. Wider raw inventory:64assets×16leads=1,024/1,024 ledgers reconcile. Blacklisting is not recovery.',
    f'621unique completely valued swaps showUSD43.728M signed trade-time shortfall in this bounded sample. Selected profits/payments can be reconstructed; causal whole-event MEV remains unresolved. Eight reproducible figures;{test_count}tests passed. Price timing comparisons use identical transaction sets.'
    ]
    sources=[['docs/research_plan_supplied.md'],['docs/teacher_group12_source.txt','data/processed/coverage.json'],['data/processed/wallet_registry.json','data/fixtures/identity_observations.json','data/processed/incident_delegation.json'],['reports/case_studies/N1_abnormal_swap.json','reports/tables/fig02_price_observations.parquet','reports/tables/fig02_reference_prices.parquet'],['reports/case_studies/A1_arbitrage.json'],['data/processed/arbitrage_cases.json'],['reports/case_studies/S1_sandwich.json'],['data/processed/auction_outcomes.json','data/processed/proposer_payments.parquet'],['data/processed/auction_submissions.json','data/processed/auction_coverage.json','data/processed/auction_timing_assessment.json','data/processed/loss_reconciliation.json'],['data/processed/suspicious_transactions.parquet','data/processed/anomaly_case_studies.json'],['data/processed/anomaly_case_studies.json','src/decoding/router.py'],['data/processed/thorchain_paths.json'],['data/processed/balance_reconciliation.json','data/processed/asset_inventory.json','data/processed/loss_reconciliation.json'],['data/processed/loss_reconciliation.json','reports/final_research_report.md','reports/pytest-results.xml']]
    assert all((ROOT/p).exists() for ss in sources for p in ss)
    extra={4:anomaly[0],5:arb[0],6:arb,7:read('reports/case_studies/S1_sandwich.json'),8:auction,9:rec['missing_relay_sensitivity'],10:[{k:r[k] for k in ['case_id','tx_hash','address','timestamp_utc','input_reference_USD','output_reference_USD','loss_USD','loss_rate','final_classification']} for r in anomaly],11:[{'case':r['case_id'],'zero_minima':r['observed_zero_minimum_bound_count'],'nonzero_bounds':r['observed_nonzero_minimum_bounds'],'intent_established':r['intentional_self_loss_established']} for r in anomaly],12:thor,13:{'asset_ledger_USD':rec['asset_ledger_USD'],'valuation_timestamp_utc':rec['valuation_timestamp_utc'],'inventory_assets':inv['asset_count'],'inventory_balanced_rows':inv['balanced_rows']},14:{'same_transaction_price_sensitivity':rec['paired_price_timing_sensitivity'],'ownership_sensitivity':rec['ownership_sensitivity']}}
    records=[];content=['# Group12 · 14-slide research presentation content','', 'English slides; UTC throughout. Compact body text below is presentation-ready. Companion notes provide exact amounts and source paths; the Canva design may summarize/round the body text.',''];notes=['# Group12 · Presenter notes and source evidence','', 'Read with the fourteen-slide presentation. These notes are the authoritative companion: exact values, original hashes, source pointers and limits. Never use an unsupported illustrative price chart.','']
    for i,(title,body,ss) in enumerate(zip(titles,bodies,sources),1):
        content += [f'## Slide {i} — {title}','',body,'',f'[Exact source notes](presenter_notes.md#slide-{i})','']
        notes += [f'<a id="slide-{i}"></a>',f'## Slide {i} — {title}','',body,'','Source files (paths relative to new/):','']
        for p in ss:notes.append(f'- [{p}](../../{p})')
        if i in extra:
            notes += ['', 'Exact evidence extract (observations and estimates retain their original field names):','', '```json',json.dumps(extra[i],indent=2),'```','']
        records.append({'slide':i,'title':title,'body':body,'sources':ss,'exact_evidence':extra.get(i),'numerical_status':'observed/estimated/unresolved as field-labelled; no full-event total inferred'})
    out=ROOT/'reports/presentation';out.mkdir(exist_ok=True)
    (out/'slide_content.md').write_text('\n'.join(content)+'\n');(out/'presenter_notes.md').write_text('\n'.join(notes)+'\n');(out/'slide_notes.json').write_text(json.dumps(records,indent=2));print('Wrote14 concise research slides plus exact presenter-source companion notes')

if __name__=='__main__':build()
