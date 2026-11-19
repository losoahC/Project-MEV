from collections import defaultdict
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.decoding.events import quantity, integer, signed_word, successful_trace, TRANSFER, USDT, validate_trace_tree, native_transfer
from src.ingestion.evidence import read_json, unwrap
from src.reconciliation.valuation import execution, previous_minute_price

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("raw,decimals,expected", [("10000000000000",6,"10000000"),("3552228717651589845452",18,"3552.228717651589845452"),("1",18,"0.000000000000000001"),(str(2**256-1),0,str(2**256-1))])
def test_token_precision(raw, decimals, expected):
    assert quantity(raw, decimals) == Decimal(expected)


@pytest.mark.parametrize("decimals", [None,-1,256])
def test_invalid_metadata_not_zero(decimals):
    with pytest.raises(ValueError):
        quantity(10, decimals)


def test_reference_uses_completed_minute_no_lookahead():
    candles = [[60,0,0,0,2,0],[120,0,0,0,99,0]]
    assert previous_minute_price(candles, 179) == (Decimal(2),60)
    assert previous_minute_price(candles, 240) == (None,180)


def test_missing_reference_never_fills_zero_or_stale():
    assert previous_minute_price([], 100) == (None,0)
    with pytest.raises(ValueError):
        previous_minute_price([[0,0,0,0,1,0],[0,0,0,0,2,0]],100)


def test_buy_and_sell_direction():
    assert execution("3000","1","2200","buy")["adverse_loss_usd"] == 800
    assert execution("1800","1","2200","sell")["adverse_loss_usd"] == 400
    assert execution("2300","1","2200","sell")["adverse_loss_usd"] == -100


def test_signed_swap_amounts():
    assert signed_word("f"*64) == -1
    assert signed_word("0"*63+"1") == 1


def test_reverted_parent_excludes_nominally_successful_child():
    assert not successful_trace({"traceAddress":[1,2,3]}, [[1,2]])
    assert successful_trace({"traceAddress":[1,3]}, [[1,2]])
    assert not successful_trace({"traceAddress":[1]}, [[]])


def test_incomplete_or_ambiguous_trace_tree_rejected():
    with pytest.raises(ValueError):
        validate_trace_tree([{"traceAddress":[],"subtraces":1}])
    with pytest.raises(ValueError):
        validate_trace_tree([{"traceAddress":[],"subtraces":0},{"traceAddress":[],"subtraces":0}])
    validate_trace_tree([{"traceAddress":[],"subtraces":1},{"traceAddress":[0],"subtraces":0}])


def test_create_and_selfdestruct_native_value_not_lost():
    sender, recipient = "0x"+"a"*40,"0x"+"b"*40
    created = native_transfer({"type":"create","action":{"from":sender,"value":"0x10"},"result":{"address":recipient}})
    destroyed = native_transfer({"type":"suicide","action":{"address":sender,"refundAddress":recipient,"balance":"0x10"}})
    assert created == destroyed
    assert int(created["amount_raw"]) == 16


@pytest.fixture(scope="module")
def edges():
    return pd.read_parquet(ROOT / "data/processed/wallet_edges.parquet")


def test_graph_deduplicates_cross_wallet_and_multihop_events(edges):
    assert edges.edge_id.is_unique
    assert edges.tx_hash.str.fullmatch(r"0x[0-9a-f]{64}").all()
    assert (edges.amount_raw.map(int) > 0).all()
    assert edges.confidence.eq("observed_cached_execution").all()
    assert edges[edges.usd_value.isna()].reference_price_usd.isna().all()


def test_no_recipient_ownership_inference():
    wallets = read_json(ROOT / "data/processed/wallet_registry.json")
    assert len(wallets) == 16
    assert len({w["address"] for w in wallets}) == 16
    assert all(w["ownership_cluster"] is None for w in wallets)
    assert all(w["label_status"] == "legacy_label_not_freshly_verified" for w in wallets)


def test_raw_objects_match_manifest():
    for obj in read_json(ROOT / "data/raw/manifest.json")["objects"]:
        raw = (ROOT / obj["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == obj["sha256"], obj["path"]
        assert len(raw) == obj["bytes"]


def test_every_graph_log_matches_original_receipt(edges):
    for path, group in edges[edges.event_location.str.startswith("log:")].groupby("evidence_path"):
        receipts = unwrap(read_json(ROOT / path))
        original = {(r["transactionHash"].lower(), integer(l["logIndex"])): l for r in receipts for l in r["logs"]}
        for e in group.to_dict("records"):
            log = original[(e["tx_hash"], int(e["log_index"]))]
            assert log["topics"][0].lower() == TRANSFER
            assert log["address"].lower() == e["token"]
            assert "0x"+log["topics"][1][-40:].lower() == e["sender"]
            assert "0x"+log["topics"][2][-40:].lower() == e["recipient"]
            assert integer(log["data"]) == int(e["amount_raw"])
            assert log["blockHash"] == e["block_hash"]


def test_real_swap_wallet_balance_and_gas(edges):
    case = read_json(ROOT / "reports/case_studies/m1_real_swap.json")
    selected = edges[edges.tx_hash.eq(case["tx_hash"])]
    wallet = case["wallet"]
    net = defaultdict(int)
    for e in selected.to_dict("records"):
        net[e["token"]] += int(e["amount_raw"]) * ((e["recipient"] == wallet) - (e["sender"] == wallet))
    assert net[USDT] == -10_000_000_000_000
    assert net["native:eth"] == 3552228717651589845452
    assert Decimal(case["gas_ETH"]) == Decimal("0.35185578020075793")
    with localcontext() as ctx:
        ctx.prec=80
        loss = Decimal("10000000")*Decimal("0.99876")-Decimal("3552.228717651589845452")*Decimal("2248.4")
        assert abs(Decimal(case["adverse_loss_usd"])-loss) < Decimal("1e-60")
    assert case["observed_swap_events"] == 17


def test_multihop_case_is_event_ordered():
    swaps = pd.read_parquet(ROOT / "data/processed/decoded_swaps.parquet")
    case = read_json(ROOT / "reports/case_studies/m1_real_swap.json")
    legs = swaps[swaps.tx_hash.eq(case["tx_hash"])].sort_values("log_index")
    assert len(legs) == 17 and legs.log_index.is_unique
    assert legs.pool.nunique() > 3
    assert legs.transaction_index.eq(2).all()
