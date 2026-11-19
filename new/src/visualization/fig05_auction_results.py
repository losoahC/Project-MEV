"""Delivered payloads, retained received bids and the limits of observable competition."""
from decimal import Decimal
import json

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT,export_interactive,export_static,RED,TEAL,BLUE,GREY

NAME='fig05_auction_results';E=Decimal(10)**18


def build():
    deliveries=pd.read_parquet(ROOT/'data/processed/auction_deliveries.parquet')
    submissions=read_json(ROOT/'data/processed/auction_submissions.json')
    outcomes=read_json(ROOT/'data/processed/auction_outcomes.json')
    coverage=read_json(ROOT/'data/processed/auction_coverage.json')
    titles=['Observed received submissions by slot','Delivered value vs. other retained submissions','Delivered payload frequency by observed builder key','Relay-declared delivered value over event window','Whole-block payout vs. selected realized arbitrage surplus','Baseline vs. event observed delivered values']
    fig=make_subplots(rows=3,cols=2,subplot_titles=titles,vertical_spacing=.15,horizontal_spacing=.16)
    static,axes=plt.subplots(3,2,figsize=(17,15));flat=axes.ravel()
    for cls,color in [('delivered payload candidate',TEAL),('non-delivered submission (may be revision or losing bid)',GREY)]:
        ss=[s for s in submissions if s['classification']==cls]
        if ss:
            fig.add_trace(go.Scatter(x=[str(s['slot']) for s in ss],y=[float(s['value_ETH']) for s in ss],mode='markers',name=cls,marker=dict(color=color,size=4,opacity=.5),text=[s['relay']+'<br>'+s['builder_pubkey']+'<br>'+s['block_hash'] for s in ss],hovertemplate='%{text}<br>%{y:.9f} ETH<extra></extra>'),row=1,col=1)
            xs={str(o['slot']):i for i,o in enumerate(outcomes)}
            flat[0].scatter([xs[str(s['slot'])] for s in ss],[float(s['value_ETH']) for s in ss],s=8,color=color,alpha=.4,label='Delivered candidate' if cls.startswith('delivered') else 'Non-delivered / revision')
    flat[0].set_xticks(range(3));flat[0].set_xticklabels([str(o['slot']) for o in outcomes],fontsize=8);flat[0].set_ylabel('Submitted value (ETH)');flat[0].legend(fontsize=8)
    comparisons=[]
    for o in outcomes:
        other=[Decimal(s['value_ETH']) for s in submissions if s['case_id']==o['case_id'] and not s['delivered_block_hash_match']]
        comparisons.append({'case_id':o['case_id'],'delivered_ETH':str(Decimal(o['delivered_value_wei'])/E),'maximum_observed_other_ETH':str(max(other)) if other else None,'other_submission_rows':len(other)})
    fig.add_trace(go.Bar(x=[c['case_id'] for c in comparisons],y=[float(c['delivered_ETH']) for c in comparisons],name='Delivered payload',marker_color=TEAL),row=1,col=2)
    fig.add_trace(go.Bar(x=[c['case_id'] for c in comparisons],y=[float(c['maximum_observed_other_ETH']) if c['maximum_observed_other_ETH'] is not None else None for c in comparisons],name='Max retained non-delivered submission',marker_color=GREY),row=1,col=2)
    for i,c in enumerate(comparisons):
        flat[1].bar(i-.18,float(c['delivered_ETH']),width=.35,color=TEAL,label='Delivered' if i==0 else None)
        if c['maximum_observed_other_ETH'] is not None:
            flat[1].bar(i+.18,float(c['maximum_observed_other_ETH']),width=.35,color=GREY,label='Max retained other' if i==0 else None)
    flat[1].set_xticks(range(3));flat[1].set_xticklabels([c['case_id'] for c in comparisons]);flat[1].set_ylabel('Value (ETH)')
    identity=deliveries.builder_pubkey.fillna('UNRESOLVED relay-specific keys')
    flat[1].legend(fontsize=8)
    all_counts=identity.value_counts()
    counts=all_counts.head(9)
    labels=['Unresolved keys' if x.startswith('UNRESOLVED') else x[:10]+'…' for x in counts.index]
    fig.add_trace(go.Bar(x=counts.values,y=labels,orientation='h',marker_color=BLUE,name='Observed delivered blocks',text=list(counts.index),hovertemplate='%{text}<br>%{x} delivered blocks<extra></extra>'),row=2,col=1)
    flat[2].barh(labels,list(counts.values),color=BLUE);flat[2].invert_yaxis();flat[2].set_xlabel('Unique delivered blocks; brand/owner not inferred')
    times=pd.to_datetime(deliveries.timestamp_utc,utc=True)
    values=deliveries.value_ETH.astype(float)
    fig.add_trace(go.Scatter(x=deliveries.timestamp_utc,y=values,mode='markers',marker=dict(color=GREY,size=3),name='Relay-declared value'),row=2,col=2)
    fig.add_trace(go.Scatter(x=[o['timestamp_utc'] for o in outcomes],y=[float(Decimal(o['onchain_proposer_payment_wei'])/E) for o in outcomes],mode='markers',marker=dict(color=RED,size=10,symbol='diamond'),name='On-chain reconciled selected cases',text=[o['case_id'] for o in outcomes]),row=2,col=2)
    flat[3].scatter(times,values,s=6,color=GREY);flat[3].scatter(pd.to_datetime([o['timestamp_utc'] for o in outcomes],utc=True),[float(Decimal(o['onchain_proposer_payment_wei'])/E) for o in outcomes],color=RED,s=40)
    flat[3].set_ylabel('Value (ETH)');flat[3].tick_params(axis='x',rotation=25,labelsize=8)
    for o in outcomes:
        x=float(o['selected_searcher_gross_after_pool_fees_ETH']);y=float(Decimal(o['onchain_proposer_payment_wei'])/E)
        fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers+text',text=[o['case_id']],textposition='top center',marker=dict(size=11,color=TEAL),name=o['case_id'],showlegend=False),row=3,col=1)
        flat[4].scatter([x],[y],color=TEAL,s=50);flat[4].annotate(o['case_id'],(x,y),xytext=(5,5),textcoords='offset points')
    flat[4].set_xlabel('Selected realized gross surplus after pool fees (ETH)');flat[4].set_ylabel('Whole-block proposer payment (ETH)')
    periods=['pre-event baseline','event window'];groups=[]
    for period,color in zip(periods,[BLUE,RED]):
        group=deliveries[deliveries.period.eq(period)].value_ETH.astype(float)
        groups.append(group.values)
        fig.add_trace(go.Box(y=group,name=f'{period} (n={len(group)})',marker_color=color,boxpoints=False),row=3,col=2)
    flat[5].boxplot(groups,tick_labels=[f'Baseline\nn={len(groups[0])}',f'Event\nn={len(groups[1])}'],showfliers=False)
    flat[5].set_yscale('log');flat[5].set_ylabel('Declared delivered value (ETH, log)')
    for row,col,title in [(1,1,'Submitted value (ETH)'),(1,2,'Value (ETH)'),(2,2,'Declared / paid ETH'),(3,1,'Whole-block proposer paid ETH')]:
        fig.update_yaxes(title_text=title,row=row,col=col)
    fig.update_xaxes(title_text='Selected slot',row=1,col=1)
    fig.update_xaxes(title_text='Selected realized gross surplus (ETH); NOT maximum opportunity size',row=3,col=1)
    fig.update_yaxes(type='log',title_text='ETH (log)',row=3,col=2)
    fig.update_layout(title='05 | Auction results and observable competition<br><sup>Relay views are partial; non-delivered submissions include revisions and may arrive after selection</sup>',height=1400,legend=dict(orientation='h',y=1.08),showlegend=False,barmode='group')
    caption=f"Observed deliveries: {deliveries.timestamp_utc.min()} – {deliveries.timestamp_utc.max()} (UTC).\nEthereum blocks 26,300,640–26,303,950 · {len(deliveries)} de-duplicated delivered blocks / 3,311 sampled blocks. Baseline: 130 blocks; event: 3,181.\n{len(submissions)} retained submission observations in three slots; endpoints may cap results. Same payload's relay-specific signing keys are unresolved, not extra wins. Received values are not a complete time-eligible auction book; baseline is descriptive, not causal."
    export_interactive(fig,NAME,caption.replace('\n','<br>'))
    for ax,title in zip(flat,titles):
        ax.set_title(title,loc='left',fontsize=11,fontweight='bold',pad=15);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    static.suptitle('05 | MEV auction outcomes and observable competition',x=.06,ha='left',fontsize=23,fontweight='bold')
    static.subplots_adjust(top=.9,bottom=.16,left=.08,right=.95,hspace=.55,wspace=.55)
    export_static(static,NAME,caption)
    pd.DataFrame(comparisons).to_parquet(ROOT/'reports/tables/fig05_bid_comparison.parquet',index=False)
    pd.DataFrame({'builder_key_or_unresolved':list(all_counts.index),'delivered_blocks':list(all_counts.values)}).to_parquet(ROOT/'reports/tables/fig05_builder_frequency.parquet',index=False)
    print('Figure 5: six auction views with partial coverage and revision caveats')


if __name__=='__main__':
    build()
