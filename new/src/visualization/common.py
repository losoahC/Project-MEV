from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import textwrap

ROOT = Path(__file__).resolve().parents[2]
RED, TEAL, BLUE, GREY = "#e56c76", "#30b8a5", "#4b82dc", "#8292a8"


def export_static(fig, name, caption):
    fig.patch.set_facecolor("white")
    caption='\n'.join(textwrap.fill(p,width=165) for p in caption.split('\n'))
    fig.text(.06,.025,caption,fontsize=9,color="#526377",va="bottom")
    for ext in ("png","svg"):
        fig.savefig(ROOT/f"reports/figures/{name}.{ext}",dpi=180)
    plt.close(fig)


def export_interactive(fig,name,caption):
    fig.update_layout(template="plotly_dark",paper_bgcolor="#0d1625",plot_bgcolor="#0d1625",font=dict(family="Arial",size=13),margin=dict(l=max(fig.layout.margin.l or 0,90),r=max(fig.layout.margin.r or 0,60),t=max(fig.layout.margin.t or 0,125),b=max(fig.layout.margin.b or 0,110)))
    fig.add_annotation(text=caption,x=0,y=-.16,xref="paper",yref="paper",showarrow=False,xanchor="left",align="left",font=dict(size=10,color="#adbed2"))
    fig.write_html(ROOT/f"reports/figures/{name}.html",include_plotlyjs=True,config={"displaylogo":False,"responsive":True})
