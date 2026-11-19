# N4：钱包 4 的异常执行调查

交易：[Ethereum 原始交易](https://etherscan.io/tx/0xb7d294873bf18a56ce99115794b8a9a76542791b58456e7a4f94d74f1ae4e41f)。钱包 `0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb`；区块 26,300,970，交易索引 13，UTC 2026-10-29T21:04:47+00:00。

输入 $19,975,200.00，输出 $16,718,091.17，参考价值差额 **$3,257,108.83（16.31%）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。

同一钱包在样本中共 2 条筛查合格记录。同块共享池邻居 37 条；完整重算套利关联：`[]`。相邻顺序和共享池不证明利润来源或控制关系。

已解码 16 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `unsupported_selector`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。

## 流动性、价格影响与邻居核查

JSON 的 `major_ETH_USDT_pool_price_states` 保存主要 ETH/USDT 池实际执行前后价格与活动流动性；`v2_mechanical_leg_checks` 保存 V2 Sync 储备、常数乘积曲线/fee/residual 分解。该分解只适用于已检验的单腿，不能代表整笔混合 V2/V3/V4 多跳路由的无 MEV 反事实。

`observed_profitable_inventory_closed_neighbor_candidates` 是明确地址边界下的暂定流量；`other_incoming_transfers_next_10min` 是观察到的后续转账，未认定为补偿。逐项原始来源、共享池、完整哈希、交易顺序和资金流均见配套 JSON。

## 保护下限与敏感性

```json
[
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
]
```

| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |
|---|---:|---:|---:|---|
| stale_5min | $19,975,200.00 | $16,718,091.17 | $3,257,108.83 | True |
| lookback_5min | $19,976,400.00 | $16,788,582.65 | $3,187,817.35 | True |
| lookback_15min | $19,975,800.00 | $16,816,645.25 | $3,159,154.75 | True |
| binance_ETH_same_minute | $19,975,200.00 | $16,723,901.66 | $3,251,298.34 | True |

分类：**insufficient_evidence**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.

完整可审计数据：[JSON](N4_abnormal_swap.json)。来源收据 `data/raw/objects/49e046ffe9566bd5235314a4c72b79f46c8c4f5f2aec40c67dfa940be0f0c439.json.gz`、轨迹 `data/raw/objects/039cd15fbde9f3a7688458f60acd2d8a82d4e3dde3408d7523071b0c6677bb32.json.gz`、新读取收据 `data/raw/public_rpc/6b280a7c2fcec3d7083822093eaa2c5e9a4b877ad3947f11a240673a211aff5f.json`；这些路径以项目 new/ 为根目录。
