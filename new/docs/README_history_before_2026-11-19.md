# 最新扩展研究：套利、收益去向与 MEV 标准

先看 [中文完整核验报告](reports/mev_expansion/完整套利与MEV核验报告.md) 或 [带图 HTML](reports/mev_expansion/完整套利与MEV核验报告.html)。新报告涵盖 Ethereum 完整窗口、12,249 个去重操作单元、22 个新鲜目标条件执行实验、9 笔订单及四个 TRON 点名地址；每个结果区分资产闭合、参考损益、排序证据和因果归因。

逐笔交付包括 [判据与利润表](reports/mev_expansion/全部操作单元与判据.csv)、[49,922 条池事件路径](reports/mev_expansion/全部候选池路径.csv)、[逐地址留存](reports/mev_expansion/闭合循环逐地址净变化.csv)、[九笔订单逐地址分配](reports/mev_expansion/九笔订单逐地址分配.csv)、[TRON 路线](reports/mev_expansion/TRON逐笔池路径.csv)。76 项检查通过；[20 项扩展交付核对](reports/mev_expansion/expanded_requirements_audit.json)保留全事件损失、最终控制人、价格和仓位边界。

此前 14 页 Canva 已按批准保存，验证见 `reports/presentation/canva_saved_verification.json`。它是扩展前的版本；新增报告和金额没有被冒充为已同步 Canva。复现顺序见新报告第 10 节；新结果不是旧三案例利润的简单外推。

## 扩展前的阶段说明（保留历史）

# Group 12 · Binance Incident × DEX Arbitrage × MEV Auctions

