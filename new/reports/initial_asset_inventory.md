# Observed initial sweeps and expanded asset inventory

**Observed scope:** 64 assets in 3 exchange-address-to-lead transactions, 103 distinct transfer events. Historical opening/closing snapshots cover every one of these assets at all 16 address leads: 1024/1024 raw-unit ledgers reconcile exactly, with 0 failed balance calls.

Source address: `0x28c6c06298d514db089934071355e5743bf21d60`. Opening block 26,300,639; closing block 26,303,950. This raw-token inventory expands beyond the four-asset USD snapshot. It does not combine amounts across currencies or imply that every recipient shares an owner.

## Sweep transactions

- [Ethereum transaction 0x31c4c9fe287d54fb9d3b79980477a8c793a11f774b98d0a9a92de1dad888a91d](https://etherscan.io/tx/0x31c4c9fe287d54fb9d3b79980477a8c793a11f774b98d0a9a92de1dad888a91d)
- [Ethereum transaction 0x53bd38b816c23e74134786c29a8c18d792777998a3b9326047b583100e88e2f3](https://etherscan.io/tx/0x53bd38b816c23e74134786c29a8c18d792777998a3b9326047b583100e88e2f3)
- [Ethereum transaction 0x55ba4dabc41b468e580751373ad31acdee6f5ba398682df2c93e5a8340870556](https://etherscan.io/tx/0x55ba4dabc41b468e580751373ad31acdee6f5ba398682df2c93e5a8340870556)

These are the three observed sweeps from the stated source address. Other incident source addresses, other chains, custody-account USDC and intermediate conversion inflows are not silently relabeled as part of these three sweeps. The total event theft remains unresolved.

## Asset-by-asset raw accounting

| Exact token identity | Display symbol¹ | Historical decimals | Three-sweep input quantity | Closing quantity across 16 leads | Raw ledger residual |
|---|---|---:|---:|---:|---:|
| `0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e` | YFI | 18 | 569.267763064489008117 | 0 | 0 |
| `0x0fc2a55d5bd13033f1ee0cdd11f60f7efe66f467` | LA | 18 | 27959136.702249697544916028 | 27959136.702249697544916028 | 0 |
| `0x111111111117dc0aa78b770fa6a738034120c302` | 1INCH | 18 | 19034040.188979962646782079 | 0 | 0 |
| `0x163f8c2467924be0ae7b5347228cabf260318753` | WLD | 18 | 17317869.012723827497623979 | 0.002723827497623979 | 0 |
| `0x1776e1f26f98b1a5df9cd347953a26dd3cb46671` | NMR | 18 | 127141.454377099413004075 | 0 | 0 |
| `0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` | UNI | 18 | 6198795.232152540012203478 | 0 | 0 |
| `0x2260fac5e5542a773aa44fbcfedf7c193bc2c599` | WBTC | 8 | 82.64579097 | 0 | 0 |
| `0x31c8eacbffdd875c74b94b077895bd78cf1e64a3` | RAD | 18 | 4067615.227510924409618559 | 0 | 0 |
| `0x320623b8e4ff03373931769a31fc52a4e78b5d70` | RSR | 18 | 3382160847.124631394736317301 | 0.004631394736317301 | 0 |
| `0x3845badade8e6dff049820680d1f14bd3903a5d0` | SAND | 18 | 58397344.209173655699131855 | 0 | 0 |
| `0x419d0d8bdd9af5e606ae2232ed285aff190e711b` | FUN | 8 | 714911344.00837754 | 580766087.75937762 | 0 |
| `0x45804880de22913dafe09f4980848ece6ecbaf78` | PAXG | 18 | 1906.667728691225080377 | 1906.667728691225080377 | 0 |
| `0x4a220e6096b25eadb88358cb44068a3248254675` | QNT | 18 | 7492.16569120606138023 | 0 | 0 |
| `0x4c1746a800d224393fe2470c70a35717ed4ea5f1` | PLUME | 18 | 66315587.465925278165394319 | 0 | 0 |
| `0x4c9edd5852cd905f086c759e8383e09bff1e68b3` | USDE | 18 | 9707546.773204598785601727 | 0.003204598785601727 | 0 |
| `0x4d224452801aced8b2f0aebe155379bb5d594381` | APE | 18 | 8815018.804907549935130844 | 0 | 0 |
| `0x4e3fbd56cd56c3e72c1403e103b45db9da5b9d2b` | CVX | 18 | 541770.235934315966698916 | 0 | 0 |
| `0x514910771af9ca656af840dff83e8264ecf986ca` | LINK | 18 | 2270249.951132306194104996 | 0 | 0 |
| `0x526526528f35ac738177003b8773b402b8df8143` | RE | 18 | 3621588.724525093768186479 | 3621588.724525093768186479 | 0 |
| `0x57e114b691db790c35207b2e685d4a43181e6061` | ENA | 18 | 198678176.610793666524433584 | 0 | 0 |
| `0x58d97b57bb95320f9a05dc918aef65434969c2b2` | MORPHO | 18 | 1763059.912239729673844021 | 0.002239729673844021 | 0 |
| `0x5a98fcbea516cf06857215779fd812ca3bef1b32` | LDO | 18 | 6244624.492298031064280373 | 0 | 0 |
| `0x6033f7f88332b8db6ad452b7c6d5bb643990ae3f` | LSK | 18 | 9258136.282411374706092852 | 9258136.282411374706092852 | 0 |
| `0x62d0a8458ed7719fdaf978fe5929c6d342b0bfce` | BEAM | 18 | 984249380.289818649027468455 | 0 | 0 |
| `0x643c4e15d7d62ad0abec4a9bd4b001aa3ef52d66` | SYRUP | 18 | 5779551.427121723970838001 | 0 | 0 |
| `0x68749665ff8d2d112fa859aa293f07a622782f38` | XAUT | 6 | 11374.746797 | 12574.046797 | 0 |
| `0x6982508145454ce325ddbe47a25d4ec3d2311933` | PEPE | 18 | 7189384030595.868168766645550511 | 218340.611353711790393013 | 0 |
| `0x6985884c4392d348587b19cb9eaaf157f13271cd` | ZRO | 18 | 3601631.162981804936636057 | 0.002981804936636057 | 0 |
| `0x6b7774cb12ed7573a7586e7d0e62a2a563ddd3f0` | SOPH | 18 | 1693247180.546698021872626186 | 1693247180.546698021872626186 | 0 |
| `0x6c5ba91642f10282b576d91922ae6448c9d52f4e` | PHA | 18 | 25917840.74153016274808275 | 0 | 0 |
| `0x7cf9a80db3b29ee8efe3710aadb7b95270572d47` | NIL | 6 | 32825145.809786 | 32825145.809786 | 0 |
| `0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9` | AAVE | 18 | 128034.312130556282284061 | 6.886E-15 | 0 |
| `0x808507121b80c02388fad14726482e061b8da827` | PENDLE | 18 | 1682533.416434663109015357 | 0 | 0 |
| `0x8207c1ffc5b6804f6024322ccf34f29c3541ae26` | OGN | 18 | 59506795.58997043273394924 | 0 | 0 |
| `0x8292bb45bf1ee4d140127049757c2e0ff06317ed` | RLUSD | 18 | 62597239.679797044969015518 | 40541065.479797044969015518 | 0 |
| `0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d` | USD1 | 18 | 27824039.936896471320891162 | 27824039.936896471320891162 | 0 |
| `0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce` | SHIB | 18 | 499926072560.261941522417599274 | 0 | 0 |
| `0x9c7beba8f6ef6643abd725e45a4e8387ef260649` | G | 18 | 324356073.899507705142876653 | 0 | 0 |
| `0xa12cc123ba206d4031d1c7f6223d1c2ec249f4f3` | ZAMA | 18 | 87853170.571862717852910399 | 53329985.142895796079244946 | 0 |
| `0xa2e3356610840701bdf5611a53974510ae27e2e1` | WBETH | 18 | 29934.013163146020067927 | 29934.013163146020067927 | 0 |
| `0xaea46a60368a7bd060eec7df8cba43b7ef41ad85` | FET | 18 | 19791934.70943571616342132 | 0 | 0 |
| `0xb8c77482e45f1f44de1745f52c74426c631bdd52` | BNB | 18 | 1936.943327346786375659 | 0 | 0 |
| `0xbb0e17ef65f82ab018d8edd776e8dd940327b28b` | AXS | 18 | 1547423.266454360532103137 | 0 | 0 |
| `0xc00e94cb662c3520282e6f5717214004a7f26888` | COMP | 18 | 82650.673658824600017531 | 0 | 0 |
| `0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f` | SNX | 18 | 8405741.578047242292666519 | 0 | 0 |
| `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` | ETH | 18 | 668.132228390272982085 | 0 | 0 |
| `0xc18360217d8f7ab5e7c516566761ea12ce7f9d72` | ENS | 18 | 235232.054020043491921784 | 0 | 0 |
| `0xc43c6bfeda065fe2c4c11765bf838789bd0bb5de` | RED | 18 | 11955689.546251646882572239 | 0 | 0 |
| `0xc5f0f7b66764f6ec8c8dff7ba683102295e16409` | FDUSD | 18 | 3454894.923080018305112463 | 3454894.923080018305112463 | 0 |
| `0xcccccccccc33d538dbc2ee4feab0a7a1ff4e8a94` | CFG | 18 | 12731967.064871607906670299 | 0 | 0 |
| `0xd533a949740bb3306d119cc777fa900ba034cd52` | CRV | 18 | 8148735.009458259185285243 | 0 | 0 |
| `0xda5e1988097297dcdc1f90d4dfe7909e847cbef6` | WLFI | 18 | 48525612.007680240499693533 | 48525612.007680240499693533 | 0 |
| `0xdac17f958d2ee523a2206206994597c13d831ec7` | USDT | 6 | 1819724910.565362 | 1205464712.876062 | 0 |
| `0xdc035d45d973e3ec169d2276ddab16f1e407384f` | USDS | 18 | 1014445.385338046096540901 | 0 | 0 |
| `0xddb3422497e61e13543bea06989c0789117555c5` | COTI | 18 | 68849376.011900100816143418 | 0 | 0 |
| `0xde30da39c46104798bb5aa3fe8b9e0e1f348163f` | GTC | 18 | 14457610.138737493544626994 | 0 | 0 |
| `0xe2ad0bf751834f2fbdc62a41014f84d67ca1de2a` | ERA | 18 | 38603848.935213817280136568 | 38603848.935213817280136568 | 0 |
| `0xe53ec727dbdeb9e2d5456c3be40cff031ab40a55` | SUPER | 18 | 6525851.915579130530187564 | 0 | 0 |
| `0xec53bf9167f50cdeb3ae105f56099aaab9061f83` | EIGEN | 18 | 13171428.415695420192025058 | 0 | 0 |
| `0xf57e7e7c23978c3caec3c3548e3d615c346e79ff` | IMX | 18 | 8212155.867146262094904757 | 0 | 0 |
| `0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3` | ONDO | 18 | 21851870.659222511571157103 | 0.009222511571157103 | 0 |
| `0xfc82bb4ba86045af6f327323a46e80412b91b27d` | PROM | 18 | 911984.828175117742273585 | 908792.881305117742273585 | 0 |
| `0xfe0c30065b384f05761f15d0cc899d4f9f9cc0eb` | ETHFI | 18 | 3414721.297490244527791671 | 0 | 0 |
| `native:eth` | ETH | 18 | 169534.002601469787170247 | 275881.319891286446287936 | 0 |

¹ Display symbols are carried from legacy metadata only. Exact contract address is the identity; no symbol-only price match is permitted. Decimals and balances are historical RPC results, not inferred from symbols.

Closing balance may include other inflows, intermediate swaps, debt proceeds and conversions during the window. It is therefore not the same as “remaining original stolen units”. Likewise, a zero closing balance inside these leads does not prove funds were recovered or economically destroyed; transfers to other addresses need separate provenance.

## Verification and reproducibility

Read-only Ethereum historical calls use Multicall3 aggregate3 to return all 16 balances plus decimals per token/block. Both endpoint bytecodes, exact ABI-encoded requests, returned bytes and acquisition timestamps are retained. Deployment source: [official Multicall3 repository](https://github.com/mds1/multicall3). Overlapping four-asset rows are checked against the independently requested direct-RPC snapshots; disagreement raises an error. This is not a cryptographic state proof.

Supporting datasets: `data/processed/asset_inventory.json`, `asset_inventory.parquet`, `initial_sweep_assets.parquet`. Each row includes exact opening/closing RPC evidence and all contributing transfer edge IDs; each asset lists the original sweep events.

```bash
python -m src.reconciliation.inventory --online  # only if raw objects are missing
python -m src.reconciliation.inventory           # cached, read-only offline reconstruction
python -m src.reporting.inventory_report
```

The four-asset USD ledger and observed USDT/USDC blacklist snapshot remain separate: [M6 reconciliation](milestone6_report.md). The wider inventory does not replace missing price or recovery observations with invented USD values.
