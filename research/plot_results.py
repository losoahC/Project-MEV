import json,gzip
from pathlib import Path
from datetime import datetime,timezone,timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
R=Path(__file__).resolve().parent;O=R/'figures';O.mkdir(exist_ok=True)
v=json.loads((R/'expanded_valuation.json').read_text());bc=json.loads((R/'window_block_costs.json').read_text())['rows'];bl=json.loads((R/'baseline_block_costs.json').read_text())['rows']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'#fafafa','axes.facecolor':'#fafafa'})
fig,ax=plt.subplots(2,2,figsize=(13,8),layout='constrained')
fig.suptitle('Binance incident: observed execution costs and network activity',fontsize=17,ha='left',x=.06)
sw=[r for r in v['rows'] if r['shortfall_usd'] is not None and float(r['net_assets'].get('USDT',0))<-1e5]
eth=json.loads((R/'prices_raw/ETH.json').read_text());usdt={r[0]:r[4] for r in json.loads((R/'prices_raw/USDT.json').read_text())};eth=sorted(r for r in eth if 1793305200<=r[0]<=1793308800)
ax[0,0].plot([datetime.fromtimestamp(r[0],timezone.utc) for r in eth],[r[4]/usdt[r[0]] for r in eth],color='#336a86',lw=2,label='Coinbase ETH/USDT reference')
ax[0,0].scatter([datetime.fromtimestamp(r['timestamp'],timezone.utc) for r in sw],[-float(r['net_assets']['USDT'])/float(r['net_assets']['ETH']) for r in sw],s=[max(25,-float(r['net_assets']['USDT'])/4e5) for r in sw],alpha=.75,color='#b25035',label='Attacker-linked execution')
ax[0,0].set(title='A. USDT-to-ETH execution prices',ylabel='USDT per ETH',xlabel='29 October 2026, UTC');ax[0,0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M',tz=timezone.utc));ax[0,0].legend(frameon=False,fontsize=8)
symbols=sorted([s for s,d in v['summary'].items() if d['shortfall_usd'] is not None],key=lambda s:float(v['summary'][s]['shortfall_usd']),reverse=True);values=[float(v['summary'][s]['shortfall_usd'])/1e6 for s in symbols]
ax[0,1].barh(symbols[::-1],values[::-1],color=['#b25035' if s=='USDT' else '#779891' for s in symbols[::-1]])
for i,(s,n) in enumerate(zip(symbols[::-1],values[::-1])):ax[0,1].text(n+.5,i,f'{n:.2f}' if n>=.01 else '<0.01',va='center',fontsize=9)
ax[0,1].set(title='B. Priced execution shortfall — not MEV',xlabel='USD million, available priced transactions');ax[0,1].set_xlim(0,max(values)*1.18)
times=[];base=[]
for r in bc:
 b=json.loads(gzip.decompress((R/'window_raw'/f"{r['block']}_block.json.gz").read_bytes()));times.append(datetime.fromtimestamp(r['timestamp'],timezone.utc));base.append(int(b['baseFeePerGas'],16)/1e9)
ax[1,0].plot(times,base,color='#b25035',lw=1.4,label='Incident day')
ax[1,0].plot([datetime.fromtimestamp(r['timestamp']+86400,timezone.utc) for r in bl],[int(r['base_fee_wei'])/1e9 for r in bl],color='#336a86',lw=1.4,label='Prior day, same UTC clock')
ax[1,0].set(yscale='log',title='C. Base fee versus preceding day',ylabel='Gwei (log scale)',xlabel='UTC clock time');ax[1,0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M',tz=timezone.utc));ax[1,0].legend(frameon=False,fontsize=8)
burn=sum(int(r['base_burn_wei']) for r in bc)/1e18;priority=sum(int(r['priority_fee_wei']) for r in bc)/1e18
ax[1,1].bar(['Base fee burned','Priority fee'],[burn,priority],color=['#8a929b','#336a86'],width=.55)
for i,n in enumerate([burn,priority]):ax[1,1].text(i,n+35,f'{n:,.2f} ETH',ha='center')
ax[1,1].set(title='D. Whole-window gas decomposition',ylabel='ETH',ylim=(0,max(burn,priority)*1.23));ax[1,1].text(.02,.95,'Direct builder tips excluded.\nWhole-window fees are not causal MEV.',transform=ax[1,1].transAxes,va='top',fontsize=9)
for a in ax.flat:a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
fig.savefig(O/'research_overview.png',dpi=180);fig.savefig(O/'research_overview.svg');plt.close(fig)
print('Saved research_overview.png and .svg')
