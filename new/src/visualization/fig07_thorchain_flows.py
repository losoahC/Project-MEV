"""Three observed conversions; Sankey width uses a single deposit-time USD mark per path."""
import json
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey
import pandas as pd
import plotly.graph_objects as go
from src.visualization.common import ROOT,export_static,export_interactive,RED,TEAL,BLUE,GREY
NAME='fig07_thorchain_flows'

def build():
    rows=json.loads((ROOT/'data/processed/thorchain_paths.json').read_text())
    labels=[];colors=[];sources=[];targets=[];values=[];details=[]
    for r in rows:
        base=len(labels);cid=r['case_id'];inp=float(r['input_reference_USD']);out=float(r['output_reference_USD']);loss=float(r['estimated_execution_shortfall_USD'])
        assert loss>=0,'Favorable execution needs a distinct signed diagram'
        labels += [f"{cid} | Ethereum · {r['input_ETH']} ETH",f'{cid} | THORChain streaming swap',f"{cid} | Bitcoin · {r['output_BTC']} BTC",f'{cid} | estimated execution shortfall']
        colors += [BLUE,TEAL,TEAL,RED]
        for a,b,v,kind in [(base,base+1,inp,'input reference value'),(base+1,base+2,out,'output at same deposit-time mark'),(base+1,base+3,loss,'reference shortfall; not an extra fee')]:
            sources.append(a);targets.append(b);values.append(v)
            details.append(f"{cid} · {kind}<br>Deposit UTC: {r['deposit_utc']}<br>ETH tx: {r['ethereum_deposit']}<br>BTC tx: {r['bitcoin_txid']}<br>Receiver: {r['destination_address']}<br>ETH gas separately: {r['ethereum_gas_ETH']} ETH<br>Network fee already in output: {r['network_fee_BTC']} BTC<br>Liquidity fee reported: {r['reported_liquidity_fee_RUNE']} RUNE<br>BTC inclusion delay: {r['inclusion_delay_seconds']} sec<br>Flow association only; control/exclusive provenance unresolved")
    fig=go.Figure(go.Sankey(node=dict(label=labels,color=colors,pad=22,thickness=18),link=dict(source=sources,target=targets,value=values,customdata=details,hovertemplate='%{customdata}<br>USD reference width: %{value:,.2f}<extra></extra>')))
    fig.update_layout(title='07 | Verified ETH → THORChain → BTC conversions',height=1000)
    caption='17 Nov 2026, 13:39:47–14:56:35 UTC deposits. Width = USD at each deposit’s prior completed Coinbase minute.<br>Execution shortfall includes fees/timing effects; gas shown separately. Three cases are not a complete flow census. Funding links establish transfers, not ownership.'
    export_interactive(fig,NAME,caption)
    static,axes=plt.subplots(3,1,figsize=(16,12))
    for ax,r in zip(axes,rows):
        inp=float(r['input_reference_USD'])/1000;out=float(r['output_reference_USD'])/1000;loss=inp-out
        Sankey(ax=ax,scale=1/inp,offset=.16,head_angle=120,unit=None,format='%.2f').add(flows=[inp,-out,-loss],orientations=[0,0,-1],labels=[f"Ethereum\n{r['input_ETH']} ETH\n${inp:,.2f}k",f"Bitcoin\n{r['output_BTC']} BTC\n${out:,.2f}k",f"Reference shortfall\n${loss*1000:,.2f}"],pathlengths=[.25,.25,.15],facecolor='#d0e8e6',edgecolor=TEAL).finish()
        ax.text(.52,.88,'THORChain streaming swap',transform=ax.transAxes,ha='center',fontsize=10,color=TEAL)
        ax.set_title(f"{r['case_id']}  |  {r['deposit_utc']}  |  BTC inclusion after {r['inclusion_delay_seconds']/60:.1f} min",loc='left',fontsize=12,fontweight='bold');ax.axis('off')
        ax.text(.02,.04,f"Gas (separate): {r['ethereum_gas_ETH']} ETH  ·  LP fee (embedded): {r['reported_liquidity_fee_RUNE']} RUNE\nBTC receiver {r['destination_address']}\nDeposit {r['ethereum_deposit'][:18]}…  ·  BTC {r['bitcoin_txid'][:18]}…",transform=ax.transAxes,fontsize=9,color='#526377')
    static.suptitle('07 | Three observed cross-chain conversions',x=.06,ha='left',fontsize=23,fontweight='bold')
    static.subplots_adjust(top=.92,bottom=.15,hspace=.45)
    export_static(static,NAME,caption.replace('<br>','\n')+'\nRaw receipts, THORNode/Midgard and confirmed BTC outputs: thorchain_paths.json. USD marks differ by deposit time; do not treat as a single valuation-date balance.')
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows]).to_parquet(ROOT/'reports/tables/fig07_crosschain_paths.parquet',index=False)
    print('Figure 7: three matched cross-chain paths, with same-time reference valuation per conversion')

if __name__=='__main__':build()
