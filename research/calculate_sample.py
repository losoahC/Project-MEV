"""Recalculate selected observed swaps. Does not estimate MEV or fetch data."""
import json
from decimal import Decimal, getcontext
from pathlib import Path
from datetime import datetime

getcontext().prec = 50
root = Path(__file__).resolve().parent
data = json.loads((root / "swaps_observed.json").read_text())
rows = data["swaps"]
for row in rows:
    row["execution_price_usdt_per_eth"] = str(Decimal(row["input"]) / Decimal(row["output"]))
    row["source_url"] = "https://etherscan.io/tx/" + row["tx_hash"]
total_in = sum(Decimal(r["input"]) for r in rows)
total_out = sum(Decimal(r["output"]) for r in rows)
total_fee = sum(Decimal(r["fee"]) for r in rows)
result = {
    "scope": data["scope"],
    "total_usdt": str(total_in),
    "total_eth_received_before_gas": str(total_out),
    "total_gas_eth": str(total_fee),
    "weighted_execution_price_usdt_per_eth": str(total_in / total_out),
    "mev_profit": None,
    "swaps": rows,
}
eth_path = root / "coinbase_eth_usd_candles.json"
usdt_path = root / "coinbase_usdt_usd_candles.json"
if eth_path.exists() and usdt_path.exists():
    eth = {int(c[0]): c for c in json.loads(eth_path.read_text(), parse_float=Decimal)}
    usdt = {int(c[0]): c for c in json.loads(usdt_path.read_text(), parse_float=Decimal)}
    loss_total = Decimal(0)
    low_total = Decimal(0)
    high_total = Decimal(0)
    gas_usd = Decimal(0)
    for row in rows:
        minute = int(datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")).timestamp()) // 60 * 60
        e, u = eth[minute - 60], usdt[minute - 60]
        ec, uc = Decimal(e[4]), Decimal(u[4])
        inp, out = Decimal(row["input"]), Decimal(row["output"])
        loss = inp * uc - out * ec
        low = inp * Decimal(u[1]) - out * Decimal(e[2])
        high = inp * Decimal(u[2]) - out * Decimal(e[1])
        row["benchmark"] = {"method":"previous completed minute close; Coinbase spot", "minute_start_unix":minute-60, "eth_usd":str(ec), "usdt_usd":str(uc)}
        row["execution_value_shortfall_usd"] = str(loss)
        row["previous_minute_extrema_sensitivity_usd"] = [str(low), str(high)]
        loss_total += loss
        low_total += low
        high_total += high
        gas_usd += Decimal(row["fee"]) * ec
    result["price_benchmark"] = "Coinbase ETH-USD and USDT-USD spot; previous completed minute close"
    result["execution_value_shortfall_usd"] = str(loss_total)
    result["previous_minute_extrema_sensitivity_usd"] = [str(low_total),str(high_total)]
    result["sender_gas_usd_previous_minute_close"] = str(gas_usd)
    result["valuation_limitations"] = ["Single venue; no exact-time executable quote", "Extrema sensitivity is not a confidence interval", "Execution shortfall is not identified MEV", "Previous minute prices may themselves reflect broader event effects"]
(root / "sample_calculated.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "swaps"}, indent=2))
