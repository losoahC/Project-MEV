"""Parse Etherscan's displayed ETH net transfers, not node traces.
Nonzero-value cross-check shows the summary includes top-level value. Gas is separate.
"""
import re,json,gzip,subprocess
from pathlib import Path
from decimal import Decimal
from html.parser import HTMLParser
R=Path(__file__).resolve().parent; C=R/'etherscan_raw';C.mkdir(exist_ok=True)
class Section(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.parts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='div' and a.get('id')=='nav_pane_eth_summary':self.depth=1;return
  if self.depth:
   if tag=='div':self.depth+=1
   self.parts.append(self.get_starttag_text())
 def handle_endtag(self,tag):
  if self.depth:
   if tag=='div':self.depth-=1
   self.parts.append('</'+tag+'>')
 def handle_data(self,s):
  if self.depth:self.parts.append(s)
def parse(s,h):
 if h.lower() not in s.lower() or 'Transaction Details' not in s:raise ValueError('Not a transaction detail page')
 p=Section();p.feed(s);section=''.join(p.parts)
 pattern=r'href=[\"\']/address/(0x[0-9a-fA-F]{40})#internaltx[\"\'].*?<span class="fw-medium">\s*(received|sent)\s*</span><span>([0-9,.]+)</span>'
 rows=re.findall(pattern,section,re.S);net={}
 for a,d,v in rows:net[a.lower()]=str(Decimal(v.replace(',',''))*(1 if d=='received' else -1))
 if section and not rows:raise ValueError('ETH summary present but failed to parse')
 return {'hash':h,'source':'https://etherscan.io/tx/'+h,'method':'Displayed ETH net summary; includes top-level value, excludes gas','includes_top_level_value':True,'summary_present':bool(section),'native_internal_net_eth':net,'net_conservation_eth':str(sum(map(Decimal,net.values()),Decimal(0)))}
def fetch(h):
 p=C/(h+'.html.gz')
 if p.exists():s=gzip.decompress(p.read_bytes()).decode()
 else:
  z=subprocess.run(['curl','-L','--fail','--compressed','--silent','--show-error','--max-time','35','https://etherscan.io/tx/'+h],capture_output=True)
  if z.returncode:raise RuntimeError(z.stderr.decode()[:160])
  s=z.stdout.decode();parse(s,h);p.write_bytes(gzip.compress(z.stdout))
 return parse(s,h)
if __name__=='__main__':
 h='0xb7d294873bf18a56ce99115794b8a9a76542791b58456e7a4f94d74f1ae4e41f'
 print(json.dumps(parse(Path('/tmp/etherscan_probe.html').read_text(),h),indent=2))
