from collections import defaultdict
from decimal import Decimal

from src.decoding.events import WETH, integer, transfer, native_transfer, successful_trace, validate_trace_tree

DEPOSIT = "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
WITHDRAWAL = "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"
SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
E = Decimal(10)**18


def token_net(receipt, accounts):
    net = defaultdict(int)
    for log in receipt["logs"]:
        flow = transfer(log)
        if flow:
            net[flow["token"]] += int(flow["amount_raw"]) * ((flow["recipient"] in accounts) - (flow["sender"] in accounts))
        topics = log.get("topics", [])
        if log["address"].lower() == WETH and len(topics) == 2 and topics[0].lower() in (DEPOSIT, WITHDRAWAL):
            actor = "0x" + topics[1][-40:].lower()
            if actor in accounts:
                net[WETH] += integer(log["data"]) * (1 if topics[0].lower() == DEPOSIT else -1)
    return {t:v for t,v in net.items() if v}


def native_flows(traces):
    validate_trace_tree(traces)
    failed = [t["traceAddress"] for t in traces if t.get("error")]
    result = []
    for tr in traces:
        if successful_trace(tr, failed):
            flow = native_transfer(tr)
            if flow:
                result.append({**flow, "trace_address":tr["traceAddress"]})
    return result


def cashflow(receipt, traces, accounts, fee_recipient):
    accounts = {a.lower() for a in accounts}
    assert receipt["from"].lower() in accounts, "Gas payer must be inside stated accounting boundary"
    net = token_net(receipt, accounts)
    flows = native_flows(traces)
    native = sum(int(f["amount_raw"]) * ((f["recipient"] in accounts) - (f["sender"] in accounts)) for f in flows)
    gas_wei = integer(receipt["gasUsed"]) * integer(receipt["effectiveGasPrice"])
    payment_wei = sum(int(f["amount_raw"]) for f in flows if f["sender"] in accounts and f["recipient"] == fee_recipient.lower())
    retained_before_gas = native + net.get(WETH,0)
    return {"token_net_raw":{t:str(v) for t,v in net.items()}, "other_token_residual_raw":{t:str(v) for t,v in net.items() if t != WETH},
            "native_net_wei":str(native), "gas_wei":str(gas_wei), "identified_builder_payment_wei":str(payment_wei),
            "cashflow_before_gas_ETH":str(Decimal(retained_before_gas)/E),
            "gross_after_pool_fees_before_gas_and_builder_ETH":str(Decimal(retained_before_gas + payment_wei)/E),
            "net_after_gas_and_builder_ETH":str(Decimal(retained_before_gas - gas_wei)/E),
            "payment_note":"Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again."}


def v2_quote(amount_in, reserve_in, reserve_out, fee_numerator=997, fee_denominator=1000):
    if min(amount_in, reserve_in, reserve_out) <= 0:
        raise ValueError("Nonpositive amount/reserve")
    return amount_in * fee_numerator * reserve_out // (reserve_in * fee_denominator + amount_in * fee_numerator)


def v2_execution_decomposition(amount_in, amount_out, reserve_in, reserve_out, fee_numerator=997, fee_denominator=1000):
    """One-leg output-token units. This is a mechanical curve/fee decomposition, not MEV attribution."""
    marginal = Decimal(amount_in) * Decimal(reserve_out) / Decimal(reserve_in)
    zero_fee = Decimal(amount_in) * Decimal(reserve_out) / Decimal(reserve_in + amount_in)
    fee_adjusted = v2_quote(amount_in,reserve_in,reserve_out,fee_numerator,fee_denominator)
    return {"marginal_output_raw":str(marginal),"no_fee_curve_output_raw":str(zero_fee),
            "modeled_fee_adjusted_output_raw":str(fee_adjusted),"actual_output_raw":str(amount_out),
            "mechanical_impact_output_raw":str(marginal-zero_fee),
            "fee_effect_output_raw":str(zero_fee-Decimal(fee_adjusted)),
            "unexplained_model_residual_raw":str(Decimal(fee_adjusted)-Decimal(amount_out))}
