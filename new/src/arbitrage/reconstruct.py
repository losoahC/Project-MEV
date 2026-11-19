"""Milestone 2: independently rebuild three real cycles and one sandwich episode."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal, getcontext
import json
from pathlib import Path

import pandas as pd

from src.arbitrage.accounting import cashflow, token_net, v2_execution_decomposition, SYNC
from src.decoding.events import integer, transfer, swap, signed_word, WETH, USDT, USDC
from src.ingestion.evidence import EvidenceStore, read_json, unwrap, find_block, block_candidates
from src.ingestion.public_evidence import PublicEvidence
from src.reconciliation.valuation import previous_minute_price

getcontext().prec = 90
ROOT = Path(__file__).resolve().parents[2]


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


class Reconstruction:
    def __init__(self, legacy, online=False):
        self.legacy = Path(legacy).resolve()
        self.store = EvidenceStore(ROOT,self.legacy)
        self.public = PublicEvidence(ROOT,online)
        self.archive_by_origin = {r["legacy_source"]:ROOT/r["path"] for r in self.store.records.values()}
        self.cache = {}

    def source(self, relative):
        local = self.legacy / relative
        return local if local.exists() else self.archive_by_origin.get(relative)

    def block_source(self,number,kind):
        return find_block(self.legacy,number,kind) or next((self.source(name) for name in block_candidates(number,kind) if self.source(name)),None)

    def block(self, number):
        if number in self.cache:
            return self.cache[number]
        paths = {}
        for kind in ("header","receipts","traces"):
            path = self.block_source(number,kind)
            if not path:
                raise FileNotFoundError((number,kind))
            if path.is_relative_to(self.legacy):
                ref = self.store.archive(path,"Ethereum execution RPC (legacy public endpoints)",{"header":"eth_getBlockByNumber","receipts":"eth_getBlockReceipts","traces":"trace_block"}[kind])
            else:
                ref = str(path.relative_to(ROOT))
            paths[kind] = ref
        header,receipts,traces = [unwrap(read_json(ROOT/paths[k])) for k in ("header","receipts","traces")]
        rs = {r["transactionHash"].lower():r for r in receipts}
        ts = defaultdict(list)
        for t in traces:
            ts[t.get("transactionHash","").lower()].append(t)
        for h,r in rs.items():
            assert r["blockHash"] == header["hash"] and integer(r["blockNumber"]) == number
            tx = header["transactions"][integer(r["transactionIndex"])]
            assert (tx["hash"] if isinstance(tx,dict) else tx).lower() == h
        self.cache[number] = header,rs,ts,paths
        return self.cache[number]

    def metadata(self, pool, protocol, block):
        result = {"pool":pool,"protocol":protocol,"block":block,"sources":{}}
        for field,signature in (("token0","token0()"),("token1","token1()"),("factory","factory()")):
            value,source = self.public.call(pool,signature,block)
            result[field] = "0x"+value[-40:].lower()
            result["sources"][field] = source
        if protocol.startswith("V3"):
            value,source = self.public.call(pool,"fee()",block)
            result["fee_pips"] = integer(value)
            result["sources"]["fee"] = source
        else:
            result["fee_pips"] = 3000
            result["fee_assumption"] = "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone."
        for i in (0,1):
            value,source = self.public.call(result[f"token{i}"],"decimals()",block)
            result[f"decimals{i}"] = integer(value)
            result["sources"][f"decimals{i}"] = source
        return result

    def states(self, number, meta):
        header,rs,_,paths = self.block(number)
        records = []
        for pool,m in meta.items():
            v3 = m["protocol"].startswith("V3")
            current = None
            if v3:
                slot,source = self.public.call(pool,"slot0()",number-1)
                words = [slot[i:i+64] for i in range(2,len(slot),64)]
                liq,lsource = self.public.call(pool,"liquidity()",number-1)
                current = {"sqrt_price_x96":str(int(words[0],16)),"tick":signed_word(words[1]),"active_liquidity":str(integer(liq)),"state_evidence":source,"liquidity_evidence":lsource}
            for receipt in sorted(rs.values(),key=lambda r:integer(r["transactionIndex"])):
                sync = None
                for log in sorted(receipt["logs"],key=lambda l:integer(l["logIndex"])):
                    if log["address"].lower() != pool or not log.get("topics"):
                        continue
                    topic = log["topics"][0].lower()
                    if topic == SYNC:
                        sync = [int(log["data"][i:i+64],16) for i in (2,66)]
                    event = swap(log)
                    if event:
                        if v3:
                            before = dict(current)
                            words = [log["data"][i:i+64] for i in range(2,len(log["data"]),64)]
                            after = {"sqrt_price_x96":event["sqrt_price_x96_after"],"tick":signed_word(words[4]),"active_liquidity":event["liquidity_after"],"state_evidence":paths["receipts"],"log_index":event["log_index"]}
                        else:
                            assert sync is not None,"Missing Sync before V2 Swap"
                            after = {"reserve0_raw":str(sync[0]),"reserve1_raw":str(sync[1]),"state_evidence":paths["receipts"]}
                            before = {"reserve0_raw":str(sync[0]-int(event["amount0_raw"])),"reserve1_raw":str(sync[1]-int(event["amount1_raw"])),"state_evidence":paths["receipts"],"inference":"Sync after minus Swap net amounts"}
                        records.append({"block":number,"tx_hash":receipt["transactionHash"].lower(),"transaction_index":integer(receipt["transactionIndex"]),**event,"before":before,"after":after,"evidence_path":paths["receipts"]})
                        current = after
                    # Mint/Burn event names are hashed locally; only active-range liquidity changes matter here.
                    elif v3 and len(log["topics"]) == 4:
                        from web3 import Web3
                        mint = "0x"+Web3.keccak(text="Mint(address,address,int24,int24,uint128,uint256,uint256)").hex().removeprefix("0x")
                        burn = "0x"+Web3.keccak(text="Burn(address,int24,int24,uint128,uint256,uint256)").hex().removeprefix("0x")
                        if topic in (mint,burn):
                            lower,upper = signed_word(log["topics"][2][2:]),signed_word(log["topics"][3][2:])
                            words = [log["data"][i:i+64] for i in range(2,len(log["data"]),64)]
                            amount = int(words[1 if topic==mint else 0],16)
                            if lower <= current["tick"] < upper:
                                current = {**current,"active_liquidity":str(int(current["active_liquidity"])+amount*(1 if topic==mint else -1)),"liquidity_evidence":paths["receipts"]}
        return sorted(records,key=lambda s:(s["transaction_index"],s["log_index"]))

    def route(self, receipt, metas, states):
        pools = {s["pool"] for s in states if s["tx_hash"] == receipt["transactionHash"].lower()}
        flow = defaultdict(lambda:defaultdict(int))
        for log in receipt["logs"]:
            t = transfer(log)
            if not t:
                continue
            if t["recipient"] in pools:
                flow[t["recipient"]][t["token"]] += int(t["amount_raw"])
            if t["sender"] in pools:
                flow[t["sender"]][t["token"]] -= int(t["amount_raw"])
        route = []
        for pool,balance in flow.items():
            positive = [(t,v) for t,v in balance.items() if v>0]
            negative = [(t,-v) for t,v in balance.items() if v<0]
            assert len(positive)==len(negative)==1, "Non-simple net pool flow; requires explicit reconstruction"
            inp,amount_in = positive[0]
            out,amount_out = negative[0]
            meta = metas[pool]
            assert {inp,out} == {meta["token0"],meta["token1"]}
            pin = 0 if inp==meta["token0"] else 1
            pout = 1-pin
            amount = Decimal(amount_in)/Decimal(10)**meta[f"decimals{pin}"]
            output = Decimal(amount_out)/Decimal(10)**meta[f"decimals{pout}"]
            events = [s for s in states if s["tx_hash"]==receipt["transactionHash"].lower() and s["pool"]==pool]
            route.append({"pool":pool,"input_token":inp,"output_token":out,"input_raw":str(amount_in),"output_raw":str(amount_out),
                "input_quantity":str(amount),"output_quantity":str(output),"output_per_input":str(output/amount),
                "swap_log_indices":[s["log_index"] for s in events],"protocol":meta["protocol"],"fee_pips":meta["fee_pips"],
                "fee_note":"Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."})
        return route


def run(legacy,online=False):
    engine = Reconstruction(legacy,online)
    spec = read_json(ROOT/"data/fixtures/arbitrage_cases.json")
    cases = spec["cases"]
    sandwich = spec["sandwich"]
    state_rows,all_routes,outputs,canonical = [],[],[],[]
    targets = set(pd.read_parquet(ROOT/"data/processed/transactions.parquet").tx_hash)
    for c in [*cases,sandwich]:
        n = c["block"]
        header,rs,ts,paths = engine.block(n)
        live,livesource = engine.public.rpc("eth_getBlockByNumber",[hex(n),False])
        assert live["hash"] == header["hash"], "Cached block differs from independent current RPC read"
        canonical.append({"block":n,"block_hash":header["hash"],"fresh_read_evidence":livesource,"matched":True})
        hashes = [c["tx_hash"],c["target"]] if "tx_hash" in c else [c["front"],c["target"],c["back"]]
        assert c["target"] in targets, "Target must lie in the stated 16-wallet transaction sample"
        pools = {}
        for h in hashes:
            assert integer(rs[h]["status"]) == 1
            for log in rs[h]["logs"]:
                event = swap(log)
                if event:
                    pools[event["pool"]] = event["protocol"]
        print(f"{c['case_id']}: reading metadata/state for {len(pools)} pools",flush=True)
        with ThreadPoolExecutor(max_workers=5) as executor:
            metas = dict(zip(pools,executor.map(lambda p:engine.metadata(p,pools[p],n-1),pools)))
        states = engine.states(n,metas)
        for s in states:
            state_rows.append({"case_id":c["case_id"],**s})
        if "tx_hash" in c:
            receipt = rs[c["tx_hash"]]
            assert set(c["accounts"]) == {receipt["from"].lower(),receipt["to"].lower()}, "Standalone boundary must be sender plus private executor, not an expanded router cluster"
            result = cashflow(receipt,ts[c["tx_hash"]],c["accounts"],header["miner"])
            assert not result["other_token_residual_raw"]
            assert Decimal(result["net_after_gas_and_builder_ETH"]) > 0
            route = engine.route(receipt,metas,states)
            residual = defaultdict(int)
            for leg in route:
                residual[leg["input_token"]] -= int(leg["input_raw"])
                residual[leg["output_token"]] += int(leg["output_raw"])
            assert not {t:v for t,v in residual.items() if t != WETH and v},"Pool cycle is not inventory closed"
            assert residual[WETH] > 0
            result["pool_flow_surplus_ETH"] = str(Decimal(residual[WETH])/Decimal(10)**18)
            result["unallocated_pool_surplus_vs_operational_gross_ETH"] = str(Decimal(result["pool_flow_surplus_ETH"])-Decimal(result["gross_after_pool_fees_before_gas_and_builder_ETH"]))
            # Positive edge cycle and operational balance closure are separately observed.
            samepool = []
            for a in states:
                if a["tx_hash"]!=c["tx_hash"]:
                    continue
                for t in states:
                    if t["tx_hash"]==c["target"] and a["pool"]==t["pool"] and int(a["amount0_raw"])*int(t["amount0_raw"])<0:
                        samepool.append(a["pool"])
            assert samepool
            result.update({**c,"timestamp_utc":datetime.fromtimestamp(integer(header["timestamp"]),timezone.utc).isoformat(),
                "sender":receipt["from"].lower(),"executor":receipt["to"].lower(),
                "actor_index":integer(receipt["transactionIndex"]),"target_index":integer(rs[c["target"]]["transactionIndex"]),
                "same_pool_opposite_direction":sorted(set(samepool)),"route":route,"metadata":metas,"evidence":paths,
                "classification":"observed_inventory_closed_profitable_atomic_arbitrage",
                "attribution_limit":"Same-block/pool association is observed. This cash flow is not all causally attributable to removing the hacker's trade; operational boundary is not beneficial ownership."})
            assert result["target_index"] < result["actor_index"]
            for leg in route:
                all_routes.append({"case_id":c["case_id"],"tx_hash":c["tx_hash"],**leg})
            outputs.append(result)
            save(ROOT/f"reports/case_studies/{c['case_id']}_arbitrage.json",result)
        else:
            front = cashflow(rs[c["front"]],ts[c["front"]],c["accounts"],header["miner"])
            back = cashflow(rs[c["back"]],ts[c["back"]],c["accounts"],header["miner"])
            assert rs[c["front"]]["from"] == rs[c["back"]]["from"]
            idx = [integer(rs[h]["transactionIndex"]) for h in hashes]
            assert idx[0]<idx[1]<idx[2]
            residual = defaultdict(int)
            for r in (front,back):
                for t,v in r["other_token_residual_raw"].items():
                    residual[t]+=int(v)
            assert not {t:v for t,v in residual.items() if v}
            poolstates = [s for s in states if s["pool"]==c["pool"] and s["tx_hash"] in hashes]
            grouped = {h:[s for s in poolstates if s["tx_hash"]==h] for h in hashes}
            assert all(grouped.values())
            assert int(grouped[c["front"]][0]["amount0_raw"])*int(grouped[c["target"]][0]["amount0_raw"])>0
            assert int(grouped[c["back"]][0]["amount0_raw"])*int(grouped[c["target"]][0]["amount0_raw"])<0
            output = {**c,"front_cashflow":front,"back_cashflow":back,
                "episode_net_ETH":str(Decimal(front["net_after_gas_and_builder_ETH"])+Decimal(back["net_after_gas_and_builder_ETH"])),
                "episode_gas_ETH":str((Decimal(front["gas_wei"])+Decimal(back["gas_wei"]))/Decimal(10)**18),
                "episode_builder_payment_ETH":str((Decimal(front["identified_builder_payment_wei"])+Decimal(back["identified_builder_payment_wei"]))/Decimal(10)**18),
                "evidence":paths,"transaction_indices":idx,"metadata":metas,
                "classification":"same-sender inventory-closed directional sandwich with cross-pool back leg",
                "limit":"Bracketing and observed PnL are established. Incremental victim loss requires a separate executable counterfactual; back-leg cash inflow alone is not episode profit."}
            save(ROOT/"reports/case_studies/S1_sandwich.json",output)

    # Reconstruct V2 leg impact/fee mechanics from actual Sync and Swap, separately from reference-price loss.
    decomposition=[]
    for s in state_rows:
        if not s["protocol"].startswith("V2"):
            continue
        a0,a1=int(s["amount0_raw"]),int(s["amount1_raw"])
        if a0*a1 >= 0:
            continue
        j=0 if a0>0 else 1
        rin,rout=[int(s["before"][f"reserve{k}_raw"]) for k in (j,1-j)]
        d=v2_execution_decomposition([a0,a1][j],-[a0,a1][1-j],rin,rout)
        decomposition.append({"case_id":s["case_id"],"tx_hash":s["tx_hash"],"pool":s["pool"],"log_index":s["log_index"],**d})
    save(ROOT/"data/processed/arbitrage_cases.json",outputs)
    save(ROOT/"data/processed/pool_states.json",state_rows)
    save(ROOT/"data/processed/v2_price_impact_decomposition.json",decomposition)
    save(ROOT/"data/processed/canonical_block_crosscheck.json",canonical)
    pd.DataFrame(all_routes).to_parquet(ROOT/"data/processed/arbitrage_routes.parquet",index=False)
    pd.DataFrame([{k:(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in o.items() if k not in ("metadata","route","evidence","same_pool_opposite_direction","accounts")} for o in outputs]).to_parquet(ROOT/"data/processed/arbitrage_pnl.parquet",index=False)
    engine.store.save()
    print("Rebuilt three independent arbitrage cases and one complete two-leg sandwich episode",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--legacy",type=Path,default=ROOT.parent/"research")
    p.add_argument("--online",action="store_true")
    args=p.parse_args()
    run(args.legacy,args.online)
