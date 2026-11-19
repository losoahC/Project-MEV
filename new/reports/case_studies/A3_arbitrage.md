# A3 · WETH / AXS two-pool cycle

交易：[完整哈希](https://etherscan.io/tx/0xbe7e1a0554942e23cb6c960274ab52033c9851445810c061a1f34f9e041d74a4) `0xbe7e1a0554942e23cb6c960274ab52033c9851445810c061a1f34f9e041d74a4`。目标交易：[完整哈希](https://etherscan.io/tx/0xbf3fc95e45d932b1ad0a55e91e77fea8652906a3eeb0efd65850976059aef9d7) `0xbf3fc95e45d932b1ad0a55e91e77fea8652906a3eeb0efd65850976059aef9d7`。

区块 26302437，UTC 2026-10-30T01:59:11+00:00，目标索引 3，套利索引 33。

记账边界是发送者 `0x5205b8122e1f6fa6066ba487e49f6e4cc81c2cbd` 及本次执行合约 `0xe45572dff1865af5f12208b09ce7506847f628bd`；不把其他路由器归入共同所有权。

扣池费后的毛价差 0.007001958297245002 ETH，gas 0.002419126290265662 ETH，直接向区块 fee recipient 支付 0.002398332464181997 ETH，净现金流 0.002184499542797343 ETH。非 WETH 代币净库存为零，池流量层面的 WETH 盈余也与该毛价差精确一致。

| 池地址 | 输入合约 / 数量 | 输出合约 / 数量 | Swap log index |
|---|---|---|---|
| `0x0c365789dbbb94a29f8720dc465554c587e897db` | `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` / 0.030182152608108832 | `0xbb0e17ef65f82ab018d8edd776e8dd940327b28b` / 113.083412574719274907 | [176] |
| `0xa040832b1e5026da6dc843e6773a9e4d02fff9b1` | `0xbb0e17ef65f82ab018d8edd776e8dd940327b28b` / 113.083412574719274907 | `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` / 0.037184110905353834 | [173] |

上表按池的净流量列出经济腿；同一池可多次调用，不能将净腿顺序误作 EVM 回调顺序。精确的执行顺序、交易前后储备、V3 sqrtPrice/tick/活跃流动性、原始来源路径见 [完整 JSON](A3_arbitrage.json) 和 [图 3 交互附表](../figures/fig03_transaction_reconstruction.html)。

所有代币数量按历史 RPC decimals 处理；池 token0/token1/factory 及 V3 fee tier 来自归档的历史合约调用。V3 重建是交易前后价格及活跃流动性状态，不代表已经重新计算全部 tick bitmap、fee growth、LP 头寸及协议债务。

判定依据是实际库存闭合、跨池有向闭环、正净现金流和同区块同池反向关联。没有把全部净利润因果归到目标兑换；没有用钱包所有者或品牌的推测替代地址级收支。池费已经包含在实际输出里，不能再从净收益重复扣除。