"""Keep selected searcher surplus and whole-block onward payments in distinct accounting panels."""
from decimal import Decimal
import json
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT,export_interactive,export_static,RED,TEAL,BLUE,GREY

NAME="fig04_mev_value_attribution";E=Decimal(10)**18


def build():
    rows=read_json(ROOT/'data/processed/auction_outcomes.json')
    swaps=read_json(ROOT/'data/processed/wallet_swap_valuations.json')
    targets={a['case_id']:next((v for v in swaps if v['tx_hash']==a['target']),None) for a in read_json(ROOT/'data/processed/arbitrage_cases.json')}
    target_text=[]
    for case,v in targets.items():
        value=f"USD {Decimal(v['loss_USD']):,.2f}" if v and v['loss_USD'] is not None else 'Unresolved price coverage'
        target_text.append(f'{case}: {value}')
    categories=[('Searcher retained',TEAL,'selected_searcher_retained_ETH',False),('Direct builder payment',BLUE,'selected_searcher_direct_builder_wei',True),('Priority fee',GREY,'selected_searcher_priority_wei',True),('Base-fee burn',RED,'selected_searcher_burn_wei',True)]
    fig=make_subplots(rows=2,cols=2,specs=[[{'type':'xy'},{'type':'domain'}],[{'type':'table','colspan':2},None]],row_heights=[.58,.42],subplot_titles=('Selected searcher surplus allocation (after pool fees)','Attribution boundaries','Whole-block payment reconciliation (different denominator)'))
    static=plt.figure(figsize=(15,10));grid=static.add_gridspec(2,2,height_ratios=[1.5,1]);ax=static.add_subplot(grid[0,0]);info=static.add_subplot(grid[0,1]);tab=static.add_subplot(grid[1,:])
    bottom=np.zeros(3);table_rows=[]
    for label,color,key,iswei in categories:
        amounts=[Decimal(r[key])/E if iswei else Decimal(r[key]) for r in rows]
        percentages=[float(v/Decimal(r['selected_searcher_gross_after_pool_fees_ETH'])*100) for v,r in zip(amounts,rows)]
        fig.add_trace(go.Bar(x=[r['case_id'] for r in rows],y=percentages,name=label,marker_color=color,customdata=[str(v) for v in amounts],hovertemplate='%{x}: %{customdata} ETH<br>%{y:.3f}%<extra>'+label+'</extra>'),row=1,col=1)
        ax.bar([r['case_id'] for r in rows],percentages,bottom=bottom,color=color,label=label,width=.6)
        bottom+=np.array(percentages)
    for i,r in enumerate(rows):
        ax.text(i,103,f"Gross {float(r['selected_searcher_gross_after_pool_fees_ETH']):.6f} ETH",ha='center',fontsize=9)
        receipts=(Decimal(r['whole_block_priority_wei'])+Decimal(r['whole_block_native_receipts_wei']))/E
        costs=(Decimal(r['whole_block_other_native_outflow_wei'])+Decimal(r['fee_recipient_own_gas_wei']))/E
        table_rows.append([r['case_id'],f"{receipts:.6f}",f"{Decimal(r['onchain_proposer_payment_wei'])/E:.6f}",f"{Decimal(r['fee_recipient_funded_proposer_wei'])/E:.6f}",f"{costs:.6f}",f"{Decimal(r['builder_execution_balance_margin_proxy_wei'])/E:.6f}",f"{Decimal(r['builder_margin_proxy_wei'])/E:.6f}" if r['builder_margin_proxy_wei'] is not None else 'Unresolved payer'])
    boundary="Target swap reference shortfalls (gas excluded):<br>"+"<br>".join(target_text)+"<br>These estimates are NOT the shown ETH surplus.<br><br>LP fees: embedded in observed swaps; exact per-LP value not allocated here.<br><br>Searcher → builder and builder → proposer are internal transfers.<br><br>Whole-block payout is NOT attributed entirely to one selected searcher.<br><br>A3 proposer payer differs from fee recipient; common ownership is unresolved."
    fig.add_annotation(text=boundary,x=.97,y=.98,xref='paper',yref='paper',xanchor='right',yanchor='top',showarrow=False,align='left',font=dict(size=13),width=440)
    headers=['Case','Fee-recipient receipts (ETH)','All proposer paid (ETH)','Recipient-funded proposer (ETH)','Other recipient costs (ETH)','Fee-recipient balance proxy (ETH)','Builder margin proxy (ETH)']
    fig.add_trace(go.Table(header=dict(values=headers,fill_color='#263a55'),cells=dict(values=list(map(list,zip(*table_rows))),fill_color='#142237',height=35)),row=2,col=1)
    fig.update_layout(title='04 | Observed MEV value transfers<br><sup>Three selected arbitrages; pool fees embedded, no repeated subtraction of onward payments</sup>',barmode='stack',height=950,legend=dict(orientation='h',y=1.08))
    fig.update_yaxes(title_text='Share of observed after-pool-fee surplus (%)',range=[0,112],row=1,col=1)
    caption=f"Selected blocks: {min(r['timestamp_utc'] for r in rows)} – {max(r['timestamp_utc'] for r in rows)} (UTC).\nReceipts − recipient-funded proposer payout − other recipient costs = recipient balance proxy. A3 proposer paid from a separate address is not subtracted from this recipient's balance.\nObserved execution ETH cash flows, not event-wide causal loss. A1/A2 partial builder proxies exclude offchain costs/assets; A3 builder proxy unavailable. Transaction paths: auction_outcomes.json."
    export_interactive(fig,NAME,caption)
    ax.set_ylim(0,114);ax.set_ylabel('Share of selected gross surplus (%)');ax.set_title('Searcher-level allocation',loc='left',fontweight='bold');ax.spines[['top','right']].set_visible(False);ax.legend(loc='upper left',bbox_to_anchor=(0,-.12),fontsize=9,ncol=2,frameon=False)
    info.axis('off');wrapped='\n\n'.join(textwrap.fill(p,width=52) for p in boundary.replace('<br>','\n').split('\n\n'));info.text(0,1,wrapped,va='top',fontsize=10.5,color='#526377')
    tab.axis('off');short_headers=['Case','Receipts\nETH','All proposer\npaid ETH','Recipient-funded\nproposer ETH','Other costs\nETH','Recipient proxy\nETH','Builder proxy\nETH']
    table=tab.table(cellText=table_rows,colLabels=short_headers,loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,2.3)
    tab.set_title('Whole-block ETH ledger — separate from selected-searcher surplus',loc='left',fontsize=12,fontweight='bold')
    static.suptitle('04 | MEV value transfers and accounting boundaries',x=.06,ha='left',fontsize=22,fontweight='bold')
    static.subplots_adjust(top=.86,bottom=.17,left=.07,right=.95,hspace=.55,wspace=.4)
    export_static(static,NAME,caption)
    pd.DataFrame(table_rows,columns=headers).to_parquet(ROOT/'reports/tables/fig04_whole_block_ledger.parquet',index=False)
    (ROOT/'reports/tables/fig04_attribution_status.json').write_text(json.dumps({'hacker_execution_loss':{case:({'tx_hash':v['tx_hash'],'input_reference_USD':v['input_reference_USD'],'output_reference_USD':v['output_reference_USD'],'shortfall_USD':v['loss_USD'],'reference_time':'prior completed minute per target swap','gas_excluded':True,'causal_MEV_loss_established':False} if v else None) for case,v in targets.items()},'LP_value_capture':'Fee tiers and V2 mechanical fee effects available; exact per-LP attribution unmeasured.','searcher':'Observed net cash flow in explicit sender/executor boundary','builder':'Partial execution-ETH proxy for A1/A2; A3 ownership boundary unresolved','proposer':'Three exact relay-to-onchain matches, including forwarding-contract SELFDESTRUCT paths','other_costs':'Base-fee burn and identifiable gas/native payments; unknown offchain costs remain missing.'},indent=2))
    print('Figure 4: separate searcher and whole-block ledgers, unknown attribution explicit')


if __name__=='__main__':
    build()
