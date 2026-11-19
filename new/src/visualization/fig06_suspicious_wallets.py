"""Rank measured execution shortfalls, with auditable detail and no intent inference."""
import json
from decimal import Decimal

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT,export_static,export_interactive,RED,GREY

NAME='fig06_suspicious_wallets'


def scenario_bounds(row):
    scenarios=json.loads(row['sensitivity']) if isinstance(row['sensitivity'],str) else row['sensitivity']
    values=[Decimal(row['loss_USD'])]+[Decimal(v['loss_USD']) for v in scenarios.values() if v.get('loss_USD') is not None]
    return min(values),max(values)


def build():
    data=pd.read_parquet(ROOT/'data/processed/suspicious_transactions.parquet').sort_values('rank')
    data['scenario_min_USD']=[str(scenario_bounds(r)[0]) for r in data.to_dict('records')]
    data['scenario_max_USD']=[str(scenario_bounds(r)[1]) for r in data.to_dict('records')]
    top=data.head(20).iloc[::-1]
    labels=[f"#{r['rank']} · Wallet {r['wallet']} · {r['address'][:8]}…{r['address'][-4:]}" for r in top.to_dict('records')]
    hover=[[r['tx_hash'],r['address'],r['input_reference_USD'],r['output_reference_USD'],float(r['loss_rate'])*100,r['timestamp_utc'],r['classification']] for r in top.to_dict('records')]
    fig=go.Figure(go.Bar(x=top.loss_USD.astype(float)/1e6,y=labels,orientation='h',marker_color=RED,error_x=dict(type='data',symmetric=False,array=[max(0,(float(r['scenario_max_USD'])-float(r['loss_USD']))/1e6) for r in top.to_dict('records')],arrayminus=[max(0,(float(r['loss_USD'])-float(r['scenario_min_USD']))/1e6) for r in top.to_dict('records')],color=GREY,thickness=1.2,width=3),customdata=hover,hovertemplate='Wallet %{customdata[1]}<br>Tx %{customdata[0]}<br>Input reference $%{customdata[2]}<br>Output reference $%{customdata[3]}<br>Shortfall %{x:.6f}M USD (%{customdata[4]:.3f}%)<br>%{customdata[5]}<br>Classification: %{customdata[6]}<extra></extra>'))
    fig.update_layout(title='06 | Largest screened execution shortfalls<br><sup>Input > $100,000 and reference loss rate > 5%; transaction intent remains unresolved</sup>',height=1050,xaxis_title='Estimated execution shortfall (USD millions)',margin=dict(l=300))
    coverage=read_json(ROOT/'data/processed/anomaly_coverage.json')
    cases=read_json(ROOT/'data/processed/anomaly_case_studies.json')
    allswaps=pd.read_parquet(ROOT/'data/processed/wallet_swap_valuations.parquet')
    caption=f"Ethereum swaps: {allswaps.timestamp_utc.min()} – {allswaps.timestamp_utc.max()} (UTC).\n{coverage['two_sided_swap_wallet_rows']} two-sided wallet/swap rows, {coverage['fully_valued_rows']} strictly valued, {coverage['qualified_rows']} qualify. USD at prior completed Coinbase minute; contract identities and decimals checked.\nNo price or identity → no numerical loss. Same-block associations are not causal MEV or evidence of intentional self-loss. Whiskers = available price-feed/timing scenario min–max, not statistical confidence intervals. Click a top-five bar for detailed evidence below."
    export_interactive(fig,NAME,caption.replace('\n','<br>'))
    path=ROOT/f'reports/figures/{NAME}.html'
    payload=json.dumps(cases,ensure_ascii=False).replace('</','<\\/')
    detail='''<section style="background:#0d1625;color:#dce9f6;padding:32px;font:14px Arial"><h2>Top-five case evidence</h2><p>Insufficient evidence of deliberate self-loss. Zero intermediate minimums coexist with nonzero final guards; unknown V4 / deployed-contract semantics remain unresolved.</p><select id="case-select" style="padding:10px;background:#1b2c43;color:white"></select><div id="case-summary" style="padding:18px"></div><details><summary>Exact transaction, pool-state, router-limit and neighbouring-flow evidence</summary><pre id="case-json" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre></details></section><script>(function(){const cases=__CASES__;const choose=document.querySelector('#case-select'),summary=document.querySelector('#case-summary'),detail=document.querySelector('#case-json');for(const c of cases){const o=document.createElement('option');o.value=c.tx_hash;o.textContent=c.case_id+' · Wallet '+c.wallet+' · $'+Number(c.loss_USD).toLocaleString(undefined,{maximumFractionDigits:2});choose.appendChild(o)}function show(hash){const c=cases.find(c=>c.tx_hash===hash);if(!c)return;choose.value=hash;summary.textContent=c.timestamp_utc+' | '+c.tx_hash+' | Loss rate '+(100*Number(c.loss_rate)).toFixed(3)+'% | Exact reconstructed arbitrage case links: '+(c.verified_arbitrage_cases_linked.join(', ')||'none in selected A1–A3 sample')+' | Classification: '+c.final_classification;detail.textContent=JSON.stringify(c,null,2)}choose.onchange=()=>show(choose.value);const plot=document.querySelector('.plotly-graph-div');plot.on('plotly_click',ev=>show(ev.points[0].customdata[0]));show(cases[0].tx_hash)})();</script>'''.replace('__CASES__',payload)
    path.write_text(path.read_text().replace('</body>',detail+'</body>'))
    static,ax=plt.subplots(figsize=(15,10))
    selected=data.head(12).iloc[::-1]
    short=[f"#{r['rank']}  Wallet {r['wallet']}  {r['address'][:8]}…{r['address'][-4:]}\nTx {r['tx_hash'][:12]}…{r['tx_hash'][-6:]}" for r in selected.to_dict('records')]
    values=selected.loss_USD.astype(float)/1e6
    ax.barh(short,values,color=RED,height=.65)
    ax.errorbar(values,range(len(selected)),xerr=[(selected.loss_USD.astype(float)-selected.scenario_min_USD.astype(float))/1e6,(selected.scenario_max_USD.astype(float)-selected.loss_USD.astype(float))/1e6],fmt='none',ecolor=GREY,capsize=3,linewidth=1)
    for i,(v,rate) in enumerate(zip(values,selected.loss_rate.astype(float))):
        ax.text(max(v,float(selected.iloc[i].scenario_max_USD)/1e6)+.06,i,f'${v:.3f}M · {rate*100:.2f}%',va='center',fontsize=9)
    ax.set_xlabel('Estimated reference-value shortfall (USD millions; gas excluded)')
    ax.set_xlim(0,max(values)*1.25);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.tick_params(axis='y',labelsize=9)
    static.suptitle('06 | Largest screened execution shortfalls',x=.06,ha='left',fontsize=23,fontweight='bold')
    static.text(.06,.91,'Five cases exceed USD 1M; two exceed USD 5M. These are execution-value estimates, not proof of intentional loss.',fontsize=11,color='#526377')
    static.subplots_adjust(top=.85,bottom=.17,left=.27,right=.94)
    export_static(static,NAME,caption.replace('Click a top-five bar for detailed evidence below.','Exact hashes, UTC timestamps, sources and interpretation: interactive companion and case-study tables.'))
    top.to_parquet(ROOT/'reports/tables/fig06_ranked_shortfalls.parquet',index=False)
    print('Figure 6: ranked reference-value losses with five expandable forensic case studies')


if __name__=='__main__':
    build()
