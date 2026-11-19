"""Read-only public RPC requests, cached with request, endpoint and acquisition UTC."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from collections import defaultdict
import threading
import base64

import requests
from web3 import Web3

from src.ingestion.evidence import read_json


class PublicEvidence:
    def __init__(self, root, online=False):
        self.root, self.online = Path(root), online
        self.directory = self.root / "data/raw/public_rpc"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.locks = defaultdict(threading.Lock)

    def rpc(self, method, params):
        key = json.dumps([method,params],sort_keys=True)
        with self.locks[key]:
            return self._rpc(method,params)

    def _rpc(self, method, params):
        request = {"jsonrpc":"2.0", "id":1, "method":method, "params":params}
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        path = self.directory / (key + ".json")
        if path.exists():
            doc = read_json(path)
            if doc["response"].get("result") is not None:
                return doc["response"]["result"], str(path.relative_to(self.root))
        if not self.online:
            raise FileNotFoundError(f"Missing public RPC evidence for {method} {params}; run with --online")
        errors = []
        for endpoint in ("https://eth.drpc.org", "https://ethereum-rpc.publicnode.com"):
            try:
                response = requests.post(endpoint, json=request, timeout=18)
                response.raise_for_status()
                doc = response.json()
                if doc.get("result") is None:
                    raise ValueError(str(doc.get("error", "null result")))
                body = {"request":request,"endpoint":endpoint,"acquired_at_utc":datetime.now(timezone.utc).isoformat(),"response":doc,
                        "response_body_sha256":hashlib.sha256(response.content).hexdigest(),
                        "response_body_base64":base64.b64encode(response.content).decode()}
                if path.exists():
                    raise ValueError("Refusing to overwrite an immutable RPC record")
                path.write_text(json.dumps(body, indent=2))
                return doc["result"], str(path.relative_to(self.root))
            except (requests.RequestException, ValueError) as exc:
                errors.append({"endpoint":endpoint,"error":str(exc)})
        raise RuntimeError(errors)

    def call(self, address, signature, block):
        data = "0x" + Web3.keccak(text=signature).hex().removeprefix("0x")[:8]
        return self.rpc("eth_call", [{"to":Web3.to_checksum_address(address),"data":data},hex(block)])

    def get(self,url):
        directory=self.root/"data/raw/public_http"
        directory.mkdir(parents=True,exist_ok=True)
        path=directory/(hashlib.sha256(url.encode()).hexdigest()+".json")
        if path.exists():
            return read_json(path),str(path.relative_to(self.root))
        if not self.online:
            raise FileNotFoundError(f"Missing HTTP evidence for {url}; run with --online")
        body={"url":url,"acquired_at_utc":datetime.now(timezone.utc).isoformat()}
        try:
            response=requests.get(url,timeout=20)
            body.update({"http_status":response.status_code,"response_headers":{k:v for k,v in response.headers.items() if k.lower() in ("date","retry-after","content-type")},"response_body_base64":base64.b64encode(response.content).decode(),"response_body_sha256":hashlib.sha256(response.content).hexdigest()})
            try:
                body["response"]=response.json()
            except ValueError:
                body["response"]=None
            if response.status_code != 200:
                body["error"]=f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            body["error"]=str(exc)
        path.write_text(json.dumps(body,indent=2))
        return body,str(path.relative_to(self.root))

    def write_index(self):
        records=[]
        for folder in ("public_rpc","public_http"):
            for path in sorted((self.root/"data/raw"/folder).glob("*.json")):
                if path.name=="index.json":
                    continue
                doc=read_json(path)
                records.append({"path":str(path.relative_to(self.root)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"acquired_at_utc":doc.get("acquired_at_utc"),"source":doc.get("endpoint") or doc.get("url")})
        (self.root/"data/raw/public_index.json").write_text(json.dumps(records,indent=2))
