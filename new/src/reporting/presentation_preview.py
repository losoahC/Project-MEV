"""Package existing Canva review images into a 14-page review PDF; no invented visuals."""
import argparse,hashlib,json,shutil
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
from src.visualization.common import ROOT


def build(source):
    source=Path(source);out=ROOT/'reports/presentation';images=out/'review_images';images.mkdir(exist_ok=True)
    overrides={4:'slide-04-wide.png',6:'slide-06-after.png',14:'slide-14-after.png'}
    records=[]
    for i in range(1,15):
        original=source/overrides.get(i,f'slide-{i:02}.png')
        if not original.exists():original=source/f'slide-{i:02}.png'
        target=images/f'slide-{i:02}.png'
        if original.resolve()!=target.resolve():shutil.copyfile(original,target)
        records.append({'page':i,'image':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    pdf=out/'presentation_review.pdf';c=canvas.Canvas(str(pdf),pagesize=(960,540));c.setTitle('Group12 research presentation —14-page review');c.setAuthor('Group12');c.setSubject('Review copy from Canva previews; exact sources in companion presenter notes')
    for row in records:
        c.drawImage(ImageReader(str(ROOT/row['image'])),0,0,width=960,height=540,preserveAspectRatio=True,anchor='c');c.showPage()
    c.save();reader=PdfReader(pdf);assert len(reader.pages)==14
    assert all(tuple(float(v) for v in p.mediabox[2:])==(960,540) for p in reader.pages)
    saved=json.loads((out/'canva_draft_review.json').read_text())
    (out/'review_manifest.json').write_text(json.dumps({'pages':14,'design_id':'DAHbT7iYK6M','editing_transaction':saved['editing_transaction'],'status':saved['status'],'preview_resolution':'Canva returns600×337pixel previews; PDF is a review copy, not a full-resolution or editable PPTX export','pdf':str(pdf.relative_to(ROOT)),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'images':records,'source_notes':'reports/presentation/presenter_notes.md','changes':['Removed unsupported illustrative chart from slide4; inserted actual N1 values','Corrected slide6 exact-value disclosure to companion notes','Updated slide14 to1024 reconciled ledgers and52tests']},indent=2))
    print('Packaged14checked slide previews as a review PDF, with exact-source companion notes')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');a=p.parse_args();build(a.source)