成果入口：[综合学术报告](reports/final_research_report.md)、[八图索引与方法](reports/final_research_report.md#figure-and-evidence-index)、[14 页演示内容与证据](reports/presentation/slide_content.md)、[验证状态](reports/validation.json)。演示设计仍为待审核草稿；研究报告保留全事件未知数量。

# Group 12 · Binance Hack × DEX Arbitrage × MEV Auction

本目录按 [本次提供的研究计划](docs/research_plan_supplied.md)重新组织研究。当前已有 **M1 管线和图 1、M2 三个套利案例与图 2/3、M3 三个拍卖付款匹配与图 4/5、M4 五个异常案例与图 6、M5 三条完整跨链配对与图 7、限定资产对账与图 8**；钱包身份、完整因果归因和后续阶段仍有明确缺口。研究优先级为 DEX 套利、拍卖结果、异常交易及损失对账，其次为 THORChain 和夹击。

先看 [套利与拍卖报告](reports/milestone23_report.md)、[研究进度和验收状态](docs/progress.md)、[第一阶段报告](reports/milestone1_report.md)和 [交互资金流图](reports/figures/fig01_stolen_fund_flow.html)。本轮未发布全事件 MEV 总额。

## 复现

Python 3.11+。项目路径含冒号，macOS 的 `venv` 会拒绝在这个路径内创建环境，因此把环境放在不含冒号的路径：

```bash
python3 -m venv /tmp/group12-research-venv
/tmp/group12-research-venv/bin/python -m pip install -r requirements.lock.txt
cd '/Users/wuhaolun/Desktop/FT565/Project-MEV:PredMarket/new'

# 首次从父项目缓存导入；保留原始字节及 SHA-256
/tmp/group12-research-venv/bin/python -m src.ingestion.milestone1 --legacy ../research

# 后续可仅凭本目录的归档原始对象离线重建，不依赖父项目
/tmp/group12-research-venv/bin/python -m src.ingestion.milestone1 --from-archive

MPLCONFIGDIR=/tmp/group12-mpl /tmp/group12-research-venv/bin/python -m src.visualization.fig01_stolen_fund_flow
/tmp/group12-research-venv/bin/python -m pytest -q
```

`requirements.lock.txt` 记录本机本次验证的依赖版本；跨平台可按 `pyproject.toml` 的版本范围安装。当前原始对象约 466 MB，本地保存在 `data/raw/objects/`，另有约 35 MB 公开 RPC/HTTP 响应。复制本目录交接时，必须同时复制这些对象和清单；只复制 Git 中的代码不等于完整证据交接。当前离线复现以既有缓存为起点，不是从空目录重新抓取链上全部历史。

## 数据及图表

| 文件 | 用途 |
|---|---|
| `data/raw/manifest.json` | 原始字节哈希、来源方法、旧缓存路径；无法可靠恢复的原始抓取时间保留空值 |
| `data/processed/wallet_registry.json` | 16 个历史标签线索、独立来源和置信状态 |
| `data/processed/transactions.parquet` | 收据与区块成员关系核对后的交易、顺序、gas 和来源 |
| `data/processed/wallet_edges.parquet` | ERC20 转账事件、成功 ETH 调用及事件定位；去重后的边 |
| `data/processed/decoded_swaps.parquet` | V2/V3 兼容 Swap 事件；事件相同不等于协议工厂已认证 |
| `data/processed/research.duckdb` | 可重建的查询副本 |
| `reports/case_studies/m1_real_swap.json` | 从原始日志和轨迹重算的一笔真实兑换 |
| `reports/figures/fig01_stolen_fund_flow.{html,png,svg}` | 全数据交互筛选及适合浅底演示的静态选图 |
| `reports/tables/fig01_static_edges.parquet` | 静态图所展示事件的完整数据 |

HTML 内置压缩数据和 Plotly，可直接用支持 `DecompressionStream` 的现代浏览器打开。支持按合约、UTC 时间、最低 USD 和未估值记录筛选。当前只有 Ethereum 数据，链控件明确只提供 Ethereum。默认展示符合筛选条件的最大 120 条边，页面显示筛选总数和实际显示数；完整边表保存在 Parquet。静态图展示最大的 18 个已估值转账事件，加 4 个池路由事件并去重。

转账记录既包含路由腿，也可能包含同笔交易中的其他事件和垃圾代币。它们不是 57,042 笔黑客转账，也不能求和成为被盗额。未知资产不按同名 ticker 匹配价格，不把未知收款人归为黑客，不把参考价差直接当作 MEV 收益。

## 后续阶段

M4/M5 观察样本已完成，见 [异常交易与跨链报告](reports/milestone45_report.md)。M6：统一估值日期的资产对账和经济损失归因及 Figure 8。缺失的历史拍卖出价、身份或跨链证据必须保持未解决状态，不用示意数补齐。

## 套利和拍卖阶段复现

首次公开来源补抓：`python -m src.arbitrage.reconstruct --online` 和 `python -m src.auction.reconstruct --online`。之后可以离线运行，加入 `--legacy /不存在的目录` 可验证不依赖父项目旧缓存。源响应保存于 `data/raw/public_rpc/`、`data/raw/public_http/`，索引为 `data/raw/public_index.json`。归档原始对象和这些公开响应必须一起交接。

```bash
python -m src.arbitrage.reconstruct
python -m src.auction.reconstruct
python -m src.auction.timing
python -m src.visualization.fig02_eth_price_dislocation
python -m src.visualization.fig03_transaction_reconstruction
python -m src.visualization.fig04_mev_value_attribution
python -m src.visualization.fig05_auction_results
python -m src.reporting.milestone23
python -m src.ingestion.catalog
python -m pytest -q
```

本机请用上述临时虚拟环境中的 Python；其他机器安装依赖后替换为自己的解释器。M2/M3 的图、底表、完整案例位于 `reports/figures/`、`reports/tables/`、`reports/case_studies/`。图 4 明确区分所选 searcher 和整块资金流，图 5 的其他提交包含修订及可能晚到记录；A3 的 builder 所有权边界未解决，未报精确 builder 利润。

## 异常与跨链阶段复现

```bash
python -m src.anomaly.screen
python -m src.anomaly.investigate
python -m src.thorchain.discover
python -m src.thorchain.reconstruct
python -m src.visualization.fig06_suspicious_wallets
python -m src.visualization.fig07_thorchain_flows
python -m src.reporting.milestone45
```

首次缺失来源时可加 `--online`，随后公开响应可供离线复现。三案跨链重建不依赖旧目录。钱包来源归因现为 15/16，但钱包 9 的独立资料属于 Arbitrum 冻结关联，钱包 13 未证实，16 个新 Etherscan 标签页均为 403；没有把转账收款人默认并入黑客控制集合。

## 资产对账与稳健性

见 [限定资产对账报告](reports/milestone6_report.md) 和 [图 8](reports/figures/fig08_loss_reconciliation.html)。64 个钱包/资产账户精确对平；期末统一估值约 USD 2.6466B，其中黑名单稳定币约 USD 2.0260B。范围仅 16 地址、Ethereum 的四种资产，不是全事件盗款、不可追回或 MEV 损失总额。

```bash
python -m src.reconciliation.balances --legacy /不存在的目录
python -m src.reconciliation.summary
python -m src.visualization.fig08_loss_reconciliation
python -m src.reporting.milestone6
```

## 扩展库存、签名证据与最终审核

[64 资产原币种库存报告](reports/initial_asset_inventory.md)覆盖三笔已观察 sweep 中的所有资产：16 地址 × 64 资产 = 1,024 个账户均精确对平。所有初始转账及期末数量按原币种提供，未取得可靠行情的资产不混加成 USD。`data/processed/incident_delegation.json` 保存 50 个 EIP-7702 授权签名恢复和历史 delegation-code 证据；它认证签名/委托能力，不认证最终人类身份。

```bash
python -m src.reconciliation.inventory
python -m src.ingestion.genesis
python -m src.reporting.inventory_report
python -m src.reporting.presentation_notes
python -m src.reporting.acceptance_audit
```

图 1 的交互版现含 10 条另有日期的 THORChain 伴随边，其中 3 条为已确认 Bitcoin 输出。原 October 账表仍为 `wallet_edges.parquet`；扩展图表数据是 `fund_flow_graph_edges.parquet`。链控件现在可选 Ethereum / Bitcoin / 全部；BTC 估值使用对应 ETH 入金参考时点，资金链中缺价的边保留 null。实际 HTML 筛选逻辑已在 Node 执行验证，此扩展没有新浏览器渲染测试。

当前 52 项测试通过。[47 项验收表](reports/acceptance_audit.json)逐项记录证据及数据限制。[14 页审核 PDF](reports/presentation/presentation_review.pdf)是 Canva 返回的 600px 预览汇编，供审核使用；可编辑源设计已获批准保存，并已读回核对：[Canva 演示稿](https://www.canva.com/d/vplY4YKW4tAvurG)。精确数据和来源见 [逐页讲稿](reports/presentation/presenter_notes.md)。


补充核对：[与 Bitquery 口径的核对说明](reports/bitquery_check/核对说明.md)，[带金额、时刻和逐笔证据的 USDT 主干图](reports/bitquery_check/usdt_backbone.html)。关键两地址四笔买入的差额接近其报道；全量金额尚未同口径复现。PublicNode 空回执与 dRPC 匹配回执的来源分歧已单列。


当前扩展任务仍在进行：[套利路径索引与 30 份逐笔中文记录](reports/mev_expansion/route_index.md)。该候选集和参考价格账尚不能作为全事件利润结论，参见 [扩展进度](reports/mev_expansion/progress.md)。


新增：[22 份 hacker 收款差异与 bot 现金流执行干预案例](reports/mev_expansion/victim_intervention_index.md)。每案有实际前缀复现、删前腿的固定调用情景及真实付款地址；结果不代表全事件总额。完整窗口候选与发送者核算见 data/processed/mev_full_window/。
