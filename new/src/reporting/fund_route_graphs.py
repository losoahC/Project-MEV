"""Actual transaction flow diagrams. Mixed-asset arrows keep their own units."""
import json
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from src.arbitrage.discover import ROOT

def canvas(title,subtitle):
    fig,ax=plt.subplots(figsize=(16,9));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off');fig.patch.set_facecolor('#f7fafc');ax.set_facecolor('#f7fafc');fig.text(.05,.94,title,fontsize=23,weight='bold',color='#102a43');fig.text(.05,.90,subtitle,fontsize=11,color='#526377');return fig,ax
def box(ax,x,y,title,detail,w=.23,h=.12,color='#e6f3f4'):
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.012',fc=color,ec='#829ab1',lw=1.2));ax.text(x,y+.022,title,ha='center',va='center',fontsize=13,weight='bold',color='#102a43');ax.text(x,y-.025,detail,ha='center',va='center',fontsize=10,color='#334e68')
def arrow(ax,p,q,label,xy,rad=0,color='#227c9d'):
    ax.add_patch(FancyArrowPatch(p,q,connectionstyle=f'arc3,rad={rad}',arrowstyle='-|>',mutation_scale=16,lw=2,color=color));ax.text(*xy,label,ha='center',va='center',fontsize=10,color=color,bbox={'fc':'#f7fafc','ec':'none','pad':2})
def save(fig,name,footer):
    fig.text(.05,.035,footer,fontsize=10,color='#526377');fig.subplots_adjust(left=.025,right=.975,top=.84,bottom=.10)
    for ext in ['png','svg']:fig.savefig(ROOT/'reports/mev_expansion'/f'{name}.{ext}',dpi=150)
    plt.close(fig)

