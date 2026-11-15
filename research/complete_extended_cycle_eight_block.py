"""Eight-block EVM baseline and nonce-preserving interventions for the E53 cross-block cycle.

Self-contained: fetches headers/receipts over public RPC, runs eth_simulateV1 from the
historical parent of block 26302728 through the exit leg in 26302735, then repeats with
each hacker target (and both) replaced by a same-nonce zero-value self-transfer.
Output: extended_cycle_eight_block_EVM.json. Raw requests/responses cached (gitignored).
"""
import json, gzip, time, sys, urllib.request
from decimal import Decimal as D
from pathlib import Path

R = Path(__file__).resolve().parent
RAW = R / 'evm_replay_raw'; RAW.mkdir(exist_ok=True)
URLS = sys.argv[1:] or ['https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org']
START, END = 26302728, 26302735
ENTRY = '0x920240f243228a6f22471b409f980cffd356e5d053fd3764ea7868923d27d9b6'
EXIT = '0xc1f4442a5de3c70625a46ba4d0b6b1576b4305b047e32c0f9a83dac9d23a4803'
BOT = '0x3d63c340fa1735637e962e3b0b7d0f7cf1f722a1'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TARGETS = ['0x176905446185e22c310f5b6d8be9d0594b3cf721633fec088622d5f72e388763',
           '0x179f57544bcb4a6b8350ea74bc44ddb67db32a672f4298f2acb5c0922ca45fe4']


def rpc(method, params, timeout=120, urls=None):
    last = None
    for attempt in range(3):
        for u in urls or URLS:
            try:
                body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
                req = urllib.request.Request(u, body, {'Content-Type': 'application/json', 'User-Agent': 'research-client'})
                r = json.load(urllib.request.urlopen(req, timeout=timeout))
                if r.get('result') is not None:
                    return r['result'], u
                last = (u, r.get('error'))
            except Exception as e:
                last = (u, str(e))
        time.sleep(2 + 3 * attempt)
    raise RuntimeError(last)


def cached(name, fn):
    p = RAW / name
    if p.exists():
        return json.loads(gzip.decompress(p.read_bytes()))
    v = fn()
    p.write_bytes(gzip.compress(json.dumps(v).encode()))
    return v


def txcall(t):
    keys = ['from', 'to', 'gas', 'value', 'input', 'nonce', 'accessList', 'authorizationList',
            'maxFeePerBlobGas', 'blobVersionedHashes']
    keys += ['maxFeePerGas', 'maxPriorityFeePerGas'] if 'maxFeePerGas' in t else ['gasPrice']
    return {k: t[k] for k in keys if k in t}


def placeholder(t):
    """Same sender, same nonce, same fee fields; a 21000-gas zero-value self-transfer."""
    c = {'from': t['from'], 'to': t['from'], 'gas': hex(21000), 'value': '0x0', 'input': '0x', 'nonce': t['nonce']}
    for k in ('maxFeePerGas', 'maxPriorityFeePerGas', 'gasPrice'):
        if k in t:
            c[k] = t[k]
    return c


def weth_net(logs, who):
    n = 0
    for l in logs:
        if l['address'].lower() == WETH and l['topics'] and l['topics'][0] == TRANSFER and len(l['topics']) == 3:
            v = int(l['data'], 16)
            if '0x' + l['topics'][2][-40:] == who: n += v
            if '0x' + l['topics'][1][-40:] == who: n -= v
    return n


