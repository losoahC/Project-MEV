"""Download public Ethereum evidence and screen same-block transactions.

Candidate screening is not a counterfactual proof of event-attributable MEV.
"""
import json
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "chain_raw"
RAW.mkdir(exist_ok=True)
RPC = "https://ethereum-rpc.publicnode.com"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SWAP_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
DEPOSIT = "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
WITHDRAWAL = "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"

def rpc(method, params):
    raw = subprocess.check_output(["curl","-L","--fail","--compressed","--silent","--show-error","--max-time","50","-H","Content-Type: application/json","--data",json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}),RPC])
    data = json.loads(raw)
    if "error" in data:
        raise RuntimeError(data["error"])
    if data.get("result") is None:
        raise RuntimeError("RPC returned null")
    return data

def download(task):
    number, method, suffix, params = task
    path = RAW / f"{number}_{suffix}.json"
    if not path.exists():
        data = rpc(method, params)
        path.write_text(json.dumps(data))
    return str(path.name)

def main():
    swaps = json.loads((ROOT / "swaps_observed.json").read_text())["swaps"]
    tasks = []
    for number in sorted({r["block"] for r in swaps}):
        tasks.extend([(number,"eth_getBlockByNumber","block",[hex(number),True]), (number,"eth_getBlockReceipts","receipts",[hex(number)])])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(download,tasks):
            print("Saved",name,flush=True)
    summaries=[]
    for target in swaps:
        number=target["block"]
        block=json.loads((RAW/f"{number}_block.json").read_text())["result"]
        receipts=json.loads((RAW/f"{number}_receipts.json").read_text())["result"]
        byhash={r["transactionHash"].lower():r for r in receipts}
        target_receipt=byhash[target["tx_hash"]]
        assert int(block["number"],16)==number
        assert target_receipt["blockHash"]==block["hash"]
        assert len(byhash)==len(block["transactions"])
        target_index=int(target_receipt["transactionIndex"],16)
        pools={log["address"].lower() for log in target_receipt["logs"] if log["topics"] and log["topics"][0].lower()==SWAP_V3}
        candidates=[]
        for tx in block["transactions"]:
            receipt=byhash[tx["hash"].lower()]
            shared=pools & {log["address"].lower() for log in receipt["logs"] if log["topics"] and log["topics"][0].lower()==SWAP_V3}
            if not shared or tx["hash"].lower()==target["tx_hash"]:
                continue
            flows={}
            for log in receipt["logs"]:
                topics=log["topics"]
                if log["address"].lower()==WETH and len(topics)==2 and topics[0].lower() in [DEPOSIT,WITHDRAWAL]:
                    address="0x"+topics[1][-40:].lower()
                    delta=int(log["data"],16)*(1 if topics[0].lower()==DEPOSIT else -1)
                    flows.setdefault(address,{})
                    flows[address][WETH]=flows[address].get(WETH,0)+delta
                    continue
                if len(topics)!=3 or topics[0].lower()!=TRANSFER:
                    continue
                token=log["address"].lower()
                sender="0x"+topics[1][-40:].lower()
                recipient="0x"+topics[2][-40:].lower()
                amount=int(log["data"],16)
                for address,delta in [(sender,-amount),(recipient,amount)]:
                    flows.setdefault(address,{})
                    flows[address][token]=flows[address].get(token,0)+delta
            flows={a:{t:str(n) for t,n in f.items() if n} for a,f in flows.items()}
            effective=int(receipt["effectiveGasPrice"],16)
            base=int(block["baseFeePerGas"],16)
            gas=int(receipt["gasUsed"],16)
            candidates.append({"hash":tx["hash"],"index":int(tx["transactionIndex"],16),"relative_position":int(tx["transactionIndex"],16)-target_index,"from":tx["from"],"to":tx["to"],"status":int(receipt["status"],16),"shared_v3_pools":sorted(shared),"gas_fee_wei":str(gas*effective),"base_fee_burn_wei":str(gas*base),"priority_fee_wei":str(gas*max(0,effective-base)),"erc20_net_raw":flows})
        summaries.append({"block":number,"target_hash":target["tx_hash"],"target_index":target_index,"block_transaction_count":len(block["transactions"]),"target_v3_pools":sorted(pools),"candidates":candidates})
    (ROOT/"mev_candidates.json").write_text(json.dumps({"rpc":RPC,"method":"same-block overlap of Uniswap V3 Swap emitters; excludes V2/V4-only overlap; not proof of MEV", "flow_note":"erc20_net_raw includes WETH Deposit/Withdrawal corrections, but excludes native ETH flows", "blocks":summaries},indent=2))
    for s in summaries:
        print("Block",s["block"],"target position",s["target_index"],"shared-pool candidates",len(s["candidates"]))

if __name__=="__main__":
    main()
