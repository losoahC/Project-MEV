"""Supplemental Bitquery comparison and evidence graph; does not overwrite the core sample."""
import json,html,hashlib,datetime
from pathlib import Path
from decimal import Decimal,getcontext
from collections import Counter
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/bitquery_check'
D=Decimal
getcontext().prec=90

def build():
    OUT.mkdir(exist_ok=True)
    registry=json.loads((ROOT/'data/processed/wallet_registry.json').read_text());reg={x['address']:x['number'] for x in registry}
    edges=pd.read_parquet(OUT/'usdt_backbone_edges.parquet')
    checks=json.loads((OUT/'fresh_edge_receipts.json').read_text());assert len(checks)==len(edges)==15 and all(x['match_exact_receipt_event'] for x in checks)
    valuations=json.loads((ROOT/'data/processed/wallet_swap_valuations.json').read_text());counts=Counter(x['tx_hash'] for x in valuations)
    clean=[x for x in valuations if counts[x['tx_hash']]==1 and x.get('valuation_complete') and not x['position_or_debt_events'] and not x['internal_wallet_transfer']]
    overlap=[x for x in clean if x['wallet'] in [4,5]]
    assert len(overlap)==4
    overlap_sum=sum((D(x['loss_USD']) for x in overlap),D(0))
    parity_delta=sum((-D(a['quantity'])-(-D(a['USD'])) for x in overlap for a in x['assets'] if a['symbol']=='USDT'),D(0))
    # Stablecoin parity change only: keep our ETH prices and timestamps unchanged.
    detail={'source_url':'https://bitquery.io/investigations/binance-hack-who-profited','local_four_trade_shortfall_USD':str(overlap_sum),'stablecoin_parity_only_delta_USD':str(parity_delta),'stablecoin_parity_only_shortfall_USD':str(overlap_sum+parity_delta),'not_exact_replication':'No same-minute Hyperliquid series or complete order-fill/universe reproduction; parity-only sensitivity retains our prior-minute ETH prices.','trades':overlap,'graph_event_count':len(edges),'fresh_drpc_exact_matches':len(checks),'independent_provider_caveat':'PublicNode returned null receipts for three probes; this is a source disagreement, not proof of nonexistence. dRPC exact receipt events match all 15 plotted-source events.'}
    (OUT/'comparison.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2))
    source='0x28c6c06298d514db089934071355e5743bf21d60';second='0xdfd5293d8e347dfe59e90efd55b2956a1343963d';branch='0x9749292d74fd460982d0912ea9515ea24736c762';branch2='0x23878914efe38d27c4d67ab83ed1b93a74d4086a'
    addr=lambda n:next(a for a,v in reg.items() if v==n)
    pos={source:(0,2.3),second:(0,.65),addr(2):(1.5,1.5),addr(10):(3,1.5),addr(3):(4.5,1.5),addr(4):(6,1.5),addr(5):(7.5,1.5),branch:(3,3),branch2:(6,3)}
    early=edges[edges.timestamp_utc.str.startswith('2026-10-29')].copy()
    fig,ax=plt.subplots(figsize=(18,8),facecolor='white');ax.set_xlim(-.7,8.4);ax.set_ylim(-.5,3.65);ax.axis('off')
    ax.set_title('USDT transfer backbone | 29 October 2026',loc='left',fontsize=24,fontweight='bold',pad=16)
    ax.text(0,1.01,'9 observed events / 8 address pairs; individual transfers >= 50M USDT; UTC; amounts are tokens, not USD',transform=ax.transAxes,fontsize=12,color='#526377')
    groups=list(early.groupby(['sender','recipient'],sort=False))
    for (a,b),rows in groups:
        value=sum((D(x) for x in rows.amount),D(0));x,y=pos[a];xx,yy=pos[b]
        rad=.08 if a in [source,second] else 0
        patch=FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',mutation_scale=18,linewidth=1.5+3*float(value/D('1815807270.797435')),color='#62869e',connectionstyle=f'arc3,rad={rad}',shrinkA=20,shrinkB=20);ax.add_patch(patch)
        times=[str(t)[11:19] for t in rows.timestamp_utc];t=times[0] if len(times)==1 else times[0]+' / '+times[-1]
        caption=f'{value/D(10**6):,.3f}M USDT\n{t}'+(f' · {len(rows)} events' if len(rows)>1 else '')
        mx=(x+xx)/2;my=(y+yy)/2+.17
        if b==branch:my+=.15
        ax.text(mx,my,caption,ha='center',va='bottom',fontsize=10,color='#243b53',bbox=dict(facecolor='white',edgecolor='none',alpha=.95,pad=2))
    for a,(x,y) in pos.items():
        color='#4b82dc' if a==source else '#e37a69' if a in reg else '#9aa9bc'
        ax.scatter(x,y,s=650 if a==addr(2) else 430,c=color,zorder=3,edgecolor='white',linewidth=2)
        name='Binance 14 (reported)' if a==source else f'Wallet {reg[a]} (local ID)' if a in reg else 'Unclassified address'
        ax.text(x,y-.25,name+'\n'+a[:8]+'…'+a[-4:],ha='center',va='top',fontsize=11,color='#102a43')
    ax.text(.01,.02,'Selection omits swaps, small transfers and balances: intermediate inflows and outflows need not balance.\nRepeated transfers are not additive theft or profit. No common-control inference. Later 30 October events remain in the companion evidence table.',transform=ax.transAxes,fontsize=11,color='#526377')
    fig.subplots_adjust(left=.035,right=.99,top=.85,bottom=.08)
    for ext in ['png','svg']:fig.savefig(OUT/f'usdt_backbone.{ext}',dpi=160)
    plt.close(fig)
    rows=[]
    for r in edges.to_dict('records'):
        rows.append('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['timestamp_utc','sender','recipient','amount','event_location'])+'<td><a href="'+html.escape(r['tx_url'])+'">'+r['tx_hash']+'</a></td><td>'+html.escape(r['evidence_path'])+'</td></tr>')
    (OUT/'usdt_backbone.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>USDT 主干与交易证据</title><style>body{font:15px system-ui;margin:24px;color:#19354b}img{max-width:100%}table{border-collapse:collapse;font-size:12px}td,th{padding:10px;border:1px solid #ddd;word-break:break-all}a{color:#087d86}</style><h1>USDT 主干与交易证据</h1><p>上图：10 月 29 日 9 条大额转账。下表：包含 10 月 30 日的全部 15 条筛选记录；逐条匹配新取得的 dRPC 回执。阈值为单笔 ≥ 5,000 万 USDT，非完整资金守恒图。钱包编号仅为项目内部编号；收款不证明共同控制。</p><img src="usdt_backbone.svg" alt="USDT 主干图"><h2>逐笔证据</h2><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in ['UTC','From','To','USDT','Event','Transaction','Local receipt source'])+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></html>')
    print(json.dumps({k:v for k,v in detail.items() if k!='trades'},ensure_ascii=False,indent=2))
if __name__=='__main__':build()
