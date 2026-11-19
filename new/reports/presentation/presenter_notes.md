> 新增研究交付见 [中文完整核验报告](../mev_expansion/完整套利与MEV核验报告.md)。本讲稿与已批准保存的 14 页 Canva 属于扩展前版本；新增 76 项检查、扩大样本和订单／TRON 结果不应被说成已写入旧演示。

# Group12 · Presenter notes and source evidence

Read with the fourteen-slide presentation. These notes are the authoritative companion: exact values, original hashes, source pointers and limits. Never use an unsupported illustrative price chart.

<a id="slide-1"></a>
## Slide 1 — Binance Incident, DEX Arbitrage and MEV Auctions

Group12 · FT565. Evidence from Ethereum execution, relay records and matched cross-chain conversions. Research snapshot18Nov2026.

Source files (paths relative to new/):

- [docs/research_plan_supplied.md](../../docs/research_plan_supplied.md)
<a id="slide-2"></a>
## Slide 2 — Research scope

Ethereum blocks26,300,640–26,303,950. Transfer observations29Oct20:24:23–30Oct07:02:47UTC. Observed transactions; estimated reference shortfalls; unresolved intent, causal MEV and ownership. November THOR paths are separate.

Source files (paths relative to new/):

- [docs/teacher_group12_source.txt](../../docs/teacher_group12_source.txt)
- [data/processed/coverage.json](../../data/processed/coverage.json)
<a id="slide-3"></a>
## Slide 3 — Wallets and data

16 historical address leads,15 independently source-corroborated.1,640 transactions;57,042 core transfer edges;1,155 compatible Swap events. Wallet13 unverified;wallet9 source concerns Arbitrum. All16 fresh numbered-label pages returned403. Receiving funds does not prove common control.

Source files (paths relative to new/):

- [data/processed/wallet_registry.json](../../data/processed/wallet_registry.json)
- [data/fixtures/identity_observations.json](../../data/fixtures/identity_observations.json)
- [data/processed/incident_delegation.json](../../data/processed/incident_delegation.json)
<a id="slide-4"></a>
## Slide 4 — Measuring dislocation

Execution price=input reference USD/output ETH quantity. N1:USD29,961,300 input,9,551.900920ETH output,USD3,136.68 effective price versusUSD2,260 reference. Estimated shortfallUSD8,374,003.92,gas excluded.210 observed price points in Figure2; no full no-MEV counterfactual.

Source files (paths relative to new/):

- [reports/case_studies/N1_abnormal_swap.json](../../reports/case_studies/N1_abnormal_swap.json)
- [reports/tables/fig02_price_observations.parquet](../../reports/tables/fig02_price_observations.parquet)
- [reports/tables/fig02_reference_prices.parquet](../../reports/tables/fig02_reference_prices.parquet)

Exact evidence extract (observations and estimates retain their original field names):

```json
{
  "wallet": 5,
  "address": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
  "identity_confidence": "independently_corroborated",
  "tx_hash": "0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6",
  "block": 26300992,
  "transaction_index": 3,
  "timestamp": 1793308151,
  "timestamp_utc": "2026-10-29T21:09:11+00:00",
  "net_asset_raw": {
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "-30000000000000",
    "native:eth": "9551900920261967562557"
  },
  "position_or_debt_events": [],
  "internal_wallet_transfer": false,
  "swap_event_count": 38,
  "swap_pool_keys": [
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x033c1e568baa6c8c70e7320a885027d9ec01e536391b83a5af9c565c6908ff19",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x06fa6552f739e2af86422bea6118eb8380211a43ce959cb2aad3334c23dfc313",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x17d6b899632fa2aee6257741216c25459a2d95a59f2e87260c59787db234021c",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x20c3a15e34e5d88aeba004b0753af69e4f6bea80eae2263f7a92e919cd33cc56",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x4a24fcf3c1cbebd80d09537c7aa15adf2d228aa1b9ba1b0e5fb82e66dc96c0d2",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x50b00c1a5a8e582ec808e97e71598cd135206a9f9c548eab2ed73659e7ee5fa8",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x54c72c46df32f2cc455e84e41e191b26ed73a29452cdd3d82f511097af9f427e",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x599326d9cd5e1ea0893305c87d5ec3199e7f05e94d72159f35dea381479a615e",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x6423caccdb2b6b9913b9c488ae9b0fba2440e0ddc14d2bc5de45e3ce4df57c2e",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x72331fcb696b0151904c03584b66dc8365bc63f8a144d89a773384e3a579ca73",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x89969a14876a59fa2827753c42fef33444275909789bb0622d08f4c684fa2a81",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x8c0a7616cead6ca4ca70551926ab14136ff77c247a5c1249732dd0fda96ff0ae",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0x98316e8405502774a5d0a0761276b5d26505a8195c1905169864008d5e7a3eea",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0xa8b6a77cdd9c11eba0f47ca0dc5aa08335b3be56864568d632f181258358eab1",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0xc1ea959f4616f7a7234faf5d38008437d2427fe265f7e20907742df8e83396d2",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0xd0a793a72421620eedf704d0d5554faf91d96df0138c0f71082d43cafdc68d8a",
    "0x000000000004444c5dc75cb358380d2e3de08a90:0xdce6394339af00981949f5f3baf27e3610c76326a700af57e4b3e3ae4977f78d",
    "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
    "0x11b815efb8f581194ae79006d24e0d814b7697f6",
    "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
    "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
    "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
    "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
    "0x56534741cd8b152df6d48adf7ac51f75169a83b2",
    "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f",
    "0x7486ff76f69872d27b22dada4078bd55b36a5324",
    "0x769db46f39c42ee7ad5f71f4167c47edd281e767",
    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
    "0x9db9e0e53058c89e5b94e29621a205198648425b",
    "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
    "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
    "0xc5af84701f98fa483ece78af83f11b6c38aca71d",
    "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b",
    "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",
    "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
    "0xe0554a476a092703abdb3ef35c80e0d76d32939f",
    "0xe6ff8b9a37b0fab776134636d9981aa778c4e718"
  ],
  "gas_paid_by_wallet_wei": "2344908665333204016",
  "receipt_evidence": "data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz",
  "trace_evidence": "data/raw/objects/23846b66bf1cab96103c57df38e1e1fe8325a258a58b52f8ec84326165c20365.json.gz",
  "header_evidence": "data/raw/objects/6a75fa8db5db47b4bf91177a263eff0c2f8d0f86e5d1b50030e3978cae00e820.json.gz",
  "input_reference_USD": "29961300.00000",
  "output_reference_USD": "21587296.079792046691378820",
  "assets": [
    {
      "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "raw": "-30000000000000",
      "symbol": "USDT",
      "decimals": 6,
      "identity_basis": "data/raw/objects/2dee1ab79514dae9091c87f629b1dac6ada08856fc292fb5c5b9c78e9cb3af30.json",
      "decimal_basis": "data/raw/public_rpc/dc838e64fe3324a074a2aa7d3c4f5bed164ad0db72c4e105165590fac916f31f.json",
      "quantity": "-30000000",
      "reference_USD": "0.99871",
      "USD": "-29961300.00000",
      "price_evidence": {
        "venue": "Coinbase",
        "symbol": "USDT",
        "quote": "USD",
        "bar_start": 1793308080,
        "stale_minutes": 0,
        "lookback_minutes": 1,
        "field": "close",
        "sources": [
          "data/raw/objects/81f4c7ec30f9e1192457688be32125e9d54faf2ba081b2ad458bdb5bb704c241.json",
          "data/raw/objects/ff27d857b59179d60f72cce1c67d6d024e0012bf8b67d83363c727ee4061e2a6.json"
        ]
      },
      "confidence": "reference_price_estimate_from_contract_matched_market"
    },
    {
      "address": "native:eth",
      "raw": "9551900920261967562557",
      "symbol": "ETH",
      "decimals": 18,
      "identity_basis": "Ethereum native ETH",
      "decimal_basis": "Ethereum wei denomination",
      "quantity": "9551.900920261967562557",
      "reference_USD": "2260",
      "USD": "21587296.079792046691378820",
      "price_evidence": {
        "venue": "Coinbase",
        "symbol": "ETH",
        "quote": "USD",
        "bar_start": 1793308080,
        "stale_minutes": 0,
        "lookback_minutes": 1,
        "field": "close",
        "sources": [
          "data/raw/objects/070745a7dbf6cbc338dd866e7ab7bf414ffb6c5972bbaa0601531273b0580bdd.json",
          "data/raw/objects/1d8aab7d5926e9afab770a83a5f0385df2638dd35cbf906a69faad1960b11665.json"
        ]
      },
      "confidence": "reference_price_estimate_from_contract_matched_market"
    }
  ],
  "missing_assets": [],
  "loss_USD": "8374003.920207953308621180",
  "loss_rate": "0.279494011281484892465319595611672390717358726089989419684726630686919459436005780790553147",
  "qualifies": true,
  "reason": "reference_shortfall_screen_only",
  "valuation_complete": true,
  "sensitivity": {
    "stale_5min": {
      "loss_USD": "8374003.920207953308621180",
      "loss_rate": "0.279494011281484892465319595611672390717358726089989419684726630686919459436005780790553147",
      "qualifies": true,
      "reason": "reference_shortfall_screen_only",
      "valuation_complete": true,
      "input_reference_USD": "29961300.00000",
      "output_reference_USD": "21587296.079792046691378820",
      "missing_contracts": []
    },
    "lookback_5min": {
      "loss_USD": "8495939.94784006457861190048",
      "loss_rate": "0.283552438809847795698352957196495619524405506883604505632040050062578222778473091364205257",
      "qualifies": true,
      "reason": "reference_shortfall_screen_only",
      "valuation_complete": true,
      "input_reference_USD": "29962500.00000",
      "output_reference_USD": "21466560.05215993542138809952",
      "missing_contracts": []
    },
    "lookback_15min": {
      "loss_USD": "8348989.96456680146171664141",
      "loss_rate": "0.278636816032959930239477815156339170396179377046225933379389060763523863875289099810771033",
      "qualifies": true,
      "reason": "reference_shortfall_screen_only",
      "valuation_complete": true,
      "input_reference_USD": "29963700.00000",
      "output_reference_USD": "21614710.03543319853828335859",
      "missing_contracts": []
    },
    "binance_ETH_same_minute": {
      "loss_USD": "8372469.6289292145736099026692724000000",
      "loss_rate": "0.279442802179118214950950148",
      "qualifies": true,
      "reason": "reference_shortfall_screen_only",
      "valuation_complete": true,
      "input_reference_USD": "29961300.00000",
      "output_reference_USD": "21588830.3710707854263900973307276000000",
      "missing_contracts": []
    }
  },
  "classification": "insufficient_evidence",
  "intent": "unresolved; no intent inferred from economic loss",
  "priority_million_plus": true,
  "five_million_focus": true,
  "rank": 1,
  "wallet_qualifying_swap_count": 2,
  "case_id": "N1",
  "transaction_input_evidence": "data/raw/objects/6a75fa8db5db47b4bf91177a263eff0c2f8d0f86e5d1b50030e3978cae00e820.json.gz",
  "fresh_receipt_evidence": "data/raw/public_rpc/93054e2640d1d86aeea59924b6d5f6ea93711774fd40f846b3354ce597c11120.json",
  "router_limit_inspection": {
    "status": "ABI_compatible_fields_decoded",
    "selector": "0x3593564c",
    "deadline": "1793309916",
    "limits": [
      {
        "command_location": "0",
        "command_type": 8,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "180000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": [
          "0xdac17f958d2ee523a2206206994597c13d831ec7",
          "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        ],
        "payer_is_user": true
      },
      {
        "command_location": "1",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "480000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000064a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "payer_is_user": true
      },
      {
        "command_location": "2",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "4650000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec70001f42260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "payer_is_user": true
      },
      {
        "command_location": "3",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "3600000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000bb82260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "payer_is_user": true
      },
      {
        "command_location": "4",
        "command_type": 8,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "780000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": [
          "0xdac17f958d2ee523a2206206994597c13d831ec7",
          "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        ],
        "payer_is_user": true
      },
      {
        "command_location": "5",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "1590000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec70001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": true
      },
      {
        "command_location": "6",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "10680000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": true
      },
      {
        "command_location": "7",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "150000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec7002710c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": true
      },
      {
        "command_location": "8",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "1320000000000",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": true
      },
      {
        "command_location": "10",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "184689301453",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb480001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "11",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "978248027502",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "12",
        "command_type": 8,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "84165924689",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": [
          "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
          "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        ],
        "payer_is_user": false
      },
      {
        "command_location": "13",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "57896044618658097711785492504343953926634992332820282019728792003956564819968",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "14",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "3415148077",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c5990001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "15",
        "command_type": 8,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "301225866",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": [
          "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
          "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        ],
        "payer_is_user": false
      },
      {
        "command_location": "16",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "1638987618",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "17",
        "command_type": 0,
        "allow_revert": false,
        "recipient": "0x0000000000000000000000000000000000000002",
        "amount_raw": "169533128",
        "bound_raw": "0",
        "bound_kind": "minimum_output",
        "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "payer_is_user": false
      },
      {
        "command_location": "19",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
        "bound_raw": "4934380635394559234997",
        "bound_kind": "unwrap_minimum"
      },
      {
        "command_location": "20",
        "command_type": 4,
        "allow_revert": false,
        "token": "0x0000000000000000000000000000000000000000",
        "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
        "bound_raw": "0",
        "bound_kind": "sweep_minimum"
      }
    ],
    "undecoded_commands": [
      {
        "command_location": "9",
        "command_type": 16,
        "payload_bytes": 6784
      },
      {
        "command_location": "18",
        "command_type": 16,
        "payload_bytes": 2432
      }
    ],
    "meaning_limit": "Numeric ABI-compatible fields only. Contract implementation, recipient aliases, V4 actions and per-hop limits need separate validation. A low/zero bound is not evidence of deliberate self-loss."
  },
  "successful_router_call_inspections": [
    {
      "trace_address": [],
      "call_type": "call",
      "caller": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
      "callee": "0x23617e59a5925b2a4bf75d73ff6711cd0b29de85",
      "inspection": {
        "status": "ABI_compatible_fields_decoded",
        "selector": "0x3593564c",
        "deadline": "1793309916",
        "limits": [
          {
            "command_location": "0",
            "command_type": 8,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "180000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": [
              "0xdac17f958d2ee523a2206206994597c13d831ec7",
              "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            ],
            "payer_is_user": true
          },
          {
            "command_location": "1",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "480000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000064a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "payer_is_user": true
          },
          {
            "command_location": "2",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "4650000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec70001f42260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "payer_is_user": true
          },
          {
            "command_location": "3",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "3600000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000bb82260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "payer_is_user": true
          },
          {
            "command_location": "4",
            "command_type": 8,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "780000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": [
              "0xdac17f958d2ee523a2206206994597c13d831ec7",
              "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            ],
            "payer_is_user": true
          },
          {
            "command_location": "5",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "1590000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec70001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": true
          },
          {
            "command_location": "6",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "10680000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": true
          },
          {
            "command_location": "7",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "150000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec7002710c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": true
          },
          {
            "command_location": "8",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "1320000000000",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xdac17f958d2ee523a2206206994597c13d831ec7000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": true
          },
          {
            "command_location": "10",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "184689301453",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb480001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "11",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "978248027502",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "12",
            "command_type": 8,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "84165924689",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": [
              "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
              "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            ],
            "payer_is_user": false
          },
          {
            "command_location": "13",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "57896044618658097711785492504343953926634992332820282019728792003956564819968",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "14",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "3415148077",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c5990001f4c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "15",
            "command_type": 8,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "301225866",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": [
              "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
              "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            ],
            "payer_is_user": false
          },
          {
            "command_location": "16",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "1638987618",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599000bb8c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "17",
            "command_type": 0,
            "allow_revert": false,
            "recipient": "0x0000000000000000000000000000000000000002",
            "amount_raw": "169533128",
            "bound_raw": "0",
            "bound_kind": "minimum_output",
            "path": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599000064c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "payer_is_user": false
          },
          {
            "command_location": "19",
            "command_type": 12,
            "allow_revert": false,
            "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
            "bound_raw": "4934380635394559234997",
            "bound_kind": "unwrap_minimum"
          },
          {
            "command_location": "20",
            "command_type": 4,
            "allow_revert": false,
            "token": "0x0000000000000000000000000000000000000000",
            "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
            "bound_raw": "0",
            "bound_kind": "sweep_minimum"
          }
        ],
        "undecoded_commands": [
          {
            "command_location": "9",
            "command_type": 16,
            "payload_bytes": 6784
          },
          {
            "command_location": "18",
            "command_type": 16,
            "payload_bytes": 2432
          }
        ],
        "meaning_limit": "Numeric ABI-compatible fields only. Contract implementation, recipient aliases, V4 actions and per-hop limits need separate validation. A low/zero bound is not evidence of deliberate self-loss."
      }
    }
  ],
  "observed_nonzero_minimum_bounds": [
    {
      "command_location": "19",
      "command_type": 12,
      "allow_revert": false,
      "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
      "bound_raw": "4934380635394559234997",
      "bound_kind": "unwrap_minimum",
      "trace_address": []
    }
  ],
  "observed_zero_minimum_bound_count": 18,
  "same_block_pool_neighbors": [
    {
      "tx_hash": "0xc4e4c05a82546d4b9b6b78303718f6ee3a8aaef03f136e64e7b977a452a70f09",
      "transaction_index": 0,
      "relative_index": -3,
      "shared_pools": [
        "0x3416cf6c708da44db2624d63ea0aaef7113527c6"
      ],
      "sender": "0xd92c4e3e434e2d05062c7b842a16ccd3e7a5b9b2",
      "executor": "0x51c72848c68a965f66fa7a88855f9f7784502a7f",
      "provisional_native_WETH_net_after_gas_ETH": "-2.812372761008610229",
      "other_token_residual_raw": {
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "133553251973",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "-126693860711"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x036d8a1cf3d03a8718f0dc5f5dd377c78167cb7a34e37afba2a8b4f0946b5c53",
      "transaction_index": 1,
      "relative_index": -2,
      "shared_pools": [
        "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"
      ],
      "sender": "0x05a94a8dd7eb1ba5b1114cc5ef18855a221ac317",
      "executor": "0x51c72848c68a965f66fa7a88855f9f7784502a7f",
      "provisional_native_WETH_net_after_gas_ETH": "-0.775170047284643191",
      "other_token_residual_raw": {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "-56324860204",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "58204634014"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x37cf616dfdf12c4b077f5b2b3c448861190805d97875ae92dcc049792472561a",
      "transaction_index": 4,
      "relative_index": 1,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x54c72c46df32f2cc455e84e41e191b26ed73a29452cdd3d82f511097af9f427e",
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x98316e8405502774a5d0a0761276b5d26505a8195c1905169864008d5e7a3eea",
        "0x000000000004444c5dc75cb358380d2e3de08a90:0xdce6394339af00981949f5f3baf27e3610c76326a700af57e4b3e3ae4977f78d",
        "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x56534741cd8b152df6d48adf7ac51f75169a83b2",
        "0xbb2b8038a1640196fbe3e38816f3e67cba72d940"
      ],
      "sender": "0x2ee36e41387f87b7e6f678a86d1e575b23b996f5",
      "executor": "0x50d3865a63d52c0a54e4679949647ea752107390",
      "provisional_native_WETH_net_after_gas_ETH": "2.350005243968626965",
      "other_token_residual_raw": {
        "0x4ea40dcee961675683e0a2e1721bd49cb9bca913": "5039102704393458029456"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x339afd92df59623dd7749d0302374d48d7317f51f268c1d7f9eabb159e88a9c7",
      "transaction_index": 5,
      "relative_index": 2,
      "shared_pools": [
        "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b"
      ],
      "sender": "0x480a15f9fdb1757d1db6cedc620772553f496637",
      "executor": "0xd226997439ecfbeff8e110c8c78c8a7eefd19f89",
      "provisional_native_WETH_net_after_gas_ETH": "0.105046220497056325",
      "other_token_residual_raw": {
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "1",
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "-2"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xc928a4d1734fb5b529ab925bed9d92f169d3d9699e6f692eb7b4e83eb10d083b",
      "transaction_index": 6,
      "relative_index": 3,
      "shared_pools": [
        "0xbb2b8038a1640196fbe3e38816f3e67cba72d940"
      ],
      "sender": "0x8a3999c2a419d11635a5146035824a49c33ca211",
      "executor": "0xd226997439ecfbeff8e110c8c78c8a7eefd19f89",
      "provisional_native_WETH_net_after_gas_ETH": "0.563091303670829013",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x509e3e1e434979f1eb286ee03838b4ba5159a0cbdce4a8aabb3fbcf3e7e1f131",
      "transaction_index": 7,
      "relative_index": 4,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x72331fcb696b0151904c03584b66dc8365bc63f8a144d89a773384e3a579ca73",
        "0x769db46f39c42ee7ad5f71f4167c47edd281e767"
      ],
      "sender": "0x2221612f8dc99f8e738bc6dc8918261e614476f0",
      "executor": "0xaf13a8a98cac93275e8be78d443f6e593de11154",
      "provisional_native_WETH_net_after_gas_ETH": "0.558490431838027375",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x3b4ae9044e973d444d2b284d51dc2c1f10fa293aeff64facb34b20d2fc116506",
      "transaction_index": 8,
      "relative_index": 5,
      "shared_pools": [
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "0x7486ff76f69872d27b22dada4078bd55b36a5324",
        "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
        "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed"
      ],
      "sender": "0xc77614364aa36e34b062a1a56500b7c37841c8ec",
      "executor": "0x584a31052c643d32f3134a956956dad722ff4161",
      "provisional_native_WETH_net_after_gas_ETH": "1.208078492805590993",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xd7c893a4d66fe7c13f57e18a7cb5de181e5610c9f8689090d8c0a7493667cfc5",
      "transaction_index": 9,
      "relative_index": 6,
      "shared_pools": [
        "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852"
      ],
      "sender": "0x2b3707f1a7e56c7a5191330b18858a6671dac0f2",
      "executor": "0x584a31052c643d32f3134a956956dad722ff4161",
      "provisional_native_WETH_net_after_gas_ETH": "0.962037858678982778",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x1518caa8497345a072740736dbc0f037162826a6300d87dd8b2775f9cf357841",
      "transaction_index": 10,
      "relative_index": 7,
      "shared_pools": [
        "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f"
      ],
      "sender": "0x68c0d9a97dfcdf7de78a6063891475b60823fdfe",
      "executor": "0x51c72848c68a965f66fa7a88855f9f7784502a7f",
      "provisional_native_WETH_net_after_gas_ETH": "-0.653023467437273892",
      "other_token_residual_raw": {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "-65003454980",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "67506266654"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xb759c6ce80d1db69f5b323c814366e5093685c7673575f6187e72769e8fca276",
      "transaction_index": 11,
      "relative_index": 8,
      "shared_pools": [
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x56534741cd8b152df6d48adf7ac51f75169a83b2"
      ],
      "sender": "0x00000000fd3a7b3fa5bcfa843c648714b11e089b",
      "executor": "0x00000000fd3a7b3fa5bcfa843c648714b11e089b",
      "provisional_native_WETH_net_after_gas_ETH": "1.259924023163429789",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xf491b8716bfd957292fc27a5dbf90b79e2a94235a9c926e5764c45f9bb14818a",
      "transaction_index": 13,
      "relative_index": 10,
      "shared_pools": [
        "0x11b815efb8f581194ae79006d24e0d814b7697f6",
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "0xe0554a476a092703abdb3ef35c80e0d76d32939f"
      ],
      "sender": "0x76dfa069f33bbdf111e5b83a360c751cdf06cda1",
      "executor": "0xea51075ccbd58174834da36372b0ed52199c483c",
      "provisional_native_WETH_net_after_gas_ETH": "1.132824163717725486",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x850e38b99170ea0357d4c02390879b9c17d61f2b92c2037d2864ba71361a2db9",
      "transaction_index": 14,
      "relative_index": 11,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x599326d9cd5e1ea0893305c87d5ec3199e7f05e94d72159f35dea381479a615e",
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0"
      ],
      "sender": "0x8d564be86df01ef7ec1b2dadd1cc39eee23edbab",
      "executor": "0x28265208ccfef43a86f115e5d3bb389edb2f6196",
      "provisional_native_WETH_net_after_gas_ETH": "0.132183726770076114",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xb276d6be27bbe0ff7133ea5dd9ebf1c8714f3b29e1817fd5d1bc5fe1fb269f88",
      "transaction_index": 15,
      "relative_index": 12,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x54c72c46df32f2cc455e84e41e191b26ed73a29452cdd3d82f511097af9f427e",
        "0x000000000004444c5dc75cb358380d2e3de08a90:0xdce6394339af00981949f5f3baf27e3610c76326a700af57e4b3e3ae4977f78d",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x56534741cd8b152df6d48adf7ac51f75169a83b2"
      ],
      "sender": "0x63c3eddef94eae0e2ee6fb33a95dd830c2c73263",
      "executor": "0x824520adebfa988772ae597ba1d2d81203380b9e",
      "provisional_native_WETH_net_after_gas_ETH": "0.396112243573540123",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x3d527a0382cbd24bc4d45e758252eeccd5e0bda92b363c7704c478402c1625b0",
      "transaction_index": 16,
      "relative_index": 13,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x50b00c1a5a8e582ec808e97e71598cd135206a9f9c548eab2ed73659e7ee5fa8",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
      ],
      "sender": "0x47ba0ab4d2138207db79a3aa5378c968134e8df4",
      "executor": "0x10ae4adc14e6806cf5c66fba8f86ceb2cc5a750a",
      "provisional_native_WETH_net_after_gas_ETH": "-0.16857082058620781",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xbb7f800bca5b60cda721055cbb4258f541a86b00538673bcffbd94efa4056b18",
      "transaction_index": 17,
      "relative_index": 14,
      "shared_pools": [
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
      ],
      "sender": "0xa57e3e178e41201b05b4e4aa6dde347fdcd5614e",
      "executor": "0xd226997439ecfbeff8e110c8c78c8a7eefd19f89",
      "provisional_native_WETH_net_after_gas_ETH": "0.134296930767582316",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x1255adaec34abea3b5a66b454000a78abed6bf8f9ce2b2c9207d0201a4801066",
      "transaction_index": 18,
      "relative_index": 15,
      "shared_pools": [
        "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f"
      ],
      "sender": "0xd64c19d791227e330de8fed3a5d587433a372918",
      "executor": "0x2ffea7c181ff67314363b90b978519a83e12e4d0",
      "provisional_native_WETH_net_after_gas_ETH": "0.479808532176556622",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x30a8774d8ccf813ce6ed5b20f8d1e19c6aef6874bf8b0038f7288decca0ebdf6",
      "transaction_index": 19,
      "relative_index": 16,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x98316e8405502774a5d0a0761276b5d26505a8195c1905169864008d5e7a3eea",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
      ],
      "sender": "0x0000000000ea39366718bfc07b48016b2c12f939",
      "executor": "0x0000000000d3c71f9d0a31e2f2139da1ca37b599",
      "provisional_native_WETH_net_after_gas_ETH": "0.046009064740715523",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c",
      "transaction_index": 20,
      "relative_index": 17,
      "shared_pools": [
        "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
      ],
      "sender": "0xc77a078a0e45bb30912c1e3bb0c20571e6728dfa",
      "executor": "0xb7c2f4c212e83c9503beb0cbe53013bfbdb51f2e",
      "provisional_native_WETH_net_after_gas_ETH": "2.745812294499937065",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x0f6abb1e4389618548a23450bc22729e0665e868839b824e4fc4f85537e336f4",
      "transaction_index": 21,
      "relative_index": 18,
      "shared_pools": [
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
      ],
      "sender": "0x333c92538e7f47d17c79e5975d4e40e901427558",
      "executor": "0x06cff7088619c7178f5e14f0b119458d08d2f5ef",
      "provisional_native_WETH_net_after_gas_ETH": "0.144278822512342224",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x7e565318939908e7b6e552c481fac9bd75abd401bf992e1659767dd4c304c368",
      "transaction_index": 22,
      "relative_index": 19,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0x20c3a15e34e5d88aeba004b0753af69e4f6bea80eae2263f7a92e919cd33cc56",
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0"
      ],
      "sender": "0xe6618358787976f673187ca24da5f715a0496aa7",
      "executor": "0xd226997439ecfbeff8e110c8c78c8a7eefd19f89",
      "provisional_native_WETH_net_after_gas_ETH": "0.066879212427602272",
      "other_token_residual_raw": {
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "1",
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "-2"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0x9bca773910eb6bfca33f7f1bf19fecc17c468782f7977efc1f88dbc865116925",
      "transaction_index": 23,
      "relative_index": 20,
      "shared_pools": [
        "0x4585fe77225b41b697c938b018e2ac67ac5a20c0"
      ],
      "sender": "0xbb805acc439f8788cb3399441173ceb35411536b",
      "executor": "0x2ffea7c181ff67314363b90b978519a83e12e4d0",
      "provisional_native_WETH_net_after_gas_ETH": "0.140146141150870663",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xd97d7dd55551d7d8a53e0c400f97ca5b6a3d83c74ac5fac6b6a1a52c9bd7208c",
      "transaction_index": 24,
      "relative_index": 21,
      "shared_pools": [
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
      ],
      "sender": "0xe0416611e9ef39033d59128b223fb62527e9167f",
      "executor": "0x8feab81d36e7576107d5de0758c1b839be31b4f6",
      "provisional_native_WETH_net_after_gas_ETH": "-1.02520685369280529",
      "other_token_residual_raw": {
        "0xdac17f958d2ee523a2206206994597c13d831ec7": "3292416985"
      },
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    },
    {
      "tx_hash": "0xadc7de247a2a06ac7fadb3c264dfb8e65a59875d711fa3d2e98825a2e6cd2cbc",
      "transaction_index": 25,
      "relative_index": 22,
      "shared_pools": [
        "0x000000000004444c5dc75cb358380d2e3de08a90:0xdce6394339af00981949f5f3baf27e3610c76326a700af57e4b3e3ae4977f78d",
        "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "0x56534741cd8b152df6d48adf7ac51f75169a83b2"
      ],
      "sender": "0x1ce52d9c4a886dfb220fe09a5ba0937661a0e9d7",
      "executor": "0x3884cf9171f53f3cb29bbca1594af8a0efd5567e",
      "provisional_native_WETH_net_after_gas_ETH": "0.591114364153355044",
      "other_token_residual_raw": {},
      "boundary_limit": "Sender+destination boundary is provisional; public routers are NOT authenticated owner clusters. This is not by itself proof of arbitrage or a causal link."
    }
  ],
  "observed_profitable_inventory_closed_neighbor_candidates": 15,
  "verified_arbitrage_cases_linked": [
    "A1"
  ],
  "v2_mechanical_leg_checks": [
    {
      "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
      "log_index": 13,
      "before_reserves_raw": [
        "1808177772492",
        "1815770042416"
      ],
      "after_reserves_raw": [
        "1645542098333",
        "1995770042416"
      ],
      "marginal_output_raw": "179247366927.311104606405099222214989448294116303913360642157814592285441577744268293010192",
      "no_fee_curve_output_raw": "163080912194.952338365092979604972605598581981355840942999769793975139629692037392576570425",
      "modeled_fee_adjusted_output_raw": "162635674159",
      "actual_output_raw": "162635674159",
      "mechanical_impact_output_raw": "16166454732.358766241312119617242383849712134948072417642388020617145811885706875716439767",
      "fee_effect_output_raw": "445238035.952338365092979604972605598581981355840942999769793975139629692037392576570425",
      "unexplained_model_residual_raw": "0",
      "limit": "Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV."
    },
    {
      "pool": "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
      "log_index": 26,
      "before_reserves_raw": [
        "2717617444424360199591",
        "7860424948944"
      ],
      "after_reserves_raw": [
        "2472958773628420931921",
        "8640424948944"
      ],
      "marginal_output_raw": "269672647524708606430.632263512769455329445584850714023750376754004934281858286885830816431",
      "no_fee_curve_output_raw": "245328397524020823011.297145645588853335476495183522562615835211452455470178442204571018809",
      "modeled_fee_adjusted_output_raw": "244658670795939267670",
      "actual_output_raw": "244658670795939267670",
      "mechanical_impact_output_raw": "24344250000687783419.335117867180601993969089667191461134541542552478811679844681259797622",
      "fee_effect_output_raw": "669726728081555341.297145645588853335476495183522562615835211452455470178442204571018809",
      "unexplained_model_residual_raw": "0",
      "limit": "Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV."
    },
    {
      "pool": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
      "log_index": 106,
      "before_reserves_raw": [
        "10525318500539",
        "3894453039111477699939"
      ],
      "after_reserves_raw": [
        "10609484425228",
        "3863649970359115494864"
      ],
      "marginal_output_raw": "31142073389790363684.6212119726315328839456595803303519495587653997537295854308579596382539",
      "no_fee_curve_output_raw": "30895020724596590266.7660300856842386231660822287241477572413604171296919383426523328024844",
      "modeled_fee_adjusted_output_raw": "30803068752362205075",
      "actual_output_raw": "30803068752362205075",
      "mechanical_impact_output_raw": "247052665193773417.8551818869472942607795773516062041923174049826240376470882056268357695",
      "fee_effect_output_raw": "91951972234385191.7660300856842386231660822287241477572413604171296919383426523328024844",
      "unexplained_model_residual_raw": "0",
      "limit": "Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV."
    },
    {
      "pool": "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
      "log_index": 116,
      "before_reserves_raw": [
        "5735974103",
        "1674092546652117795861"
      ],
      "after_reserves_raw": [
        "6037199969",
        "1590801880832056173015"
      ],
      "marginal_output_raw": "87915316226006605419.3342895966000144962648901275905917387646894681246785259413853389219181",
      "no_fee_curve_output_raw": "83528784820582706093.9350741300581889007824580806095873085034795209050329868243594036233919",
      "modeled_fee_adjusted_output_raw": "83290665820061622846",
      "actual_output_raw": "83290665820061622846",
      "mechanical_impact_output_raw": "4386531405423899325.3992154665418255954824320469810044302612099472196455391170259352985262",
      "fee_effect_output_raw": "238119000521083247.9350741300581889007824580806095873085034795209050329868243594036233919",
      "unexplained_model_residual_raw": "0",
      "limit": "Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV."
    },
    {
      "pool": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
      "log_index": 127,
      "before_reserves_raw": [
        "1685140534",
        "494307917945680485834"
      ],
      "after_reserves_raw": [
        "1786888659",
        "466240927789118956314"
      ],
      "marginal_output_raw": "29846118355626024768.5066729574021391381473944178474078530473470885010472366929605884134528",
      "no_fee_curve_output_raw": "28146635533393265149.5431318029312088213326110768046460582522506232997475194116165689985500",
      "modeled_fee_adjusted_output_raw": "28066990156561529520",
      "actual_output_raw": "28066990156561529520",
      "mechanical_impact_output_raw": "1699482822232759618.9635411544709303168147833410427617947950964652012997172813440194149028",
      "fee_effect_output_raw": "79645376831735629.5431318029312088213326110768046460582522506232997475194116165689985500",
      "unexplained_model_residual_raw": "0",
      "limit": "Output-token raw units for this V2-compatible leg only. 997/1000 fee model tested, residual retained. Not the entire multi-pool route or incremental MEV."
    }
  ],
  "major_ETH_USDT_pool_price_states": [
    {
      "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
      "log_index": 32,
      "before_spot_USD_per_ETH": "2923.92303448154248035002448046345567295580407808408228443662377932099258257875862556623766",
      "after_spot_USD_per_ETH": "3477.51464978743215080799001325195719579462217362912221114033273047511543808363950223281926",
      "actual_leg_average_USD_per_ETH": "3145.83016410043628509621269239091804270573995060494607772219468772629291685772050814246441",
      "before_active_liquidity": "4369438665906748545",
      "after_active_liquidity": "1602744874638683361",
      "before_state": {
        "sqrt_price_x96": "4286895063943638323230954",
        "tick": -196501,
        "active_liquidity": "4369438665906748545",
        "state_evidence": "data/raw/public_rpc/f52575052fc4d606c121366794ca4ee5de3abf0c00c1f6f26bc10a90a549943a.json",
        "liquidity_evidence": "data/raw/public_rpc/d3edbe557e36d447d2dc1772f6735a646bdb7fb2b390800600ab5ff0b70ec986.json"
      },
      "after_state": {
        "sqrt_price_x96": "4675137287308093157927606",
        "tick": -194767,
        "active_liquidity": "1602744874638683361",
        "state_evidence": "data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz",
        "log_index": 32
      },
      "metadata": {
        "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/d5c217c7d661b2b405da5be7b4b2b85a8958172b6ebf435c9c92c950b1e6e650.json",
          "token1": "data/raw/public_rpc/14c16b47de8b64a7ae9b588e7762e22d12b41271a36d779dcecfe9df041340ec.json",
          "factory": "data/raw/public_rpc/ccf4dc43d2e1de33ceb42cf6ab95392c216bf525acf3ef41cecd7cb41e3fcefb.json",
          "fee": "data/raw/public_rpc/2526e31bc8c8883d47ccb74fd932a6e06b700cd7c099b25f40e7f393a1e0de6a.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 6
      },
      "limit": "Observed marginal pool-state movement and trade-size average. Does not quantify no-fee full-route impact, tick-level opportunity or causal MEV."
    }
  ],
  "other_incoming_transfers_next_10min": [],
  "repeated_qualifying_swaps_by_same_wallet": 2,
  "compensating_profit_established": false,
  "counterfactual_incremental_MEV_loss_USD": null,
  "intentional_self_loss_established": false,
  "final_classification": "insufficient_evidence",
  "classification_detail": "Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.",
  "confidence": {
    "asset_flows": "observed receipts and complete successful call trees",
    "reference_loss": "estimated prior completed minute close",
    "slippage_fields": "ABI-compatible numeric inspection; exact deployed command semantics unresolved",
    "same_block_associations": "observed, causal assignment unresolved",
    "intent": "unresolved"
  }
}
```

