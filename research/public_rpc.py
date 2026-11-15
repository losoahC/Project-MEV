"""Minimal public Ethereum JSON-RPC helper (no API key). Retries across two public endpoints."""
import json, time, urllib.request

URLS = ['https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org']


def rpc(method, params, timeout=60, tries=3):
    last = None
    for attempt in range(tries):
        for u in URLS:
            try:
                body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
                req = urllib.request.Request(u, body, {'Content-Type': 'application/json', 'User-Agent': 'research-client'})
                r = json.load(urllib.request.urlopen(req, timeout=timeout))
                if r.get('result') is not None:
                    return r['result']
                last = (u, r.get('error'))
            except Exception as e:
                last = (u, str(e))
        time.sleep(1 + 2 * attempt)
    raise RuntimeError(last)
