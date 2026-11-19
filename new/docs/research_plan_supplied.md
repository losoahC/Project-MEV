# Group 12 Research Plan
## Binance Hack × DEX Arbitrage × MEV Auction

### Research Objective

Build a reproducible on-chain forensic research system to investigate how much value was lost during the October 2026 Binance hack through abnormal DEX execution, arbitrage, and MEV, and how the extracted value was distributed among Searchers, Builders, Proposers, and other participants.

**Main Research Question**

*How much of the hacker's lost value can be attributed to MEV and DEX arbitrage, who captured it, and how was it redistributed through block auctions?*

This is an academic research and forensic analysis project, not a live trading system.

### Research Priorities

| Priority | Research Area |
|---|---|
| P0 | DEX Arbitrage Reconstruction and Profit Attribution |
| P0 | MEV Auction Results and Builder/Proposer Payments |
| P0 | Suspicious Wallets and Economically Irrational Transactions |
| P0 | Binance Loss Reconciliation |
| P1 | THORChain Cross-Chain Fund Flows |
| P1 | Sandwich Attack Reconstruction |

The professor specifically recommended emphasizing DEX Arbitrage over Sandwich Attacks and closely investigating Auction Results.

---

## 1. Technical Architecture

Use Python 3.11+, Web3.py, pandas/Polars, DuckDB, Parquet, Plotly, NetworkX, and pytest.

Before implementation, inspect the repository, available credentials, and `Advanced Blockchain Marching Orders.pdf`, particularly Group 12 on pages 8–10.

Suggested repository structure:

```text
binance-mev-research/
├── src/
│   ├── ingestion/
│   ├── decoding/
│   ├── graph/
│   ├── arbitrage/
│   ├── auction/
│   ├── anomaly/
│   ├── thorchain/
│   ├── reconciliation/
│   └── visualization/
├── data/
│   ├── raw/
│   ├── processed/
│   └── fixtures/
├── notebooks/
├── reports/
│   ├── figures/
│   ├── tables/
│   └── case_studies/
├── docs/
├── tests/
└── README.md
```

All quantitative claims must be traceable to original transactions, source datasets, timestamps, and calculation methods.

Use immutable raw data, reproducible pipelines, and explicit confidence levels. Never invent missing observations.

---

## 2. Phase 1 — Hacker Wallet Identification and Fund Flow

### Tasks

1. Identify Etherscan-labeled Binance Hot Wallet Exploiter 1–16 wallets.
2. Verify wallet identities against independent sources.
3. Collect transactions, token transfers, decoded DEX events, receipts, and available execution traces.
4. Build a directed fund-flow graph.
5. Identify recipients, exchanges, DEX protocols, cross-chain bridges, and THORChain-related transactions.
6. Track assets through verified wallet relationships without assuming that every recipient is controlled by the hacker.
7. Preserve block timestamps, transaction indices, token amounts, and original transaction hashes.

### Required Figure 1: Stolen Fund Flow Network

Create an interactive directed network or Sankey diagram:

**Binance Hot Wallets → Hacker Wallets → DEX / THORChain → Other Wallets**

Design requirements:

- Node size represents transferred USD value.
- Edge width represents transfer amount.
- Node colors distinguish verified hackers, liquidity pools, exchanges, THORChain, unidentified addresses, and other entities.
- Hover details display addresses, amounts, timestamps, and supporting transaction hashes.
- Use labeled wallet clusters where ownership is verified.
- Allow filtering by chain, token, time range, and transfer size.

Export:

- `fig01_stolen_fund_flow.html`
- `fig01_stolen_fund_flow.png`
- `wallet_edges.parquet`

Acceptance: Every displayed edge must map to a verified transaction. Avoid double-counting intermediary transfers as new losses.

---

## 3. Phase 2 — DEX Arbitrage Reconstruction [P0]

### Research Questions

- Which pools became mispriced?
- How large were the DEX/CEX price differences?
- Which Searchers captured the arbitrage?
- What were their realized profits after execution costs?
- How much execution loss was attributable to arbitrage-related mechanisms rather than ordinary market impact?

### Implementation

Reconstruct major hacker-related swaps and contemporaneous DEX pool states.

Use reference prices from independent liquid markets.

Calculate:

`Execution Price = USD input value / output token quantity`

`Price Dislocation = DEX executable price / reference price - 1`

`Execution Loss = actual traded quantity × adverse execution price difference`

Use direction-aware formulas for buys and sells.

For identified arbitrage transactions, reconstruct all observable swap legs and inventory changes.

Calculate gross and net PnL after pool fees, gas, and identifiable builder payments.

Separate:

- Mechanical AMM price impact
- DEX trading and liquidity fees
- Arbitrageurs' realized profits
- Sandwich-induced additional losses
- Auction payments

Do not equate total execution loss with MEV profit.

### Required Figure 2: ETH Price Dislocation

Create a synchronized time-series chart comparing:

- External ETH reference price
- DEX ETH executable price
- Hacker swap timestamps
- Arbitrage transaction timestamps
- Major price-convergence periods