<a id="slide-5"></a>
## Slide 5 — Actual arbitrage A1

A1,block26,300,992:14 aggregated pool legs; non-WETH inventory closes.12.137824ETH gross after pool fees−1.139064ETHgas−8.252948ETHbuilder=2.745812ETH retained net. The target’sUSD8.374M shortfall is a different quantity.

Source files (paths relative to new/):

- [reports/case_studies/A1_arbitrage.json](../../reports/case_studies/A1_arbitrage.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
{
  "token_net_raw": {},
  "other_token_residual_raw": {},
  "native_net_wei": "3884876592117177857",
  "gas_wei": "1139064297617240792",
  "identified_builder_payment_wei": "8252947611860856740",
  "cashflow_before_gas_ETH": "3.884876592117177857",
  "gross_after_pool_fees_before_gas_and_builder_ETH": "12.137824203978034597",
  "net_after_gas_and_builder_ETH": "2.745812294499937065",
  "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again.",
  "pool_flow_surplus_ETH": "12.137824203978034597",
  "unallocated_pool_surplus_vs_operational_gross_ETH": "0E-18",
  "case_id": "A1",
  "block": 26300992,
  "tx_hash": "0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c",
  "target": "0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6",
  "accounts": [
    "0xb7c2f4c212e83c9503beb0cbe53013bfbdb51f2e",
    "0xc77a078a0e45bb30912c1e3bb0c20571e6728dfa"
  ],
  "route_label": "Multi-pool atomic cycle",
  "timestamp_utc": "2026-10-29T21:09:11+00:00",
  "sender": "0xc77a078a0e45bb30912c1e3bb0c20571e6728dfa",
  "executor": "0xb7c2f4c212e83c9503beb0cbe53013bfbdb51f2e",
  "actor_index": 20,
  "target_index": 3,
  "same_pool_opposite_direction": [
    "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
    "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
    "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
  ],
  "route": [
    {
      "pool": "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801",
      "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "output_token": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
      "input_raw": "33646353211685082679",
      "output_raw": "12287672430249561022277",
      "input_quantity": "33.646353211685082679",
      "output_quantity": "12287.672430249561022277",
      "output_per_input": "365.200720355695499579144280006829666879032484799823046605456692877062476154997225181610214",
      "swap_log_indices": [
        635,
        645
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x3470447f3cecffac709d3e783a307790b0208d60",
      "input_token": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
      "output_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "input_raw": "12287672430249561022277",
      "output_raw": "115356979190",
      "input_quantity": "12287.672430249561022277",
      "output_quantity": "115356.97919",
      "output_per_input": "9.38802526229592163846274739371591076485445013639599558082036967666473626601929983786649720",
      "swap_log_indices": [
        627,
        640
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
      "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "input_raw": "80429611872",
      "output_raw": "65059624026",
      "input_quantity": "80429.611872",
      "output_quantity": "65059.624026",
      "output_per_input": "0.808901379874111249273293024302809108550213643880656124720879966003971716890893117351284985",
      "swap_log_indices": [
        630,
        673
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 100,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
      "input_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "input_raw": "135154907455",
      "output_raw": "49855579730893551332",
      "input_quantity": "135154.907455",
      "output_quantity": "49.855579730893551332",
      "output_per_input": "0.000368877317662276011892519851971807929643482289638330025372736473825585218369901476397707323",
      "swap_log_indices": [
        633,
        656,
        666
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 500,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
      "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "output_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "input_raw": "223597615814844981869",
      "output_raw": "742879535658",
      "input_quantity": "223.597615814844981869",
      "output_quantity": "742879.535658",
      "output_per_input": "3322.39470868579409417789440424821327235430529754447935805700819869206742329688074244230048",
      "swap_log_indices": [
        643,
        692
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0xc5c7c21f4e60770ca5991a8832127a40f5236f73",
      "input_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "input_raw": "155076940",
      "output_raw": "225935056207902670770",
      "input_quantity": "155.07694",
      "output_quantity": "225.93505620790267077",
      "output_per_input": "1.45692232647808675338835032468399234599289875077493791146510886789486560671109450573373449",
      "swap_log_indices": [
        658,
        690
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0xc756bba710d45647715079ce50aa16aab36ded42",
      "input_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "output_token": "0x45804880de22913dafe09f4980848ece6ecbaf78",
      "input_raw": "12261537",
      "output_raw": "12233835233377731831",
      "input_quantity": "12.261537",
      "output_quantity": "12.233835233377731831",
      "output_per_input": "0.997740759040056057490998069817837682176386206721066045798336701181915448283522693769957225",
      "swap_log_indices": [
        650
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 100,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x5ae13baaef0620fdae1d355495dc51a17adb4082",
      "input_token": "0x45804880de22913dafe09f4980848ece6ecbaf78",
      "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "input_raw": "12233835233377731831",
      "output_raw": "49633067329",
      "input_quantity": "12.233835233377731831",
      "output_quantity": "49633.067329",
      "output_per_input": "4057.03251532973541066473536627727382626632026538394747992468042751513937444778104147527430",
      "swap_log_indices": [
        653
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 500,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
      "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "output_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "input_raw": "6458362563059708841",
      "output_raw": "23835238",
      "input_quantity": "6.458362563059708841",
      "output_quantity": "0.23835238",
      "output_per_input": "0.0369060079350946753343891965872143207561288282986489409971515824710416919201595750536943349",
      "swap_log_indices": [
        668
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 500,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16",
      "input_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "input_raw": "23835238",
      "output_raw": "18339767537",
      "input_quantity": "0.23835238",
      "output_quantity": "18339.767537",
      "output_per_input": "76943.9245246890339420986692056525720448019021249127027806477115940692515845656754088211748",
      "swap_log_indices": [
        663
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 500,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0",
      "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "input_raw": "822195333527466219",
      "output_raw": "2122448563",
      "input_quantity": "0.822195333527466219",
      "output_quantity": "2122.448563",
      "output_per_input": "2581.44077988627696608559348111994303444023047273661045100706926845498943095673197304355294",
      "swap_log_indices": [
        682
      ],
      "protocol": "V2-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x80fa4c1fd0fbb9a4f071999af69531dee1016644",
      "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "output_token": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
      "input_raw": "2661933100",
      "output_raw": "3235337039146687442629",
      "input_quantity": "2661.9331",
      "output_quantity": "3235.337039146687442629",
      "output_per_input": "1.21540884673122981288635691107338497725581458076463304055237150775877876119426141851573956",
      "swap_log_indices": [
        676
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x06f00544c0bc62e6db10f46d370dfccdc23d8189",
      "input_token": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
      "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "input_raw": "3235337039146687442629",
      "output_raw": "871715188299052103",
      "input_quantity": "3235.337039146687442629",
      "output_quantity": "0.871715188299052103",
      "output_per_input": "0.000269435665512290781236581828695527542942693982997950107087524581157553499550506681113876641",
      "swap_log_indices": [
        679
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 3000,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    },
    {
      "pool": "0x6546055f46e866a4b9a4a13e81273e3152bae5da",
      "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "output_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "input_raw": "775144969876",
      "output_raw": "167338477",
      "input_quantity": "775144.969876",
      "output_quantity": "167.338477",
      "output_per_input": "0.000215880233379788491614792743814404549684410858217743380853003766799612293276123464190497565",
      "swap_log_indices": [
        687
      ],
      "protocol": "V3-compatible (event only)",
      "fee_pips": 500,
      "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
    }
  ],
  "metadata": {
    "0x3470447f3cecffac709d3e783a307790b0208d60": {
      "pool": "0x3470447f3cecffac709d3e783a307790b0208d60",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/3ad3522278671d29439fbcf8da1f686e247a0eb6d63fe8ce5302a1529eb70fa6.json",
        "token1": "data/raw/public_rpc/6b2cab25177e656316ce6ab2e4bc5868af5b20353a41e76c0212cb1699129c8f.json",
        "factory": "data/raw/public_rpc/063a4d806a6692f9612f275c45cd3421c0b6aaddd8ccd7afc6a470d3bdc4d860.json",
        "fee": "data/raw/public_rpc/dcccfdd239b2b692fdaa23e564d6d002f4c44d7d336196bf5e5e77337eff09b5.json",
        "decimals0": "data/raw/public_rpc/07da2de22a070eaba28889a249529759bcff3c34770b777956cea0e5532c3338.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 6
    },
    "0x3416cf6c708da44db2624d63ea0aaef7113527c6": {
      "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/fd6cfac6671895b52101251ba1635db0bd815e704ebf9884f4960fa5a0fbe1a2.json",
        "token1": "data/raw/public_rpc/dc8e9644d282f44030d673342820d5a1624d33101c1547d8d97271bee3520835.json",
        "factory": "data/raw/public_rpc/1727d6573e559029ebc2354a571af2af22f50e05ce142ca86c73f082f2e22146.json",
        "fee": "data/raw/public_rpc/4945e1ac6f1e19bf360b9e70684c8f598d51c44997385fb9ff60b328a2a3e10e.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 100,
      "decimals0": 6,
      "decimals1": 6
    },
    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640": {
      "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/d8f584a1a8582fbf288fe59fd4d7372b501b17454ac46a1d6b898644c32ceecf.json",
        "token1": "data/raw/public_rpc/77826eeb6f24b8405b1a8499bf0fdfe84d2e8d3b83898d891d1d411ec25f2b50.json",
        "factory": "data/raw/public_rpc/cf89b55dc8ffb03d90b4b726dbe220924689b212479a3dbcfec4b6d68bf7165c.json",
        "fee": "data/raw/public_rpc/4222faf083dd3bf201cd5aa131f3280a57e5c175ca53d0850e443e136b31b12b.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 6,
      "decimals1": 18
    },
    "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801": {
      "pool": "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/8fad6c7da4b1bb67da3b73ead3e115a02ebb31160808a4a47df967745e2e1b73.json",
        "token1": "data/raw/public_rpc/353a1328b0cdf44094984c028aa2c98d7fcae25bcb20f4e7ac8af7055bc585cf.json",
        "factory": "data/raw/public_rpc/17d4c16f0245f22259abf3c1d26f797411f79c232faad7ba128a02d002df45cc.json",
        "fee": "data/raw/public_rpc/1301588479e170e01fd688d1df23280cee4ce961ec7d9eb3f3c7c77a36380618.json",
        "decimals0": "data/raw/public_rpc/07da2de22a070eaba28889a249529759bcff3c34770b777956cea0e5532c3338.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 18
    },
    "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36": {
      "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/d5c217c7d661b2b405da5be7b4b2b85a8958172b6ebf435c9c92c950b1e6e650.json",
        "token1": "data/raw/public_rpc/14c16b47de8b64a7ae9b588e7762e22d12b41271a36d779dcecfe9df041340ec.json",
        "factory": "data/raw/public_rpc/ccf4dc43d2e1de33ceb42cf6ab95392c216bf525acf3ef41cecd7cb41e3fcefb.json",
        "fee": "data/raw/public_rpc/2526e31bc8c8883d47ccb74fd932a6e06b700cd7c099b25f40e7f393a1e0de6a.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 6
    },
    "0xc756bba710d45647715079ce50aa16aab36ded42": {
      "pool": "0xc756bba710d45647715079ce50aa16aab36ded42",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/2621499d8d286a3eb3f684e39800b76f5cb11a1a351c45873780eb52b6b7c6fb.json",
        "token1": "data/raw/public_rpc/52bda38a9a854a938b0e5e9ab97a1f319a59cdb08b1a00c12e79f6ef9c310fa3.json",
        "factory": "data/raw/public_rpc/ae6ba11c4c745b084d58e7f693209a9d4d069bb7d08a549981fe4a6a349336e3.json",
        "fee": "data/raw/public_rpc/d0f7a54531891b0acc06fe8a21180037d5d10914e482cfb647b9aef43ad7451a.json",
        "decimals0": "data/raw/public_rpc/b4b00ccd56e72b52a52667f476251622a2665027eac737348b8711744b4746a4.json",
        "decimals1": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json"
      },
      "token0": "0x45804880de22913dafe09f4980848ece6ecbaf78",
      "token1": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 100,
      "decimals0": 18,
      "decimals1": 6
    },
    "0x5ae13baaef0620fdae1d355495dc51a17adb4082": {
      "pool": "0x5ae13baaef0620fdae1d355495dc51a17adb4082",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/827f3b9ffc6a168089ad0b5cf340b67421e938c71ffd28dfb0458973d4ef3f06.json",
        "token1": "data/raw/public_rpc/16f766a4470917c920f80ab27f6febc4ac1351ac7d1478043452873b15333120.json",
        "factory": "data/raw/public_rpc/d418056a1e8612d330d661d383bd87890217555153553a60641751e95586a74c.json",
        "fee": "data/raw/public_rpc/45d655083d8caf8706e79174331740ca5ae71dd8ca412be440580309389929e4.json",
        "decimals0": "data/raw/public_rpc/b4b00ccd56e72b52a52667f476251622a2665027eac737348b8711744b4746a4.json",
        "decimals1": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json"
      },
      "token0": "0x45804880de22913dafe09f4980848ece6ecbaf78",
      "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 18,
      "decimals1": 6
    },
    "0xc5c7c21f4e60770ca5991a8832127a40f5236f73": {
      "pool": "0xc5c7c21f4e60770ca5991a8832127a40f5236f73",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/ee4ebf24b8f904d8fd6d272c913d1e1c6dfa06faa990d7136de128d1dc5720c6.json",
        "token1": "data/raw/public_rpc/0c00cdafaf7c3933a217f181a278796b042764affe081559012b70bb23100fc8.json",
        "factory": "data/raw/public_rpc/51cd870019dd70b37713648f93ad5b3a1ec1df1e50ed177056e792ea5d57543f.json",
        "fee": "data/raw/public_rpc/be92def5f6400304243d12e0e116796d9e1c2a24f6fef2b3b39bc8acbb6db78c.json",
        "decimals0": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 6,
      "decimals1": 18
    },
    "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16": {
      "pool": "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/3fbf0c51d7bb50c283aa0709b3d8a81f9d8bbeddb7d8c80fec8f1ddfc740bc82.json",
        "token1": "data/raw/public_rpc/028517cbc0811d54aa439f00d1b8971b28379468ecf62979326610f8564be22a.json",
        "factory": "data/raw/public_rpc/1525b8090a7ece837b86eb5e1e3d71d22fe8fd169a08495d092b95ffc3dbf18b.json",
        "fee": "data/raw/public_rpc/a4921946befd07081f5083dc1233a62ad17df6fadea0ef0e38f055e9796e7e33.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 8,
      "decimals1": 6
    },
    "0x4585fe77225b41b697c938b018e2ac67ac5a20c0": {
      "pool": "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/b8074b21bf3f650c3ff015212df1a16352e11dc4ab61311da4c7b68140ec942d.json",
        "token1": "data/raw/public_rpc/8c1cf96ecf9328ef1ae65d652c37354fd8f6744754c26fc7390d05bf86184d63.json",
        "factory": "data/raw/public_rpc/3faf1882fc1567b54a84bf7ad18aeb4964d7118337df6c8eedc3cfa5574acd8d.json",
        "fee": "data/raw/public_rpc/fee633087a4bc81ea0ccd5832b9ad6a36650edba06c16c5ef87a366e416ea065.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 8,
      "decimals1": 18
    },
    "0x80fa4c1fd0fbb9a4f071999af69531dee1016644": {
      "pool": "0x80fa4c1fd0fbb9a4f071999af69531dee1016644",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/a06c9d493d5a913063d345843059b0cf34ce78518410b195a83f6f5d15c14571.json",
        "token1": "data/raw/public_rpc/1fa249f5b4414d9b1c075b4affbc99f9037136cf5556428216e1c295989ed8cf.json",
        "factory": "data/raw/public_rpc/b33766d11cf93cf5cacdf18148fbb2135c911b464de1ee940734becf91c242c4.json",
        "fee": "data/raw/public_rpc/7cf93af4d57f1b93d4ceb631be8d89f0a68a33ce8049c8a2e171bf4581638276.json",
        "decimals0": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json",
        "decimals1": "data/raw/public_rpc/2eb1a6aab77702a447b72031b24ebc72e4b0c6ae16ba5e1b71fdbffbb32da7dc.json"
      },
      "token0": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "token1": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 6,
      "decimals1": 18
    },
    "0x06f00544c0bc62e6db10f46d370dfccdc23d8189": {
      "pool": "0x06f00544c0bc62e6db10f46d370dfccdc23d8189",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/74991e1a0ddd5bb7af640ff00325ecb0db6683da914c38964a72a18e72a3dd2a.json",
        "token1": "data/raw/public_rpc/8bbc33c4ad578305e2c77276cb4d2e94be2fe5818899f9a3c60470b5aa8e7219.json",
        "factory": "data/raw/public_rpc/e9fd30d3f0f48ce2bfedaca39cb13011797e6a65cfff392703fd6956ca4df901.json",
        "fee": "data/raw/public_rpc/d6d40d527a8ed4e922ac03966f57d9be1ecb7a2c69994cd5aeb7bc4e2d55cdc2.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/2eb1a6aab77702a447b72031b24ebc72e4b0c6ae16ba5e1b71fdbffbb32da7dc.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 18
    },
    "0x397ff1542f962076d0bfe58ea045ffa2d347aca0": {
      "pool": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/28ef0b4e0d916f3e9e59117fe99a12ade34ea8dd1de198ab96c23d770bd612ed.json",
        "token1": "data/raw/public_rpc/c3be2b50282006a5b7a827af0eb59175005cb42dfb9681b4aca331e0ea7d2535.json",
        "factory": "data/raw/public_rpc/8d47ca7c5162848ffd3d198d9b27e925c533a5e6d193524d69090186be44340b.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 6,
      "decimals1": 18
    },
    "0x6546055f46e866a4b9a4a13e81273e3152bae5da": {
      "pool": "0x6546055f46e866a4b9a4a13e81273e3152bae5da",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/83281e3c1b303940d3532754ca26967cec08e053fa290c9cf58f5788d6ebe712.json",
        "token1": "data/raw/public_rpc/749afbfac6728a372d1c60f0fea2bd53f567657f64cdf7d818d082abce86ad23.json",
        "factory": "data/raw/public_rpc/e6754df18db4e855f6b688f22f9e88f5024848bf02333622bdd71f2123ba9b17.json",
        "fee": "data/raw/public_rpc/8d9c58f841f437c97bc56437ff03642c95f0d7e824a3aed184a153add64f0bae.json",
        "decimals0": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0x68749665ff8d2d112fa859aa293f07a622782f38",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 6,
      "decimals1": 6
    },
    "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f": {
      "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/7f13f859166840394532189e50affc5f878a5bd20726f9ed2d4971a838f8070d.json",
        "token1": "data/raw/public_rpc/770a3776657593e913f39a32de1b03e68426a754d5b43664b35846e9a92d58a6.json",
        "factory": "data/raw/public_rpc/2151033e351531565f75f980ed10b4578e2c8dd4cfbfb9e5e434438fff3f92dd.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 6,
      "decimals1": 6
    },
    "0x56534741cd8b152df6d48adf7ac51f75169a83b2": {
      "pool": "0x56534741cd8b152df6d48adf7ac51f75169a83b2",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/f20f5bb8342ea3989c64eac980924441cb86d38b83fb2e939da68b2b2ccc50a6.json",
        "token1": "data/raw/public_rpc/ca1183b3b4fe44373cf86e211fa3da334a86537d583865e218adef5459151648.json",
        "factory": "data/raw/public_rpc/88f064f8fb574997546a6f8d5b9564b9497f5be7d4028bce9610c76765df3e13.json",
        "fee": "data/raw/public_rpc/b3936e17ed018e4115c74493d9d13ec1ea2837b7aac24dd7357bdd43ad654b49.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 8,
      "decimals1": 6
    },
    "0x9db9e0e53058c89e5b94e29621a205198648425b": {
      "pool": "0x9db9e0e53058c89e5b94e29621a205198648425b",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/9a866d72bb762723a8b86db975f2c5d7c5692ad04cfd54bbd8e23aa6bfc91720.json",
        "token1": "data/raw/public_rpc/81af50ae051277b6995ee91b64a8ba5e2e49ccc2a42301bbde5a7a1e2e56f65a.json",
        "factory": "data/raw/public_rpc/0d9f16e76e047cdd741f9fe0d947c9e6a6d388a643570c8d934305dfabb75be3.json",
        "fee": "data/raw/public_rpc/ee9a8adf38d71d23c0facbf714c3e48514b6bd6317f216368327188534733e5f.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 8,
      "decimals1": 6
    },
    "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852": {
      "pool": "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/497ffd0af7c45256d50dbf6a4eae8b6614c95818b861379fdda357e5e482c2db.json",
        "token1": "data/raw/public_rpc/adf4e92c5944f45f5a83003726fe981809aa4ab31bbaea3d3405c86f2e392c3e.json",
        "factory": "data/raw/public_rpc/e2539bf23b390df876f5c8ff45ccfb18bc6a7b9e1416b031bd1a60f438bfa42c.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 18,
      "decimals1": 6
    },
    "0x11b815efb8f581194ae79006d24e0d814b7697f6": {
      "pool": "0x11b815efb8f581194ae79006d24e0d814b7697f6",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/47ca6bf8e0e514b923b34ec6eba523a99df45eee640f25ab4a5782d6abe10cb4.json",
        "token1": "data/raw/public_rpc/365fa00117bdedc7c7ba8efe69be57d6c17ba9d87614bcce11b310cae408b568.json",
        "factory": "data/raw/public_rpc/12f1c4de4c37ddad39430236cb0fdd43482772d5ee843c14f5705cf63cdd32e1.json",
        "fee": "data/raw/public_rpc/ee9ae917fa0977de8e8ef78e5ea7b3772ea24c368f28a70431219c5c625415d3.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 500,
      "decimals0": 18,
      "decimals1": 6
    },
    "0xc5af84701f98fa483ece78af83f11b6c38aca71d": {
      "pool": "0xc5af84701f98fa483ece78af83f11b6c38aca71d",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/e2ab09ebc4cac910d2064c8a316b4e2d7d49db0a17a131e5afe3ed1241875fba.json",
        "token1": "data/raw/public_rpc/84c77315e0d790a2a2db462e868e1909010a1f1485694a12b3a46d7de7e8ccb5.json",
        "factory": "data/raw/public_rpc/cb34830e4cfcbd2477caa5f98190e5a5b3a17c1be6fb8db3ddfa707e0fc7e546.json",
        "fee": "data/raw/public_rpc/27e6b31ec7a0568b5a2c435905e1558cf908b588a8e2e89548a0b4db3d2b56be.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 10000,
      "decimals0": 18,
      "decimals1": 6
    },
    "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b": {
      "pool": "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/85bb5ef9a959b4d2f5be1219131a85869455bf6d24dde6c17297d9500444bfa0.json",
        "token1": "data/raw/public_rpc/eabad5367228ecd223544a9cda4fe65916896b5ac068267bb2d2c450e9a44b6f.json",
        "factory": "data/raw/public_rpc/72be324beea3e52ca063b099e4258523410539696f4770bb0b9740e00149480a.json",
        "fee": "data/raw/public_rpc/c273e49d1b8830878d4e72ebd5cc2a4d6cd9eae6e69b11a807f6314db47ef62b.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 100,
      "decimals0": 18,
      "decimals1": 6
    },
    "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f": {
      "pool": "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/18c9eaaf69c971c27ff15c33dd4c4bb64f81849e60771676059064d0f5b506fd.json",
        "token1": "data/raw/public_rpc/62af3fa3cfd1f9d618caad07ec735b65f832bf7a47b04e43e88b761697500947.json",
        "factory": "data/raw/public_rpc/2e0760a225e9377230081ed38249d804c8c66c05fcc1c85e79304502c0d8a9fa.json",
        "fee": "data/raw/public_rpc/884452860d16bf7a8388ef2cc4769f346329e43b1aec726296869c506c181c65.json",
        "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
        "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
      },
      "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
      "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 6
    },
    "0x769db46f39c42ee7ad5f71f4167c47edd281e767": {
      "pool": "0x769db46f39c42ee7ad5f71f4167c47edd281e767",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/77c00f3b298dd0913453856a00fb7fca56e77ec745261aafa1424ce53ac85ca6.json",
        "token1": "data/raw/public_rpc/a82e79eb46c2690e390b6a52da86cff89a23323cff78a0284eb52bd785844a68.json",
        "factory": "data/raw/public_rpc/e988f2b387e5fd975b48947232774e87139aa4588e8a4d2920538915ba50468c.json",
        "fee": "data/raw/public_rpc/cd3c6006d6d968d18fe0987cbdde8a91c60f072e6ec1a04df139e07ca4ed86e2.json",
        "decimals0": "data/raw/public_rpc/ee7d2fb6a98d9f60c095fac02d67929c06a642072c2add9426d8e96609c50d48.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x6b175474e89094c44da98b954eedeac495271d0f",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 18
    },
    "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8": {
      "pool": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/040a4430ebbfe8a127bf30c6665f2ceb0395e0ed8336d5b5af1acdc63caaad40.json",
        "token1": "data/raw/public_rpc/146a3da7e25210ac6f9057984e74bc883d8eaf9276aa33649c1dec9fb364e6ef.json",
        "factory": "data/raw/public_rpc/7a6543c78150a49f22fc91f9b4d4a6b7bd140e36812c2b884835fadf36a3457d.json",
        "fee": "data/raw/public_rpc/89c216bb5d3a576b9ef3eecafdc5b400cad731bb7d03c9048d696e11f8fa4333.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 6,
      "decimals1": 18
    },
    "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc": {
      "pool": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/cbed78d5eca0d2cd4d740d8566fa793c63b46d4186f054edba8896a78717fadc.json",
        "token1": "data/raw/public_rpc/12d3608e73f110a0454bc322b122450e0bc35e6f2b9516b2305164676a412ff1.json",
        "factory": "data/raw/public_rpc/67804454be83b3acdb1eb586fc6e4d252999b3812b9e33726de567c60b8f4b5f.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 6,
      "decimals1": 18
    },
    "0xe0554a476a092703abdb3ef35c80e0d76d32939f": {
      "pool": "0xe0554a476a092703abdb3ef35c80e0d76d32939f",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/e3b3f8ab48fb1cc9810b5a36dc38c466f31d9f8431e359a9327449f9086a884a.json",
        "token1": "data/raw/public_rpc/0ebf9d05f98b1cd502e6bf67124bd61aeeeb0e09ca7c89e3935ac42a3147d1c4.json",
        "factory": "data/raw/public_rpc/f7ea73389ab3063738fba1867af3ef03d87c7e9fe1d2360276e3dc87b4a6fedb.json",
        "fee": "data/raw/public_rpc/36919ed2ea3704887e8e6d643ed581c04e564c9c4ab7f9dae2efbcd32f65fdec.json",
        "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 100,
      "decimals0": 6,
      "decimals1": 18
    },
    "0xbb2b8038a1640196fbe3e38816f3e67cba72d940": {
      "pool": "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/7e2670988ab73dfcd2e07303b22c971649cf3f86d571e2b7a6c40662ed7a1040.json",
        "token1": "data/raw/public_rpc/eb8432925cef8aec2fc5a84ce395d3614f70189236ff638018c795362f2d935e.json",
        "factory": "data/raw/public_rpc/7b3e1929c1b4be22be8f4927e5fea24be20488390b8763d131adaec2c3db14b6.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 8,
      "decimals1": 18
    },
    "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed": {
      "pool": "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/3b823bb6ccae68aaf4ce0c5166924e43bee9b2f45126d3581d318e6d7b1668c7.json",
        "token1": "data/raw/public_rpc/8ca782b34b3575832bb08a8ef1532180ad52422431510f566412a448791eba20.json",
        "factory": "data/raw/public_rpc/bd7d50312152092d243ed06375555786a8a3b48a0e55df4145b8fcaedf4f385d.json",
        "fee": "data/raw/public_rpc/cbec2b7808e4e5f5c1074f8bd071cab82a9f33faada1850c4dbfa0441614a5ec.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 8,
      "decimals1": 18
    },
    "0xe6ff8b9a37b0fab776134636d9981aa778c4e718": {
      "pool": "0xe6ff8b9a37b0fab776134636d9981aa778c4e718",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/9631d9b160b372fe0351754134cf51ec9c058168f99ea92d29a1cb288c841fcd.json",
        "token1": "data/raw/public_rpc/091a9ba2871b6bad9aaee75469f2d78e538e203b4c5aa687f563b3d3c8a4eb10.json",
        "factory": "data/raw/public_rpc/377f10bd922bafd28c430367e42068c7ca2a7d312e4a5f9f9f2224d52698ce1c.json",
        "fee": "data/raw/public_rpc/bb29c247de05ccb256ca271d82b76f8b7248a016677389b11bd8d234ec120d70.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 100,
      "decimals0": 8,
      "decimals1": 18
    },
    "0xceff51756c56ceffca006cd410b03ffc46dd3a58": {
      "pool": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
      "protocol": "V2-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/7ecd507bd0f88ac2dfb25522256ec12596fc7439dec6d6b7b26f87d58a1bbb11.json",
        "token1": "data/raw/public_rpc/2103f7252142bde0075646231d386554088005466ac09d47ef99f19568fe6551.json",
        "factory": "data/raw/public_rpc/f5bb1cd64183c3c23dc4d40d8223eb9da9a645141bcae3cb0e52676ce16e8326.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 8,
      "decimals1": 18
    },
    "0x7486ff76f69872d27b22dada4078bd55b36a5324": {
      "pool": "0x7486ff76f69872d27b22dada4078bd55b36a5324",
      "protocol": "V3-compatible (event only)",
      "block": 26300991,
      "sources": {
        "token0": "data/raw/public_rpc/9b31c17f6913bfaf70640f1bef4f90a5fd46dfda02cbfe390f5fc3b8fb4e2290.json",
        "token1": "data/raw/public_rpc/ac7d2e9204b376f9729e20e3185e6f3f79551b2a963a0eca7a2ec65f7d6d6d98.json",
        "factory": "data/raw/public_rpc/706ee6f33bd4ed88ddf0374f04fbaf09334d35dd6875c812bd87c232e5520f0f.json",
        "fee": "data/raw/public_rpc/5f151fda4955ec4c821a746ba66bd6e30743afe536744c3e305f3917cc435fef.json",
        "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
        "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
      },
      "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
      "fee_pips": 3000,
      "decimals0": 8,
      "decimals1": 18
    }
  },
  "evidence": {
    "header": "data/raw/objects/6a75fa8db5db47b4bf91177a263eff0c2f8d0f86e5d1b50030e3978cae00e820.json.gz",
    "receipts": "data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz",
    "traces": "data/raw/objects/23846b66bf1cab96103c57df38e1e1fe8325a258a58b52f8ec84326165c20365.json.gz"
  },
  "classification": "observed_inventory_closed_profitable_atomic_arbitrage",
  "attribution_limit": "Same-block/pool association is observed. This cash flow is not all causally attributable to removing the hacker's trade; operational boundary is not beneficial ownership."
}
```

<a id="slide-6"></a>
## Slide 6 — Three arbitrage cases

A1/A2/A3 retained net:2.745812,0.000065,0.002184ETH. Selected total gross12.147692ETH; net2.748062ETH. Display rounded to6decimals; exact amounts below. These are selected cases, not event-wide MEV.

Source files (paths relative to new/):

- [data/processed/arbitrage_cases.json](../../data/processed/arbitrage_cases.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "token_net_raw": {},
    "other_token_residual_raw": {},
    "native_net_wei": "3884876592117177857",
    "gas_wei": "1139064297617240792",
    "identified_builder_payment_wei": "8252947611860856740",
    "cashflow_before_gas_ETH": "3.884876592117177857",
    "gross_after_pool_fees_before_gas_and_builder_ETH": "12.137824203978034597",
    "net_after_gas_and_builder_ETH": "2.745812294499937065",
    "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again.",
    "pool_flow_surplus_ETH": "12.137824203978034597",
    "unallocated_pool_surplus_vs_operational_gross_ETH": "0E-18",
    "case_id": "A1",
    "block": 26300992,
    "tx_hash": "0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c",
    "target": "0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6",
    "accounts": [
      "0xb7c2f4c212e83c9503beb0cbe53013bfbdb51f2e",
      "0xc77a078a0e45bb30912c1e3bb0c20571e6728dfa"
    ],
    "route_label": "Multi-pool atomic cycle",
    "timestamp_utc": "2026-10-29T21:09:11+00:00",
    "sender": "0xc77a078a0e45bb30912c1e3bb0c20571e6728dfa",
    "executor": "0xb7c2f4c212e83c9503beb0cbe53013bfbdb51f2e",
    "actor_index": 20,
    "target_index": 3,
    "same_pool_opposite_direction": [
      "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
      "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
      "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36"
    ],
    "route": [
      {
        "pool": "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        "input_raw": "33646353211685082679",
        "output_raw": "12287672430249561022277",
        "input_quantity": "33.646353211685082679",
        "output_quantity": "12287.672430249561022277",
        "output_per_input": "365.200720355695499579144280006829666879032484799823046605456692877062476154997225181610214",
        "swap_log_indices": [
          635,
          645
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x3470447f3cecffac709d3e783a307790b0208d60",
        "input_token": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        "output_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "input_raw": "12287672430249561022277",
        "output_raw": "115356979190",
        "input_quantity": "12287.672430249561022277",
        "output_quantity": "115356.97919",
        "output_per_input": "9.38802526229592163846274739371591076485445013639599558082036967666473626601929983786649720",
        "swap_log_indices": [
          627,
          640
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
        "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "input_raw": "80429611872",
        "output_raw": "65059624026",
        "input_quantity": "80429.611872",
        "output_quantity": "65059.624026",
        "output_per_input": "0.808901379874111249273293024302809108550213643880656124720879966003971716890893117351284985",
        "swap_log_indices": [
          630,
          673
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 100,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "input_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "input_raw": "135154907455",
        "output_raw": "49855579730893551332",
        "input_quantity": "135154.907455",
        "output_quantity": "49.855579730893551332",
        "output_per_input": "0.000368877317662276011892519851971807929643482289638330025372736473825585218369901476397707323",
        "swap_log_indices": [
          633,
          656,
          666
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 500,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "input_raw": "223597615814844981869",
        "output_raw": "742879535658",
        "input_quantity": "223.597615814844981869",
        "output_quantity": "742879.535658",
        "output_per_input": "3322.39470868579409417789440424821327235430529754447935805700819869206742329688074244230048",
        "swap_log_indices": [
          643,
          692
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0xc5c7c21f4e60770ca5991a8832127a40f5236f73",
        "input_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "input_raw": "155076940",
        "output_raw": "225935056207902670770",
        "input_quantity": "155.07694",
        "output_quantity": "225.93505620790267077",
        "output_per_input": "1.45692232647808675338835032468399234599289875077493791146510886789486560671109450573373449",
        "swap_log_indices": [
          658,
          690
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0xc756bba710d45647715079ce50aa16aab36ded42",
        "input_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "output_token": "0x45804880de22913dafe09f4980848ece6ecbaf78",
        "input_raw": "12261537",
        "output_raw": "12233835233377731831",
        "input_quantity": "12.261537",
        "output_quantity": "12.233835233377731831",
        "output_per_input": "0.997740759040056057490998069817837682176386206721066045798336701181915448283522693769957225",
        "swap_log_indices": [
          650
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 100,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x5ae13baaef0620fdae1d355495dc51a17adb4082",
        "input_token": "0x45804880de22913dafe09f4980848ece6ecbaf78",
        "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "input_raw": "12233835233377731831",
        "output_raw": "49633067329",
        "input_quantity": "12.233835233377731831",
        "output_quantity": "49633.067329",
        "output_per_input": "4057.03251532973541066473536627727382626632026538394747992468042751513937444778104147527430",
        "swap_log_indices": [
          653
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 500,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "input_raw": "6458362563059708841",
        "output_raw": "23835238",
        "input_quantity": "6.458362563059708841",
        "output_quantity": "0.23835238",
        "output_per_input": "0.0369060079350946753343891965872143207561288282986489409971515824710416919201595750536943349",
        "swap_log_indices": [
          668
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 500,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16",
        "input_token": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "input_raw": "23835238",
        "output_raw": "18339767537",
        "input_quantity": "0.23835238",
        "output_quantity": "18339.767537",
        "output_per_input": "76943.9245246890339420986692056525720448019021249127027806477115940692515845656754088211748",
        "swap_log_indices": [
          663
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 500,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "input_raw": "822195333527466219",
        "output_raw": "2122448563",
        "input_quantity": "0.822195333527466219",
        "output_quantity": "2122.448563",
        "output_per_input": "2581.44077988627696608559348111994303444023047273661045100706926845498943095673197304355294",
        "swap_log_indices": [
          682
        ],
        "protocol": "V2-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x80fa4c1fd0fbb9a4f071999af69531dee1016644",
        "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "output_token": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
        "input_raw": "2661933100",
        "output_raw": "3235337039146687442629",
        "input_quantity": "2661.9331",
        "output_quantity": "3235.337039146687442629",
        "output_per_input": "1.21540884673122981288635691107338497725581458076463304055237150775877876119426141851573956",
        "swap_log_indices": [
          676
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x06f00544c0bc62e6db10f46d370dfccdc23d8189",
        "input_token": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
        "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "input_raw": "3235337039146687442629",
        "output_raw": "871715188299052103",
        "input_quantity": "3235.337039146687442629",
        "output_quantity": "0.871715188299052103",
        "output_per_input": "0.000269435665512290781236581828695527542942693982997950107087524581157553499550506681113876641",
        "swap_log_indices": [
          679
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0x6546055f46e866a4b9a4a13e81273e3152bae5da",
        "input_token": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "output_token": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "input_raw": "775144969876",
        "output_raw": "167338477",
        "input_quantity": "775144.969876",
        "output_quantity": "167.338477",
        "output_per_input": "0.000215880233379788491614792743814404549684410858217743380853003766799612293276123464190497565",
        "swap_log_indices": [
          687
        ],
        "protocol": "V3-compatible (event only)",
        "fee_pips": 500,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      }
    ],
    "metadata": {
      "0x3470447f3cecffac709d3e783a307790b0208d60": {
        "pool": "0x3470447f3cecffac709d3e783a307790b0208d60",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/3ad3522278671d29439fbcf8da1f686e247a0eb6d63fe8ce5302a1529eb70fa6.json",
          "token1": "data/raw/public_rpc/6b2cab25177e656316ce6ab2e4bc5868af5b20353a41e76c0212cb1699129c8f.json",
          "factory": "data/raw/public_rpc/063a4d806a6692f9612f275c45cd3421c0b6aaddd8ccd7afc6a470d3bdc4d860.json",
          "fee": "data/raw/public_rpc/dcccfdd239b2b692fdaa23e564d6d002f4c44d7d336196bf5e5e77337eff09b5.json",
          "decimals0": "data/raw/public_rpc/07da2de22a070eaba28889a249529759bcff3c34770b777956cea0e5532c3338.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 6
      },
      "0x3416cf6c708da44db2624d63ea0aaef7113527c6": {
        "pool": "0x3416cf6c708da44db2624d63ea0aaef7113527c6",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/fd6cfac6671895b52101251ba1635db0bd815e704ebf9884f4960fa5a0fbe1a2.json",
          "token1": "data/raw/public_rpc/dc8e9644d282f44030d673342820d5a1624d33101c1547d8d97271bee3520835.json",
          "factory": "data/raw/public_rpc/1727d6573e559029ebc2354a571af2af22f50e05ce142ca86c73f082f2e22146.json",
          "fee": "data/raw/public_rpc/4945e1ac6f1e19bf360b9e70684c8f598d51c44997385fb9ff60b328a2a3e10e.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 100,
        "decimals0": 6,
        "decimals1": 6
      },
      "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640": {
        "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/d8f584a1a8582fbf288fe59fd4d7372b501b17454ac46a1d6b898644c32ceecf.json",
          "token1": "data/raw/public_rpc/77826eeb6f24b8405b1a8499bf0fdfe84d2e8d3b83898d891d1d411ec25f2b50.json",
          "factory": "data/raw/public_rpc/cf89b55dc8ffb03d90b4b726dbe220924689b212479a3dbcfec4b6d68bf7165c.json",
          "fee": "data/raw/public_rpc/4222faf083dd3bf201cd5aa131f3280a57e5c175ca53d0850e443e136b31b12b.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 6,
        "decimals1": 18
      },
      "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801": {
        "pool": "0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/8fad6c7da4b1bb67da3b73ead3e115a02ebb31160808a4a47df967745e2e1b73.json",
          "token1": "data/raw/public_rpc/353a1328b0cdf44094984c028aa2c98d7fcae25bcb20f4e7ac8af7055bc585cf.json",
          "factory": "data/raw/public_rpc/17d4c16f0245f22259abf3c1d26f797411f79c232faad7ba128a02d002df45cc.json",
          "fee": "data/raw/public_rpc/1301588479e170e01fd688d1df23280cee4ce961ec7d9eb3f3c7c77a36380618.json",
          "decimals0": "data/raw/public_rpc/07da2de22a070eaba28889a249529759bcff3c34770b777956cea0e5532c3338.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 18
      },
      "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36": {
        "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/d5c217c7d661b2b405da5be7b4b2b85a8958172b6ebf435c9c92c950b1e6e650.json",
          "token1": "data/raw/public_rpc/14c16b47de8b64a7ae9b588e7762e22d12b41271a36d779dcecfe9df041340ec.json",
          "factory": "data/raw/public_rpc/ccf4dc43d2e1de33ceb42cf6ab95392c216bf525acf3ef41cecd7cb41e3fcefb.json",
          "fee": "data/raw/public_rpc/2526e31bc8c8883d47ccb74fd932a6e06b700cd7c099b25f40e7f393a1e0de6a.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 6
      },
      "0xc756bba710d45647715079ce50aa16aab36ded42": {
        "pool": "0xc756bba710d45647715079ce50aa16aab36ded42",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/2621499d8d286a3eb3f684e39800b76f5cb11a1a351c45873780eb52b6b7c6fb.json",
          "token1": "data/raw/public_rpc/52bda38a9a854a938b0e5e9ab97a1f319a59cdb08b1a00c12e79f6ef9c310fa3.json",
          "factory": "data/raw/public_rpc/ae6ba11c4c745b084d58e7f693209a9d4d069bb7d08a549981fe4a6a349336e3.json",
          "fee": "data/raw/public_rpc/d0f7a54531891b0acc06fe8a21180037d5d10914e482cfb647b9aef43ad7451a.json",
          "decimals0": "data/raw/public_rpc/b4b00ccd56e72b52a52667f476251622a2665027eac737348b8711744b4746a4.json",
          "decimals1": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json"
        },
        "token0": "0x45804880de22913dafe09f4980848ece6ecbaf78",
        "token1": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 100,
        "decimals0": 18,
        "decimals1": 6
      },
      "0x5ae13baaef0620fdae1d355495dc51a17adb4082": {
        "pool": "0x5ae13baaef0620fdae1d355495dc51a17adb4082",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/827f3b9ffc6a168089ad0b5cf340b67421e938c71ffd28dfb0458973d4ef3f06.json",
          "token1": "data/raw/public_rpc/16f766a4470917c920f80ab27f6febc4ac1351ac7d1478043452873b15333120.json",
          "factory": "data/raw/public_rpc/d418056a1e8612d330d661d383bd87890217555153553a60641751e95586a74c.json",
          "fee": "data/raw/public_rpc/45d655083d8caf8706e79174331740ca5ae71dd8ca412be440580309389929e4.json",
          "decimals0": "data/raw/public_rpc/b4b00ccd56e72b52a52667f476251622a2665027eac737348b8711744b4746a4.json",
          "decimals1": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json"
        },
        "token0": "0x45804880de22913dafe09f4980848ece6ecbaf78",
        "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 18,
        "decimals1": 6
      },
      "0xc5c7c21f4e60770ca5991a8832127a40f5236f73": {
        "pool": "0xc5c7c21f4e60770ca5991a8832127a40f5236f73",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/ee4ebf24b8f904d8fd6d272c913d1e1c6dfa06faa990d7136de128d1dc5720c6.json",
          "token1": "data/raw/public_rpc/0c00cdafaf7c3933a217f181a278796b042764affe081559012b70bb23100fc8.json",
          "factory": "data/raw/public_rpc/51cd870019dd70b37713648f93ad5b3a1ec1df1e50ed177056e792ea5d57543f.json",
          "fee": "data/raw/public_rpc/be92def5f6400304243d12e0e116796d9e1c2a24f6fef2b3b39bc8acbb6db78c.json",
          "decimals0": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 6,
        "decimals1": 18
      },
      "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16": {
        "pool": "0x9a772018fbd77fcd2d25657e5c547baff3fd7d16",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/3fbf0c51d7bb50c283aa0709b3d8a81f9d8bbeddb7d8c80fec8f1ddfc740bc82.json",
          "token1": "data/raw/public_rpc/028517cbc0811d54aa439f00d1b8971b28379468ecf62979326610f8564be22a.json",
          "factory": "data/raw/public_rpc/1525b8090a7ece837b86eb5e1e3d71d22fe8fd169a08495d092b95ffc3dbf18b.json",
          "fee": "data/raw/public_rpc/a4921946befd07081f5083dc1233a62ad17df6fadea0ef0e38f055e9796e7e33.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 8,
        "decimals1": 6
      },
      "0x4585fe77225b41b697c938b018e2ac67ac5a20c0": {
        "pool": "0x4585fe77225b41b697c938b018e2ac67ac5a20c0",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/b8074b21bf3f650c3ff015212df1a16352e11dc4ab61311da4c7b68140ec942d.json",
          "token1": "data/raw/public_rpc/8c1cf96ecf9328ef1ae65d652c37354fd8f6744754c26fc7390d05bf86184d63.json",
          "factory": "data/raw/public_rpc/3faf1882fc1567b54a84bf7ad18aeb4964d7118337df6c8eedc3cfa5574acd8d.json",
          "fee": "data/raw/public_rpc/fee633087a4bc81ea0ccd5832b9ad6a36650edba06c16c5ef87a366e416ea065.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 8,
        "decimals1": 18
      },
      "0x80fa4c1fd0fbb9a4f071999af69531dee1016644": {
        "pool": "0x80fa4c1fd0fbb9a4f071999af69531dee1016644",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/a06c9d493d5a913063d345843059b0cf34ce78518410b195a83f6f5d15c14571.json",
          "token1": "data/raw/public_rpc/1fa249f5b4414d9b1c075b4affbc99f9037136cf5556428216e1c295989ed8cf.json",
          "factory": "data/raw/public_rpc/b33766d11cf93cf5cacdf18148fbb2135c911b464de1ee940734becf91c242c4.json",
          "fee": "data/raw/public_rpc/7cf93af4d57f1b93d4ceb631be8d89f0a68a33ce8049c8a2e171bf4581638276.json",
          "decimals0": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json",
          "decimals1": "data/raw/public_rpc/2eb1a6aab77702a447b72031b24ebc72e4b0c6ae16ba5e1b71fdbffbb32da7dc.json"
        },
        "token0": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "token1": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 6,
        "decimals1": 18
      },
      "0x06f00544c0bc62e6db10f46d370dfccdc23d8189": {
        "pool": "0x06f00544c0bc62e6db10f46d370dfccdc23d8189",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/74991e1a0ddd5bb7af640ff00325ecb0db6683da914c38964a72a18e72a3dd2a.json",
          "token1": "data/raw/public_rpc/8bbc33c4ad578305e2c77276cb4d2e94be2fe5818899f9a3c60470b5aa8e7219.json",
          "factory": "data/raw/public_rpc/e9fd30d3f0f48ce2bfedaca39cb13011797e6a65cfff392703fd6956ca4df901.json",
          "fee": "data/raw/public_rpc/d6d40d527a8ed4e922ac03966f57d9be1ecb7a2c69994cd5aeb7bc4e2d55cdc2.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/2eb1a6aab77702a447b72031b24ebc72e4b0c6ae16ba5e1b71fdbffbb32da7dc.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 18
      },
      "0x397ff1542f962076d0bfe58ea045ffa2d347aca0": {
        "pool": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/28ef0b4e0d916f3e9e59117fe99a12ade34ea8dd1de198ab96c23d770bd612ed.json",
          "token1": "data/raw/public_rpc/c3be2b50282006a5b7a827af0eb59175005cb42dfb9681b4aca331e0ea7d2535.json",
          "factory": "data/raw/public_rpc/8d47ca7c5162848ffd3d198d9b27e925c533a5e6d193524d69090186be44340b.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 6,
        "decimals1": 18
      },
      "0x6546055f46e866a4b9a4a13e81273e3152bae5da": {
        "pool": "0x6546055f46e866a4b9a4a13e81273e3152bae5da",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/83281e3c1b303940d3532754ca26967cec08e053fa290c9cf58f5788d6ebe712.json",
          "token1": "data/raw/public_rpc/749afbfac6728a372d1c60f0fea2bd53f567657f64cdf7d818d082abce86ad23.json",
          "factory": "data/raw/public_rpc/e6754df18db4e855f6b688f22f9e88f5024848bf02333622bdd71f2123ba9b17.json",
          "fee": "data/raw/public_rpc/8d9c58f841f437c97bc56437ff03642c95f0d7e824a3aed184a153add64f0bae.json",
          "decimals0": "data/raw/public_rpc/ff5704855d55c710b2c11db954f96eb6c1b89a89f6943cc3d70aa4c8c55c3a74.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0x68749665ff8d2d112fa859aa293f07a622782f38",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 6,
        "decimals1": 6
      },
      "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f": {
        "pool": "0x3041cbd36888becc7bbcbc0045e3b1f144466f5f",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/7f13f859166840394532189e50affc5f878a5bd20726f9ed2d4971a838f8070d.json",
          "token1": "data/raw/public_rpc/770a3776657593e913f39a32de1b03e68426a754d5b43664b35846e9a92d58a6.json",
          "factory": "data/raw/public_rpc/2151033e351531565f75f980ed10b4578e2c8dd4cfbfb9e5e434438fff3f92dd.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 6,
        "decimals1": 6
      },
      "0x56534741cd8b152df6d48adf7ac51f75169a83b2": {
        "pool": "0x56534741cd8b152df6d48adf7ac51f75169a83b2",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/f20f5bb8342ea3989c64eac980924441cb86d38b83fb2e939da68b2b2ccc50a6.json",
          "token1": "data/raw/public_rpc/ca1183b3b4fe44373cf86e211fa3da334a86537d583865e218adef5459151648.json",
          "factory": "data/raw/public_rpc/88f064f8fb574997546a6f8d5b9564b9497f5be7d4028bce9610c76765df3e13.json",
          "fee": "data/raw/public_rpc/b3936e17ed018e4115c74493d9d13ec1ea2837b7aac24dd7357bdd43ad654b49.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 8,
        "decimals1": 6
      },
      "0x9db9e0e53058c89e5b94e29621a205198648425b": {
        "pool": "0x9db9e0e53058c89e5b94e29621a205198648425b",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/9a866d72bb762723a8b86db975f2c5d7c5692ad04cfd54bbd8e23aa6bfc91720.json",
          "token1": "data/raw/public_rpc/81af50ae051277b6995ee91b64a8ba5e2e49ccc2a42301bbde5a7a1e2e56f65a.json",
          "factory": "data/raw/public_rpc/0d9f16e76e047cdd741f9fe0d947c9e6a6d388a643570c8d934305dfabb75be3.json",
          "fee": "data/raw/public_rpc/ee9a8adf38d71d23c0facbf714c3e48514b6bd6317f216368327188534733e5f.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 8,
        "decimals1": 6
      },
      "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852": {
        "pool": "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/497ffd0af7c45256d50dbf6a4eae8b6614c95818b861379fdda357e5e482c2db.json",
          "token1": "data/raw/public_rpc/adf4e92c5944f45f5a83003726fe981809aa4ab31bbaea3d3405c86f2e392c3e.json",
          "factory": "data/raw/public_rpc/e2539bf23b390df876f5c8ff45ccfb18bc6a7b9e1416b031bd1a60f438bfa42c.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 18,
        "decimals1": 6
      },
      "0x11b815efb8f581194ae79006d24e0d814b7697f6": {
        "pool": "0x11b815efb8f581194ae79006d24e0d814b7697f6",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/47ca6bf8e0e514b923b34ec6eba523a99df45eee640f25ab4a5782d6abe10cb4.json",
          "token1": "data/raw/public_rpc/365fa00117bdedc7c7ba8efe69be57d6c17ba9d87614bcce11b310cae408b568.json",
          "factory": "data/raw/public_rpc/12f1c4de4c37ddad39430236cb0fdd43482772d5ee843c14f5705cf63cdd32e1.json",
          "fee": "data/raw/public_rpc/ee9ae917fa0977de8e8ef78e5ea7b3772ea24c368f28a70431219c5c625415d3.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 500,
        "decimals0": 18,
        "decimals1": 6
      },
      "0xc5af84701f98fa483ece78af83f11b6c38aca71d": {
        "pool": "0xc5af84701f98fa483ece78af83f11b6c38aca71d",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/e2ab09ebc4cac910d2064c8a316b4e2d7d49db0a17a131e5afe3ed1241875fba.json",
          "token1": "data/raw/public_rpc/84c77315e0d790a2a2db462e868e1909010a1f1485694a12b3a46d7de7e8ccb5.json",
          "factory": "data/raw/public_rpc/cb34830e4cfcbd2477caa5f98190e5a5b3a17c1be6fb8db3ddfa707e0fc7e546.json",
          "fee": "data/raw/public_rpc/27e6b31ec7a0568b5a2c435905e1558cf908b588a8e2e89548a0b4db3d2b56be.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 10000,
        "decimals0": 18,
        "decimals1": 6
      },
      "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b": {
        "pool": "0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/85bb5ef9a959b4d2f5be1219131a85869455bf6d24dde6c17297d9500444bfa0.json",
          "token1": "data/raw/public_rpc/eabad5367228ecd223544a9cda4fe65916896b5ac068267bb2d2c450e9a44b6f.json",
          "factory": "data/raw/public_rpc/72be324beea3e52ca063b099e4258523410539696f4770bb0b9740e00149480a.json",
          "fee": "data/raw/public_rpc/c273e49d1b8830878d4e72ebd5cc2a4d6cd9eae6e69b11a807f6314db47ef62b.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 100,
        "decimals0": 18,
        "decimals1": 6
      },
      "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f": {
        "pool": "0x6a11ed98b1a3ac36a768ebbbba36ded101da5a3f",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/18c9eaaf69c971c27ff15c33dd4c4bb64f81849e60771676059064d0f5b506fd.json",
          "token1": "data/raw/public_rpc/62af3fa3cfd1f9d618caad07ec735b65f832bf7a47b04e43e88b761697500947.json",
          "factory": "data/raw/public_rpc/2e0760a225e9377230081ed38249d804c8c66c05fcc1c85e79304502c0d8a9fa.json",
          "fee": "data/raw/public_rpc/884452860d16bf7a8388ef2cc4769f346329e43b1aec726296869c506c181c65.json",
          "decimals0": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json",
          "decimals1": "data/raw/public_rpc/22c1a6985ae3792b6c10a91a1620a738c9684d3c120c2fbc9cc91a68fa96a837.json"
        },
        "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "token1": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 6
      },
      "0x769db46f39c42ee7ad5f71f4167c47edd281e767": {
        "pool": "0x769db46f39c42ee7ad5f71f4167c47edd281e767",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/77c00f3b298dd0913453856a00fb7fca56e77ec745261aafa1424ce53ac85ca6.json",
          "token1": "data/raw/public_rpc/a82e79eb46c2690e390b6a52da86cff89a23323cff78a0284eb52bd785844a68.json",
          "factory": "data/raw/public_rpc/e988f2b387e5fd975b48947232774e87139aa4588e8a4d2920538915ba50468c.json",
          "fee": "data/raw/public_rpc/cd3c6006d6d968d18fe0987cbdde8a91c60f072e6ec1a04df139e07ca4ed86e2.json",
          "decimals0": "data/raw/public_rpc/ee7d2fb6a98d9f60c095fac02d67929c06a642072c2add9426d8e96609c50d48.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x6b175474e89094c44da98b954eedeac495271d0f",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
        "fee_pips": 3000,
        "decimals0": 18,
        "decimals1": 18
      },
      "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8": {
        "pool": "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/040a4430ebbfe8a127bf30c6665f2ceb0395e0ed8336d5b5af1acdc63caaad40.json",
          "token1": "data/raw/public_rpc/146a3da7e25210ac6f9057984e74bc883d8eaf9276aa33649c1dec9fb364e6ef.json",
          "factory": "data/raw/public_rpc/7a6543c78150a49f22fc91f9b4d4a6b7bd140e36812c2b884835fadf36a3457d.json",
          "fee": "data/raw/public_rpc/89c216bb5d3a576b9ef3eecafdc5b400cad731bb7d03c9048d696e11f8fa4333.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 6,
        "decimals1": 18
      },
      "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc": {
        "pool": "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/cbed78d5eca0d2cd4d740d8566fa793c63b46d4186f054edba8896a78717fadc.json",
          "token1": "data/raw/public_rpc/12d3608e73f110a0454bc322b122450e0bc35e6f2b9516b2305164676a412ff1.json",
          "factory": "data/raw/public_rpc/67804454be83b3acdb1eb586fc6e4d252999b3812b9e33726de567c60b8f4b5f.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 6,
        "decimals1": 18
      },
      "0xe0554a476a092703abdb3ef35c80e0d76d32939f": {
        "pool": "0xe0554a476a092703abdb3ef35c80e0d76d32939f",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/e3b3f8ab48fb1cc9810b5a36dc38c466f31d9f8431e359a9327449f9086a884a.json",
          "token1": "data/raw/public_rpc/0ebf9d05f98b1cd502e6bf67124bd61aeeeb0e09ca7c89e3935ac42a3147d1c4.json",
          "factory": "data/raw/public_rpc/f7ea73389ab3063738fba1867af3ef03d87c7e9fe1d2360276e3dc87b4a6fedb.json",
          "fee": "data/raw/public_rpc/36919ed2ea3704887e8e6d643ed581c04e564c9c4ab7f9dae2efbcd32f65fdec.json",
          "decimals0": "data/raw/public_rpc/0b9fdcfad845dd77843e02338b5479cabed066f8eca0d888cf7ddb1315b67c01.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 100,
        "decimals0": 6,
        "decimals1": 18
      },
      "0xbb2b8038a1640196fbe3e38816f3e67cba72d940": {
        "pool": "0xbb2b8038a1640196fbe3e38816f3e67cba72d940",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/7e2670988ab73dfcd2e07303b22c971649cf3f86d571e2b7a6c40662ed7a1040.json",
          "token1": "data/raw/public_rpc/eb8432925cef8aec2fc5a84ce395d3614f70189236ff638018c795362f2d935e.json",
          "factory": "data/raw/public_rpc/7b3e1929c1b4be22be8f4927e5fea24be20488390b8763d131adaec2c3db14b6.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 8,
        "decimals1": 18
      },
      "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed": {
        "pool": "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/3b823bb6ccae68aaf4ce0c5166924e43bee9b2f45126d3581d318e6d7b1668c7.json",
          "token1": "data/raw/public_rpc/8ca782b34b3575832bb08a8ef1532180ad52422431510f566412a448791eba20.json",
          "factory": "data/raw/public_rpc/bd7d50312152092d243ed06375555786a8a3b48a0e55df4145b8fcaedf4f385d.json",
          "fee": "data/raw/public_rpc/cbec2b7808e4e5f5c1074f8bd071cab82a9f33faada1850c4dbfa0441614a5ec.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 3000,
        "decimals0": 8,
        "decimals1": 18
      },
      "0xe6ff8b9a37b0fab776134636d9981aa778c4e718": {
        "pool": "0xe6ff8b9a37b0fab776134636d9981aa778c4e718",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/9631d9b160b372fe0351754134cf51ec9c058168f99ea92d29a1cb288c841fcd.json",
          "token1": "data/raw/public_rpc/091a9ba2871b6bad9aaee75469f2d78e538e203b4c5aa687f563b3d3c8a4eb10.json",
          "factory": "data/raw/public_rpc/377f10bd922bafd28c430367e42068c7ca2a7d312e4a5f9f9f2224d52698ce1c.json",
          "fee": "data/raw/public_rpc/bb29c247de05ccb256ca271d82b76f8b7248a016677389b11bd8d234ec120d70.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "fee_pips": 100,
        "decimals0": 8,
        "decimals1": 18
      },
      "0xceff51756c56ceffca006cd410b03ffc46dd3a58": {
        "pool": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
        "protocol": "V2-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/7ecd507bd0f88ac2dfb25522256ec12596fc7439dec6d6b7b26f87d58a1bbb11.json",
          "token1": "data/raw/public_rpc/2103f7252142bde0075646231d386554088005466ac09d47ef99f19568fe6551.json",
          "factory": "data/raw/public_rpc/f5bb1cd64183c3c23dc4d40d8223eb9da9a645141bcae3cb0e52676ce16e8326.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 8,
        "decimals1": 18
      },
      "0x7486ff76f69872d27b22dada4078bd55b36a5324": {
        "pool": "0x7486ff76f69872d27b22dada4078bd55b36a5324",
        "protocol": "V3-compatible (event only)",
        "block": 26300991,
        "sources": {
          "token0": "data/raw/public_rpc/9b31c17f6913bfaf70640f1bef4f90a5fd46dfda02cbfe390f5fc3b8fb4e2290.json",
          "token1": "data/raw/public_rpc/ac7d2e9204b376f9729e20e3185e6f3f79551b2a963a0eca7a2ec65f7d6d6d98.json",
          "factory": "data/raw/public_rpc/706ee6f33bd4ed88ddf0374f04fbaf09334d35dd6875c812bd87c232e5520f0f.json",
          "fee": "data/raw/public_rpc/5f151fda4955ec4c821a746ba66bd6e30743afe536744c3e305f3917cc435fef.json",
          "decimals0": "data/raw/public_rpc/b43a685a331982e835a685fad2e7fda25601417461c47d104ccb6df2104a3d1d.json",
          "decimals1": "data/raw/public_rpc/655dd788f4fbc7a5f1e930d9ba8a3385bc32f73c3907a56ee063c369adaf71da.json"
        },
        "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0xbaceb8ec6b9355dfc0269c18bac9d6e2bdc29c4f",
        "fee_pips": 3000,
        "decimals0": 8,
        "decimals1": 18
      }
    },
    "evidence": {
      "header": "data/raw/objects/6a75fa8db5db47b4bf91177a263eff0c2f8d0f86e5d1b50030e3978cae00e820.json.gz",
      "receipts": "data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz",
      "traces": "data/raw/objects/23846b66bf1cab96103c57df38e1e1fe8325a258a58b52f8ec84326165c20365.json.gz"
    },
    "classification": "observed_inventory_closed_profitable_atomic_arbitrage",
    "attribution_limit": "Same-block/pool association is observed. This cash flow is not all causally attributable to removing the hacker's trade; operational boundary is not beneficial ownership."
  },
  {
    "token_net_raw": {},
    "other_token_residual_raw": {},
    "native_net_wei": "1037969594978888",
    "gas_wei": "972496905296097",
    "identified_builder_payment_wei": "1828100586247377",
    "cashflow_before_gas_ETH": "0.001037969594978888",
    "gross_after_pool_fees_before_gas_and_builder_ETH": "0.002866070181226265",
    "net_after_gas_and_builder_ETH": "0.000065472689682791",
    "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again.",
    "pool_flow_surplus_ETH": "0.002866070181226265",
    "unallocated_pool_surplus_vs_operational_gross_ETH": "0E-18",
    "case_id": "A2",
    "block": 26302300,
    "tx_hash": "0xa48203e21f385c7685c5656c7492feae9498c6c40b53c709a39d8b94639eb851",
    "target": "0x2ccafec913543cb6a8f13d9bf8f4fc77b3adb0b9bed4e32171560dac9670976d",
    "accounts": [
      "0x0124d0fa0dfb1430dfcff16ec6a96945e7a0bc10",
      "0x36331e299247e5d0d3261e1d9852f6e0cffee95c"
    ],
    "route_label": "WETH / SHIB two-pool cycle",
    "timestamp_utc": "2026-10-30T01:31:47+00:00",
    "sender": "0x0124d0fa0dfb1430dfcff16ec6a96945e7a0bc10",
    "executor": "0x36331e299247e5d0d3261e1d9852f6e0cffee95c",
    "actor_index": 333,
    "target_index": 329,
    "same_pool_opposite_direction": [
      "0xcf6daab95c476106eca715d48de4b13287ffdeaa"
    ],
    "route": [
      {
        "pool": "0x811beed0119b4afce20d2583eb608c6f7af1954f",
        "input_token": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "input_raw": "263597153258982257484624477",
        "output_raw": "527170826041131280",
        "input_quantity": "263597153.258982257484624477",
        "output_quantity": "0.52717082604113128",
        "output_per_input": "1.99991092287400325005001828161744121941887258873686311602303625360499560792031614480429949E-9",
        "swap_log_indices": [
          575
        ],
        "protocol": "V2-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0xcf6daab95c476106eca715d48de4b13287ffdeaa",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "input_raw": "524304755859905015",
        "output_raw": "263597153258982257484624477",
        "input_quantity": "0.524304755859905015",
        "output_quantity": "263597153.258982257484624477",
        "output_per_input": "502755602.181521687418968835514692771024374135252490689046096797745913628883354633635459782",
        "swap_log_indices": [
          573
        ],
        "protocol": "V2-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      }
    ],
    "metadata": {
      "0xcf6daab95c476106eca715d48de4b13287ffdeaa": {
        "pool": "0xcf6daab95c476106eca715d48de4b13287ffdeaa",
        "protocol": "V2-compatible (event only)",
        "block": 26302299,
        "sources": {
          "token0": "data/raw/public_rpc/66351b5f7436bf921497a026e7903c917a5698df0ac1da4b648ff63d929c8707.json",
          "token1": "data/raw/public_rpc/cd7ff44c8bd50bee9b587f90010240c00e85c0c28957941d40116bbfd707be20.json",
          "factory": "data/raw/public_rpc/6a22da88650ab51edb2f77c53e6f9662341012f58fe29a91f7b788803532b36e.json",
          "decimals0": "data/raw/public_rpc/b7dbd0f8ec2c4b8caeb06473d4f9f342a45ace84de4dbb38603f599f15b966f6.json",
          "decimals1": "data/raw/public_rpc/5901a64ae084be2e97a4e61ceff229d53e35b83474c9aa27842871d412222cb4.json"
        },
        "token0": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x115934131916c8b277dd010ee02de363c09d037c",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 18,
        "decimals1": 18
      },
      "0x811beed0119b4afce20d2583eb608c6f7af1954f": {
        "pool": "0x811beed0119b4afce20d2583eb608c6f7af1954f",
        "protocol": "V2-compatible (event only)",
        "block": 26302299,
        "sources": {
          "token0": "data/raw/public_rpc/03fa8b83e10d6bd03949b9db539287cf3b72d85ef53543bd6e46bf21f3e7c743.json",
          "token1": "data/raw/public_rpc/3468d4476486f58c3934cbd7629159956e6ef731af126e591d0f6ada974f13f1.json",
          "factory": "data/raw/public_rpc/390b8ae24613398b7cd9d2dad59daaff0bfd67436b2f30c076374fc9c47fe102.json",
          "decimals0": "data/raw/public_rpc/b7dbd0f8ec2c4b8caeb06473d4f9f342a45ace84de4dbb38603f599f15b966f6.json",
          "decimals1": "data/raw/public_rpc/5901a64ae084be2e97a4e61ceff229d53e35b83474c9aa27842871d412222cb4.json"
        },
        "token0": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 18,
        "decimals1": 18
      }
    },
    "evidence": {
      "header": "data/raw/objects/45133a022257bd66fbd1201c9cddb42ecb54581e9990e5c30bc4fe534c439fa1.json.gz",
      "receipts": "data/raw/objects/56a8dc4e6a3b2d391906afafbb810f4ad15c4755fb3613394e183fdbfe0ebc3d.json.gz",
      "traces": "data/raw/objects/6c11b035027eb7bbe905188bf5321fa5b7612cc4f205bd2ec8ee26f408bd2e7d.json.gz"
    },
    "classification": "observed_inventory_closed_profitable_atomic_arbitrage",
    "attribution_limit": "Same-block/pool association is observed. This cash flow is not all causally attributable to removing the hacker's trade; operational boundary is not beneficial ownership."
  },
  {
    "token_net_raw": {
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "7001958297245002"
    },
    "other_token_residual_raw": {},
    "native_net_wei": "-2398332464181997",
    "gas_wei": "2419126290265662",
    "identified_builder_payment_wei": "2398332464181997",
    "cashflow_before_gas_ETH": "0.004603625833063005",
    "gross_after_pool_fees_before_gas_and_builder_ETH": "0.007001958297245002",
    "net_after_gas_and_builder_ETH": "0.002184499542797343",
    "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again.",
    "pool_flow_surplus_ETH": "0.007001958297245002",
    "unallocated_pool_surplus_vs_operational_gross_ETH": "0E-18",
    "case_id": "A3",
    "block": 26302437,
    "tx_hash": "0xbe7e1a0554942e23cb6c960274ab52033c9851445810c061a1f34f9e041d74a4",
    "target": "0xbf3fc95e45d932b1ad0a55e91e77fea8652906a3eeb0efd65850976059aef9d7",
    "accounts": [
      "0x5205b8122e1f6fa6066ba487e49f6e4cc81c2cbd",
      "0xe45572dff1865af5f12208b09ce7506847f628bd"
    ],
    "route_label": "WETH / AXS two-pool cycle",
    "timestamp_utc": "2026-10-30T01:59:11+00:00",
    "sender": "0x5205b8122e1f6fa6066ba487e49f6e4cc81c2cbd",
    "executor": "0xe45572dff1865af5f12208b09ce7506847f628bd",
    "actor_index": 33,
    "target_index": 3,
    "same_pool_opposite_direction": [
      "0x0c365789dbbb94a29f8720dc465554c587e897db"
    ],
    "route": [
      {
        "pool": "0x0c365789dbbb94a29f8720dc465554c587e897db",
        "input_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "output_token": "0xbb0e17ef65f82ab018d8edd776e8dd940327b28b",
        "input_raw": "30182152608108832",
        "output_raw": "113083412574719274907",
        "input_quantity": "0.030182152608108832",
        "output_quantity": "113.083412574719274907",
        "output_per_input": "3746.69805838626400016344739158951282224855054117447678062919492024491997620078778143689505",
        "swap_log_indices": [
          176
        ],
        "protocol": "V2-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      },
      {
        "pool": "0xa040832b1e5026da6dc843e6773a9e4d02fff9b1",
        "input_token": "0xbb0e17ef65f82ab018d8edd776e8dd940327b28b",
        "output_token": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "input_raw": "113083412574719274907",
        "output_raw": "37184110905353834",
        "input_quantity": "113.083412574719274907",
        "output_quantity": "0.037184110905353834",
        "output_per_input": "0.000328820205003847285801898113567471063980735663399401094429840729170956563880223921463967513",
        "swap_log_indices": [
          173
        ],
        "protocol": "V2-compatible (event only)",
        "fee_pips": 3000,
        "fee_note": "Pool fees embedded in observed net proceeds; fee tier alone does not allocate fee-growth to individual LPs."
      }
    ],
    "metadata": {
      "0xa040832b1e5026da6dc843e6773a9e4d02fff9b1": {
        "pool": "0xa040832b1e5026da6dc843e6773a9e4d02fff9b1",
        "protocol": "V2-compatible (event only)",
        "block": 26302436,
        "sources": {
          "token0": "data/raw/public_rpc/8525e0eb50118a654d67abba3d5570b8658e01fa211a73c2bdaf47f5f0ee3923.json",
          "token1": "data/raw/public_rpc/4a5d8b30881d718eb0851669bb28499705d916d47685a13e09e972e4aaff5396.json",
          "factory": "data/raw/public_rpc/e694021cddfc9ee89a28dcc3969cf71553ead311d29c676cd71f26888434819b.json",
          "decimals0": "data/raw/public_rpc/e0aa821c9db617b64058221bf3a73690de751aac1f941f54c39bf4cfb25f6cd7.json",
          "decimals1": "data/raw/public_rpc/9bb48d8535eaef902359d792eeb3f173326b54a7a451e38659c690bc850eb800.json"
        },
        "token0": "0xbb0e17ef65f82ab018d8edd776e8dd940327b28b",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 18,
        "decimals1": 18
      },
      "0x0c365789dbbb94a29f8720dc465554c587e897db": {
        "pool": "0x0c365789dbbb94a29f8720dc465554c587e897db",
        "protocol": "V2-compatible (event only)",
        "block": 26302436,
        "sources": {
          "token0": "data/raw/public_rpc/9f3357755f9f555c84ae7d8e43fbe78befe3c18599a41b73a3049d0c694b7a53.json",
          "token1": "data/raw/public_rpc/6ef9bb705ac29e086f1cb01f3d7bb7e60eba86d8027355ef6fa7073c80ae2942.json",
          "factory": "data/raw/public_rpc/cbf245435b718325a1493d16753331bd59360ff70767b33d44d5f34b13094273.json",
          "decimals0": "data/raw/public_rpc/e0aa821c9db617b64058221bf3a73690de751aac1f941f54c39bf4cfb25f6cd7.json",
          "decimals1": "data/raw/public_rpc/9bb48d8535eaef902359d792eeb3f173326b54a7a451e38659c690bc850eb800.json"
        },
        "token0": "0xbb0e17ef65f82ab018d8edd776e8dd940327b28b",
        "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "factory": "0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac",
        "fee_pips": 3000,
        "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
        "decimals0": 18,
        "decimals1": 18
      }
    },
    "evidence": {
      "header": "data/raw/objects/17e4f5d5610dab0ff277d8f39b898a375b68d3cccd4e9e924d5e88c9fddbd192.json.gz",
      "receipts": "data/raw/objects/8f52986bdac633f9e6fdadacb25bdb0e1dce4ccde853426255d232d4978487ca.json.gz",
      "traces": "data/raw/objects/7931587fbae126fbc90c97a183137280b6ca7af4d9b9108c2e72f2543727648c.json.gz"
    },
    "classification": "observed_inventory_closed_profitable_atomic_arbitrage",
    "attribution_limit": "Same-block/pool association is observed. This cash flow is not all causally attributable to removing the hacker's trade; operational boundary is not beneficial ownership."
  }
]
```

<a id="slide-7"></a>
## Slide 7 — A complete sandwich episode

Block26,301,609; indices9/10/11. Front≈−555.599628ETH; back≈+567.679662ETH. Full episode net12.080033775421395622ETH. Back-leg proceeds are not episode profit. No causal incremental victim loss established.

Source files (paths relative to new/):

- [reports/case_studies/S1_sandwich.json](../../reports/case_studies/S1_sandwich.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
{
  "case_id": "S1",
  "block": 26301609,
  "front": "0xb85a8b174f8258c4d729e3b1112fe46fe90b6e4d761792b47b133e9dd77f2d7b",
  "target": "0x625e674d10c864a1d98d8ba9b5c05ed2f325d74cca62b8b67cd6268edbd8f051",
  "back": "0xf3935c9604416f38ea2942652ea8c652bc2ea0cfac2ad0316181031bdcd607c2",
  "accounts": [
    "0x45e9b04942176a513b22acc1ced75c34d2fd9215",
    "0x4cd4499d6e6a0eb8995a2cabd400d1ad35c4d03e",
    "0x5aae4d2f360e156de3416936049837a7bb685588"
  ],
  "pool": "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f",
  "front_cashflow": {
    "token_net_raw": {
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "-555550581789369600566"
    },
    "other_token_residual_raw": {},
    "native_net_wei": "0",
    "gas_wei": "49047195733257436",
    "identified_builder_payment_wei": "0",
    "cashflow_before_gas_ETH": "-555.550581789369600566",
    "gross_after_pool_fees_before_gas_and_builder_ETH": "-555.550581789369600566",
    "net_after_gas_and_builder_ETH": "-555.599628985102858002",
    "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again."
  },
  "back_cashflow": {
    "token_net_raw": {
      "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "567748941300978878840"
    },
    "other_token_residual_raw": {},
    "native_net_wei": "0",
    "gas_wei": "69278540454625216",
    "identified_builder_payment_wei": "5177157980132707435",
    "cashflow_before_gas_ETH": "567.74894130097887884",
    "gross_after_pool_fees_before_gas_and_builder_ETH": "572.926099281111586275",
    "net_after_gas_and_builder_ETH": "567.679662760524253624",
    "payment_note": "Direct native transfers to block fee recipient only; not assumed to identify every searcher payment. Pool trading fees are already embedded in swap proceeds and are NOT deducted again."
  },
  "episode_net_ETH": "12.080033775421395622",
  "episode_gas_ETH": "0.118325736187882652",
  "episode_builder_payment_ETH": "5.177157980132707435",
  "evidence": {
    "header": "data/raw/objects/44e58ce84954e269e6621a13c32f0eb00d62e8aa5ed0a6c8fb98283334ce330f.json.gz",
    "receipts": "data/raw/objects/52ef85116cfa424378c8d1eb68f9f2b0a17c210d7162190d9b7d3e3f7b9db15e.json.gz",
    "traces": "data/raw/objects/b6f380c27c683a582cdcb8c5ef8b5ac26e854347c4f75379576b2f9102a2011b.json.gz"
  },
  "transaction_indices": [
    9,
    10,
    11
  ],
  "metadata": {
    "0x11950d141ecb863f01007add7d1a342041227b58": {
      "pool": "0x11950d141ecb863f01007add7d1a342041227b58",
      "protocol": "V3-compatible (event only)",
      "block": 26301608,
      "sources": {
        "token0": "data/raw/public_rpc/509616967ce8a864ecd50acecbdde95570b93905ce1351ebf2a58efa777c5192.json",
        "token1": "data/raw/public_rpc/880586fd3a6f277cfb073dcfb81f9cc38ba7bb5fe605535b64a2ed6cd151693e.json",
        "factory": "data/raw/public_rpc/e9e9fefe2ad43da1bcad0620d0c63423131136276bde2fe17f27307265ee5b65.json",
        "fee": "data/raw/public_rpc/7029df2ea1695ea5f98c21ac6c95caf4d813f63e32233f78a3bc5023b2477399.json",
        "decimals0": "data/raw/public_rpc/1fb4cc29cbb1e48dbe5b2024522fb0d050ec1a6675765464e943ce261f03919d.json",
        "decimals1": "data/raw/public_rpc/646d6c6d387d7be6cc9cdc61bf3778393bf7209be291e8590d90ca3e37b125a1.json"
      },
      "token0": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
      "fee_pips": 3000,
      "decimals0": 18,
      "decimals1": 18
    },
    "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f": {
      "pool": "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f",
      "protocol": "V2-compatible (event only)",
      "block": 26301608,
      "sources": {
        "token0": "data/raw/public_rpc/d34fa54a93aa46d8e975676bbb42fc423695a72ef4662fbc71efc2764ed8611d.json",
        "token1": "data/raw/public_rpc/5f965de214afa07c9f2897c70e1c01e040dca6d0b13813193e1f5a8b9788a36d.json",
        "factory": "data/raw/public_rpc/f26fc057c0d253c2ad7270222483d69d3dd03fc95cbfbad97cfb7264d52dd1e9.json",
        "decimals0": "data/raw/public_rpc/1fb4cc29cbb1e48dbe5b2024522fb0d050ec1a6675765464e943ce261f03919d.json",
        "decimals1": "data/raw/public_rpc/646d6c6d387d7be6cc9cdc61bf3778393bf7209be291e8590d90ca3e37b125a1.json"
      },
      "token0": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
      "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
      "factory": "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f",
      "fee_pips": 3000,
      "fee_assumption": "997/1000 V2 model tested against observed amount-out; suboptimal outputs retain nonzero model residuals. Not inferred from event topic alone.",
      "decimals0": 18,
      "decimals1": 18
    }
  },
  "classification": "same-sender inventory-closed directional sandwich with cross-pool back leg",
  "limit": "Bracketing and observed PnL are established. Incremental victim loss requires a separate executable counterfactual; back-leg cash inflow alone is not episode profit."
}
```

<a id="slide-8"></a>
## Slide 8 — Auction results and proposer payments

A1/A2/A3 proposer payments36.437514095553389525,3.120166160586952436,0.578802351165718120ETH. All3 exactly reconcile. SELFDESTRUCT forwarding matters; A3 payer differs from fee recipient. Whole-block payments are not solely one searcher’s cost.

Source files (paths relative to new/):

- [data/processed/auction_outcomes.json](../../data/processed/auction_outcomes.json)
- [data/processed/proposer_payments.parquet](../../data/processed/proposer_payments.parquet)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "case_id": "A1",
    "block": 26300992,
    "slot": 15540344,
    "block_hash": "0x7b7f6cd5e75c6afbb6db23d13ea27aeda34f01c851b953b79b876da6f3365793",
    "timestamp_utc": "2026-10-29T21:09:11+00:00",
    "relays": [
      "ultrasound"
    ],
    "builder_pubkey": "0x88857150299287cedfbadea1ee3fb7ac121f1e4e16bef44b4a7bad35432973c4009efb90394facca3fdc0759ba70f93f",
    "proposer_pubkey": "0xb532943de7e0c619f1911cda18f38fd98a3f326e1239f7ca96665b166e33342b1b595accd814e4bb7ba5488ea1d5ad0f",
    "builder_fee_recipient": "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97",
    "proposer_fee_recipient": "0x388c818ca8b9251b393131c08a736a67ccb19297",
    "delivered_value_wei": "36437514095553389525",
    "onchain_proposer_payment_wei": "36437514095553389525",
    "proposer_payment_exact_match": true,
    "proposer_payment_payers": [
      "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97"
    ],
    "fee_recipient_funded_proposer_wei": "36437514095553389525",
    "separate_payer_proposer_wei": "0",
    "whole_block_priority_wei": "725813224783048078",
    "whole_block_native_receipts_wei": "86133252907079031203",
    "whole_block_other_native_outflow_wei": "550685620864951701",
    "fee_recipient_own_gas_wei": "9948873739923090",
    "builder_execution_balance_margin_proxy_wei": "49860917541703814965",
    "whole_block_base_burn_wei": "6850377652681750000",
    "builder_margin_proxy_wei": "49860917541703814965",
    "builder_margin_status": "partial execution-ETH proxy",
    "selected_searcher_gross_after_pool_fees_ETH": "12.137824203978034597",
    "selected_searcher_retained_ETH": "2.745812294499937065",
    "selected_searcher_direct_builder_wei": "8252947611860856740",
    "selected_searcher_priority_wei": "91661779990833822",
    "selected_searcher_burn_wei": "1047402517626406970",
    "selected_searcher_tx_hash": "0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c",
    "relay_evidence": "data/raw/objects/470d9d1a09515fed98f006920385c0fd9cf426cdcf3e751b42e750405cb06898.json",
    "evidence": {
      "header": "data/raw/objects/6a75fa8db5db47b4bf91177a263eff0c2f8d0f86e5d1b50030e3978cae00e820.json.gz",
      "receipts": "data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz",
      "traces": "data/raw/objects/23846b66bf1cab96103c57df38e1e1fe8325a258a58b52f8ec84326165c20365.json.gz"
    },
    "limits": "Builder proxy is execution-ETH cash flow, not exact realized profit: excludes token positions, withdrawals, offchain costs and financing. Whole-block proposer payment cannot be causally allocated to this single searcher. Searcher pool fees are already embedded in gross observed swap surplus."
  },
  {
    "case_id": "A2",
    "block": 26302300,
    "slot": 15541657,
    "block_hash": "0x4ed95783368be58748f1f89890b435dfc5a9f82f40fcf45f554e2ea02a04fbe1",
    "timestamp_utc": "2026-10-30T01:31:47+00:00",
    "relays": [
      "aestus",
      "ultrasound"
    ],
    "builder_pubkey": "0xa73f9853fcccb73f888def9d332b54393a642d4b562b9a9cb13eb95938fc4616d2c5b2e6df382255e7016775328860f6",
    "proposer_pubkey": "0xac3312eacf241eeacac91a5d0c9f3d9fa8a243479050a0553b3c29dfc7f416019f1e9ce81ec1d0bd6ef2c58cf21d6170",
    "builder_fee_recipient": "0x6c42a0b5d13059fa36d5567ab04f83bab57bbf0e",
    "proposer_fee_recipient": "0x73f7b1184b5cd361cc0f7654998953e2a251dd58",
    "delivered_value_wei": "3120166160586952436",
    "onchain_proposer_payment_wei": "3120166160586952436",
    "proposer_payment_exact_match": true,
    "proposer_payment_payers": [
      "0x6c42a0b5d13059fa36d5567ab04f83bab57bbf0e"
    ],
    "fee_recipient_funded_proposer_wei": "3120166160586952436",
    "separate_payer_proposer_wei": "0",
    "whole_block_priority_wei": "48721382786983102",
    "whole_block_native_receipts_wei": "3335866184701098162",
    "whole_block_other_native_outflow_wei": "13837843249715799",
    "fee_recipient_own_gas_wei": "736563000280632",
    "builder_execution_balance_margin_proxy_wei": "249847000651132397",
    "whole_block_base_burn_wei": "299596930570602487",
    "builder_margin_proxy_wei": "249847000651132397",
    "builder_margin_status": "partial execution-ETH proxy",
    "selected_searcher_gross_after_pool_fees_ETH": "0.002866070181226265",
    "selected_searcher_retained_ETH": "0.000065472689682791",
    "selected_searcher_direct_builder_wei": "1828100586247377",
    "selected_searcher_priority_wei": "0",
    "selected_searcher_burn_wei": "972496905296097",
    "selected_searcher_tx_hash": "0xa48203e21f385c7685c5656c7492feae9498c6c40b53c709a39d8b94639eb851",
    "relay_evidence": "data/raw/objects/9ff9a3e3cadb5c8e514571a4201d636517bc900bad967154ecb94643fda1fc4d.json",
    "evidence": {
      "header": "data/raw/objects/45133a022257bd66fbd1201c9cddb42ecb54581e9990e5c30bc4fe534c439fa1.json.gz",
      "receipts": "data/raw/objects/56a8dc4e6a3b2d391906afafbb810f4ad15c4755fb3613394e183fdbfe0ebc3d.json.gz",
      "traces": "data/raw/objects/6c11b035027eb7bbe905188bf5321fa5b7612cc4f205bd2ec8ee26f408bd2e7d.json.gz"
    },
    "limits": "Builder proxy is execution-ETH cash flow, not exact realized profit: excludes token positions, withdrawals, offchain costs and financing. Whole-block proposer payment cannot be causally allocated to this single searcher. Searcher pool fees are already embedded in gross observed swap surplus."
  },
  {
    "case_id": "A3",
    "block": 26302437,
    "slot": 15541794,
    "block_hash": "0x8217239f2fd9eaef9cbb8da30993321b357e1ad7bdf6c95fd5ca06176e2a7ba8",
    "timestamp_utc": "2026-10-30T01:59:11+00:00",
    "relays": [
      "ultrasound"
    ],
    "builder_pubkey": "0x88857150299287cedfbadea1ee3fb7ac121f1e4e16bef44b4a7bad35432973c4009efb90394facca3fdc0759ba70f93f",
    "proposer_pubkey": "0xb3692da73d53c7a05e234024765b62418bee74d1b42ce03f9a6a765bbd9223e87f071b19230475ff41bd128623604e45",
    "builder_fee_recipient": "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97",
    "proposer_fee_recipient": "0x388c818ca8b9251b393131c08a736a67ccb19297",
    "delivered_value_wei": "578802351165718120",
    "onchain_proposer_payment_wei": "578802351165718120",
    "proposer_payment_exact_match": true,
    "proposer_payment_payers": [
      "0x9fc3da866e7df3a1c57ade1a97c9f00a70f010c8"
    ],
    "fee_recipient_funded_proposer_wei": "0",
    "separate_payer_proposer_wei": "578802351165718120",
    "whole_block_priority_wei": "558875452413728985",
    "whole_block_native_receipts_wei": "254763915110230872",
    "whole_block_other_native_outflow_wei": "1247813896231108",
    "fee_recipient_own_gas_wei": "201475703768892",
    "builder_execution_balance_margin_proxy_wei": "812190077923959857",
    "whole_block_base_burn_wei": "280797254823906198",
    "builder_margin_proxy_wei": null,
    "builder_margin_status": "unresolved: proposer payer differs from fee recipient; common economic ownership not assumed",
    "selected_searcher_gross_after_pool_fees_ETH": "0.007001958297245002",
    "selected_searcher_retained_ETH": "0.002184499542797343",
    "selected_searcher_direct_builder_wei": "2398332464181997",
    "selected_searcher_priority_wei": "3479670000000",
    "selected_searcher_burn_wei": "2415646620265662",
    "selected_searcher_tx_hash": "0xbe7e1a0554942e23cb6c960274ab52033c9851445810c061a1f34f9e041d74a4",
    "relay_evidence": "data/raw/objects/dc7efe053bb80925c0370a02c0403f1d7084de996109588ff43e17114fb0c778.json",
    "evidence": {
      "header": "data/raw/objects/17e4f5d5610dab0ff277d8f39b898a375b68d3cccd4e9e924d5e88c9fddbd192.json.gz",
      "receipts": "data/raw/objects/8f52986bdac633f9e6fdadacb25bdb0e1dce4ccde853426255d232d4978487ca.json.gz",
      "traces": "data/raw/objects/7931587fbae126fbc90c97a183137280b6ca7af4d9b9108c2e72f2543727648c.json.gz"
    },
    "limits": "Builder proxy is execution-ETH cash flow, not exact realized profit: excludes token positions, withdrawals, offchain costs and financing. Whole-block proposer payment cannot be causally allocated to this single searcher. Searcher pool fees are already embedded in gross observed swap surplus."
  }
]
```

<a id="slide-9"></a>
## Slide 9 — Auction coverage and sensitivity

2,939 delivered blocks/3,311; baseline109/130,event2,830/3,181.7,958 retained submissions;3slots,4relays. Revisions/late bids may appear. Drop Ultrasound:3,129 records,1/3retained relay outcome support,3/3independent onchain payments. No decision cutoff known.

Source files (paths relative to new/):

- [data/processed/auction_submissions.json](../../data/processed/auction_submissions.json)
- [data/processed/auction_coverage.json](../../data/processed/auction_coverage.json)
- [data/processed/auction_timing_assessment.json](../../data/processed/auction_timing_assessment.json)
- [data/processed/loss_reconciliation.json](../../data/processed/loss_reconciliation.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "removed_relay": null,
    "submission_observations": 7958,
    "selected_delivered_outcomes_with_retained_relay_support": 3,
    "selected_onchain_proposer_payment_matches": 3,
    "meaning": "Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed."
  },
  {
    "removed_relay": "aestus",
    "submission_observations": 6762,
    "selected_delivered_outcomes_with_retained_relay_support": 3,
    "selected_onchain_proposer_payment_matches": 3,
    "meaning": "Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed."
  },
  {
    "removed_relay": "agnostic",
    "submission_observations": 6633,
    "selected_delivered_outcomes_with_retained_relay_support": 3,
    "selected_onchain_proposer_payment_matches": 3,
    "meaning": "Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed."
  },
  {
    "removed_relay": "flashbots",
    "submission_observations": 7350,
    "selected_delivered_outcomes_with_retained_relay_support": 3,
    "selected_onchain_proposer_payment_matches": 3,
    "meaning": "Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed."
  },
  {
    "removed_relay": "ultrasound",
    "submission_observations": 3129,
    "selected_delivered_outcomes_with_retained_relay_support": 1,
    "selected_onchain_proposer_payment_matches": 3,
    "meaning": "Onchain payment remains observed even when a relay source is removed; no missing losing bids imputed."
  }
]
```

<a id="slide-10"></a>
## Slide 10 — Largest abnormal swaps

N1–N5 shortfalls≈USD8.374M,6.047M,4.279M,3.257M,2.001M.810two-sided rows;621complete valuations;241qualify(input>USD100k and loss>5%).Five aboveUSD1M,two aboveUSD5M. No deliberate loss proven.

Source files (paths relative to new/):

- [data/processed/suspicious_transactions.parquet](../../data/processed/suspicious_transactions.parquet)
- [data/processed/anomaly_case_studies.json](../../data/processed/anomaly_case_studies.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "case_id": "N1",
    "tx_hash": "0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6",
    "address": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
    "timestamp_utc": "2026-10-29T21:09:11+00:00",
    "input_reference_USD": "29961300.00000",
    "output_reference_USD": "21587296.079792046691378820",
    "loss_USD": "8374003.920207953308621180",
    "loss_rate": "0.279494011281484892465319595611672390717358726089989419684726630686919459436005780790553147",
    "final_classification": "insufficient_evidence"
  },
  {
    "case_id": "N2",
    "tx_hash": "0xcb8075f1d07bc56e54e59ccd4477d75b6a7b21f265dabe2ee86beeb3f3b38a9d",
    "address": "0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb",
    "timestamp_utc": "2026-10-29T21:05:59+00:00",
    "input_reference_USD": "29962500.00000",
    "output_reference_USD": "23915444.57507889215845872864",
    "loss_USD": "6047055.42492110784154127136",
    "loss_rate": "0.201820790151726586284231000750938673341677096370463078848560700876095118898623279098873592",
    "final_classification": "insufficient_evidence"
  },
  {
    "case_id": "N3",
    "tx_hash": "0x808f54a951b7fd051600937b45c6c3fb42d59850c6bf459cea8615dfadbcad39",
    "address": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
    "timestamp_utc": "2026-10-29T21:08:23+00:00",
    "input_reference_USD": "19974400.00000",
    "output_reference_USD": "15695652.83192229034611203100",
    "loss_USD": "4278747.16807770965388796900",
    "loss_rate": "0.214211549186844643838511745033643063120794617109900672861262415892342198013457225248317847",
    "final_classification": "insufficient_evidence"
  },
  {
    "case_id": "N4",
    "tx_hash": "0xb7d294873bf18a56ce99115794b8a9a76542791b58456e7a4f94d74f1ae4e41f",
    "address": "0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb",
    "timestamp_utc": "2026-10-29T21:04:47+00:00",
    "input_reference_USD": "19975200.00000",
    "output_reference_USD": "16718091.17233770638788479885",
    "loss_USD": "3257108.82766229361211520115",
    "loss_rate": "0.163057632847846009657735649705634987384356602186711522287636669470142977291841883936080740",
    "final_classification": "insufficient_evidence"
  },
  {
    "case_id": "N5",
    "tx_hash": "0x152e005f6dcccd941e0a2c7156b955c6baad08a347685bcf5518776dab04f8cc",
    "address": "0x0ddf0480016e6bcb2c1f5d190d221fba1320697e",
    "timestamp_utc": "2026-10-29T20:47:47+00:00",
    "input_reference_USD": "9987600.00000",
    "output_reference_USD": "7986831.0487678346085142768",
    "loss_USD": "2000768.9512321653914857232",
    "loss_rate": "0.200325298493348291029448836557331090552284833193159517802074572469862629660779366414353799",
    "final_classification": "insufficient_evidence"
  }
]
```

<a id="slide-11"></a>
## Slide 11 — Slippage protection and intent

All5 have zero intermediate minima AND nonzero final unwrap minima. Zero-bound counts18/17/17/16/16. N3/N4 internal execute calls decoded despite unsupported root selector. Classification:insufficient_evidence. Adjacent profits and later incoming transfers are not compensating-profit proof.

Source files (paths relative to new/):

- [data/processed/anomaly_case_studies.json](../../data/processed/anomaly_case_studies.json)
- [src/decoding/router.py](../../src/decoding/router.py)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "case": "N1",
    "zero_minima": 18,
    "nonzero_bounds": [
      {
        "command_location": "19",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
        "bound_raw": "4934380635394559234997",
        "bound_kind": "unwrap_minimum",
        "trace_address": []
      }
    ],
    "intent_established": false
  },
  {
    "case": "N2",
    "zero_minima": 17,
    "nonzero_bounds": [
      {
        "command_location": "18",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb",
        "bound_raw": "5036275042459249547130",
        "bound_kind": "unwrap_minimum",
        "trace_address": []
      }
    ],
    "intent_established": false
  },
  {
    "case": "N3",
    "zero_minima": 17,
    "nonzero_bounds": [
      {
        "command_location": "18",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
        "bound_raw": "3288582155412741290554",
        "bound_kind": "unwrap_minimum",
        "trace_address": [
          2
        ]
      }
    ],
    "intent_established": false
  },
  {
    "case": "N4",
    "zero_minima": 16,
    "nonzero_bounds": [
      {
        "command_location": "17",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb",
        "bound_raw": "3370036000278739766929",
        "bound_kind": "unwrap_minimum",
        "trace_address": [
          2
        ]
      }
    ],
    "intent_established": false
  },
  {
    "case": "N5",
    "zero_minima": 16,
    "nonzero_bounds": [
      {
        "command_location": "18",
        "command_type": 12,
        "allow_revert": false,
        "recipient": "0x0ddf0480016e6bcb2c1f5d190d221fba1320697e",
        "bound_raw": "1980814897275601244478",
        "bound_kind": "unwrap_minimum",
        "trace_address": []
      }
    ],
    "intent_established": false
  }
]
```

<a id="slide-12"></a>
## Slide 12 — Three matched THORChain paths

17Nov2026:T1 36ETH→1.00484202BTC;T2 61ETH→1.68897154BTC;T3 40ETH→1.10797406BTC. Estimated deposit-time shortfallsUSD316.17/754.33/429.72. Every path matches ETHreceipt,THORNode,Midgard and confirmed BTCvout/OUTmemo. Prior funding association is not exclusive taint/control.

Source files (paths relative to new/):

- [data/processed/thorchain_paths.json](../../data/processed/thorchain_paths.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
[
  {
    "case_id": "T1",
    "ethereum_deposit": "0x8136b0834bb7d45761421875688a3a2106051e3d9f3fd23e351ffef3ad384172",
    "source_address": "0x8b8820b6e1f9d158c0cb0a1d07cb42609da38b69",
    "source_block": 26435121,
    "deposit_timestamp": 1794922787,
    "deposit_utc": "2026-11-17T13:39:47+00:00",
    "router": "0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146",
    "vault": "0x51649cf810ea9f1f61165044b7149070c67f79c8",
    "memo": "=:b:bc1qx5arvvlstn42vlzhqgv96yg0ww99g0fxwv334j:99648378/1/0",
    "input_ETH": "36",
    "output_BTC": "1.00484202",
    "BTC_per_ETH": "0.027912278333333333333333333333333333333333333333333333333333333333333333333333333",
    "destination_address": "bc1qx5arvvlstn42vlzhqgv96yg0ww99g0fxwv334j",
    "bitcoin_txid": "791f9c1b8ef19b11aad20ca8742f8dbe2b6fce2dc6a43655d8b382a28af4a7d8",
    "bitcoin_outputs": [
      {
        "index": 0,
        "value_sats": 100484202
      }
    ],
    "bitcoin_confirmed_block": {
      "confirmed": true,
      "block_height": 976285,
      "block_hash": "00000000000000000000a450e1814ead4f07ecf996b4d59d1bbd2fe841ababbd",
      "block_time": 1794925686
    },
    "inclusion_delay_seconds": 2899,
    "delay_definition": "Ethereum inclusion to Bitcoin block timestamp; coarse cross-chain clocks, not exact service latency",
    "funding_path": [
      {
        "sender": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
        "recipient": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "tx_hash": "0xa024c760b7fcabe748798b52c4806f4581389f770acff43ebac2938c4961d2e4",
        "amount_wei": "14040000000000000000000",
        "timestamp": 1793320547,
        "timestamp_utc": "2026-10-30T00:35:47+00:00",
        "evidence": [
          "data/raw/public_rpc/90f36fe6e8be602056c84098dd172be4fe047e951dc7d4e70f4c50407cc30be7.json",
          "data/raw/public_rpc/b5969e2575ab05af47d7f0f5ab09d5def6b40199d262cbb02398c26978e219db.json",
          "data/raw/public_rpc/9ab0f4c8d8fcaa141bded289a8141826996e5bb90a3cbdc7687dceee6d487a76.json"
        ],
        "index_evidence": "data/raw/objects/53f9eec92d643186b2507e1749e50e23f37ab783234f9f0400b5561b7659ac6b.json.gz"
      },
      {
        "sender": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "recipient": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "tx_hash": "0xcd7a591142ba2544835a46d42dbba102caa86e4393a32506f4781e87136ecdbe",
        "amount_wei": "12000000000000000000000",
        "timestamp": 1794898511,
        "timestamp_utc": "2026-11-17T06:55:11+00:00",
        "evidence": [
          "data/raw/public_rpc/ebae947bd587f947776b8656a753d896ec4bf8c4cf2ac1ce0d76964deea1af8f.json",
          "data/raw/public_rpc/f9b8b4f43786422a19f5a93eb7e50b628b581eef0ba67019f4eaf12b0699c527.json",
          "data/raw/public_rpc/44b416ff1cdedfb63b8fa7934a271df947ff7fc558d51d50cb851c1ba9eb0865.json"
        ],
        "index_evidence": "data/raw/public_http/454f247347920b0241aec2c27f07e32d33b41919232a3409fae1060537e8d971.json"
      },
      {
        "sender": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "recipient": "0x8b8820b6e1f9d158c0cb0a1d07cb42609da38b69",
        "tx_hash": "0xe396dc2ddbd65249a50c5844f2b0d9c162e0fc9e3ddd731f340dc20fdeb760a1",
        "amount_wei": "58780372441045460000",
        "timestamp": 1794921575,
        "timestamp_utc": "2026-11-17T13:19:35+00:00",
        "evidence": [
          "data/raw/public_rpc/a229db23e2a0bb76944b00a72e6ac429e926e71aaebcb5817e615c8a0fd9b9d2.json",
          "data/raw/public_rpc/9cdaa3ab859429e019b7a68893554ffc82fc189c63e300310833d300b248b777.json",
          "data/raw/public_rpc/4610dff86852a6d9c4ba2b5c2525e2e15a0b1e067be51259beb7bdf81e0fb4ff.json"
        ],
        "index_evidence": "data/raw/public_http/9cee6bd6675ebe99b32037f1d5bfc6400e932577b7592c54d1d59e6f6c377834.json"
      }
    ],
    "incident_anchor_address": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
    "common_control_established": false,
    "exclusive_stolen_unit_provenance_established": false,
    "funding_scope": "Chronologically prior ordinary transfers, each >= the next transfer. Fund-flow association, not exclusive coin-taint accounting or ownership. Other inputs and intervening spending not exhausted.",
    "reference": {
      "venue": "Coinbase",
      "method": "prior completed minute close for both assets at deposit time; output valued at same reference time",
      "minute_utc": "2026-11-17T13:38:00+00:00",
      "ETH_USD": "1819.99",
      "BTC_USD": "64889.27",
      "evidence": {
        "ETH": "data/raw/public_http/761b9c3e9e872dc0c02b08a743d75e4d14c624c962a75bafd9668151f9341953.json",
        "BTC": "data/raw/public_http/82c3d957fa86fd31121da610ffe28220af75606d6fee8c9303e48b327f4cc60f.json"
      }
    },
    "input_reference_USD": "65519.64",
    "output_reference_USD": "65203.4651431254",
    "estimated_execution_shortfall_USD": "316.1748568746",
    "shortfall_rate": "0.0048256500932331130024523944270756066425273398938089403421630521779423696467196706",
    "ethereum_gas_ETH": "0.001183358619918202",
    "ethereum_gas_reference_USD": "2.15370085466492845798",
    "network_fee_BTC": "0.00001053",
    "network_fee_reference_USD": "0.6832840131",
    "actual_bitcoin_network_fee_sats": 1000,
    "reported_liquidity_fee_RUNE": "236.62030563",
    "reported_swap_slip_bps": "20",
    "streaming_swap": {
      "count": "18",
      "depositedCoin": {
        "amount": "3600000000",
        "asset": "ETH.ETH"
      },
      "inCoin": {
        "amount": "3600000000",
        "asset": "ETH.ETH"
      },
      "interval": "1",
      "lastHeight": "28711421",
      "outCoin": {
        "amount": "100485255",
        "asset": "BTC.BTC"
      },
      "outEstimation": "100820484",
      "quantity": "18"
    },
    "midgard_price_mark_USD": {
      "ETH": "1837.7372695609315",
      "BTC": "65874.02458557482"
    },
    "price_impact_USD": null,
    "price_impact_limit": "No historical THOR pool/counterfactual replay; liquidity fee RUNE-denominated. No invented USD fee/additive decomposition. Shortfall includes market/streaming/timing effects.",
    "sensitivity": {
      "prior_5min_USD": "357.7570579002",
      "prior_15min_USD": "268.8728428854"
    },
    "evidence": {
      "ethereum": [
        "data/raw/public_rpc/3533175b7ce18ca0bd8849bb71cf7f2cde552a90d83d5a898c4cdf756e3bad14.json",
        "data/raw/public_rpc/1f5c894432d98f4426ddd470a613bb513ea868e49b019d92dd599454803fd680.json",
        "data/raw/public_rpc/60d3a63e7e938a29ca9f57357e75ba23635dfbb6ad4d95b1066564be99cfc7ec.json"
      ],
      "thornode": "data/raw/public_http/7c80787c55f4b6b3f8b1d6c229e96348558aa16bb297d3e46c37dcf31103d5ca.json",
      "midgard": "data/raw/public_http/44b7009aff5775492911a14811df25a8d9ecfb0072633de347c11fe00ffa73ba.json",
      "bitcoin": "data/raw/public_http/69ca4dfa880f39e089fab4929e9e42f845c087f863d9aec39c9e5914c0ce2615.json"
    },
    "classification": "observed conversion; estimated reference shortfall; incident fund-flow association only",
    "ethereum_MEV_link_established": false
  },
  {
    "case_id": "T2",
    "ethereum_deposit": "0x6c796881f623a50383d112545ff2fbf224b5a8c26d8f824c53c681de0269612e",
    "source_address": "0xcb9838cd45c741d0f75a056813e04d9234c4f2b2",
    "source_block": 26435489,
    "deposit_timestamp": 1794927227,
    "deposit_utc": "2026-11-17T14:53:47+00:00",
    "router": "0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146",
    "vault": "0x0d15b57a5ba0a31a4774c03ddfacf79b289db9ce",
    "memo": "=:b:bc1qxhfhvxy6fvdde5rmxcaavkle6v3arqev8dzfgh:168430609/1/0",
    "input_ETH": "61",
    "output_BTC": "1.68897154",
    "BTC_per_ETH": "0.027688058032786885245901639344262295081967213114754098360655737704918032786885246",
    "destination_address": "bc1qxhfhvxy6fvdde5rmxcaavkle6v3arqev8dzfgh",
    "bitcoin_txid": "539f1bc99cd3586dfb12640eb3944b959e977a91a234e8f408c2c7361888ca80",
    "bitcoin_outputs": [
      {
        "index": 0,
        "value_sats": 168897154
      }
    ],
    "bitcoin_confirmed_block": {
      "confirmed": true,
      "block_height": 976293,
      "block_hash": "000000000000000000013519768592e430a736bd03d8c04fa4e912f0862df3f1",
      "block_time": 1794928738
    },
    "inclusion_delay_seconds": 1511,
    "delay_definition": "Ethereum inclusion to Bitcoin block timestamp; coarse cross-chain clocks, not exact service latency",
    "funding_path": [
      {
        "sender": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
        "recipient": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "tx_hash": "0xa024c760b7fcabe748798b52c4806f4581389f770acff43ebac2938c4961d2e4",
        "amount_wei": "14040000000000000000000",
        "timestamp": 1793320547,
        "timestamp_utc": "2026-10-30T00:35:47+00:00",
        "evidence": [
          "data/raw/public_rpc/90f36fe6e8be602056c84098dd172be4fe047e951dc7d4e70f4c50407cc30be7.json",
          "data/raw/public_rpc/b5969e2575ab05af47d7f0f5ab09d5def6b40199d262cbb02398c26978e219db.json",
          "data/raw/public_rpc/9ab0f4c8d8fcaa141bded289a8141826996e5bb90a3cbdc7687dceee6d487a76.json"
        ],
        "index_evidence": "data/raw/objects/53f9eec92d643186b2507e1749e50e23f37ab783234f9f0400b5561b7659ac6b.json.gz"
      },
      {
        "sender": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "recipient": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "tx_hash": "0xcd7a591142ba2544835a46d42dbba102caa86e4393a32506f4781e87136ecdbe",
        "amount_wei": "12000000000000000000000",
        "timestamp": 1794898511,
        "timestamp_utc": "2026-11-17T06:55:11+00:00",
        "evidence": [
          "data/raw/public_rpc/ebae947bd587f947776b8656a753d896ec4bf8c4cf2ac1ce0d76964deea1af8f.json",
          "data/raw/public_rpc/f9b8b4f43786422a19f5a93eb7e50b628b581eef0ba67019f4eaf12b0699c527.json",
          "data/raw/public_rpc/44b416ff1cdedfb63b8fa7934a271df947ff7fc558d51d50cb851c1ba9eb0865.json"
        ],
        "index_evidence": "data/raw/public_http/454f247347920b0241aec2c27f07e32d33b41919232a3409fae1060537e8d971.json"
      },
      {
        "sender": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "recipient": "0xcb9838cd45c741d0f75a056813e04d9234c4f2b2",
        "tx_hash": "0x8df9a63635a20c1e9ab6440fc20f324937100a610c78a182007f75acd1f6f416",
        "amount_wei": "94153206773977670000",
        "timestamp": 1794926939,
        "timestamp_utc": "2026-11-17T14:48:59+00:00",
        "evidence": [
          "data/raw/public_rpc/e5b4a92f1bd4e3568a0e0b2da7cb966002ca4d124d741c37047523a00306956b.json",
          "data/raw/public_rpc/64c709cb74a0255a5de9a5896fd6b1ebb52eab36b00e286e66539c88ce7a6c56.json",
          "data/raw/public_rpc/ee2b9159900f08c68a623155255914a69144bcb5d2518b50daac28cdf8c049fd.json"
        ],
        "index_evidence": "data/raw/public_http/0d36c8921ea33c03d79e0091209ab74c308e42047b09f36271157aabb6cc2cdc.json"
      }
    ],
    "incident_anchor_address": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
    "common_control_established": false,
    "exclusive_stolen_unit_provenance_established": false,
    "funding_scope": "Chronologically prior ordinary transfers, each >= the next transfer. Fund-flow association, not exclusive coin-taint accounting or ownership. Other inputs and intervening spending not exhausted.",
    "reference": {
      "venue": "Coinbase",
      "method": "prior completed minute close for both assets at deposit time; output valued at same reference time",
      "minute_utc": "2026-11-17T14:52:00+00:00",
      "ETH_USD": "1807.14",
      "BTC_USD": "64821.23",
      "evidence": {
        "ETH": "data/raw/public_http/761b9c3e9e872dc0c02b08a743d75e4d14c624c962a75bafd9668151f9341953.json",
        "BTC": "data/raw/public_http/82c3d957fa86fd31121da610ffe28220af75606d6fee8c9303e48b327f4cc60f.json"
      }
    },
    "input_reference_USD": "110235.54",
    "output_reference_USD": "109481.2126577942",
    "estimated_execution_shortfall_USD": "754.3273422058",
    "shortfall_rate": "0.0068428688443472948923731856350501843597808837331408727167300128434078519504689685",
    "ethereum_gas_ETH": "0.00119098729904113",
    "ethereum_gas_reference_USD": "2.1522807875891876682",
    "network_fee_BTC": "0.00001039",
    "network_fee_reference_USD": "0.6734925797",
    "actual_bitcoin_network_fee_sats": 2292,
    "reported_liquidity_fee_RUNE": "400.05350197",
    "reported_swap_slip_bps": "20",
    "streaming_swap": {
      "count": "30",
      "depositedCoin": {
        "amount": "6100000000",
        "asset": "ETH.ETH"
      },
      "inCoin": {
        "amount": "6100000000",
        "asset": "ETH.ETH"
      },
      "interval": "1",
      "lastHeight": "28712161",
      "outCoin": {
        "amount": "168898193",
        "asset": "BTC.BTC"
      },
      "outEstimation": "168870090",
      "quantity": "30"
    },
    "midgard_price_mark_USD": {
      "ETH": "1807.365174121175",
      "BTC": "65336.30858027031"
    },
    "price_impact_USD": null,
    "price_impact_limit": "No historical THOR pool/counterfactual replay; liquidity fee RUNE-denominated. No invented USD fee/additive decomposition. Shortfall includes market/streaming/timing effects.",
    "sensitivity": {
      "prior_5min_USD": "1023.3420853766",
      "prior_15min_USD": "1182.093907010"
    },
    "evidence": {
      "ethereum": [
        "data/raw/public_rpc/8e18995e2b2045bfbdcd18a7638697e9b3811da4f6a3a63c846148c2bda4e878.json",
        "data/raw/public_rpc/25be4fb1834bbcd2e94c3fb9bf00a9a6b4d1489ca464a6054482373c9aa3c9f1.json",
        "data/raw/public_rpc/846dc67f098fba07dff42eb1ab05eab7f7813c6c9857445a164a976be492bb32.json"
      ],
      "thornode": "data/raw/public_http/bf9e49399aa1264591b2ea7ac84abe8708558ab595d2c869923f2fd91e54403b.json",
      "midgard": "data/raw/public_http/959773faea21a5eb504b70683e418beb85d221d8aedeece843cfa526991f43ee.json",
      "bitcoin": "data/raw/public_http/86a167476dd58052d68326c8dabf81ea4f57b07beb287f68c9b7c9dae1c6a6ed.json"
    },
    "classification": "observed conversion; estimated reference shortfall; incident fund-flow association only",
    "ethereum_MEV_link_established": false
  },
  {
    "case_id": "T3",
    "ethereum_deposit": "0x7f8d415a1661815c4150d7b4f313af0a491026bc3908947aa342c22c621adc6b",
    "source_address": "0x53a95853f2b9449841c7b85367a38c6500c505f4",
    "source_block": 26435503,
    "deposit_timestamp": 1794927395,
    "deposit_utc": "2026-11-17T14:56:35+00:00",
    "router": "0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146",
    "vault": "0x46f3fb8c14006268d153b18000495c8ee858e94b",
    "memo": "=:b:bc1qpwd8yanakftutvz5r2njrahju5g859w3pmue98:110170770/1/0",
    "input_ETH": "40",
    "output_BTC": "1.10797406",
    "BTC_per_ETH": "0.0276993515",
    "destination_address": "bc1qpwd8yanakftutvz5r2njrahju5g859w3pmue98",
    "bitcoin_txid": "102dcc81ee7f7e987febaedebaca7c9c22189619f86fbd685fd743687db93025",
    "bitcoin_outputs": [
      {
        "index": 0,
        "value_sats": 110797406
      }
    ],
    "bitcoin_confirmed_block": {
      "confirmed": true,
      "block_height": 976292,
      "block_hash": "000000000000000000004479287b9f561d3bad27229070b9809799839f961cea",
      "block_time": 1794928691
    },
    "inclusion_delay_seconds": 1296,
    "delay_definition": "Ethereum inclusion to Bitcoin block timestamp; coarse cross-chain clocks, not exact service latency",
    "funding_path": [
      {
        "sender": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
        "recipient": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "tx_hash": "0xa024c760b7fcabe748798b52c4806f4581389f770acff43ebac2938c4961d2e4",
        "amount_wei": "14040000000000000000000",
        "timestamp": 1793320547,
        "timestamp_utc": "2026-10-30T00:35:47+00:00",
        "evidence": [
          "data/raw/public_rpc/90f36fe6e8be602056c84098dd172be4fe047e951dc7d4e70f4c50407cc30be7.json",
          "data/raw/public_rpc/b5969e2575ab05af47d7f0f5ab09d5def6b40199d262cbb02398c26978e219db.json",
          "data/raw/public_rpc/9ab0f4c8d8fcaa141bded289a8141826996e5bb90a3cbdc7687dceee6d487a76.json"
        ],
        "index_evidence": "data/raw/objects/53f9eec92d643186b2507e1749e50e23f37ab783234f9f0400b5561b7659ac6b.json.gz"
      },
      {
        "sender": "0x79e70d139fc05aa75f75611fdf2680e9952b544a",
        "recipient": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "tx_hash": "0xcd7a591142ba2544835a46d42dbba102caa86e4393a32506f4781e87136ecdbe",
        "amount_wei": "12000000000000000000000",
        "timestamp": 1794898511,
        "timestamp_utc": "2026-11-17T06:55:11+00:00",
        "evidence": [
          "data/raw/public_rpc/ebae947bd587f947776b8656a753d896ec4bf8c4cf2ac1ce0d76964deea1af8f.json",
          "data/raw/public_rpc/f9b8b4f43786422a19f5a93eb7e50b628b581eef0ba67019f4eaf12b0699c527.json",
          "data/raw/public_rpc/44b416ff1cdedfb63b8fa7934a271df947ff7fc558d51d50cb851c1ba9eb0865.json"
        ],
        "index_evidence": "data/raw/public_http/454f247347920b0241aec2c27f07e32d33b41919232a3409fae1060537e8d971.json"
      },
      {
        "sender": "0x381aed84964b5e68445f9e121a42d0743c081c2b",
        "recipient": "0x53a95853f2b9449841c7b85367a38c6500c505f4",
        "tx_hash": "0xdf9264009c3e9156bbf15e96e39d13134dd807fbec46c56bf9fa75ea54c22dd4",
        "amount_wei": "40459046881944670000",
        "timestamp": 1794927107,
        "timestamp_utc": "2026-11-17T14:51:47+00:00",
        "evidence": [
          "data/raw/public_rpc/5e16bb02ca119bb47e0e96cafed50f76eae31d16c8ab7133f01a7738d750d48e.json",
          "data/raw/public_rpc/1ee8a83e0ed3bccc7bb8e89d73162497042c83254827e2fe57d70651be5ae17b.json",
          "data/raw/public_rpc/497bf000bcb43113d933cd4720f2b8e7ce7c3d81af944c3e51b1d99dd60c53d4.json"
        ],
        "index_evidence": "data/raw/public_http/34a7e62f9470a70da8bb43505e0de967ecd54ae50b07c136bd32a06b1447bd4a.json"
      }
    ],
    "incident_anchor_address": "0x600d6f00eadabdb514561ceeb43730a7103e8298",
    "common_control_established": false,
    "exclusive_stolen_unit_provenance_established": false,
    "funding_scope": "Chronologically prior ordinary transfers, each >= the next transfer. Fund-flow association, not exclusive coin-taint accounting or ownership. Other inputs and intervening spending not exhausted.",
    "reference": {
      "venue": "Coinbase",
      "method": "prior completed minute close for both assets at deposit time; output valued at same reference time",
      "minute_utc": "2026-11-17T14:55:00+00:00",
      "ETH_USD": "1806.31",
      "BTC_USD": "64823.43",
      "evidence": {
        "ETH": "data/raw/public_http/761b9c3e9e872dc0c02b08a743d75e4d14c624c962a75bafd9668151f9341953.json",
        "BTC": "data/raw/public_http/82c3d957fa86fd31121da610ffe28220af75606d6fee8c9303e48b327f4cc60f.json"
      }
    },
    "input_reference_USD": "72252.40",
    "output_reference_USD": "71822.6789202258",
    "estimated_execution_shortfall_USD": "429.7210797742",
    "shortfall_rate": "0.0059474990418892659620995288737813553598219574713089115378866307555181557982849013",
    "ethereum_gas_ETH": "0.001190339390995059",
    "ethereum_gas_reference_USD": "2.15012194534828502229",
    "network_fee_BTC": "0.00001038",
    "network_fee_reference_USD": "0.6728672034",
    "actual_bitcoin_network_fee_sats": 1000,
    "reported_liquidity_fee_RUNE": "260.35439669",
    "reported_swap_slip_bps": "20",
    "streaming_swap": {
      "count": "20",
      "depositedCoin": {
        "amount": "4000000000",
        "asset": "ETH.ETH"
      },
      "inCoin": {
        "amount": "4000000000",
        "asset": "ETH.ETH"
      },
      "interval": "1",
      "lastHeight": "28712178",
      "outCoin": {
        "amount": "110798444",
        "asset": "BTC.BTC"
      },
      "outEstimation": "110495060",
      "quantity": "20"
    },
    "midgard_price_mark_USD": {
      "ETH": "1815.2991331069957",
      "BTC": "65576.05975832186"
    },
    "price_impact_USD": null,
    "price_impact_limit": "No historical THOR pool/counterfactual replay; liquidity fee RUNE-denominated. No invented USD fee/additive decomposition. Shortfall includes market/streaming/timing effects.",
    "sensitivity": {
      "prior_5min_USD": "536.4056119296",
      "prior_15min_USD": "699.2174537172"
    },
    "evidence": {
      "ethereum": [
        "data/raw/public_rpc/98a354c90a02776e29d1e34f7637e652dac8cb992a7e45effe64858b98f3706a.json",
        "data/raw/public_rpc/c5f9e350b5359a48d286123fe19871ce2843d6af0a24af6ab1e2bfd769c3cd91.json",
        "data/raw/public_rpc/02c4b2ed9dd0ff2f8a324f7c1528273a009c314144691a76b617556b6e813a48.json"
      ],
      "thornode": "data/raw/public_http/059f97d6334e194c14532610ffded7b98c2bd05548dc0a0e6a78352383deb997.json",
      "midgard": "data/raw/public_http/95bf89eb5a3fa5e2e702c4aaa0a569959d21ea2deaecfece05c24db51fe6b8f8.json",
      "bitcoin": "data/raw/public_http/586b0c99ac5613593d93667b53d02621149ce7c30d62b21d1767d585f1ee612e.json"
    },
    "classification": "observed conversion; estimated reference shortfall; incident fund-flow association only",
    "ethereum_MEV_link_established": false
  }
]
```

<a id="slide-13"></a>
## Slide 13 — Snapshot reconciliation

Fixed closing reference30Oct07:02:47UTC:four-asset balancesUSD2.646601359B,includingUSD2.026000812B blacklisted stablecoins andUSD0.620600547B other lead balances.64/64four-asset accounts reconcile. Wider raw inventory:64assets×16leads=1,024/1,024 ledgers reconcile. Blacklisting is not recovery.

Source files (paths relative to new/):

- [data/processed/balance_reconciliation.json](../../data/processed/balance_reconciliation.json)
- [data/processed/asset_inventory.json](../../data/processed/asset_inventory.json)
- [data/processed/loss_reconciliation.json](../../data/processed/loss_reconciliation.json)

Exact evidence extract (observations and estimates retain their original field names):

```json
{
  "asset_ledger_USD": {
    "opening": "3094.70932359258238221744",
    "external_inflow": "3482110499.02796360232288526200",
    "external_outflow": "833981065.37140150003795987800",
    "gas": "28192.41128351046973726152",
    "wrapper_net": "-1502976.81040848687865984920",
    "closing": "2646601359.14419369751891049072",
    "frozen_closing": "2026000811.9894566897800",
    "nonblacklisted_closing": "620600547.15473700773891049072",
    "unexplained_change": "0E-13"
  },
  "valuation_timestamp_utc": "2026-10-30T07:02:47+00:00",
  "inventory_assets": 64,
  "inventory_balanced_rows": 1024
}
```

<a id="slide-14"></a>
## Slide 14 — Conclusions and limits

621unique completely valued swaps showUSD43.728M signed trade-time shortfall in this bounded sample. Selected profits/payments can be reconstructed; causal whole-event MEV remains unresolved. Eight reproducible figures;52tests passed. Price timing comparisons use identical transaction sets.

Source files (paths relative to new/):

- [data/processed/loss_reconciliation.json](../../data/processed/loss_reconciliation.json)
- [reports/final_research_report.md](../../reports/final_research_report.md)
- [reports/pytest-results.xml](../../reports/pytest-results.xml)

Exact evidence extract (observations and estimates retain their original field names):

```json
{
  "same_transaction_price_sensitivity": {
    "same_transactions": 293,
    "trade_time": {
      "rows": 293,
      "signed_net_shortfall_USD": "38207162.89088384396094504737252125",
      "adverse_only_USD": "38207164.70745173522844239139567125",
      "favorable_only_USD": "1.81656789126749734402315"
    },
    "fixed_closing_mark": {
      "rows": 293,
      "signed_net_shortfall_USD": "49801599.88485977162653255948179456",
      "adverse_only_USD": "49817560.98819117005162653164089456",
      "favorable_only_USD": "15961.1033313984250939721591"
    },
    "interpretation": "Same-transaction comparison. Full 621-row and 315-row sample totals have different coverage and cannot be compared as pure price sensitivity."
  },
  "ownership_sensitivity": [
    {
      "scenario": "all_16_teacher_leads",
      "wallet_numbers": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16
      ],
      "primary_trade_time": {
        "rows": 621,
        "signed_net_shortfall_USD": "43727932.59248871806181198929786924",
        "adverse_only_USD": "43728046.58801969970781983615701924",
        "favorable_only_USD": "113.99553098164600784685915"
      },
      "fixed_mark": {
        "rows": 315,
        "signed_net_shortfall_USD": "51019941.10190204465616681210184456",
        "adverse_only_USD": "51035902.20523344308126078426094456",
        "favorable_only_USD": "15961.1033313984250939721591"
      },
      "snapshot_closing_USD": "2646601359.14419369751891049072",
      "ownership_meaning": "Each address is its own boundary; recipient common control is never assumed. Excluding an address tests the lead set, not proof of innocence."
    },
    {
      "scenario": "exclude_unverified_wallet13",
      "wallet_numbers": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        14,
        15,
        16
      ],
      "primary_trade_time": {
        "rows": 621,
        "signed_net_shortfall_USD": "43727932.59248871806181198929786924",
        "adverse_only_USD": "43728046.58801969970781983615701924",
        "favorable_only_USD": "113.99553098164600784685915"
      },
      "fixed_mark": {
        "rows": 315,
        "signed_net_shortfall_USD": "51019941.10190204465616681210184456",
        "adverse_only_USD": "51035902.20523344308126078426094456",
        "favorable_only_USD": "15961.1033313984250939721591"
      },
      "snapshot_closing_USD": "2646600738.14589622209360601464",
      "ownership_meaning": "Each address is its own boundary; recipient common control is never assumed. Excluding an address tests the lead set, not proof of innocence."
    },
    {
      "scenario": "exclude_wallet13_and_crosschain_only9",
      "wallet_numbers": [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        10,
        11,
        12,
        14,
        15,
        16
      ],
      "primary_trade_time": {
        "rows": 621,
        "signed_net_shortfall_USD": "43727932.59248871806181198929786924",
        "adverse_only_USD": "43728046.58801969970781983615701924",
        "favorable_only_USD": "113.99553098164600784685915"
      },
      "fixed_mark": {
        "rows": 315,
        "signed_net_shortfall_USD": "51019941.10190204465616681210184456",
        "adverse_only_USD": "51035902.20523344308126078426094456",
        "favorable_only_USD": "15961.1033313984250939721591"
      },
      "snapshot_closing_USD": "2646600729.64244531159122225872",
      "ownership_meaning": "Each address is its own boundary; recipient common control is never assumed. Excluding an address tests the lead set, not proof of innocence."
    }
  ]
}
```