def main():
    headers = {n: cached(f'e53_block_{n}.json.gz', lambda n=n: rpc('eth_getBlockByNumber', [hex(n), True])[0]) for n in range(START - 1, END + 1)}
    receipts = {n: cached(f'e53_receipts_{n}.json.gz', lambda n=n: rpc('eth_getBlockReceipts', [hex(n)])[0]) for n in range(START, END + 1)}
    txs = {}
    for n in range(START, END + 1):
        ts = headers[n]['transactions']
        if n == END:
            ts = ts[:next(i for i, t in enumerate(ts) if t['hash'] == EXIT) + 1]
        txs[n] = ts
    where = {t['hash']: n for n in txs for t in txs[n]}
    assert all(h in where for h in TARGETS + [ENTRY, EXIT]), 'targets/legs not in window'

    def request(removed, validation=True):
        blocks = []
        for n in range(START, END + 1):
            b = headers[n]
            ov = {k: b[v] for k, v in {'number': 'number', 'time': 'timestamp', 'gasLimit': 'gasLimit', 'feeRecipient': 'miner',
                                       'prevRandao': 'mixHash', 'baseFeePerGas': 'baseFeePerGas'}.items()}
            ov['withdrawals'] = b.get('withdrawals', [])
            ov['blockHash'] = {str(k): headers[k]['hash'] for k in range(START - 1, n)}
            blocks.append({'blockOverrides': ov, 'calls': [placeholder(t) if t['hash'] in removed else txcall(t) for t in txs[n]]})
        return [{'blockStateCalls': blocks, 'validation': validation, 'traceTransfers': False}, hex(START - 1)]

    def upfront(t):
        return int(t['gas'], 16) * int(t.get('maxFeePerGas', t.get('gasPrice')), 16) + int(t['value'], 16)

    def run(label, removed, validation=True):
        """Run; if a third-party tx becomes unfundable (-38014), neutralize exactly that tx
        (same-nonce placeholder) and retry. Neutralized txs are reported, never hidden."""
        name = f'e53_sim_{label}.json.gz'
        p = RAW / name
        if p.exists():
            d = json.loads(gzip.decompress(p.read_bytes()))
            if 'result' in d: return d
        neutralized = []
        for _ in range(12):
            t0 = time.time()
            try:
                res, url = rpc('eth_simulateV1', request(set(removed) | set(neutralized), validation), timeout=300)
                d = {'result': res, 'endpoint': url, 'seconds': round(time.time() - t0, 1), 'neutralized': neutralized}
                break
            except RuntimeError as e:
                d = {'error': str(e), 'seconds': round(time.time() - t0, 1), 'neutralized': neutralized}
                msg = str(e)
                if '-38014' not in msg or 'want ' not in msg: break
                want = int(msg.split('want ')[1].split("'")[0].split('"')[0].strip())
                hit = [t['hash'] for n in txs for t in txs[n] if upfront(t) == want and t['hash'] not in removed and t['hash'] not in neutralized]
                if len(hit) != 1: break
                neutralized.append(hit[0]); print('  neutralize', hit[0], flush=True)
        p.write_bytes(gzip.compress(json.dumps(d).encode()))
        return d

    out = {'window': [START, END], 'stops_at_exit_leg': EXIT, 'transactions': sum(map(len, txs.values())),
           'targets': TARGETS, 'bot_wallet': BOT,
           'method': 'eth_simulateV1 over 8 consecutive blocks from historical parent 26302727; actual header overrides incl. withdrawals and historical block hashes; final block truncated at exit leg. Interventions replace a target with same-nonce 21000-gas zero-value self-transfer so later sender nonces stay valid. Receipts compared (status, gasUsed, ordered logs); state root not compared.',
           'scenarios': []}
    # actual bot flows from chain receipts
    rc = {r['transactionHash']: r for n in receipts for r in receipts[n]}
    actual_in, actual_out = weth_net(rc[ENTRY]['logs'], BOT), weth_net(rc[EXIT]['logs'], BOT)
    hacker = {t['from'] for n in txs for t in txs[n] if t['hash'] in TARGETS}
    hacker_all = [t['hash'] for n in txs for t in txs[n] if t['from'] in hacker]
    plan = [('baseline', [], True), ('remove_target_1', [TARGETS[0]], True), ('remove_target_2', [TARGETS[1]], True),
            ('remove_both', TARGETS, True), ('remove_all_hacker_window_txs', hacker_all, True)]
    POOL = '0x25647e01bd0967c1b9599fa3521939871d1d0888'
    out['hacker_senders'] = sorted(hacker); out['hacker_window_txs'] = hacker_all
    for label, removed, validation in plan:
        print('running', label, flush=True)
        d = run(label, removed, validation)
        row = {'label': label, 'removed': removed, 'validation': validation, 'seconds': d.get('seconds'), 'endpoint': d.get('endpoint')}
        if 'error' in d:
            row['error'] = d['error']; out['scenarios'].append(row); print(row); continue
        sims = {}
        for n, blk in zip(range(START, END + 1), d['result']):
            for t, c in zip(txs[n], blk['calls']):
                sims[t['hash']] = c
        if label == 'baseline':
            mism = []
            for h, c in sims.items():
                r = rc[h]; key = lambda l: (l['address'].lower(), l['topics'], l['data'])
                chk = {'status': c['status'] == r['status'], 'gas': int(c['gasUsed'], 16) == int(r['gasUsed'], 16),
                       'logs': [key(l) for l in c['logs']] == [key(l) for l in r['logs']]}
                if not all(chk.values()): mism.append({'hash': h, 'checks': chk})
            row['receipt_mismatches'] = mism; row['all_receipts_match'] = not mism
        neu = d.get('neutralized', [])
        row['neutralized_unfundable_txs'] = [{'hash': h, 'from': next(t['from'] for n in txs for t in txs[n] if t['hash'] == h),
                                              'touched_cycle_pool_in_actual': any(l['address'].lower() == POOL for l in rc[h]['logs'])} for h in neu]
        changed = [h for h, c in sims.items() if h not in removed and h not in neu and c['status'] != rc[h]['status']]
        row['other_status_changes'] = len(changed); row['other_status_changes_sample'] = changed[:10]
        e, x = sims[ENTRY], sims[EXIT]
        gas_wei = sum(int(sims[h]['gasUsed'], 16) * int(rc[h]['effectiveGasPrice'], 16) for h in (ENTRY, EXIT))
        wi, wo = weth_net(e['logs'], BOT), weth_net(x['logs'], BOT)
        row.update({'entry_status': e['status'], 'exit_status': x['status'], 'bot_WETH_entry': str(wi), 'bot_WETH_exit': str(wo),
                    'bot_net_ETH_after_gas': str(D(wi + wo - gas_wei) / D(10 ** 18))})
        out['scenarios'].append(row); print({k: v for k, v in row.items() if k != 'receipt_mismatches'}, flush=True)
    out['actual_bot_WETH_entry'] = str(actual_in); out['actual_bot_WETH_exit'] = str(actual_out)
    base = next((s for s in out['scenarios'] if s['label'] == 'baseline' and 'error' not in s), None)
    if base:
        for s in out['scenarios']:
            if 'bot_net_ETH_after_gas' in s:
                s['baseline_minus_scenario_ETH'] = str(D(base['bot_net_ETH_after_gas']) - D(s['bot_net_ETH_after_gas']))
    (R / 'extended_cycle_eight_block_EVM.json').write_text(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
