"""Import and recheck existing evidence; no derived legacy totals are accepted."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, getcontext
import json
from pathlib import Path
import tempfile
import hashlib

import duckdb
import pandas as pd

from src.decoding.events import WETH, USDT, USDC, integer, quantity, transfer, swap, successful_trace, validate_trace_tree, native_transfer
from src.ingestion.evidence import EvidenceStore, find_block, read_json, unwrap
from src.reconciliation.valuation import previous_minute_price, execution
from src.ingestion.identity import wallet_record

getcontext().prec = 80
ROOT = Path(__file__).resolve().parents[2]
FIRST, LAST = 26300640, 26303950
CASE = "0x152e005f6dcccd941e0a2c7156b955c6baad08a347685bcf5518776dab04f8cc"
KNOWN = {USDT: ("USDT", 6), USDC: ("USDC", 6), WETH: ("ETH", 18), "native:eth": ("ETH", 18)}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def build(legacy):
    legacy = Path(legacy).resolve()
    store = EvidenceStore(ROOT, legacy)
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    wallet_path = legacy / "exploiter_1_16_and_bot_audit.json"
    store.archive(wallet_path, "Legacy tracker snapshot", "historical wallet leads; not verified ownership")
    wallets = read_json(wallet_path)["wallets"]
    addresses = {w["address"].lower() for w in wallets}
    sources = read_json(ROOT / "data/fixtures/identity_observations.json")
    wallet_rows = []
    for w in wallets:
        wallet_rows.append(wallet_record(w,sources['observations']))
    write_json(processed / "wallet_registry.json", wallet_rows)

    # Explorer histories discover transaction hashes; receipt logs are the edge authority.
    hashes = defaultdict(set)
    hints = {}
    metadata = {}
    history_pages = 0
    for path in sorted((legacy / "wallet_history_raw").glob("*.json.gz")):
        store.archive(path, "https://eth.blockscout.com/api/v2/addresses/", "paginated address history; cached")
        history_pages += 1
        for item in read_json(path).get("items", []):
            n = item.get("block_number")
            if n is None or not FIRST <= int(n) <= LAST:
                continue
            h = item.get("transaction_hash") or item.get("hash")
            if h:
                hashes[int(n)].add(h.lower())
                hints[h.lower()] = item
            token = item.get("token") or {}
            t = token.get("address_hash", "").lower()
            if t and token.get("decimals") is not None:
                value = (token.get("symbol"), int(token["decimals"]))
                if t in metadata and metadata[t] != value:
                    raise ValueError(f"Conflicting metadata: {t}")
                metadata[t] = value
    # Include all transactions sent by the controller, e.g. the sweep, even if its
    # ERC-20 transfers never touched the controller's own address.
    control_path = legacy / "exploiter1_raw/wallet1_all_sent_receipts.json.gz"
    store.archive(control_path, "Ethereum execution RPC", "controller transactions and receipts; cached")
    for item in read_json(control_path):
        n = integer(item["receipt"]["blockNumber"])
        if FIRST <= n <= LAST:
            hashes[n].add(item["hash"].lower())

    candles = {}
    candle_sources = {}
    for symbol in ("ETH", "USDT", "USDC"):
        path = legacy / f"prices_raw/{symbol}.json"
        if path.exists():
            candles[symbol] = read_json(path)
            candle_sources[symbol] = store.archive(path, "https://api.exchange.coinbase.com", f"GET /products/{symbol}-USD/candles; granularity=60; cached")

    edges, txrows, swaps, excluded = {}, [], [], []
    entity_roles = {}
    hot = "0x28c6c06298d514db089934071355e5743bf21d60"
    entity_roles[hot] = "exchange_hot_wallet_reported"
    case_receipt = case_header = case_traces = None

    def add_edge(base, flow, location, evidence, timestamp):
        if integer(flow["amount_raw"]) <= 0:
            return
        t = flow["token"]
        symbol, decimals = KNOWN.get(t, metadata.get(t, (None, None)))
        amount = quantity(flow["amount_raw"], decimals) if decimals is not None else None
        price = bar = None
        # A ticker is never enough to match an asset to a price feed.
        if t in KNOWN:
            price, bar = previous_minute_price(candles.get(symbol, []), timestamp)
        usd = amount * price if amount is not None and price is not None else None
        key = f"ethereum:{base['tx_hash']}:{location}"
        row = {**base, **flow, "edge_id": key, "chain": "ethereum", "event_location": location,
               "symbol": symbol or t[:10], "decimals": decimals, "amount": str(amount) if amount is not None else None,
               "timestamp": timestamp, "timestamp_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
               "usd_value": str(usd) if usd is not None else None,
               "reference_price_usd": str(price) if price is not None else None, "price_bar_start": bar,
               "price_source": candle_sources.get(symbol) if price is not None else None,
               "valuation_status": "estimated_prior_minute_close" if usd is not None else "missing_price_or_asset_identity",
               "evidence_path": evidence, "confidence": "observed_cached_execution",
               "tx_url": "https://etherscan.io/tx/" + base["tx_hash"]}
        if key in edges and edges[key] != row:
            raise ValueError(f"Conflicting duplicate edge: {key}")
        edges[key] = row

    for number, selected in sorted(hashes.items()):
        hp, rp = find_block(legacy, number, "header"), find_block(legacy, number, "receipts")
        if not hp or not rp:
            excluded.append({"block": number, "reason": "missing_header_or_receipts", "hashes": sorted(selected)})
            continue
        header, receipts = unwrap(read_json(hp)), unwrap(read_json(rp))
        assert integer(header["number"]) == number
        timestamp = integer(header["timestamp"])
        hsource = store.archive(hp, "Ethereum execution RPC (legacy public endpoints)", "eth_getBlockByNumber")
        rsource = store.archive(rp, "Ethereum execution RPC (legacy public endpoints)", "eth_getBlockReceipts")
        txmap = {t["hash"].lower(): t for t in header["transactions"] if isinstance(t, dict)}
        receiptmap = {r["transactionHash"].lower(): r for r in receipts}
        tp = find_block(legacy, number, "traces")
        traces = unwrap(read_json(tp)) if tp else []
        tsource = None
        trace_by_tx = defaultdict(list)
        for tr in traces if isinstance(traces, list) else []:
            trace_by_tx[tr.get("transactionHash", "").lower()].append(tr)
        for h in sorted(selected):
            rec = receiptmap.get(h)
            if not rec:
                excluded.append({"block": number, "tx_hash": h, "reason": "missing_receipt"})
                continue
            assert rec["blockHash"].lower() == header["hash"].lower()
            assert integer(rec["blockNumber"]) == number
            index = integer(rec["transactionIndex"])
            member = header["transactions"][index]
            assert (member["hash"] if isinstance(member, dict) else member).lower() == h
            base = {"tx_hash": h, "block_number": number, "block_hash": header["hash"], "transaction_index": index}
            txrows.append({**base, "timestamp": timestamp, "status": integer(rec["status"]),
                           "gas_used": integer(rec["gasUsed"]), "gas_fee_wei": str(integer(rec["gasUsed"]) * integer(rec["effectiveGasPrice"])),
                           "sender": rec["from"].lower(), "recipient": rec.get("to"),
                           "receipt_evidence": rsource, "header_evidence": hsource,
                           "native_trace_coverage": bool(trace_by_tx[h])})
            if integer(rec["status"]) != 1:
                continue
            for log in rec["logs"]:
                assert log["transactionHash"].lower() == h and log["blockHash"].lower() == header["hash"].lower()
                assert not log.get("removed", False)
                flow = transfer(log)
                if flow:
                    # Every routing leg is preserved; throughput is NOT stolen value.
                    add_edge(base, flow, "log:" + str(flow["log_index"]), rsource, timestamp)
                event = swap(log)
                if event:
                    swaps.append({**base, **event, "timestamp": timestamp, "evidence_path": rsource})
                    entity_roles[event["pool"]] = "swap_event_emitter"
            txtraces = trace_by_tx[h]
            if txtraces:
                validate_trace_tree(txtraces)
            failed_paths = [tr.get("traceAddress", []) for tr in txtraces if tr.get("error")]
            for tr in txtraces:
                if not successful_trace(tr, failed_paths):
                    continue
                flow = native_transfer(tr)
                if not flow:
                    continue
                # Do not include whole unrelated protocol subtrees outside the swap case.
                if not ({flow["sender"], flow["recipient"]} & addresses) and h != CASE:
                    continue
                if tsource is None:
                    tsource = store.archive(tp, "https://eth.drpc.org", "trace_block; cached")
                location = "trace:" + json.dumps(tr.get("traceAddress", []), separators=(",", ":"))
                add_edge(base, flow, location, tsource, timestamp)
            if not txtraces and h in txmap:
                tx = txmap[h]
                if integer(tx.get("value", "0x0")) and tx.get("to"):
                    flow = {"token": "native:eth", "sender": tx["from"].lower(), "recipient": tx["to"].lower(),
                            "amount_raw": str(integer(tx["value"])), "log_index": None}
                    add_edge(base, flow, "transaction_value", hsource, timestamp)
            if h == CASE:
                case_receipt, case_header, case_traces = rec, header, txtraces
        if len(txrows) % 100 < 3:
            print(f"Imported {len(txrows)} transactions, {len(edges)} transfers", flush=True)

    frame = pd.DataFrame(sorted(edges.values(), key=lambda x: (x["block_number"], x["transaction_index"], x["event_location"])))
    frame.to_parquet(processed / "wallet_edges.parquet", index=False)
    pd.DataFrame(txrows).to_parquet(processed / "transactions.parquet", index=False)
    pd.DataFrame(swaps).to_parquet(processed / "decoded_swaps.parquet", index=False)
    write_json(processed / "entities.json", entity_roles)
    write_json(processed / "excluded_observations.json", excluded)
    store.save()
    # DuckDB is an explicitly regenerable query layer, not the evidence authority.
    with duckdb.connect(str(processed / "research.duckdb")) as db:
        for name in ("wallet_edges", "transactions", "decoded_swaps"):
            path = str(processed / (name + ".parquet")).replace("'", "''")
            db.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_parquet('{path}')")
    assert case_receipt is not None and case_traces, "Representative swap must have receipts AND native traces"
    wallet = next(w["address"] for w in wallets if w["number"] == 10)
    case_edges = [e for e in edges.values() if e["tx_hash"] == CASE]
    net = defaultdict(int)
    for e in case_edges:
        if e["sender"] == wallet:
            net[e["token"]] -= int(e["amount_raw"])
        if e["recipient"] == wallet:
            net[e["token"]] += int(e["amount_raw"])
    timestamp = integer(case_header["timestamp"])
    peth, bar = previous_minute_price(candles["ETH"], timestamp)
    pusdt, _ = previous_minute_price(candles["USDT"], timestamp)
    paid = -quantity(net[USDT], 6)
    received = quantity(net[WETH] + net["native:eth"], 18)
    result = execution(str(paid * pusdt), str(received), str(peth))
    case_result = {"tx_hash": CASE, "wallet": wallet, "block": integer(case_receipt["blockNumber"]),
                   "transaction_index": integer(case_receipt["transactionIndex"]), "timestamp_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                   "net_asset_raw": dict(net), "USDT_paid": paid, "ETH_WETH_received_excluding_gas": received,
                   "gas_ETH": quantity(integer(case_receipt["gasUsed"]) * integer(case_receipt["effectiveGasPrice"]), 18),
                   "USDT_USD_reference": pusdt, "ETH_USD_reference": peth, "reference_bar_start": bar,
                   **result, "observed_swap_events": sum(s["tx_hash"] == CASE for s in swaps),
                   "interpretation": "Observed swap execution shortfall against prior-minute market benchmark; not realized arbitrage profit or causal MEV loss.",
                   "confidence": "execution observed in cached receipt/traces; valuation estimated", "edge_ids": [e["edge_id"] for e in case_edges]}
    write_json(ROOT / "reports/case_studies/m1_real_swap.json", case_result)
    write_json(processed / "coverage.json", {"first_block": FIRST, "last_block": LAST,
        "history_pages_imported": history_pages, "selected_blocks": len(hashes), "transactions_verified": len(txrows),
        "edges_verified": len(edges), "decoded_swap_events": len(swaps), "excluded_groups": len(excluded),
        "valued_edges": sum(e["usd_value"] is not None for e in edges.values()),
        "time_start_utc": frame.timestamp_utc.min(), "time_end_utc": frame.timestamp_utc.max(),
        "wallets_independently_corroborated": sum(w["identity_confidence"] == "independently_corroborated" for w in wallet_rows),
        "fresh_etherscan_numbered_labels_verified": 0,
        "limitations": ["This is an event-window sample, not complete multi-chain asset accounting.",
            "Source bytes and header/receipt agreement are checked; cryptographic receipt inclusion proofs and independent canonical-chain verification remain pending.",
            "USD values use exact prior completed Coinbase minute for ETH/USDT/USDC contract matches only.",
            "Native traces cover wallet-touching calls and the full example transaction, not every protocol leg.",
            "No recipient ownership inference; no THORChain identity inferred from an unknown address.",
            "Missing prices remain null. Intermediary transfer values cannot be summed as stolen value."]})
    print(json.dumps(read_json(processed / "coverage.json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", type=Path, default=ROOT.parent / "research")
    parser.add_argument("--from-archive", action="store_true", help="Rebuild offline using only the archived evidence objects")
    args = parser.parse_args()
    if args.from_archive:
        manifest = read_json(ROOT / "data/raw/manifest.json")
        with tempfile.TemporaryDirectory(prefix="group12-replay-") as directory:
            for obj in manifest["objects"]:
                if hashlib.sha256((ROOT / obj["path"]).read_bytes()).hexdigest() != obj["sha256"]:
                    raise ValueError(f"Archived object hash mismatch: {obj['path']}")
                dest = Path(directory) / obj["legacy_source"]
                if dest.is_absolute() and not dest.is_relative_to(directory):
                    raise ValueError("Unsafe legacy source path")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to(ROOT / obj["path"])
            build(directory)
    else:
        build(args.legacy)
