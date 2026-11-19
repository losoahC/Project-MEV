# N5：钱包 10 的异常执行调查

交易：[Ethereum 原始交易](https://etherscan.io/tx/0x152e005f6dcccd941e0a2c7156b955c6baad08a347685bcf5518776dab04f8cc)。钱包 `0x0ddf0480016e6bcb2c1f5d190d221fba1320697e`；区块 26,300,886，交易索引 2，UTC 2026-10-29T20:47:47+00:00。

输入 $9,987,600.00，输出 $7,986,831.05，参考价值差额 **$2,000,768.95（20.03%）**；gas 不包含在该差额。此为估计执行短缺，不等于 MEV 收益。

同一钱包在样本中共 1 条筛查合格记录。同块共享池邻居 39 条；完整重算套利关联：`[]`。相邻顺序和共享池不证明利润来源或控制关系。

已解码 16 个零中间输出下限，同时存在非零最终最小输出保护。根路由状态为 `ABI_compatible_fields_decoded`；成功内部 execute 调用也已检查，避免仅检查入口而漏报。V4 等未解码命令、部署代码和 recipient 别名语义仍未认证，不能写成‘完全没有滑点保护’。

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
    "recipient": "0x0ddf0480016e6bcb2c1f5d190d221fba1320697e",
    "bound_raw": "1980814897275601244478",
    "bound_kind": "unwrap_minimum",
    "trace_address": []
  }
]
```

| 情景 | 输入参考价值 | 输出参考价值 | 差额 | 仍满足筛查 |
|---|---:|---:|---:|---|
| stale_5min | $9,987,600.00 | $7,986,831.05 | $2,000,768.95 | True |
| lookback_5min | $9,988,000.00 | $8,041,002.54 | $1,946,997.46 | True |
| lookback_15min | $9,988,000.00 | $8,193,428.67 | $1,794,571.33 | True |
| binance_ETH_same_minute | $9,987,600.00 | $7,986,116.24 | $2,001,483.76 | True |

分类：**insufficient_evidence**。未建立故意自损、共同控制的补偿获利或因果增量 MEV 损失。具体解释：Large estimated execution shortfall with observable pool impact / surrounding transactions; urgency, MEV causation, compensating ownership and intent are not established.

完整可审计数据：[JSON](N5_abnormal_swap.json)。来源收据 `data/raw/objects/7418b561954963aa4c831e38009a8bbb60e03687a584fa437e454f1fdcf339d8.json.gz`、轨迹 `data/raw/objects/e7c68d6d2ea13a4ed4cc100665fa59d9a327e85d70361bd5ff5cd3a7aa2611b3.json.gz`、新读取收据 `data/raw/public_rpc/b236f37f4d1e9a13d6444594ea1022627b317cafeacbf6d8eb6ad0c1c38df28a.json`；这些路径以项目 new/ 为根目录。