Include a second panel for the percentage price deviation.

Enable zooming into individual blocks and short event windows.

Export:

- `fig02_eth_price_dislocation.html`
- `fig02_eth_price_dislocation.png`

### Required Figure 3: Transaction-Level MEV Reconstruction

Select representative arbitrage blocks and reconstruct:

1. Pre-trade liquidity pool state
2. Hacker transaction
3. Arbitrage transactions
4. Post-trade pool state
5. Actual arbitrage PnL

Use a transaction sequence diagram with token flows, effective prices, and wallet addresses.

Additionally reconstruct at least one identifiable Sandwich case to illustrate the alternative MEV mechanism.

Export:

- `fig03_transaction_reconstruction.html`
- `fig03_transaction_reconstruction.png`
- Detailed transaction-level case-study tables

Acceptance: Reproduce at least three actual arbitrage cases with verifiable transaction paths, plus one Sandwich case if supported by observable data.

---

## 4. Phase 3 — MEV Auction Analysis [P0]

### Research Objective

Determine how arbitrage-generated value moves through the MEV auction structure.

Provisionally organize analysis into:

1. Transaction
2. Gas Fee
3. Auction Bid
4. Auction Result

The professor's exact four terms remain unverified.

### Tasks

Collect available Ethereum and MEV-Boost relay data:

- Block and slot numbers
- Builder identity
- Relay identity
- Submitted bids
- Winning/delivered payload
- Proposer identity
- Proposer payment
- Priority fees and direct transfers
- Searcher-related payments where identifiable

Investigate both winning and observable losing bids.

Reconstruct auction outcomes for arbitrage-related blocks.

Calculate:

`Searcher Net Profit = Arbitrage Gross Profit - Execution Costs - Identified Auction Payments`

`Builder Margin Proxy = Identifiable Receipts - Proposer Payment - Identifiable Costs`

Do not interpret a partial builder margin estimate as exact realized profit.

### Required Figure 4: MEV Value Attribution

Create a value-distribution diagram identifying:

- Hacker execution loss
- Arbitrage profit
- Searcher-retained earnings
- Builder-retained earnings
- Proposer payments
- Liquidity provider value capture
- Other identifiable costs

Use a waterfall or flow-based visualization as appropriate.

**Important:** Clearly separate economic losses from internal transfers among MEV participants. Do not double-count Searcher payments to Builder and Builder payments to Proposer.

Export:

- `fig04_mev_value_attribution.html`
- `fig04_mev_value_attribution.png`

### Required Figure 5: Auction Results and Competition

Create:

- Builder bid distribution by slot
- Winning bid versus other observable bids
- Builder identity and auction win frequency
- Proposer payments over the event period
- Auction payments versus arbitrage opportunity size
- Event-period versus baseline auction activity

Use scatterplots, bid distributions, and a time-series visualization.

Export:

- `fig05_auction_results.html`
- `fig05_auction_results.png`

Acceptance: Reconstruct at least three auction outcomes connected to identifiable arbitrage activity, subject to historical relay data coverage.

---

## 5. Phase 4 — Economically Irrational Transaction Detection [P0]

### Research Objective

Investigate the professor's observation that some wallets appeared to intentionally lose millions of dollars in transactions.

Treat this as a hypothesis, not a confirmed finding.

### Tasks

For each swap, calculate:

`Loss Rate = 1 - Output Reference Value / Input Reference Value`

Initial screening conditions:

- Input value greater than $100,000
- Loss rate greater than 5%
- Large-loss priority queue above $1 million
- Explicit investigation of transactions approaching or exceeding $5 million in losses

For suspicious transactions, examine:

- Execution price relative to the reference market
- Liquidity and expected AMM price impact
- User slippage parameters
- Adjacent profitable transactions
- Same-block execution ordering
- Repeated losing behavior
- Wallet relationships
- Compensating flows or profits, if observable

Classify anomalies into ordinary slippage, urgent liquidation, identifiable MEV-related loss, suspicious unexplained behavior, or insufficient evidence.

### Required Figure 6: Suspicious Wallet Leaderboard

Produce a ranked horizontal bar chart showing the largest abnormal transaction losses.

Include:

- Wallet/address
- Transaction hash
- USD input value
- USD output reference value
- Absolute loss
- Loss percentage
- Transaction timestamp
- Associated MEV activity
- Confidence classification

Add an interactive detail view for the highest-ranked cases.

Export:

- `fig06_suspicious_wallets.html`
- `fig06_suspicious_wallets.png`
- `suspicious_transactions.parquet`

Acceptance: Investigate the largest observable anomalies, with a target of at least five fully documented examples if qualifying cases are available.

---

## 6. Phase 5 — THORChain Cross-Chain Analysis [P1]

### Research Objective

Determine how the hacker used THORChain and assess the economic costs of cross-chain asset conversion.

### Tasks

