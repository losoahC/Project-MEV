"""Collect named TRON trader evidence from public solidified receipts, at low rate."""
import json,base64,hashlib,datetime,time,requests
from pathlib import Path
from src.arbitrage.discover import ROOT
BOT='TUAAqYySyBJDLJDxnQKqtcPBW1JXJuqrSS'
ABC='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def decode_addr(a):
    n=0
    for c in a:n=n*58+ABC.index(c)
    b=n.to_bytes(25,'big');assert hashlib.sha256(hashlib.sha256(b[:-4]).digest()).digest()[:4]==b[-4:];assert b[0]==65;return b[:-4].hex()

def encode_addr(h):
    h=h.removeprefix('0x');h=h if len(h)==42 else '41'+h;b=bytes.fromhex(h);d=b+hashlib.sha256(hashlib.sha256(b).digest()).digest()[:4];n=int.from_bytes(d,'big');s=''
    while n:n,k=divmod(n,58);s=ABC[k]+s
    return s

def run():
    out=ROOT/'data/raw/tron_expansion';first=json.loads((out/'named_bot_first_page.json').read_text());page=json.loads(base64.b64decode(first['response_body_base64']));assert page['success'];assert not page.get('meta',{}).get('links',{}).get('next'),'Full pagination must be collected before claiming address coverage'
    txs=page['data'];bot=decode_addr(BOT);rows=[];failures=[]
    for i,t in enumerate(txs,1):
        h=t['txID'];req={'value':h};u='https://api.trongrid.io/walletsolidity/gettransactioninfobyid';key=hashlib.sha256((u+json.dumps(req,sort_keys=True)).encode()).hexdigest();p=out/(key+'.json')
        if p.exists():doc=json.loads(p.read_text())
        else:
            time.sleep(1.25);doc={'url':u,'request':req,'acquired_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            try:
                r=requests.post(u,json=req,timeout=30);doc.update(http_status=r.status_code,response_body_base64=base64.b64encode(r.content).decode(),response_body_sha256=hashlib.sha256(r.content).hexdigest());doc['response']=r.json()
            except Exception as ex:doc['error']=str(ex)
            p.write_text(json.dumps(doc,indent=2))
        info=doc.get('response',{})
        if doc.get('http_status')!=200 or info.get('id')!=h:failures.append({'tx_hash':h,'evidence':str(p.relative_to(ROOT)),'error':info or doc.get('error')});continue
        assert all(c['parameter']['value'].get('owner_address')==bot for c in t['raw_data']['contract'])
        rows.append({'tx_hash':h,'bot':BOT,'bot_hex':bot,'transaction':t,'receipt':info,'receipt_evidence':str(p.relative_to(ROOT)),'transaction_evidence':str((out/'named_bot_first_page.json').relative_to(ROOT))})
        if i%10==0:print('TRON receipts',i,'/',len(txs),'failures',len(failures),flush=True)
    dest=ROOT/'data/processed/mev_tron';dest.mkdir(exist_ok=True);(dest/'named_bot_receipts.json').write_text(json.dumps(rows,indent=2));(dest/'collection_summary.json').write_text(json.dumps({'bot':BOT,'history_rows':len(txs),'receipt_rows':len(rows),'failed_rows':len(failures),'failures':failures,'scope':'Named address account-history page within requested interval; no next page returned. Not whole TRON incident or all bot inventory.'},indent=2));print('TRON collected',len(rows),'failures',len(failures))
if __name__=='__main__':run()
