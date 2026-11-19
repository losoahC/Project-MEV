# T2：ETH → THORChain → BTC

入金 UTC **2026-11-17T14:53:47+00:00**；[ETH 入金](https://etherscan.io/tx/0x6c796881f623a50383d112545ff2fbf224b5a8c26d8f824c53c681de0269612e) → [BTC 出金](https://blockstream.info/tx/539f1bc99cd3586dfb12640eb3944b959e977a91a234e8f408c2c7361888ca80)。

`0xcb9838cd45c741d0f75a056813e04d9234c4f2b2` 通过已核验 router `0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146` 入金 61 ETH；vault `0x0d15b57a5ba0a31a4774c03ddfacf79b289db9ce`。memo `=:b:bc1qxhfhvxy6fvdde5rmxcaavkle6v3arqev8dzfgh:168430609/1/0`。

收款 `bc1qxhfhvxy6fvdde5rmxcaavkle6v3arqev8dzfgh`，实际输出 1.68897154 BTC（0.027688058032786885245901639344262295081967213114754098360655737704918032786885246 BTC/ETH）。比特币已确认区块 976293；ETH inclusion 至 BTC 区块时间相差 1511 秒。两链时间戳精度不同，这不是精确服务延迟。

## 入出匹配

Ethereum RPC 核对成功收据、区块成员关系、ABI 入参、msg.value 与 Deposit 日志一致；THORNode 与 Midgard 按入金哈希核对来源、资产、memo、出金哈希/接收人/金额；独立 Bitcoin 索引核对确认状态、实际 vout 和 OUT:入金哈希的 OP_RETURN。THORChain ETH 数量是 1e8 精度，不能错按 Ethereum 的 1e18。

## 时间在先的资金流关联

| UTC | 转账哈希 | 发送方 → 接收方 | ETH |
|---|---|---|---:|
| 2026-10-30T00:35:47+00:00 | `0xa024c760b7fcabe748798b52c4806f4581389f770acff43ebac2938c4961d2e4` | `0x600d6f00eadabdb514561ceeb43730a7103e8298` → `0x79e70d139fc05aa75f75611fdf2680e9952b544a` | 14040 |
| 2026-11-17T06:55:11+00:00 | `0xcd7a591142ba2544835a46d42dbba102caa86e4393a32506f4781e87136ecdbe` | `0x79e70d139fc05aa75f75611fdf2680e9952b544a` → `0x381aed84964b5e68445f9e121a42d0743c081c2b` | 12000 |
| 2026-11-17T14:48:59+00:00 | `0x8df9a63635a20c1e9ab6440fc20f324937100a610c78a182007f75acd1f6f416` | `0x381aed84964b5e68445f9e121a42d0743c081c2b` → `0xcb9838cd45c741d0f75a056813e04d9234c4f2b2` | 94.15320677397767 |

每段均为实际成功普通 ETH 转账，时间递增且转账金额至少覆盖下一段金额。未穷尽其他来源和中途支出，不作独占盗款单位归属或地址共同控制结论。首次浏览器发现的另三笔 funding_link 晚于入金，已被重建器拒绝使用；当前路径改用入金之前的证据。

## 费用与估值

ETH 与 BTC 均按入金前已完成分钟 2026-11-17T14:52:00+00:00 的 Coinbase USD 收盘价估值：ETH=1807.14，BTC=64821.23。输入 $110,235.54，输出按同一参考时间估值 $109,481.21，差额 $754.33。

入金 gas 0.00119098729904113 ETH（单列，约 $2.15）；Midgard 报告网络扣费 0.00001039 BTC，已包含在最终到账差额内。实际 BTC 整笔网络矿工费 2292 sat，与协议向用户扣费不同，不再重复相加。报告 LP fee 为 400.05350197 RUNE；未取得同口径 RUNE/USD 参考，保留原币种。

Streaming 片数 30，报告 swapSlip=20 bps。没有重建历史 THOR 池状态，因此不把 swapSlip 或 LP fee 再加为额外损失，也不将参考差额全部归为价格冲击。5/15 分钟前行情差额：`{'prior_5min_USD': '1023.3420853766', 'prior_15min_USD': '1182.093907010'}`。

该跨链差额未与 Ethereum MEV 建立具体关联，不并入十月 MEV 总额。完整原始文件指针及字段：[JSON](T2_thorchain.json)。
