"""Transaction-order diagrams plus complete pool-state and route evidence tables."""
from decimal import Decimal
import html
import json

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT,export_interactive,export_static,RED,TEAL,BLUE,GREY

NAME="fig03_transaction_reconstruction"


def short(address):
    return address[:10]+"…"+address[-4:]


def build():
    cases=read_json(ROOT/"data/processed/arbitrage_cases.json")
    sandwich=read_json(ROOT/"reports/case_studies/S1_sandwich.json")
    states=read_json(ROOT/"data/processed/pool_states.json")
    charts=[];tables=[]
    for case in cases:
        idx0,idx1=case["target_index"],case["actor_index"]
        shared=case["same_pool_opposite_direction"][0]
        target_state=next(s for s in states if s["case_id"]==case["case_id"] and s["pool"]==shared and s["tx_hash"]==case["target"])
        actor_state=next(s for s in states if s["case_id"]==case["case_id"] and s["pool"]==shared and s["tx_hash"]==case["tx_hash"])
        charts.append({"title":f"{case['case_id']} · {case['route_label']} · block {case['block']:,} · {case['timestamp_utc']}","x":[0,1,2,3],"labels":["Pre-target\nstate",f"Wallet swap\ntx #{idx0}",f"Arbitrage ({len(case['route'])} legs)\ntx #{idx1}","Post-arbitrage\nstate"],"colors":[GREY,RED,TEAL,GREY],
            "hover":[json.dumps(target_state['before']),case['target'],case['tx_hash'],json.dumps(actor_state['after'])],
            "summary":f"Net {float(case['net_after_gas_and_builder_ETH']):.9f} ETH | gas {float(Decimal(case['gas_wei'])/Decimal(10)**18):.6f} | direct builder {float(Decimal(case['identified_builder_payment_wei'])/Decimal(10)**18):.6f}",
            "boundary":f"Sender {short(case['sender'])} · executor {short(case['executor'])}"})
        for leg in case["route"]:
            tables.append({"case_id":case["case_id"],"tx_hash":case["tx_hash"],**leg})
    idx=sandwich["transaction_indices"]
    charts.append({"title":f"S1 · complete sandwich episode · block {sandwich['block']:,}","x":[0,1,2],"labels":[f"Front leg\ntx #{idx[0]}",f"Wallet swap\ntx #{idx[1]}",f"Back leg\ntx #{idx[2]}"],"colors":[TEAL,RED,TEAL],"hover":[sandwich['front'],sandwich['target'],sandwich['back']],
        "summary":f"Two-leg net {float(sandwich['episode_net_ETH']):.6f} ETH | back-leg cash flow {float(sandwich['back_cashflow']['net_after_gas_and_builder_ETH']):.3f} ETH is NOT episode profit",
        "boundary":"Same sender · closed non-WETH token inventory · opposite back-leg direction"})
    fig=make_subplots(rows=4,cols=1,vertical_spacing=.15,subplot_titles=[c['title'] for c in charts])
    static,axes=plt.subplots(4,1,figsize=(15,13))
    for i,(c,ax) in enumerate(zip(charts,axes),1):
        fig.add_trace(go.Scatter(x=c['x'],y=[0]*len(c['x']),mode="lines+markers+text",text=[l.replace('\n','<br>') for l in c['labels']],textposition="top center",line=dict(color=GREY,width=2),marker=dict(size=15,color=c['colors']),hovertext=c['hover'],hovertemplate="%{hovertext}<extra></extra>",showlegend=False),row=i,col=1)
        fig.update_yaxes(visible=False,range=[-.5,.5],row=i,col=1)
        fig.update_xaxes(showticklabels=False,title_text="Schematic sequence; spacing is not time. Labels show actual transaction indices (0-based).",row=i,col=1)
        fig.add_annotation(text=c['summary']+"<br>"+c['boundary'],x=.5,y=-.25,xref=f"x{i if i>1 else ''} domain",yref=f"y{i if i>1 else ''}",showarrow=False,font=dict(size=11,color=TEAL))
        ax.plot(c['x'],[0]*len(c['x']),color=GREY,lw=1.8,zorder=1)
        ax.scatter(c['x'],[0]*len(c['x']),color=c['colors'],s=100,zorder=2)
        for x,label in zip(c['x'],c['labels']):
            ax.annotate(label,(x,0),xytext=(0,16),textcoords="offset points",ha="center",fontsize=10)
        ax.set_title(c['title'],loc="left",fontsize=13,fontweight="bold",pad=20)
        ax.text(.01,.06,c['summary']+"\n"+c['boundary'],transform=ax.transAxes,color="#526377",fontsize=9,va="bottom")
        ax.set_ylim(-.5,.5);ax.set_yticks([]);ax.set_xticks([])
        ax.set_xlabel("Schematic sequence; spacing is not time. Labels show actual transaction indices (0-based).",fontsize=9)
        ax.spines[["top","right","left"]].set_visible(False)
        ax.margins(x=.2)
    fig.update_layout(title="03 | Transaction-level MEV reconstruction<br><sup>Three independent atomic arbitrages and one full two-leg sandwich</sup>",height=1450)
    caption="Source: raw receipt logs and full native call trees; pool metadata / parent-block state from archived historical RPC calls.\nContextual pre/post state markers are not timestamps. Observed profit ≠ target-caused or event-total MEV. Exact states, token flows and full hashes follow below in HTML."
    export_interactive(fig,NAME,caption.replace("\n","<br>"))
    # Append auditable route and state tables, with expandable JSON and linked transactions.
    sections=['<section style="background:#0d1625;color:#dce9f6;padding:32px;font:14px Arial"><h2>Full transaction paths and pool states</h2><p>Token identities are contract addresses, not inferred from symbols. Execution order is swap log index; net pool routes may aggregate multiple calls.</p>']
    for case in cases:
        sections.append(f"<h3>{case['case_id']}: {html.escape(case['route_label'])}</h3><p>Target: <a style='color:#60d0c1' href='https://etherscan.io/tx/{case['target']}'>{case['target']}</a><br>Arbitrage: <a style='color:#60d0c1' href='https://etherscan.io/tx/{case['tx_hash']}'>{case['tx_hash']}</a></p>")
        sections.append(pd.DataFrame(case['route']).to_html(index=False,escape=True,border=0))
        sections.append('<details><summary>Exact accounting boundary, PnL and metadata evidence</summary><pre style="white-space:pre-wrap">'+html.escape(json.dumps(case,indent=2))+'</pre></details>')
    sections.append('<details><summary>All observed pre/post pool states, including intervening transactions</summary><pre style="white-space:pre-wrap">'+html.escape(json.dumps(states,indent=2))+'</pre></details>')
    sections.append('<details><summary>Full sandwich episode accounting</summary><pre style="white-space:pre-wrap">'+html.escape(json.dumps(sandwich,indent=2))+'</pre></details></section>')
    path=ROOT/f"reports/figures/{NAME}.html"
    page=path.read_text();page=page.replace('</body>',''.join(sections)+'</body>');path.write_text(page)
    static.suptitle("03 | Transaction-level MEV reconstruction",x=.06,ha="left",fontsize=24,fontweight="bold")
    static.subplots_adjust(top=.9,bottom=.13,hspace=.85,left=.07,right=.94)
    export_static(static,NAME,caption)
    pd.DataFrame([{**s,"before":json.dumps(s['before'],sort_keys=True),"after":json.dumps(s['after'],sort_keys=True)} for s in states]).to_parquet(ROOT/"reports/tables/fig03_pool_states.parquet",index=False)
    pd.DataFrame(tables).to_parquet(ROOT/"reports/tables/fig03_routes.parquet",index=False)
    print("Figure 3: three transaction sequences, one full sandwich, exact route/state companion tables")


if __name__=="__main__":
    build()
