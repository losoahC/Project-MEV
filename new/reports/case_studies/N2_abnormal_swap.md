# N2：钱包 4 的异常执行调查

交易：[Ethereum 原始交易](https://etherscan.io/tx/0xcb8075f1d07bc56e54e59ccd4477d75b6a7b21f265dabe2ee86beeb3f3b38a9d)。钱包 `0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb`；区块 26,300,976，交易索引 0，UTC 2026-10-29T21:05:59+00:00。

输入 $29,962,500.00，输出 $23,915,444.58，参考价值差额 **$6,047,055.42（20.18%）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。

同一钱包在样本中共 2 条筛查合格记录。同块共享池邻居 47 条；完整重算套利关联：`[]`。相邻顺序和共享池不证明利润来源或控制关系。

已解码 17 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `ABI_compatible_fields_decoded`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。

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
    "recipient": "0x77edef23fbd05921c26fe29fcc3a65e14d2ac3eb",
    "bound_raw": "5036275042459249547130",
    "bound_kind": "unwrap_minimum",
    "trace_address": []
  }
]
```

| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |
|---|---:|---:|---:|---|
| stale_5min | $29,962,500.00 | $23,915,444.58 | $6,047,055.42 | True |
| lookback_5min | $29,962,500.00 | $24,004,301.71 | $5,958,198.29 | True |
| lookback_15min | $29,963,700.00 | $24,197,127.00 | $5,766,573.00 | True |
| binance_ETH_same_minute | $29,962,500.00 | $23,922,536.65 | $6,039,963.35 | True |

分类：**insufficient_evidence**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.

完整可审计数据：[JSON](N2_abnormal_swap.json)。来源收据 `data/raw/objects/3c03b47e085c3229f043be2923da0624e8f5be0f43d209692e4642898c803009.json.gz`、轨迹 `data/raw/objects/b391050985c7465e95070c3cdb5a130dc710fecdc3605afc95216b39acbc73a5.json.gz`、新读取收据 `data/raw/public_rpc/369c82ef2b5ef3efd1e02883f66d87d25c79bc584999fe62666e3520e4917408.json`；这些路径以项目 new/ 为根目录。
