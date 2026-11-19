> 本文为扩展前的 M1–M6 基线报告。最新成果请看 [中文完整套利与 MEV 核验报告](mev_expansion/完整套利与MEV核验报告.md)；原三案例与 52 项测试不代表本轮完整样本。

# Binance Incident, DEX Arbitrage and MEV Auctions

**Group 12 · FT565 · Evidence-based forensic research**  
Research acquisition snapshot: 18 November 2026. All event times below are UTC.

## Abstract

We build a reproducible on-chain forensic pipeline to distinguish abnormal execution, captured arbitrage profits, and transfers among MEV participants. The bounded Ethereum sample covers blocks 26,300,640–26,303,950 and verifies 1,640 transactions, 57,042 deduplicated transfer edges, and 1,155 V2/V3-compatible Swap events. Three actual atomic arbitrage cases yield 2.748062266732417199 ETH after observed gas and identified direct builder transfers. Three associated block-auction outcomes reconcile relay-delivered values to proposer receipts. A separate, fully reconstructed sandwich episode earns 12.080033775421395622 ETH; its large back-leg proceeds are not its complete profit.

Among 810 two-sided wallet/swap observations, 621 have complete contract-matched trade-time valuations and 241 meet the prespecified screening conditions. Five exceed USD 1 million in estimated reference shortfall, including two above USD 5 million. These observations do not establish deliberate self-loss or a causal MEV decomposition. Three November ETH-to-BTC THORChain conversions are independently matched across Ethereum, THORNode, Midgard and confirmed Bitcoin outputs; they remain separate from the October MEV analysis.

A four-asset, sixteen-address historical snapshot ledger reconciles all 64 accounts exactly. At the common closing reference, balances total USD 2,646,601,359.14, including USD 2,026,000,811.99 of blacklisted stablecoins. This corroborates the order of magnitude of the professor's approximate USD 2 billion *frozen stablecoin* statement, not an assertion of USD 2 billion in unrecoverable trading losses. Full-incident stolen inventory, recovery, ultimate control and causal MEV losses remain unresolved. Missing quantities are not zero-filled.

## 1. Research question and interpretation

The central question is how much observed loss can be assigned to abnormal execution, identifiable arbitrage and MEV auction redistribution. A complete answer requires both a balance sheet and a counterfactual economic analysis. This study provides reproducible transaction-level evidence and a bounded accounting reconciliation; it does not claim complete coverage of the incident.

The professor's primary document, pages 8–10, discusses approximately USD 2 billion frozen stablecoins and asks how much of the remaining stolen value was lost to MEV. Its other approximate USD 6.3 billion / USD 4–4.3 billion background numbers have varying definitions and no common valuation date established here. We retain their source context and do not insert them into a synthetic final balance sheet. The provisional “Transaction / Gas Fee / Auction Bid / Auction Result” taxonomy is not presented as a verified verbatim quotation from the professor.

A reference-value shortfall is a comparison with an independent market mark. It can reflect market impact, pool fees, inventory conversion, timing and additional mechanisms. It is not automatically the amount captured by a searcher. Builder and proposer payments are transfers within a value-distribution system and cannot be added repeatedly as separate victim losses.

## 2. Data and provenance

### 2.1 Address attribution and sample

We retain sixteen historical “Binance Hot Wallet Exploiter” address leads. Fifteen have independent source corroboration. Wallet 13 remains an unverified lead; wallet 9's additional source is an Arbitrum freeze association rather than proof of Ethereum control. Fresh attempts to read all sixteen Etherscan numbered-label pages returned HTTP 403. Exact numbered labels therefore remain unverified. Address-level incident association is distinct from beneficial ownership or a shared control cluster. No recipient is treated as hacker-controlled merely because it received funds.

The Ethereum block interval is 26,300,640–26,303,950; actual transfer observations span 29 October 2026 20:24:23 to 30 October 07:02:47 UTC. The selected 1,640 transactions were checked against cached receipts, block hashes and within-block positions. Archive imports comprise 151 historical pagination objects and 1,207 selected blocks. The 57,042 transfer edges contain intermediate routing legs, unrelated logs and possibly spam assets; they are neither 57,042 hacker transactions nor independently additive stolen value.

### 2.2 Immutable evidence

