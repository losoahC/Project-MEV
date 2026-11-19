# N3：钱包 5 的异常执行调查

交易：[Ethereum 原始交易](https://etherscan.io/tx/0x808f54a951b7fd051600937b45c6c3fb42d59850c6bf459cea8615dfadbcad39)。钱包 `0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1`；区块 26,300,988，交易索引 0，UTC 2026-10-29T21:08:23+00:00。

输入 $19,974,400.00，输出 $15,695,652.83，参考价值差额 **$4,278,747.17（21.42%）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。

同一钱包在样本中共 2 条筛查合格记录。同块共享池邻居 15 条；完整重算套利关联：`[]`。相邻顺序和共享池不证明利润来源或控制关系。

已解码 17 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `unsupported_selector`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。

## 流动性、价格影响与邻居核查

JSON 的 `major_ETH_USDT_pool_price_states` 保存主要 ETH/USDT 池实际执行前后价格与活动流动性；`v2_mechanical_leg_checks` 保存 V2 Sync 储备、常数乘积曲线/fee/residual 分解。该分解只适用于已检验的单腿，不能代表整笔混合 V2/V3/V4 多跳路由的无 MEV 反事实。

`observed_profitable_inventory_closed_neighbor_candidates` 是明确地址边界下的暂定流量；`other_incoming_transfers_next_10min` 是观察到的后续转账，未认定为补偿。逐项原始来源、共享池、完整哈希、交易顺序和资金流均见配套 JSON。

## 保护下限与敏感性

```json
[
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
]
```

| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |
|---|---:|---:|---:|---|
| stale_5min | $19,974,400.00 | $15,695,652.83 | $4,278,747.17 | True |
| lookback_5min | $19,975,200.00 | $15,599,801.52 | $4,375,398.48 | True |
| lookback_15min | $19,975,800.00 | $15,730,103.74 | $4,245,696.26 | True |
| binance_ETH_same_minute | $19,974,400.00 | $15,694,916.23 | $4,279,483.77 | True |

分类：**insufficient_evidence**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.

完整可审计数据：[JSON](N3_abnormal_swap.json)。来源收据 `data/raw/objects/2659c596a91f5126b10b8c25d468050369c89cc8725952fcfbdb681babd5637b.json.gz`、轨迹 `data/raw/objects/60d400377d37aaca5b995467f6d887c2696bb3efb8a2e379d569c5b5ad32012f.json.gz`、新读取收据 `data/raw/public_rpc/be375ec42b23d357b52c48e652cb08a282cdc4b43c0d940c2331d0e2b7131a8b.json`；这些路径以项目 new/ 为根目录。
