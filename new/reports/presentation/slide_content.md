# Group12 · 14-slide research presentation content

English slides; UTC throughout. Compact body text below is presentation-ready. Companion notes provide exact amounts and source paths; the Canva design may summarize/round the body text.

## Slide 1 — Binance Incident, DEX Arbitrage and MEV Auctions

Group12 · FT565. Evidence from Ethereum execution, relay records and matched cross-chain conversions. Research snapshot18Nov2026.

[Exact source notes](presenter_notes.md#slide-1)

## Slide 2 — Research scope

Ethereum blocks26,300,640–26,303,950. Transfer observations29Oct20:24:23–30Oct07:02:47UTC. Observed transactions; estimated reference shortfalls; unresolved intent, causal MEV and ownership. November THOR paths are separate.

[Exact source notes](presenter_notes.md#slide-2)

## Slide 3 — Wallets and data

16 historical address leads,15 independently source-corroborated.1,640 transactions;57,042 core transfer edges;1,155 compatible Swap events. Wallet13 unverified;wallet9 source concerns Arbitrum. All16 fresh numbered-label pages returned403. Receiving funds does not prove common control.

[Exact source notes](presenter_notes.md#slide-3)

## Slide 4 — Measuring dislocation

Execution price=input reference USD/output ETH quantity. N1:USD29,961,300 input,9,551.900920ETH output,USD3,136.68 effective price versusUSD2,260 reference. Estimated shortfallUSD8,374,003.92,gas excluded.210 observed price points in Figure2; no full no-MEV counterfactual.

[Exact source notes](presenter_notes.md#slide-4)

## Slide 5 — Actual arbitrage A1

A1,block26,300,992:14 aggregated pool legs; non-WETH inventory closes.12.137824ETH gross after pool fees−1.139064ETHgas−8.252948ETHbuilder=2.745812ETH retained net. The target’sUSD8.374M shortfall is a different quantity.

[Exact source notes](presenter_notes.md#slide-5)

## Slide 6 — Three arbitrage cases

A1/A2/A3 retained net:2.745812,0.000065,0.002184ETH. Selected total gross12.147692ETH; net2.748062ETH. Display rounded to6decimals; exact amounts below. These are selected cases, not event-wide MEV.

[Exact source notes](presenter_notes.md#slide-6)

## Slide 7 — A complete sandwich episode

Block26,301,609; indices9/10/11. Front≈−555.599628ETH; back≈+567.679662ETH. Full episode net12.080033775421395622ETH. Back-leg proceeds are not episode profit. No causal incremental victim loss established.

[Exact source notes](presenter_notes.md#slide-7)

## Slide 8 — Auction results and proposer payments

A1/A2/A3 proposer payments36.437514095553389525,3.120166160586952436,0.578802351165718120ETH. All3 exactly reconcile. SELFDESTRUCT forwarding matters; A3 payer differs from fee recipient. Whole-block payments are not solely one searcher’s cost.

[Exact source notes](presenter_notes.md#slide-8)

## Slide 9 — Auction coverage and sensitivity

2,939 delivered blocks/3,311; baseline109/130,event2,830/3,181.7,958 retained submissions;3slots,4relays. Revisions/late bids may appear. Drop Ultrasound:3,129 records,1/3retained relay outcome support,3/3independent onchain payments. No decision cutoff known.

[Exact source notes](presenter_notes.md#slide-9)

## Slide 10 — Largest abnormal swaps

N1–N5 shortfalls≈USD8.374M,6.047M,4.279M,3.257M,2.001M.810two-sided rows;621complete valuations;241qualify(input>USD100k and loss>5%).Five aboveUSD1M,two aboveUSD5M. No deliberate loss proven.

[Exact source notes](presenter_notes.md#slide-10)

## Slide 11 — Slippage protection and intent

All5 have zero intermediate minima AND nonzero final unwrap minima. Zero-bound counts18/17/17/16/16. N3/N4 internal execute calls decoded despite unsupported root selector. Classification:insufficient_evidence. Adjacent profits and later incoming transfers are not compensating-profit proof.

[Exact source notes](presenter_notes.md#slide-11)

## Slide 12 — Three matched THORChain paths

17Nov2026:T1 36ETH→1.00484202BTC;T2 61ETH→1.68897154BTC;T3 40ETH→1.10797406BTC. Estimated deposit-time shortfallsUSD316.17/754.33/429.72. Every path matches ETHreceipt,THORNode,Midgard and confirmed BTCvout/OUTmemo. Prior funding association is not exclusive taint/control.

[Exact source notes](presenter_notes.md#slide-12)

## Slide 13 — Snapshot reconciliation

Fixed closing reference30Oct07:02:47UTC:four-asset balancesUSD2.646601359B,includingUSD2.026000812B blacklisted stablecoins andUSD0.620600547B other lead balances.64/64four-asset accounts reconcile. Wider raw inventory:64assets×16leads=1,024/1,024 ledgers reconcile. Blacklisting is not recovery.

[Exact source notes](presenter_notes.md#slide-13)

## Slide 14 — Conclusions and limits

621unique completely valued swaps showUSD43.728M signed trade-time shortfall in this bounded sample. Selected profits/payments can be reconstructed; causal whole-event MEV remains unresolved. Eight reproducible figures;52tests passed. Price timing comparisons use identical transaction sets.

[Exact source notes](presenter_notes.md#slide-14)

