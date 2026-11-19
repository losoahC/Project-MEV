from decimal import Decimal


def previous_minute_price(candles, timestamp):
    """Strict prior completed UTC minute; no forward lookup or silent stale fill."""
    start = int(timestamp) // 60 * 60 - 60
    matches = [c for c in candles if int(c[0]) == start]
    if not matches:
        return None, start
    if len({str(c[4]) for c in matches}) != 1:
        raise ValueError("Conflicting source candles")
    price = Decimal(str(matches[0][4]))
    if price <= 0:
        raise ValueError("Nonpositive reference price")
    return price, start


def execution(input_usd, output_quantity, reference_price, side="buy"):
    value, amount, ref = map(Decimal, (input_usd, output_quantity, reference_price))
    if amount <= 0 or ref <= 0:
        raise ValueError("Nonpositive amount/reference")
    price = value / amount
    if side not in ("buy", "sell"):
        raise ValueError("side must be buy or sell")
    adverse = (price - ref) if side == "buy" else (ref - price)
    return {"price": price, "dislocation": price / ref - 1, "adverse_loss_usd": amount * adverse}
