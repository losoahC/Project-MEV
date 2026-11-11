"""Loopback-only read-only archive RPC cache, serialized and paced for public limits."""
import json,gzip,hashlib,time,threading,subprocess
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
R=Path(__file__).resolve().parent;C=R/'local_rpc_raw';C.mkdir(exist_ok=True);lock=threading.Lock();last=0;count=0
ALLOWED={'eth_chainId','net_version','web3_clientVersion','eth_getBlockByNumber','eth_getBlockByHash','eth_getBalance','eth_getCode','eth_getStorageAt','eth_getTransactionCount','eth_getProof','eth_getTransactionByHash','eth_getTransactionReceipt','eth_getBlockReceipts'}
def request(q):
 global last,count
 if q.get('method') not in ALLOWED:return {'jsonrpc':'2.0','id':q.get('id'),'error':{'code':-32601,'message':'Read-only archive proxy: method not allowed'}}
 canonical={'method':q['method'],'params':q.get('params',[])};key=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest();path=C/(key+'.json.gz')
 with lock:
  if path.exists():r=json.loads(gzip.decompress(path.read_bytes()))['response']
  else:
   r={}
   for attempt in range(6):
    time.sleep(max(0,1.0-(time.monotonic()-last)));last=time.monotonic();wire={'jsonrpc':'2.0','id':1,**canonical}
    p=subprocess.run(['curl','--silent','--show-error','--max-time','40','-H','Content-Type: application/json','--data-binary','@-','https://eth.drpc.org'],input=json.dumps(wire),text=True,capture_output=True)
    try:r=json.loads(p.stdout)
    except ValueError:r={'jsonrpc':'2.0','id':1,'error':{'code':-32000,'message':p.stderr or 'Non-JSON public endpoint response'}}
    if 'result' in r:
     path.write_bytes(gzip.compress(json.dumps({'request':wire,'response':r,'retrieved_unix':time.time(),'endpoint':'https://eth.drpc.org'}).encode()));count+=1
     if count%25==0:print('cached public archive reads',count,flush=True)
     break
    (C/(key+f'.error_{time.time_ns()}.json')).write_text(json.dumps({'request':wire,'response':r}));print('public read retry',q['method'],attempt+1,str(r.get('error'))[:200],flush=True);time.sleep(min(60,2**(attempt+1)))
  r=dict(r);r['id']=q.get('id');return r
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  try:
   q=json.loads(self.rfile.read(int(self.headers['Content-Length'])));r=[request(x) for x in q] if isinstance(q,list) else request(q);body=json.dumps(r).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  except (BrokenPipeError,ConnectionResetError):pass
  except Exception as e:
   print('proxy handler error',repr(e),flush=True);self.send_error(500)
if __name__=='__main__':
 print('Read-only paced archive proxy on 127.0.0.1:18546; maximum one upstream request per second.',flush=True);ThreadingHTTPServer(('127.0.0.1',18546),Handler).serve_forever()
