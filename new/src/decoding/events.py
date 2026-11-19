from decimal import Decimal, localcontext

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SWAP_V2 = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
SWAP_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"


def integer(value):
    return int(value, 16) if isinstance(value, str) and value.startswith("0x") else int(value)


def quantity(raw, decimals):
    if decimals is None or not 0 <= int(decimals) <= 255:
        raise ValueError("Missing or invalid token decimals")
    with localcontext() as ctx:
        ctx.prec = 100
        return Decimal(integer(raw)) / Decimal(10) ** int(decimals)


def transfer(log):
    topics = log.get("topics", [])
    if len(topics) != 3 or topics[0].lower() != TRANSFER:
        return None
    if len(log["data"]) != 66:
        return None
    return {"token": log["address"].lower(), "sender": "0x" + topics[1][-40:].lower(),
            "recipient": "0x" + topics[2][-40:].lower(), "amount_raw": str(integer(log["data"])),
            "log_index": integer(log["logIndex"])}


def signed_word(word):
    value = int(word, 16)
    return value - 2 ** 256 if value >= 2 ** 255 else value


def swap(log):
    topics = log.get("topics", [])
    if not topics:
        return None
    words = [log["data"][i:i + 64] for i in range(2, len(log["data"]), 64)]
    if topics[0].lower() == SWAP_V3 and len(words) == 5:
        return {"pool": log["address"].lower(), "protocol": "V3-compatible (event only)",
                "amount0_raw": str(signed_word(words[0])), "amount1_raw": str(signed_word(words[1])),
                "sqrt_price_x96_after": str(int(words[2], 16)), "liquidity_after": str(int(words[3], 16)),
                "log_index": integer(log["logIndex"])}
    if topics[0].lower() == SWAP_V2 and len(words) == 4:
        a, b, c, d = [int(w, 16) for w in words]
        return {"pool": log["address"].lower(), "protocol": "V2-compatible (event only)",
                "amount0_raw": str(a - c), "amount1_raw": str(b - d),
                "sqrt_price_x96_after": None, "liquidity_after": None,
                "log_index": integer(log["logIndex"])}
    return None


def successful_trace(trace, failed_paths):
    path = trace.get("traceAddress", [])
    return not trace.get("error") and not any(path[:len(p)] == p for p in failed_paths)


def validate_trace_tree(traces):
    paths = [tuple(t["traceAddress"]) for t in traces]
    if len(set(paths)) != len(paths) or paths.count(()) != 1:
        raise ValueError("Duplicate trace paths or missing root")
    children = {p: 0 for p in paths}
    for p in paths:
        if p:
            if p[:-1] not in children:
                raise ValueError("Missing trace parent")
            children[p[:-1]] += 1
    if any(children[tuple(t["traceAddress"])] != t["subtraces"] for t in traces):
        raise ValueError("Incomplete trace tree")


def native_transfer(trace):
    action = trace["action"]
    if trace["type"] == "call" and action.get("callType") == "call":
        sender, recipient, raw = action["from"], action["to"], action["value"]
    elif trace["type"] == "create":
        sender, recipient, raw = action["from"], trace.get("result", {}).get("address"), action["value"]
    elif trace["type"] in ("suicide", "selfdestruct"):
        sender, recipient, raw = action["address"], action["refundAddress"], action["balance"]
    else:
        return None
    if not integer(raw):
        return None
    if not recipient:
        raise ValueError("Missing native transfer recipient")
    return {"token": "native:eth", "sender": sender.lower(), "recipient": recipient.lower(),
            "amount_raw": str(integer(raw)), "log_index": None}
