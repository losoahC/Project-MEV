import json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/mev-research-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
R=Path(__file__).resolve().parent;OUT=R/'figures';OUT.mkdir(exist_ok=True)
F=FontProperties(fname='/Library/Fonts/Arial Unicode.ttf')
plt.rcParams.update({'font.family':F.get_name(),'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243649','text.color':'#243649','axes.titleweight':'normal','figure.facecolor':'white','savefig.facecolor':'white'})
from matplotlib import font_manager
font_manager.fontManager.addfont(F.get_file())
def save(fig,name):
 fig.tight_layout(pad=1.5);fig.savefig(OUT/(name+'.png'),dpi=200);fig.savefig(OUT/(name+'.svg'));plt.close(fig)
def main():
 q=json.loads((R/'research_quality_analysis.json').read_text());s=q['same_sample_price_robustness'];fig,ax=plt.subplots(figsize=(7.2,3.2));ys=[float(s['shortfall_USD_by_lag'][str(k)])/1e6 for k in [1,5,15]];bars=ax.bar(['前 1 分钟','前 5 分钟','前 15 分钟'],ys,color=['#126F80','#4B8DA0','#89AAB8'],width=.55)
 ax.set_ylim(0,120);ax.set_ylabel('成交差额 / 百万美元',fontproperties=F);ax.set_title('固定 1,094 笔交易：只改变价格时点',fontproperties=F,loc='left',pad=14);ax.bar_label(bars,labels=[f'{y:.2f}' for y in ys],padding=5);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);save(fig,'fixed_sample_prices')
 d=q['local_effect_decomposition'];keys=['fee_at_unperturbed_spot','own_impact_plus_integer_rounding','preceding_trade_local_effect'];ys=[float(d['components_USD'][k])/1e6 for k in keys];fig,ax=plt.subplots(figsize=(7.2,3.3));bars=ax.barh(['参考现货下的费率影响','自身价格冲击与取整','前置交易局部影响'],ys,color=['#BCCAD0','#4B8DA0','#CB803C'],height=.5);ax.invert_yaxis();ax.set_xlim(0,1.4);ax.set_xlabel('相对前手之前池内现货的输出减少 / 百万美元',fontproperties=F);ax.set_title('77 笔严格样本：局部损失来源分解',fontproperties=F,loc='left',pad=14);ax.bar_label(bars,labels=[f'{y:.3f}' for y in ys],padding=5);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);save(fig,'local_effect_decomposition')
 w=json.loads((R/'candidate_window_sensitivity.json').read_text())['rows'];fig,ax=plt.subplots(figsize=(7.2,3.3));xs=range(len(w));a=[r['candidate_count'] for r in w];b=[r['strong_closed_cycle_count'] for r in w];bars=ax.bar(xs,a,color='#BBCDD3',width=.58,label='池重合候选');ax.bar(xs,b,color='#126F80',width=.58,label='其中：强闭合循环结构');ax.bar_label(bars,padding=4,fontsize=9);ax.set_xticks(list(xs),['同块','至后 1 块','至后 3 块','至后 5 块']);ax.set_ylim(0,19500);ax.set_ylabel('交易笔数',fontproperties=F);ax.set_title('候选数量对筛查窗口敏感；不等于已确认套利',fontproperties=F,loc='left',pad=14);ax.legend(frameon=False,prop=F,loc='upper left');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);save(fig,'candidate_window_sensitivity')
 print('3 figures written as PNG and SVG')
if __name__=='__main__':main()
