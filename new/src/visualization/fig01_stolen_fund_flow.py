"""Render the verified event-window transfer network; never sum it as loss."""
from collections import defaultdict
import base64
import gzip
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[2]
COLORS = {"exchange": "#4b82dc", "corroborated": "#ed6972", "lead": "#e9af52", "pool": "#4bc6b0", "unknown": "#9aa9bc", "thorchain": "#a788db"}


def build():
    data = pd.read_parquet(ROOT / "data/processed/wallet_edges.parquet")
    from src.graph.crosschain_edges import extend
    primary=data.copy()
    data,crosschain_entities=extend(data)
    wallets = json.loads((ROOT / "data/processed/wallet_registry.json").read_text())
    roles = json.loads((ROOT / "data/processed/entities.json").read_text())
    registry = {w["address"]: w for w in wallets}

    def kind(a):
        if a in crosschain_entities:
            return "thorchain"
        if a in registry:
            return "corroborated" if registry[a]["identity_confidence"] == "independently_corroborated" else "lead"
        if roles.get(a) == "exchange_hot_wallet_reported":
            return "exchange"
        if roles.get(a) == "swap_event_emitter":
            return "pool"
        return "unknown"

    def label(a):
        if a in registry:
            return f"Exploiter {registry[a]['number']} (" + ("corroborated" if kind(a) == "corroborated" else "lead") + ")"
        if kind(a) == "exchange":
            return "Binance 14 (reported)"
        if kind(a)=="thorchain":
            return "THORChain service " + a[:8] + "…" + a[-4:]
        return ("Swap emitter " if kind(a) == "pool" else "Unknown ") + a[:8] + "…" + a[-4:]

    nodes = {a: {"kind": kind(a), "label": label(a)} for a in set(data.sender) | set(data.recipient)}
    rows = data.astype(object).where(pd.notnull(data), None).to_dict("records")
    for r in rows:
        for key, val in list(r.items()):
            if hasattr(val, "item"):
                r[key] = val.item()
    out = ROOT / "reports/figures"
    out.mkdir(parents=True, exist_ok=True)
    # Self-contained Plotly bundle; no CDN or web server required.
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Figure 1 | Verified transfer network</title>
<style>body{margin:0;background:#0d1625;color:#e5edf8;font:15px system-ui}main{max-width:1500px;margin:auto;padding:24px}h1{font-size:27px;margin-bottom:8px}.muted{color:#aabbd0}#controls{display:flex;flex-wrap:wrap;gap:16px;padding:18px 0}label{display:grid;gap:5px}input,select,button{background:#18263a;color:#fff;border:1px solid #41536d;border-radius:5px;padding:7px}#plot{height:770px}#detail{overflow:auto;padding:15px;background:#152237}a{color:#66d5ca}table{border-collapse:collapse;width:100%;font-size:12px}td,th{text-align:left;padding:8px;border-bottom:1px solid #35465d;word-break:break-all}</style>
<main><div class="muted">GROUP 12 · FORENSIC RESEARCH · VERIFIED TRANSACTION EDGES</div><h1>Verified event-window transfer network</h1>
<p class="muted">October Ethereum sample plus separately dated November THORChain companions, UTC. Each edge is an observed receipt/call or confirmed Bitcoin recipient output.<br>USD marks and source paths are explicit per edge. BTC uses its matched ETH deposit-time reference, not BTC inclusion-time pricing. Routing throughput is not stolen value or MEV loss.<br>Receiving funds does not establish common ownership. Ethereum deposits and Bitcoin outputs are paired by case ID, not joined by an invented on-chain transfer.</p>
<div id="controls"><label>Chain<select id="chain"><option value="ethereum">ethereum</option><option value="bitcoin">bitcoin</option><option value="">All observed chains</option></select></label><label>Token<select id="token"><option value="">All contracts</option></select></label><label>From UTC<input id="start" type="datetime-local"></label><label>To UTC<input id="end" type="datetime-local"></label><label>Minimum USD<input id="minimum" type="number" value="1000000" min="0"></label><label>Show unvalued edges<input id="unvalued" type="checkbox"></label><button id="apply">Apply filters</button></div>
<p id="count" class="muted"></p><div id="plot"></div><div id="detail">Click an edge to inspect its transaction and exact event location.</div></main><script>__PLOTLY__</script><script>
(async()=>{const bytes=Uint8Array.from(atob('__PAYLOAD__'),c=>c.charCodeAt(0));const payload=JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());const edges=payload.edges,nodes=payload.nodes,colors=__COLORS__;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const tokens=[...new Set(edges.map(e=>e.token))];tokens.forEach(t=>{const o=document.createElement('option');o.value=t;o.textContent=edges.find(e=>e.token===t).symbol+' | '+t;document.querySelector('#token').appendChild(o)});
const from=Math.min(...edges.map(e=>e.timestamp)),to=Math.max(...edges.map(e=>e.timestamp));
document.querySelector('#start').value=new Date(from*1000).toISOString().slice(0,16);
document.querySelector('#end').value=new Date(to*1000+60000).toISOString().slice(0,16);
function render(){const chain=document.querySelector('#chain').value,token=document.querySelector('#token').value,min=Number(document.querySelector('#minimum').value),lo=Date.parse(document.querySelector('#start').value+'Z')/1000,hi=Date.parse(document.querySelector('#end').value+'Z')/1000;
const matching=edges.filter(e=>(!chain||e.chain===chain)&&(!token||e.token===token)&&e.timestamp>=lo&&e.timestamp<=hi&&(e.usd_value===null?document.querySelector('#unvalued').checked:Number(e.usd_value)>=min));
matching.sort((a,b)=>Number(b.usd_value||0)-Number(a.usd_value||0));const selected=matching.slice(0,120);
document.querySelector('#count').textContent=`${matching.length.toLocaleString()} matching of ${edges.length.toLocaleString()} evidence edges; showing ${selected.length} largest transfers to keep labels readable. Unvalued USD is missing, never zero. Node area = displayed USD throughput; edge width = displayed transfer USD (unvalued: fixed width).`;
const ids=[...new Set(selected.flatMap(e=>[e.sender,e.recipient]))],pos={},totals={};
const groups={exchange:[],corroborated:[],lead:[],pool:[],thorchain:[],unknown:[]};ids.forEach(a=>groups[nodes[a].kind].push(a));
const xmap={exchange:0,corroborated:1,lead:1,pool:2,thorchain:2.6,unknown:3.4};Object.entries(groups).forEach(([g,aa])=>aa.forEach((a,i)=>pos[a]=[xmap[g]+(g==='lead'?.12:0),i-(aa.length-1)/2]));
selected.forEach(e=>{for(const a of [e.sender,e.recipient])totals[a]=(totals[a]||0)+Number(e.usd_value||0)});
const max=Math.max(1,...selected.map(e=>Number(e.usd_value||0))),traces=[],arrows=[];
selected.forEach(e=>{const a=pos[e.sender],b=pos[e.recipient],c=colors[nodes[e.sender].kind];traces.push({type:'scatter',mode:'lines',x:[a[0],b[0]],y:[a[1],b[1]],line:{width:e.usd_value===null?1:1+6*Math.sqrt(Number(e.usd_value)/max),color:c,dash:e.usd_value===null?'dot':'solid'},opacity:.55,customdata:[e.edge_id,e.edge_id],text:[`${esc(e.symbol)} ${esc(e.amount)}<br>USD ${esc(e.usd_value??'unvalued')}<br>${e.timestamp_utc}<br>${e.tx_hash}<br>${e.event_location}<br>${esc(e.crosschain_case??'October core sample')}<br>${esc(e.valuation_status)}`],hoverinfo:'text',showlegend:false});arrows.push({x:a[0]*.2+b[0]*.8,y:a[1]*.2+b[1]*.8,ax:a[0]*.4+b[0]*.6,ay:a[1]*.4+b[1]*.6,xref:'x',yref:'y',axref:'x',ayref:'y',showarrow:true,arrowhead:3,arrowsize:1,arrowwidth:1,arrowcolor:c,text:''})});
Object.entries(groups).forEach(([g,aa])=>{if(aa.length)traces.push({type:'scatter',mode:'markers+text',name:g,x:aa.map(a=>pos[a][0]),y:aa.map(a=>pos[a][1]),text:aa.map(a=>nodes[a].label),textposition:'top center',textfont:{size:10},hovertext:aa.map(a=>`${a}<br>${nodes[a].label}<br>Displayed throughput USD ${totals[a].toLocaleString()}`),hoverinfo:'text',marker:{color:colors[g],size:aa.map(a=>9+34*Math.sqrt(totals[a]/Math.max(1,...Object.values(totals)))),line:{color:'#0d1625',width:1}},showlegend:true})});
Plotly.react('plot',traces,{paper_bgcolor:'#0d1625',plot_bgcolor:'#0d1625',font:{color:'#dce9f6'},xaxis:{visible:false},yaxis:{visible:false},annotations:arrows,legend:{orientation:'h'},margin:{l:80,r:80,t:35,b:25},hovermode:'closest'},{responsive:true,displaylogo:false});
document.querySelector('#plot').removeAllListeners?.('plotly_click');document.querySelector('#plot').on('plotly_click',ev=>{const id=ev.points[0].customdata,e=edges.find(e=>e.edge_id===id);if(!e)return;document.querySelector('#detail').innerHTML='<b>Transfer evidence</b><table>'+['chain','crosschain_case','valuation_status','price_bar_start','price_source','sender','recipient','symbol','token','amount_raw','decimals','amount','usd_value','timestamp_utc','block_number','transaction_index','event_location','evidence_path'].map(k=>`<tr><th>${k}</th><td>${esc(e[k])}</td></tr>`).join('')+`<tr><th>Transaction</th><td><a target="_blank" rel="noopener" href="${e.tx_url}">${e.tx_hash}</a></td></tr></table>`})}
document.querySelector('#apply').onclick=render;render();})().catch(e=>document.querySelector('#count').textContent='Unable to render: '+e.message);</script></html>'''
    payload = base64.b64encode(gzip.compress(json.dumps({"edges": rows, "nodes": nodes}, allow_nan=False, separators=(",", ":")).encode(), mtime=0)).decode()
    page = page.replace("__PLOTLY__", get_plotlyjs()).replace("__PAYLOAD__", payload).replace("__COLORS__", json.dumps(COLORS))
    (out / "fig01_stolen_fund_flow.html").write_text(page)

    # Presentation static view is explicitly a smaller, readable selection.
    valued = primary[primary.usd_value.notna()].copy()
    valued["value"] = valued.usd_value.astype(float)
    pool_rows = valued[valued.sender.map(kind).eq("pool") | valued.recipient.map(kind).eq("pool")]
    top = pd.concat([valued.sort_values("value", ascending=False).head(18), pool_rows.sort_values("value", ascending=False).head(4)]).drop_duplicates("edge_id")
    graph = nx.DiGraph()
    weights = defaultdict(float)
    throughput = defaultdict(float)
    for r in top.to_dict("records"):
        weights[(r["sender"], r["recipient"])] += r["value"]
        throughput[r["sender"]] += r["value"]
        throughput[r["recipient"]] += r["value"]
    graph.add_edges_from(weights)
    stages = defaultdict(list)
    stage_for = {"exchange": 0, "corroborated": 1, "lead": 1, "pool": 2, "thorchain": 2.6, "unknown": 3.4}
    for a in graph:
        stages[stage_for[kind(a)]].append(a)
    pos = {}
    for stage, members in stages.items():
        members.sort(key=lambda a: (registry[a]["number"] if a in registry else 99, a))
        for i, a in enumerate(members):
            pos[a] = (stage, 1-i/max(1,len(members)-1) if len(members)>1 else .5)
    fig, ax = plt.subplots(figsize=(16, 10), facecolor="white")
    sizes = [220 + 1800 * throughput[a] / max(throughput.values()) for a in graph]
    nx.draw_networkx_nodes(graph, pos, node_size=sizes, node_color=[COLORS[kind(a)] for a in graph], ax=ax, edgecolors="white")
    nx.draw_networkx_edges(graph, pos, width=[1 + 6 * weights[e] / max(weights.values()) for e in graph.edges],
                           edge_color="#8798ad", alpha=.65, arrows=True, arrowsize=18, connectionstyle="arc3,rad=0.08", ax=ax, node_size=sizes)
    short_labels = {a: (f"Exploiter {registry[a]['number']}" if a in registry else ("Binance 14" if kind(a) == "exchange" else a[:8] + "…" + a[-4:])) for a in graph}
    nx.draw_networkx_labels(graph, {a: (p[0], p[1] + .033) for a, p in pos.items()}, labels=short_labels, font_size=9, ax=ax)
    ax.set_title("01  |  Verified event-window transfer network", loc="left", fontsize=23, pad=28, fontweight="bold")
    ax.text(0, 1.025, f"{len(top)} selected transfer events (largest + pool routes) · Ethereum · 2026-10-29/30 UTC · Size/width: displayed USD throughput", transform=ax.transAxes, fontsize=11, color="#526377")
    ax.margins(x=.12, y=.15)
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=9, label=l) for l,c in [("Reported exchange",COLORS['exchange']),("Corroborated wallet",COLORS['corroborated']),("Wallet lead",COLORS['lead']),("Swap emitter",COLORS['pool']),("Unidentified",COLORS['unknown'])]]
    ax.legend(handles=handles, loc="lower left", frameon=False, ncol=3, fontsize=10)
    ax.axis("off")
    fig.text(.06, .035, "Source: archived receipt logs / successful native calls; strict prior-minute Coinbase price.\nRouting transfers are not additive losses. Ownership remains unverified. Interactive companion also includes separately dated THORChain deposits and confirmed BTC outputs.", fontsize=10, color="#526377")
    fig.subplots_adjust(top=.86, bottom=.13, left=.06, right=.96)
    for suffix in ("png", "svg"):
        fig.savefig(out / ("fig01_stolen_fund_flow." + suffix), dpi=180)
    plt.close(fig)
    top.to_parquet(ROOT / "reports/tables/fig01_static_edges.parquet", index=False)
    print(f"Figure 1: {len(data)} evidence edges; static selection {len(top)}")


if __name__ == "__main__":
    build()