def run():
    p=ROOT/'data/processed/mev_full_window';c=json.loads((p/'comet_resolver_equity.json').read_text());fig,ax=canvas('How the order resolver earned value','Ethereum block 26,300,895 | tx 0x3fd5ec...a0b6 | Actual transfers; collateral and debt shown separately')
    box(ax,.15,.78,'Flash funding hub','0xbbbb...ffcb');box(ax,.50,.56,'Resolver execution','0x9b13...3b82');box(ax,.85,.78,'Order protocol','0x1111...2a65');box(ax,.15,.31,'Order maker / swapper','0x9749...c762');box(ax,.50,.14,'Compound WETH Comet','0xa175...ae94');box(ax,.85,.31,'Block fee recipient','from actual header',color='#eee9f7')
    arrow(ax,(.26,.74),(.39,.61),'9,831.718026 WETH\nflash principal',(.27,.65),-.12);arrow(ax,(.39,.53),(.24,.72),'9,831.718026 WETH\nprincipal repaid',(.20,.54),-.20);arrow(ax,(.60,.62),(.74,.75),'9,594.665344 WETH\norder fulfilment',(.70,.67),-.08);arrow(ax,(.26,.34),(.39,.50),'28,600,454.367187 USDT',(.25,.43),-.06);arrow(ax,(.45,.49),(.45,.21),'same USDT amount\nlocked as collateral',(.34,.31));arrow(ax,(.55,.21),(.55,.49),'10,041.436485 WETH\nnew loan / liability',(.66,.32));arrow(ax,(.61,.51),(.74,.36),'335.030255 ETH\ndirect native payment',(.78,.49),-.09)
    ax.text(.88,.13,'Liquid retained after gas\n111.676131 ETH\n\nPosition equity also remains\nUSDT collateral minus WETH debt',ha='center',va='center',fontsize=11,color='#102a43');ax.text(.45,.87,f"Marked equity increase: ${Decimal(c['reference_equity_gain_after_gas_USD']):,.2f}",ha='center',fontsize=15,weight='bold',color='#17988a')
    save(fig,'order_resolver_fund_route','The marked equity increase includes collateral minus debt, not just cash received. Loan principal and flash repayments are not profit.\nNo common ownership or ordering-based MEV is inferred. Actual gas only; diagnostic read-call gas is excluded.')
    fig,ax=canvas('A closed TRON pool cycle and its payout','tx 45e73a31...a6916 | Actual TRC20 logs and non-rejected native internal transfers | Amounts retain original units')
    box(ax,.15,.69,'Affected V3 pool','TSUUVj...vZpx');box(ax,.50,.69,'Execution contract','TS5v9Z...NZC7');box(ax,.85,.69,'Official SunSwap V4 manager','TVjuTE...1Br');box(ax,.45,.23,'WTRX wrapper','TNUC9Q...jWFR');box(ax,.85,.23,'Operating EOA wallet','TUAAqY...qrSS',color='#dff4ee')
    arrow(ax,(.26,.75),(.39,.75),'7,965,429.126504 USDT',(.32,.85),-.12);arrow(ax,(.39,.64),(.26,.64),'22,507,361.780441 WTRX',(.30,.52),-.13);arrow(ax,(.61,.75),(.74,.75),'7,962,660.017313 USDT',(.69,.85),-.12);arrow(ax,(.74,.64),(.61,.64),'23,130,554.809584 TRX',(.70,.52),-.13);arrow(ax,(.45,.62),(.45,.30),'22,507,361.780442 TRX\nwrap / deposit',(.32,.41));arrow(ax,(.60,.62),(.78,.30),'623,193.029142 TRX\nactual EOA payout',(.76,.40),-.09)
    ax.text(.15,.22,'Boundary surplus\n2,769.109191 USDT\n+ 623,193.029143 TRX/WTRX\n\n1 SUN of TRX remains in executor',ha='center',va='center',fontsize=11,color='#102a43');ax.text(.51,.05,'Observed paid transaction fee: 0 TRX\nDelegated energy and offchain costs unpriced',ha='center',fontsize=10,color='#526377')
    save(fig,'tron_cycle_fund_route','PoolId dda1d581...2557e is authenticated from the five-word SunSwap V4 PoolKey. V3 brand/factory remains separately qualified.\nWTRX mint is evidenced by Deposit, so it is not drawn as an invented Transfer. No hacker-to-bot direct transfer is implied.')
    cases=json.loads((p/'victim_case_accounts.json').read_text());r=next(r for r in cases if r['block']==26301699);v=r['victim_intervention'];effect=v['victim_effects'][0];fig,ax=canvas('Sandwich evidence and the actual fee path','Ethereum block 26,301,699 | One fixed-call front-removal intervention | Conditional victim output effect, not whole-event loss')
    box(ax,.15,.75,'Front leg','0x8300d3...fb06');box(ax,.50,.75,'Target transaction',v['target'][:12]+'...'+v['target'][-5:]);box(ax,.85,.75,'Back leg','0x7890dd...3ac3');arrow(ax,(.27,.75),(.38,.75),'same pool',(.325,.81));arrow(ax,(.62,.75),(.73,.75),'opposite exit',(.675,.81))
    box(ax,.15,.30,'Execution contract','0x45e9...9215');box(ax,.50,.30,'Unwrap payment helper','0x3c26...dc2e');box(ax,.85,.30,'Block fee recipient','0xd87f...4d96',color='#eee9f7');arrow(ax,(.27,.30),(.38,.30),'90.4957032475 WETH',(.325,.40));arrow(ax,(.62,.30),(.73,.30),'90.4957032475 ETH',(.675,.40));ax.text(.50,.09,'Canonical WETH Withdrawal + zero helper terminal asset change + matching native payout',ha='center',fontsize=10,color='#526377')
    ax.text(.50,.52,f"Victim output improves by ${Decimal(effect['marked_output_improvement_USD']):,.2f} if only the front leg is removed.\nBot boundary net after actual gas and payments: {Decimal(r['net_operational_cashflow_ETH']):.9f} ETH",ha='center',va='center',fontsize=13,color='#102a43')
    save(fig,'sandwich_and_fee_route','Actual transaction prefix status, gas and logs reproduce; target inputs are unchanged and both scenarios execute successfully.\nThe victim output effect, bot retained profit and builder payment are different quantities. Helper is not merged into bot ownership.')
    print('Created 3 flow diagrams, PNG and SVG')
if __name__=='__main__':run()