1. Identify verified hacker-associated THORChain deposits.
2. Query THORNode and Midgard APIs.
3. Match inbound and outbound transactions.
4. Reconstruct asset conversions and execution rates.
5. Measure liquidity fees, network fees, price impact, and delays.
6. Check repeated swap patterns and unusual execution prices.
7. Investigate cross-chain arbitrage relationships when verifiable.
8. Keep THORChain trading losses separate from Ethereum MEV unless linked by specific evidence.

### Required Figure 7: THORChain Cross-Chain Flow

Create a Sankey diagram showing:

- Origin blockchain
- Input asset and amount
- THORChain swap
- Output asset
- Destination blockchain
- Receiving wallet
- Estimated execution cost

Export:

- `fig07_thorchain_flows.html`
- `fig07_thorchain_flows.png`

Acceptance: Reconstruct at least three complete inbound-to-outbound asset conversion paths if data availability permits.

---

## 7. Phase 6 — Final Binance Loss Reconciliation [P0]

### Research Objective

Determine how much stolen value was actually lost through market execution, how much remained held by the attacker, and how much can reasonably be attributed to MEV.

Independently verify the professor's approximate $2 billion unrecoverable-loss reference, including its valuation date and definition.

### Tasks

Construct separate reconciliations for:

**Asset accounting:**

- Initial stolen assets
- Frozen/seized assets
- Assets still controlled by hacker-linked wallets
- Assets deposited to third-party services
- Assets converted or transferred across chains
- Unresolved/untraced balances

**Economic loss attribution:**

- Total adverse execution losses
- Ordinary price impact and trading fees
- Realized DEX arbitrage profits
- Sandwich-specific incremental losses
- Searcher/Builder/Proposer value transfers
- THORChain execution losses
- Unexplained or uncertain losses

Keep these two accounting views distinct.

### Required Figure 8: Final Loss Reconciliation

Generate a research-quality reconciliation waterfall and an accompanying attribution chart.

The figures must clearly communicate:

- What was stolen
- What was frozen or seized
- What was not recovered
- What was economically lost through trading
- What portion was MEV-attributable
- What remains uncertain

Display confidence ranges where appropriate.

Export:

- `fig08_loss_reconciliation.html`
- `fig08_loss_reconciliation.png`

Acceptance: All reported totals must have consistent valuation timestamps and definitions, with no double-counting between asset flows and economic losses.

---

## 8. Visualization and Presentation Standards

All eight figures are mandatory research outputs, subject to available data.

### Design Requirements

- Professional institutional research aesthetic
- Consistent typography, labeling, units, and color meanings
- Prefer dark analytical dashboards for interactive visualizations
- Ensure readability in light-background presentations
- Display meaningful axes, legends, and data provenance
- Support interactive HTML charts where useful
- Export presentation-ready PNG and preferably SVG versions
- Do not insert stock images or invented numerical charts into final results
- Label illustrative or incomplete findings explicitly
- Include exact time windows and time zones
- Provide source transaction hashes or links when relevant

### Deliverable Quality

Each figure must be reproducible from a dedicated Python script or notebook.

For each figure produce:

- Chart image
- Interactive version where useful
- Supporting dataset
- Chart generation script
- Short written interpretation
- Data limitations

Use systematic filenames `fig01` through `fig08`.

---

## 9. Research Validation

Implement tests for:

- Token decimal handling
- USD valuation
- Swap reconstruction
- Multi-hop routing
- DEX price impact
- Arbitrage PnL
- Gas and auction payment attribution
- Wallet clustering consistency
- Cross-chain matching
- Balance reconciliation

Perform sensitivity checks for external price feeds, timing windows, wallet attribution assumptions, and missing auction data.

Distinguish observed results, estimated results, and unresolved cases throughout the research.

---

## 10. Final Deliverables

1. Reproducible Python research repository
2. Processed on-chain forensic datasets
3. Eight research figures with generation scripts
4. Three or more documented DEX arbitrage case studies, if supported by data
5. Auction analysis and value distribution
6. Suspicious wallet transaction report
7. THORChain cross-chain transaction report
8. Final Binance loss reconciliation
9. Written academic research report
10. Presentation-ready results for a 12–15-slide final presentation

## 11. Execution Milestones

**Milestone 1 — Data and Wallets**

Complete verified hacker-wallet identification, one real swap reconstruction, and Figure 1.

**Milestone 2 — DEX Arbitrage**

Reconstruct an actual arbitrage opportunity and produce Figures 2 and 3.

**Milestone 3 — Auction Analysis**

Match auction results and builder/proposer payments, producing Figures 4 and 5.

**Milestone 4 — Suspicious Transactions**

Build the anomaly detector and Figure 6.

**Milestone 5 — THORChain**

Reconstruct cross-chain paths and Figure 7.

**Milestone 6 — Reconciliation and Reporting**

Produce Figure 8, complete robustness checks, and assemble the final research outputs.

After each milestone, update `docs/progress.md` with verified findings, coverage, limitations, and next tasks.

**Begin with Milestone 1. Build and validate the research pipeline incrementally, prioritizing DEX arbitrage and auction results over broad but unverifiable data collection.**