"""Observed trade-size ETH execution prices around the A1 event, never synthetic timestamps."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import json

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.arbitrage.reconstruct import Reconstruction, ROOT
from src.decoding.events import WETH,USDT,USDC,integer,swap
from src.ingestion.evidence import read_json
from src.reconciliation.valuation import previous_minute_price
from src.visualization.common import export_interactive,export_static,RED,TEAL,BLUE,GREY

NAME="fig02_eth_price_dislocation"


def build(online=False,legacy=None):
    engine=Reconstruction(legacy or ROOT.parent/"research",online)
    a1=read_json(ROOT/"reports/case_studies/A1_arbitrage.json")
    meta=a1["metadata"]
    wanted={p:m for p,m in meta.items() if WETH in (m["token0"],m["token1"]) and ({m["token0"],m["token1"]}&{USDT,USDC})}
    candles={t:read_json(engine.source(f"prices_raw/{t}.json")) for t in ("ETH","USDT","USDC") if engine.source(f"prices_raw/{t}.json")}
    wanted={p:m for p,m in wanted.items() if ("USDT" if USDT in (m["token0"],m["token1"]) else "USDC") in candles}
    targets=set(pd.read_parquet(ROOT/"data/processed/transactions.parquet").tx_hash)
    rows=[];reference=[]
    for number in range(a1["block"]-3,a1["block"]+5):
        header,receipts,_,paths=engine.block(number)
        timestamp=integer(header["timestamp"])
        ref,bar=previous_minute_price(candles["ETH"],timestamp)
        assert ref is not None
        reference.append({"block":number,"timestamp":timestamp,"timestamp_utc":datetime.fromtimestamp(timestamp,timezone.utc).isoformat(),"reference_ETH_USD":str(ref),"reference_bar_start":bar,"order_coordinate":number-a1["block"]})
        for receipt in sorted(receipts.values(),key=lambda r:integer(r["transactionIndex"])):
            for log in receipt["logs"]:
                pool=log["address"].lower()
                if pool not in wanted:
                    continue
                event=swap(log)
                if not event:
                    continue
                m=wanted[pool];eth_i=0 if m["token0"]==WETH else 1;stable_i=1-eth_i
                amounts=[Decimal(event[f"amount{i}_raw"])/Decimal(10)**m[f"decimals{i}"] for i in (0,1)]
                stable=m[f"token{stable_i}"];symbol="USDT" if stable==USDT else "USDC"
                stable_price,_=previous_minute_price(candles[symbol],timestamp)
                if stable_price is None or amounts[eth_i]==0:
                    continue
                price=abs(amounts[stable_i]/amounts[eth_i])*stable_price
                h=receipt["transactionHash"].lower();idx=integer(receipt["transactionIndex"])
                label="Selected arbitrage" if h==a1["tx_hash"] else "Wallet-sample swap" if h in targets else "Other observed swap"
                rows.append({"block":number,"timestamp":timestamp,"timestamp_utc":datetime.fromtimestamp(timestamp,timezone.utc).isoformat(),"transaction_index":idx,"log_index":event["log_index"],"tx_hash":h,"pool":pool,"classification":label,"execution_side":"sell_ETH" if amounts[eth_i]>0 else "buy_ETH",
                    "ETH_quantity":str(abs(amounts[eth_i])),"execution_USD_per_ETH":str(price),"reference_ETH_USD":str(ref),"dislocation_pct":str((price/ref-1)*100),
                    "reference_bar_start":bar,"evidence_path":paths["receipts"],"order_coordinate":number-a1["block"]+idx/len(header["transactions"]),
                    "price_definition":"Realized average execution at actual observed trade quantity, inclusive of pool fees; not a fixed-size quote or pool midpoint."})
    engine.store.save()
    data=pd.DataFrame(rows)
    data.to_parquet(ROOT/"reports/tables/fig02_price_observations.parquet",index=False)
    pd.DataFrame(reference).to_parquet(ROOT/"reports/tables/fig02_reference_prices.parquet",index=False)
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,row_heights=[.66,.34],subplot_titles=("Observed ETH execution vs. prior-minute external market","Execution deviation from external market"))
    specs=[]
    fig.add_trace(go.Scatter(x=[r["timestamp_utc"] for r in reference],y=[float(r["reference_ETH_USD"]) for r in reference],name="Coinbase ETH/USD prior-minute close",mode="lines",line=dict(color=BLUE,width=2)),row=1,col=1)
    specs.append([r["order_coordinate"] for r in reference])
    colors={"Other observed swap":GREY,"Wallet-sample swap":RED,"Selected arbitrage":TEAL}
    for cls,color in colors.items():
        group=data[data.classification.eq(cls)]
        hover=[f"Block {r['block']} · tx index {r['transaction_index']} · log {r['log_index']}<br>{r['timestamp_utc']}<br>{r['tx_hash']}<br>{r['pool']}<br>{r['execution_side']}: {float(r['ETH_quantity']):,.5f} ETH" for r in group.to_dict("records")]
        for panel,key in ((1,"execution_USD_per_ETH"),(2,"dislocation_pct")):
            fig.add_trace(go.Scatter(x=group.timestamp_utc,y=group[key].astype(float),mode="markers",name=cls,legendgroup=cls,showlegend=panel==1,marker=dict(color=color,size=9 if cls!="Other observed swap" else 5,symbol="diamond" if cls=="Selected arbitrage" else "circle"),text=hover,hovertemplate="%{text}<br>Value: %{y:.5f}<extra></extra>"),row=panel,col=1)
            specs.append(group.order_coordinate.tolist())
    fig.add_hline(y=0,row=2,col=1,line_color=BLUE,line_dash="dot")
    original_x=[list(t.x) for t in fig.data]
    fig.update_layout(title="02 | ETH price dislocation around A1<br><sup>Actual block timestamps; select transaction-order view to separate same-block executions</sup>",height=850,legend=dict(orientation="h",y=1.07),updatemenus=[dict(type="buttons",direction="left",x=0,y=1.19,buttons=[dict(label="UTC time",method="update",args=[{"x":original_x},{"xaxis.type":"date","xaxis2.type":"date","xaxis2.title.text":"Block timestamp (UTC); same-block observations share time"}]),dict(label="Transaction order",method="update",args=[{"x":specs},{"xaxis.type":"linear","xaxis2.type":"linear","xaxis2.title.text":"Block − 26,300,992 + transaction index / block transaction count (order, NOT seconds)"}])])])
    fig.update_yaxes(title_text="USD per ETH",row=1,col=1);fig.update_yaxes(title_text="Deviation (%)",row=2,col=1)
    caption=f"{reference[0]['timestamp_utc']} – {reference[-1]['timestamp_utc']} · Ethereum · {len(data)} actual swap events.\nTrade sizes/pool fees differ. No synthetic intra-block timestamps or event-wide MEV claim. Sources: archived receipts, Coinbase candles."
    export_interactive(fig,NAME,caption.replace("\n","<br>"))
    static,axes=plt.subplots(2,1,figsize=(14,9),sharex=True,gridspec_kw={"height_ratios":[2,1]})
    axes[0].plot([r["order_coordinate"] for r in reference],[float(r["reference_ETH_USD"]) for r in reference],color=BLUE,label="External reference")
    for cls,color in colors.items():
        group=data[data.classification.eq(cls)]
        for ax,key in zip(axes,["execution_USD_per_ETH","dislocation_pct"]):
            ax.scatter(group.order_coordinate,group[key].astype(float),s=45 if cls!="Other observed swap" else 15,color=color,label=cls,alpha=.85)
    axes[1].axhline(0,color=BLUE,linestyle=":")
    axes[0].set_ylabel("USD per ETH");axes[1].set_ylabel("Deviation (%)")
    axes[1].set_xlabel("Block offset from 26,300,992 + transaction index / block transaction count (order, not seconds)")
    axes[0].legend(loc="upper right",fontsize=9)
    for ax in axes:
        ax.grid(alpha=.17);ax.spines[["top","right"]].set_visible(False)
    static.suptitle("02 | Observed ETH price dislocation",x=.07,ha="left",fontsize=23,fontweight="bold")
    static.subplots_adjust(top=.87,bottom=.18,left=.09,right=.97,hspace=.18)
    export_static(static,NAME,caption)
    print(f"Figure 2: {len(data)} executable-price observations over eight actual blocks")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--online",action="store_true");p.add_argument('--legacy');args=p.parse_args();build(args.online,args.legacy)
