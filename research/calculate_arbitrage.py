"""Combine receipt-derived token inventory changes with checked native ETH flows."""
import json
from decimal import Decimal as D, getcontext
from pathlib import Path

getcontext().prec=50
R=Path(__file__).resolve().parent
data=json.loads((R/"mev_candidates.json").read_text())
observed=json.loads((R/"verified_arbitrage_inputs.json").read_text())
W="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
S="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
out=[]
for item in observed["examples"]:
    block=next(b for b in data["blocks"] if b["block"]==item["block"])
    row=next(t for t in block["candidates"] if t["hash"]==item["hash"])
    group={row["from"],row["to"]}
    inventory={}
    for a in group:
        for token,n in row["erc20_net_raw"].get(a,{}).items():
            inventory[token]=inventory.get(token,0)+int(n)
    weth=D(inventory.get(W,0))/D(10**18)
    native=D(item["native_net_eth_before_gas"])
    fee=D(row["gas_fee_wei"])/D(10**18)
    profit=weth+native-fee
    assert row["relative_position"]>0 and row["status"]==1
    receipts=json.loads((R/"chain_raw"/f'{item["block"]}_receipts.json').read_text())["result"]
    receipts={r["transactionHash"]:r for r in receipts}
    def directions(h):
        result={}
        for log in receipts[h]["logs"]:
            if log["topics"] and log["topics"][0]==S:
                d=log["data"][2:]
                amounts=[int(d[i:i+64],16) for i in [0,64]]
                amounts=[n-2**256 if n>=2**255 else n for n in amounts]
                result.setdefault(log["address"],[]).append(amounts)
        return result
    target_dirs=directions(block["target_hash"])
    candidate_dirs=directions(item["hash"])
    opposite=[]
    for pool in row["shared_v3_pools"]:
        if any(a[0]*b[0]<0 and a[1]*b[1]<0 for a in target_dirs[pool] for b in candidate_dirs[pool]):
            opposite.append(pool)
    out.append({**item,"source_url":"https://etherscan.io/tx/"+item["hash"],"sender":row["from"],"strategy":row["to"],"target_index":block["target_index"],"index":row["index"],"shared_v3_pools":row["shared_v3_pools"],"opposite_direction_shared_v3_pools":opposite,"corrected_weth_inventory_change":str(weth),"other_token_changes_raw":{t:str(n) for t,n in inventory.items() if t!=W and n},"gas_eth":str(fee),"priority_fee_eth":str(D(row["priority_fee_wei"])/D(10**18)),"estimated_execution_net_eth":str(profit),"attribution":"Confirmed atomic arbitrage execution after target; event-specific incremental MEV unproven without replay"})
result={"verified_examples":out,"selected_examples_net_eth":str(sum(D(r["estimated_execution_net_eth"]) for r in out)),"direct_builder_payments_eth":str(sum(D(r["builder_payment_eth"]) for r in out)),"note":"Selected examples only; not event totals or lower bound of event-attributable MEV. Net includes measured sender gas and direct builder payments, excludes off-chain costs; one example has immaterial unvalued AAVE dust."}
(R/"verified_arbitrage.json").write_text(json.dumps(result,indent=2))
for r in out:
    print(r["block"],r["index"],r["hash"][:12],"netETH",r["estimated_execution_net_eth"],"tipETH",r["builder_payment_eth"],"opposite pools",len(r["opposite_direction_shared_v3_pools"]),"other",r["other_token_changes_raw"])
print("Selected example net ETH:",result["selected_examples_net_eth"])
print("Direct builder payments ETH:",result["direct_builder_payments_eth"])
