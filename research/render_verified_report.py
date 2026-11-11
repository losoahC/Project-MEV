"""Render the authoritative Chinese Markdown report; keep scientific scope visible."""
import re,html,json
from decimal import Decimal
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
R=Path(__file__).resolve().parent;ROOT=R.parent
pdfmetrics.registerFont(TTFont('MEVBody','/System/Library/Fonts/STHeiti Light.ttc'))
pdfmetrics.registerFont(TTFont('MEVBold','/System/Library/Fonts/STHeiti Medium.ttc'))
pdfmetrics.registerFontFamily('MEVBody',normal='MEVBody',bold='MEVBold')
NAVY=colors.HexColor('#17324D');TEAL=colors.HexColor('#007E87');GRAY=colors.HexColor('#536170')
styles={
 'body':ParagraphStyle('body',fontName='MEVBody',fontSize=9.5,leading=16,textColor=NAVY,spaceAfter=7,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'title':ParagraphStyle('title',fontName='MEVBold',fontSize=23,leading=32,textColor=NAVY,spaceAfter=16,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='MEVBold',fontSize=14,leading=21,textColor=TEAL,spaceBefore=15,spaceAfter=9,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='MEVBold',fontSize=11,leading=18,textColor=NAVY,spaceBefore=10,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='MEVBody',fontSize=8,leading=12,textColor=NAVY,wordWrap='CJK'),
 'headcell':ParagraphStyle('headcell',fontName='MEVBold',fontSize=8,leading=12,textColor=colors.white,wordWrap='CJK')}
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:'<link href="'+m[2]+'" color="#007E87">'+m[1]+'</link>',s)
 s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s);s=re.sub(r'`([^`]+)`',r'\1',s)
 return s
class ReportDoc(SimpleDocTemplate):
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and f.style.name in ['h2','h3']:
   key='heading_'+str(self.seq.nextf('heading'));self.canv.bookmarkPage(key);self.canv.addOutlineEntry(f.getPlainText(),key,level=0 if f.style.name=='h2' else 1,closed=False)
def footer(c,doc):
 c.saveState();w,h=A4;c.setStrokeColor(colors.HexColor('#D7E1E8'));c.line(42,40,w-42,40);c.setFont('MEVBody',7);c.setFillColor(GRAY);c.drawString(42,27,'FT565 · Group 12 | 核验版 2026-11-11');c.drawRightString(w-42,27,str(doc.page));c.restoreState()
def main():
 source=R/'最终研究报告_2026-11-11.md';lines=source.read_text().splitlines();flow=[];i=0;table_count=0
 while i<len(lines):
  line=lines[i].strip()
  if not line or line.startswith('<!--'):i+=1;continue
  if line.startswith('|'):
   block=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r'[:\- ]+',c) for c in cells):block.append(cells)
    i+=1
   n=len(block[0]);assert all(len(row)==n for row in block);width=A4[0]-84
   weights=[.24,.76] if n==2 else [.37,.20,.43] if n==3 else [.25,.22,.22,.31] if n==4 else [.12,.16,.16,.28,.28] if n==5 else [1/n]*n
   def table_display(c):return re.sub(r'(?<![\da-zA-Z])(-?\d+\.\d{9,})(?![\da-zA-Z])',lambda m:format(Decimal(m[1]),'.6f'),c)
   cells=[[Paragraph(inline(table_display(c)),styles['headcell' if j==0 else 'cell']) for c in row] for j,row in enumerate(block)]
   t=Table(cells,colWidths=[width*x for x in weights],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F8'),colors.white]),('LINEBELOW',(0,0),(-1,0),.5,TEAL),('LINEBELOW',(0,1),(-1,-1),.2,colors.HexColor('#DAE3E9'))]));flow.extend([t,Spacer(1,9)]);table_count+=1;continue
  level=next((k for prefix,k in [('### ','h3'),('## ','h2'),('# ','title')] if line.startswith(prefix)),None)
  if level:flow.append(Paragraph(inline(line.lstrip('#').strip()),styles[level]));i+=1;continue
  if line.startswith('- '):line='• '+line[2:]
  flow.append(Paragraph(inline(line),styles['body']));i+=1
 dest=ROOT/'output/pdf/MEV研究报告_核验版_2026-11-11.pdf';dest.parent.mkdir(exist_ok=True,parents=True)
 doc=ReportDoc(str(dest),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=52,title='FT565 Group 12 — Binance 事件兑换损失与 MEV 核验报告',author='Group 12 Research');doc.build(flow,onFirstPage=footer,onLaterPages=footer)
 print(json.dumps({'pdf':str(dest),'bytes':dest.stat().st_size,'tables':table_count,'source':str(source)},ensure_ascii=False))
if __name__=='__main__':main()
