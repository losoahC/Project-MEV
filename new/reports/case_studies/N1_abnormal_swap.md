# N1：钱包 5 的异常执行调查

交易：[Ethereum 原始交易](https://etherscan.io/tx/0x2a1979ae32a40c0aaa0df757f6af690857c6c8cb86097cac29316597de9469f6)。钱包 `0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1`；区块 26,300,992，交易索引 3，UTC 2026-10-29T21:09:11+00:00。

输入 $29,961,300.00，输出 $21,587,296.08，参考价值差额 **$8,374,003.92（27.95%）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。

同一钱包在样本中共 2 条筛查合格记录。同块共享池邻居 23 条；完整重算套利关联：`['A1']`。相邻顺序和共享池不证明利润来源或控制关系。

已解码 18 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `ABI_compatible_fields_decoded`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。

## 流动性、价格影响与邻居核查

JSON 的 `major_ETH_USDT_pool_price_states` 保存主要 ETH/USDT 池实际执行前后价格与活动流动性；`v2_mechanical_leg_checks` 保存 V2 Sync 储备、常数乘积曲线/fee/residual 分解。该分解只适用于已检验的单腿，不能代表整笔混合 V2/V3/V4 多跳路由的无 MEV 反事实。

`observed_profitable_inventory_closed_neighbor_candidates` 是明确地址边界下的暂定流量；`other_incoming_transfers_next_10min` 是观察到的后续转账，未认定为补偿。逐项原始来源、共享池、完整哈希、交易顺序和资金流均见配套 JSON。

## 保护下限与敏感性

```json
[
  {
    "command_location": "19",
    "command_type": 12,
    "allow_revert": false,
    "recipient": "0x7aa4d3029e4c6a8e916300014ad95b6d6c03bfd1",
    "bound_raw": "4934380635394559234997",
    "bound_kind": "unwrap_minimum",
    "trace_address": []
  }
]
```

| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |
|---|---:|---:|---:|---|
| stale_5min | $29,961,300.00 | $21,587,296.08 | $8,374,003.92 | True |
| lookback_5min | $29,962,500.00 | $21,466,560.05 | $8,495,939.95 | True |
| lookback_15min | $29,963,700.00 | $21,614,710.04 | $8,348,989.96 | True |
| binance_ETH_same_minute | $29,961,300.00 | $21,588,830.37 | $8,372,469.63 | True |

分类：**insufficient_evidence**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.

完整可审计数据：[JSON](N1_abnormal_swap.json)。来源收据 `data/raw/objects/95c1e66f7c764d17d2e9755b0332e141a52a2f935d36db992788dc7ec57d9284.json.gz`、轨迹 `data/raw/objects/23846b66bf1cab96103c57df38e1e1fe8325a258a58b52f8ec84326165c20365.json.gz`、新读取收据 `data/raw/public_rpc/93054e2640d1d86aeea59924b6d5f6ea93711774fd40f846b3354ce597c11120.json`；这些路径以项目 new/ 为根目录。
