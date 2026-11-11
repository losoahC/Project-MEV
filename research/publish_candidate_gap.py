"""Refresh human reports and integrity inventory after successful final validation."""
import json,re,hashlib
from pathlib import Path
from decimal import Decimal as D
from report_candidate_gap import main as gap_report
from build_extension_report import main as extension_report
R=Path(__file__).resolve().parent
def main():
 v=json.loads((R/'candidate_gap_validation.json').read_text());a=json.loads((R/'all_candidate_accounting.json').read_text())['summary']
 assert v['remaining']==0 and v['failed']==0 and a['native_missing']==0
 gap_report();extension_report()
 p=R/'任务完成度审查.md';text=p.read_text()
 text=re.sub(r'^\| 候选收益 \|.*$',f"| 候选收益 | 全部 {a['candidates']:,} 笔原生币收支齐全；{a['native_available_and_other_inventory_closed']:,} 笔其他 ERC-20 库存闭合，净现金流 {D(a['closed_group_cashflow_ETH']):,.6f} ETH | 原 12,934 笔原生币缺口已归零；其余代币估值和因果利润仍待研究 |",text,flags=re.M)
 text=re.sub(r'^\| 内部 ETH 收支 \|.*$','| 内部 ETH 收支 | 原净流出证据保留；全部 13,623 笔候选均有公开完整调用轨迹，按区块与原始回执核验 | 候选收支数据缺口已完成，不是本地反事实回放 |',text,flags=re.M)
 text=text.replace('全体候选内部转账、主体与库存核算','候选主体归属与其他代币库存核算')
 text=text.replace('24+14 项检查通过',f"24+14+{v['passed']} 项检查通过")
 marker='<!-- candidate-gap-complete -->';end='<!-- candidate-gap-complete-end -->'
 for path,body in [(p,text),(R/'研究报告_综合版.md',(R/'研究报告_综合版.md').read_text())]:
  body=re.sub(re.escape(marker)+r'.*?'+re.escape(end)+r'\n\n','',body,flags=re.S)
  banner=f'{marker}\n> **候选收支缺口已补齐：12,934 → 0。** 全部 13,623 笔候选均有原生币收支证据。本轮 {v["passed"]} 项核验通过。详见[缺口完成报告](候选收支缺口完成报告.md)及[中文逐笔明细](候选收支明细_中文.csv)。这项完成不代表全事件 MEV 因果核算完成。\n{end}\n\n'
  path.write_text(banner+body)
 files=[]
 for path in sorted(R.rglob('*')):
  if not path.is_file() or '__pycache__' in path.parts or path.name=='evidence_manifest.json':continue
  data=path.read_bytes();files.append({'path':str(path.relative_to(R)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 (R/'evidence_manifest.json').write_text(json.dumps({'note':'Integrity inventory; hashes do not certify ownership, source truth, counterfactual causality, or full event coverage','file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),'files':files},indent=2))
 print('Published gap completion. Files:',len(files),'bytes:',sum(r['bytes'] for r in files))
if __name__=='__main__':main()