Original cached bytes are archived under SHA-256 content addresses in `data/raw/objects/`, with source methods and original-cache provenance in `manifest.json`. Fresh public RPC and HTTP responses preserve request/URL, acquisition timestamp, response bytes and hashes. Legacy acquisition timestamps that cannot be recovered remain null. On-chain numbers refer to original hashes, event locations and calculation inputs. Header/receipt agreement and successful trace-tree validation are stronger than trusting explorer summaries, but are not cryptographic receipt Merkle inclusion proofs or universal independent canonical-chain verification.

Primary independent incident sources include [PublicAML](https://publicaml.org/binance-hack/), [Bitquery](https://bitquery.io/investigations/binance-hack-who-profited), and source-specific Arkham/Stalkchain/ZachXBT observations retained in the address registry. Their aggregate profit/loss conclusions are not imported as our calculations.

### 2.3 Source delegation and complete raw sweep inventory

The 50 EIP-7702 authorization signatures in transaction `0xad99264d5532ae0dd04b2004eebda05f25657e70dacb764f7ac8d4ccd051298b` independently recover to the exchange source address. Historical code changes from empty to the observed delegation indicator. This authenticates signing/delegation capability, not how it was obtained or ultimate actor identity; evidence and EIP specification are retained in `incident_delegation.json`.

Beyond the four-asset USD snapshot, [the expanded initial-sweep inventory](initial_asset_inventory.md) covers all 64 assets appearing in three observed source-to-lead sweeps. Historical balances for every asset at every one of the sixteen leads yield 1,024/1,024 exact raw-unit reconciliations. Other source addresses/chains and exclusive stolen-unit provenance remain outside this raw inventory; no ticker-only USD values are invented.

## 3. Methods

### 3.1 Swaps, states and reference prices

Integer raw quantities are decoded with historical token-decimal checks. V2/V3 event compatibility alone does not authenticate a factory or an implementation; selected reconstruction cases additionally query historical token0/token1/factory/fee metadata. V2 reserve updates and selected exact constant-product quotes are checked. V3 reconstruction uses the parent slot0/liquidity and ordered Mint/Burn/Swap updates, not a full tick bitmap or a replayed EVM counterfactual.

For a buy, effective ETH price is reference USD input divided by ETH output. Direction-aware adverse execution comparisons use the independent market reference. Input/output values within a trade use the same prior completed minute. No forward candle or silent stablecoin dollar parity is used. WETH/native ETH parity is an explicit wrapper redemption assumption. Coinbase assets are matched to exact Ethereum contracts; decimals of observed mapped assets are crosschecked historically. Unknown identity, missing prices, conflicting bars and mixed position/debt flows prevent complete simple-exchange valuation.

### 3.2 Arbitrage accounting

A stated sender/executor boundary is used for every selected case. ERC20 flows, WETH wrapping/unwrapping and successful native CALL/CREATE/SELFDESTRUCT transfers are reconciled; reverted ancestors are excluded and trace-tree completeness checked. Non-WETH residual inventory must close for the selected atomic arbitrage interpretation. Gross cashflow already embeds pool trading fees. We partition it into gas, identified direct fee-recipient payments and retained net profit. Unobserved payments are not assumed absent.

### 3.3 Auctions

Delivered payload reports are deduplicated by block and compared with proposer receipts. Relay-specific keys for the same payload are not automatically builder brands or distinct wins. Whole-block priority fees, base-fee burn, fee-recipient native receipts, other outflows, own gas and proposer payments are separately identified. A builder margin proxy is conditional on an explicit accounting boundary, not exact realized profit.

Historical submission responses cover only queried relays/slots and retained records. Non-delivered submissions can include revisions and late bids; no selection cutoff or complete valid losing-bid book is established. Relay-declared millisecond timestamps are not a validator's auction decision time.

### 3.4 Anomaly hypotheses

The preregistered screen is input reference value > USD 100,000 and loss rate = 1 − output value / input value > 5%. We prioritize losses above USD 1 million and explicitly inspect those above USD 5 million. Native ETH and WETH are combined without counting gas as an output loss. We inspect same-block shared-pool ordering, V2 mechanical effects, major ETH/USDT pool states, route bounds, repeated behavior and subsequent incoming transfers. ABI decoding does not authenticate deployed contract semantics, unknown V4 commands or recipient aliases. Economic shortfall alone cannot identify intent.

### 3.5 Cross-chain and balance reconciliation

THOR memo candidates become verified conversions only after source receipt/Deposit-event, THORNode/Midgard inbound/outbound and confirmed Bitcoin vout/OUT-memo matching. THORChain represents all assets in 1e8 units; Ethereum wei remains 1e18. Address funding links must precede the deposit and retain exact hashes. Flow association does not establish exclusive stolen-unit provenance or common control.

The snapshot ledger is: opening + observed inflows − observed outflows − gas + WETH mint/burn = closing. Internal transfers cancel when summing the stated sixteen-address boundary. Each asset ledger is checked in raw units before all entries are marked at one closing reference. Blacklist state is an observed token-contract restriction, not evidence of legal seizure or Binance recovery.

## 4. Results

### 4.1 Three reconstructed atomic arbitrage cases

| Case | Block | Pool route | Gross after pool fees (ETH) | Gas (ETH) | Direct builder transfer (ETH) | Retained net (ETH) |
|---|---:|---|---:|---:|---:|---:|
| [A1](case_studies/A1_arbitrage.md) | 26,300,992 | 14 aggregated pool legs | 12.137824203978034597 | 1.139064297617240792 | 8.25294761186085674 | 2.745812294499937065 |
| [A2](case_studies/A2_arbitrage.md) | 26,302,300 | SHIB/WETH, two V2 pools | 0.002866070181226265 | 0.000972496905296097 | 0.001828100586247377 | 0.000065472689682791 |
| [A3](case_studies/A3_arbitrage.md) | 26,302,437 | AXS/WETH, two V2 pools | 0.007001958297245002 | 0.002419126290265662 | 0.002398332464181997 | 0.002184499542797343 |

Selected gross profit totals 12.147692232456505864 ETH, partitioned into 1.142455920812802551 ETH gas, 8.257174044911286114 ETH direct builder transfers and 2.748062266732417199 ETH retained net. These three observed cases are not an event-wide MEV estimate or a proven causal lower bound on victim losses.

Figure 2 contains 210 observed ETH/USDT executable prices around the selected event. UTC and explicitly ordinal within-block coordinates are available; no invented sub-block timestamps are used. Figure 3 connects real swap paths, state changes and profit accounting. A separate sandwich case at block 26,301,609 uses front/target/back indices 9/10/11. Its total net is 12.080033775421395622 ETH, rather than the back leg's approximately 567.68 ETH proceeds. No counterfactual incremental victim loss is claimed.

### 4.2 Matched proposer payments and auction limits

| Case | Block | Delivered / on-chain proposer payment (ETH) | Match |
|---|---:|---:|---|
| A1 | 26,300,992 | 36.437514095553389525 | Exact |
| A2 | 26,302,300 | 3.120166160586952436 | Exact |
| A3 | 26,302,437 | 0.57880235116571812 | Exact |

All three proposer payouts pass through a forwarding contract via SELFDESTRUCT, so restricting accounting to ordinary CALLs would miss them. In A3, the proposer payer differs from the fee recipient; builder margin is left null rather than assigning a shared owner. Whole-block receipts have other transaction sources and must not be charged entirely to the selected arbitrage.

Across 3,311 window blocks, 2,939 have consistent retained relay-delivery support. Baseline coverage is 109/130 and event coverage 2,830/3,181. These are descriptive coverage and activity comparisons, not causal attack effects. The three selected slots yield 7,958 retained submission observations from four relays. Figure 5 labels non-delivered records with their revision/late-bid limits. Figure 4 separates selected searcher accounting from whole-block redistribution.

### 4.3 Abnormal execution and intent

The screen finds 241 qualifying observations among 621 complete trade-time valuations out of 810 two-sided wallet/swap rows. Five qualifying cases exceed USD 1 million, two exceed USD 5 million. Their estimated shortfalls are approximately USD 8.374M, 6.047M, 4.279M, 3.257M and 2.001M. Full addresses, input/output values, time, route evidence, neighboring transactions and sensitivity scenarios appear in the five [documented investigations](milestone45_report.md) and Figure 6.

All five contain zero intermediate minimum-output fields together with nonzero final unwrap bounds. N3/N4 have unsupported root selectors but successful internal execute calls. It would be incorrect to infer “no slippage protection” from only their entry-point selectors. Shared pools, repeated shortfalls and later incoming transfers do not establish coordinated compensating profits. All five classifications remain **insufficient evidence** for intent and counterfactual MEV loss.

### 4.4 Matched THORChain conversions

| Case | Deposit UTC, 17 Nov 2026 | Input ETH | Confirmed BTC output | Same-deposit-time reference shortfall USD | Inclusion timestamp difference |
|---|---|---:|---:|---:|---:|
| [T1](case_studies/T1_thorchain.md) | 2026-11-17T13:39:47+00:00 | 36 | 1.00484202 | 316.17 | 2899 seconds |
| [T2](case_studies/T2_thorchain.md) | 2026-11-17T14:53:47+00:00 | 61 | 1.68897154 | 754.33 | 1511 seconds |
| [T3](case_studies/T3_thorchain.md) | 2026-11-17T14:56:35+00:00 | 40 | 1.10797406 | 429.72 | 1296 seconds |

Every path has three verified chronologically prior ordinary ETH transfers linking a wallet-12 source to its depositor. Initially discovered transfer links that occurred after deposits were rejected. Other sources/intervening spending are not exhausted, so the paths prove a transfer association rather than exclusive taint or common ownership. The bounded discovery yields 441 explicit memo candidates, not 441 authenticated incident conversions.

Ethereum receipts, THORNode, Midgard and confirmed Bitcoin outputs agree on these three inbound/outbound paths. Protocol network deductions are already embedded in final output; actual Bitcoin mining fee and protocol user charge are different quantities. Ethereum gas is separate. Reported liquidity fees remain in RUNE without invented historical USD conversion. Streaming and market movement prevent assigning the entire reference difference to mechanical price impact. The coarse cross-chain block timestamp differences are not precise service latency. Figure 7 uses common deposit-time USD units within each path, with native quantities shown. November cross-chain costs are not added to October Ethereum MEV.

### 4.5 Snapshot accounting and the USD 2 billion statement

At the closing block on 2026-10-30T07:02:47+00:00, the four-asset ledger totals USD 2,646,601,359.14; blacklisted stablecoin balances account for USD 2,026,000,811.99, and other address-lead balances for USD 620,600,547.15. All 64 raw-unit accounts reconcile exactly. A 668.132228390272982085 WETH initial residual is explained by actual Withdrawal burn logs, not forced balancing. Figure 8 keeps this snapshot distinct from trading losses and profit distributions.

USDT and USDC blacklist status is read at the same historical closing block. All snapshot entries use the same valuation reference, with ETH/WETH parity explicit. Missing Coinbase USDC candles are replaced only in this documented snapshot by observed Binance USDCUSDT multiplied by contemporaneous Coinbase USDT/USD. Stablecoins are not assumed to equal one dollar.

The resulting approximately USD 2.026 billion blacklisted balance supports the professor's approximate frozen-stablecoin scale within this limited scope. It does not establish full-incident seizure, recovery, final hacker control or unrecoverable economic loss. External inflows in the snapshot ledger include DEX and wrapper conversion proceeds; adding them as a theft total would double-count recycled assets.

## 5. Robustness and identification limits

**Price and timing.** Five large cases retain their screening status under the documented independent ETH feed and time-window alternatives. At transaction-time references, the 621 complete, unique, non-mixed exchanges have signed net reference shortfall of USD 43,727,932.59. This is a bounded sample result, not the whole incident. Fixed-closing-mark coverage is 315 transactions, so its total cannot be directly compared with the 621-row total as pure price sensitivity. In the identical 293-transaction intersection, the trade-time figure is USD 38,207,162.89, versus USD 49,801,599.88 at the closing mark. Subsequent market movements are part of that difference. These scenario outcomes are not statistical confidence intervals.

**Address boundary.** We report the sixteen-lead set, exclude wallet 13, and additionally exclude wallet 9. These exclusions do not change the 621-row trade-time shortfall sample, because those addresses contribute no complete rows to it. They do not prove address ownership. The accounting never expands control to unknown recipients.

**Missing auction data.** Removing Ultrasound leaves 3,129 submission records and relay-delivery support for only one of the three selected outcomes. Independent on-chain proposer payment matches remain three. This illustrates reliance on retained relay evidence; it cannot recover unseen eligible losing bids or decision cutoffs.

**Causal limitations.** We have not executed a full counterfactual no-MEV replay over all pools, routes and blocks. Mechanical pool effects are reconstructed locally, not a complete causal decomposition. We do not infer that estimated execution shortfall minus selected searcher profit is unexplained theft, or that proposer receipts are incremental losses caused by the selected transaction. Unknown auction payments, beneficial control, other chains, other tokens and legal recovery prevent a full incident reconciliation.

## 6. Reproducibility and validation

Python 3.11+, Web3.py, pandas, DuckDB/Parquet, NetworkX, Plotly, Matplotlib and pytest form the pipeline. Dedicated figure scripts generate self-contained HTML and presentation-ready PNG/SVG files. The processed data and report support tables populate a rebuildable DuckDB query layer. Raw bytes remain authoritative; derived files can be regenerated.

The full test suite currently passes 52 tests, covering integer decimals, contract-aware valuation, missing/conflicting prices, direction-aware execution, V2 mechanics, multihop inventory, gas/auction cashflows, failed ancestors, wallet boundaries, route guards, cross-chain mismatch rejection, historical blacklist calls, WETH burns and exact balance reconciliation. M1–M3 archive replay was verified previously. M4 screening and the balance ledger also run with a nonexistent original legacy directory; THOR conversion matching runs offline from this repository's cached public responses. Missing historical observations remain explicit.

Static versions of all eight figures have been visually checked and repaired where needed. The original October Figure 1 HTML filters were tested in Chrome. Its later THORChain companion adds ten transaction edges, including three confirmed Bitcoin outputs; chain/token/time filters and edge-click links were exercised by executing the actual generated HTML logic in Node (not a browser-render test); this does not imply browser testing of every other HTML figure. PNG/SVG renders and self-contained HTML exports do not prove PowerPoint/Google Slides application behavior.

See [README](../README.md) for environment setup and stage commands, [progress](../docs/progress.md), [validation](validation.json), and the per-stage reports for detailed methods. Raw evidence must accompany a repository transfer; code alone is not an evidence handoff.

## 7. Conclusion

Identifiable transaction profits and proposer payments can be reconstructed precisely within stated accounting boundaries. Large reference-price shortfalls can also be measured, but neither their magnitude nor permissive intermediate route parameters identifies deliberate self-loss or the causal MEV share. The frozen-stablecoin snapshot and the execution/auction results answer different economic questions. This distinction is essential to avoid overstating the incident's loss or double-counting value transferred among searchers, builders and proposers.

The strongest supported conclusion is a set of reproducible observed cases and bounded sample valuations, with full-incident quantities left unresolved. Additional complete multi-chain inventory, recovery records, historical eligible auction books and pool-level counterfactual execution would be required to answer the professor's whole-incident “exact MEV loss” question.

## Figure and evidence index

| Figure | Research output | Interpretation and principal limit |
|---|---|---|
| [01](figures/fig01_stolen_fund_flow.html) | Verified transfer network | October core plus separately dated November THOR/BTC companions; real hash/event edges; unknown recipients are not hacker clusters; USD coverage is partial |
| [02](figures/fig02_eth_price_dislocation.html) | ETH executable dislocation | 210 observed ETH/USDT trade-size prices; not a full market price surface |
| [03](figures/fig03_transaction_reconstruction.html) | Three arbitrages and sandwich | Inventory and order reconstructed; full victim counterfactual unresolved |
| [04](figures/fig04_mev_value_attribution.html) | Searcher and whole-block redistribution | Accounting boundaries separate; builder margin partial/conditional |
| [05](figures/fig05_auction_results.html) | Relay outcomes and visible competition | Revisions/late bids may appear; no full eligible losing book |
| [06](figures/fig06_suspicious_wallets.html) | Five investigated large anomalies | Estimated shortfalls; insufficient evidence of intent/causal loss |
| [07](figures/fig07_thorchain_flows.html) | Three confirmed ETH-to-BTC paths | Transfer association, not exclusive stolen-unit or control attribution |
| [08](figures/fig08_loss_reconciliation.html) | Snapshot ledger and separate profit partition | Four assets/sixteen leads; whole-incident totals unresolved |

Each figure has matching PNG/SVG, an independent script in `src/visualization/`, and a support dataset in `data/processed/` or `reports/tables/`. Details and source pointers: [M1](milestone1_report.md), [M2/M3](milestone23_report.md), [M4/M5](milestone45_report.md), [M6](milestone6_report.md).
