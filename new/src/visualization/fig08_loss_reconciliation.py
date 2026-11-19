"""Evidence-limited reconciliation: snapshots and profits have separate units and boundaries."""
import json
from decimal import Decimal
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.visualization.common import ROOT,export_static,export_interactive,BLUE,RED,TEAL,GREY
NAME='fig08_loss_reconciliation'

def waterfall(ax,labels,values,measures,scale=1):
    level=0
    for i,(label,value,measure) in enumerate(zip(labels,values,measures)):
        v=value/scale
        if measure=='total':base=0;level=v;height=v;color=BLUE
        else:base=min(level,level+v);height=abs(v);level+=v;color=TEAL if v>=0 else RED
        ax.bar(i,height,bottom=base,color=color,width=.62)
        ax.annotate(f'{v:,.3f}',(i,base+height),xytext=(0,6),textcoords='offset points',ha='center',fontsize=9)
    ax.set_xticks(range(len(labels)),labels,fontsize=9);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)

def build():
    d=json.loads((ROOT/'data/processed/loss_reconciliation.json').read_text());a=d['asset_ledger_USD'];arb=d['selected_3_arbitrage_ETH']
    inventory=json.loads((ROOT/'data/processed/asset_inventory.json').read_text())
    assert inventory['balanced_rows']==inventory['wallet_asset_rows']
    labels=['Opening','External\ninflows','External\noutflows','Gas','WETH\nconversion','Closing']
    values=[float(a['opening']),float(a['external_inflow']),-float(a['external_outflow']),-float(a['gas']),float(a['wrapper_net']),float(a['closing'])];measures=['absolute']+['relative']*4+['total']
    plabels=['Gross after\npool fees','Gas','Direct builder\ntransfers','Searcher\nretained']
    pvalues=[float(arb['gross_after_pool_fees_before_gas_and_builder_ETH']),-float(arb['gas_ETH']),-float(arb['direct_builder_ETH']),float(arb['net_after_gas_and_builder_ETH'])];pmeasures=['absolute','relative','relative','total']
    holdlabels=['Blacklisted token balance','Other balance at address leads'];holdvalues=[float(a['frozen_closing']),float(a['nonblacklisted_closing'])]
    fig=make_subplots(rows=2,cols=2,specs=[[{'type':'waterfall'},{'type':'bar'}],[{'type':'waterfall'},{'type':'table'}]],subplot_titles=['A | Four-asset snapshot ledger (USD billions)','B | Closing holdings: frozen is a subset','C | Three selected arbitrage cases (ETH)','D | Sample shortfall and unresolved whole-incident quantities'],vertical_spacing=.20,horizontal_spacing=.13)
    fig.add_trace(go.Waterfall(x=[x.replace('\n','<br>') for x in labels],y=[v/1e9 for v in values],measure=measures,totals=dict(marker=dict(color=BLUE)),increasing=dict(marker=dict(color=TEAL)),decreasing=dict(marker=dict(color=RED)),text=[f'{v/1e9:,.4f}' for v in values],textposition='outside'),row=1,col=1)
    fig.add_trace(go.Bar(x=[v/1e9 for v in holdvalues],y=holdlabels,orientation='h',marker_color=[RED,TEAL],text=[f'USD {v/1e9:.4f}B' for v in holdvalues],textposition='auto'),row=1,col=2)
    fig.add_trace(go.Waterfall(x=[x.replace('\n','<br>') for x in plabels],y=pvalues,measure=pmeasures,totals=dict(marker=dict(color=BLUE)),decreasing=dict(marker=dict(color=RED)),text=[f'{v:.6f}' for v in pvalues],textposition='outside'),row=2,col=1)
    economic=d['economic_trade_time_sample']
    unknown=['Complete trade-time sample (unique swaps)','Signed reference shortfall (sample)','Whole-incident stolen inventory','Whole-incident recovered / seized','Whole-incident unrecovered value','Causal MEV share of execution loss','All-chain / all-token final balances']
    fig.add_trace(go.Table(header=dict(values=['Requested quantity','Status'],fill_color='#25354b',font=dict(color='white',size=13)),cells=dict(values=[unknown,[str(economic['rows']),f"USD {float(economic['signed_net_shortfall_USD'])/1e6:.3f}M"]+['Unresolved']*(len(unknown)-2)],fill_color='#152238',font=dict(color='white',size=12),height=38,align='left')),row=2,col=2)
    fig.update_layout(title='08 | Snapshot accounting and economic attribution',height=1100,showlegend=False)
    fig.update_yaxes(title_text='USD billions',row=1,col=1);fig.update_xaxes(title_text='USD billions',row=1,col=2);fig.update_yaxes(title_text='ETH',row=2,col=1)
    caption=f"Ethereum blocks 26,300,640–26,303,950. Fixed reference: {d['valuation_timestamp_utc']}, prior completed minute.<br>A/B cover ETH, WETH, USDT, USDC across 16 address leads. Inflows include conversions and are not theft totals. Blacklisting is not recovery.<br>C: selected observed profits in ETH, not causal victim loss. D: trade-time sample estimates, not additive to fixed balances or C. November THOR costs remain separate."
    export_interactive(fig,NAME,caption)
    static,axes=plt.subplots(2,2,figsize=(17,11));static.subplots_adjust(top=.85,bottom=.19,left=.07,right=.96,wspace=.35,hspace=.55)
    waterfall(axes[0,0],labels,values,measures,1e9);axes[0,0].set_ylabel('USD billions');axes[0,0].set_title('A | Four-asset snapshot ledger',loc='left',fontweight='bold')
    ax=axes[0,1];ax.barh([1,0],[v/1e9 for v in holdvalues],color=[RED,TEAL]);ax.set_yticks([1,0],['Blacklisted token\nbalances','Other balances at\naddress leads']);ax.set_xlim(0,max(holdvalues)/1e9*1.25)
    for i,v in zip([1,0],holdvalues):ax.text(v/1e9+.03,i,f'USD {v/1e9:.4f}B',va='center',fontsize=10)
    ax.set_xlabel('USD billions at fixed closing mark');ax.set_title('B | Closing holdings',loc='left',fontweight='bold');ax.spines[['top','right']].set_visible(False)
    waterfall(axes[1,0],plabels,pvalues,pmeasures);axes[1,0].set_ylabel('ETH');axes[1,0].set_title('C | Three selected arbitrage cases',loc='left',fontweight='bold')
    ax=axes[1,1];ax.axis('off');ax.set_title('D | Sample shortfall and remaining gaps',loc='left',fontweight='bold')
    ax.text(0,.88,f"{economic['rows']} unique completely valued exchanges\nUSD {float(economic['signed_net_shortfall_USD'])/1e6:.3f}M signed reference shortfall\nTrade-time marks; bounded sample, not total MEV",transform=ax.transAxes,fontsize=11,linespacing=1.4,va='top')
    ax.text(0,.55,f"Whole-incident stolen / recovered / unrecovered\nCausal MEV share: unresolved, never zero-filled\n{inventory['asset_count']}-asset raw inventory: {inventory['balanced_rows']:,} balances reconcile",transform=ax.transAxes,fontsize=10.5,linespacing=1.6,va='top')
    ax.text(0,.22,'Teacher PDF: ~USD 2B frozen stablecoins.\nOur limited contract snapshot supports that scale,\nnot a USD 2B unrecoverable trading loss.',transform=ax.transAxes,fontsize=10,color='#526377',linespacing=1.4,va='top')
    static.suptitle('08 | Separate balances from trading losses',x=.06,ha='left',fontsize=23,fontweight='bold')
    static.text(.06,.90,'All 64 wallet/asset snapshots reconcile exactly after WETH withdrawal accounting.',fontsize=12,color='#526377')
    export_static(static,NAME,caption.replace('<br>','\n'))
    print('Figure 8: fixed-mark snapshot accounting plus selected arbitrage attribution, with unresolved whole-incident totals explicit')

if __name__=='__main__':build()
