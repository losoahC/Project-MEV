# A2 · WETH / SHIB two-pool cycle

交易：[完整哈希](https://etherscan.io/tx/0xa48203e21f385c7685c5656c7492feae9498c6c40b53c709a39d8b94639eb851) `0xa48203e21f385c7685c5656c7492feae9498c6c40b53c709a39d8b94639eb851`。目标交易：[完整哈希](https://etherscan.io/tx/0x2ccafec913543cb6a8f13d9bf8f4fc77b3adb0b9bed4e32171560dac9670976d) `0x2ccafec913543cb6a8f13d9bf8f4fc77b3adb0b9bed4e32171560dac9670976d`。

区块 26302300，UTC 2026-10-30T01:31:47+00:00，目标索引 329，套利索引 333。

记账边界是发送者 `0x0124d0fa0dfb1430dfcff16ec6a96945e7a0bc10` 及本次执行合约 `0x36331e299247e5d0d3261e1d9852f6e0cffee95c`；不把其他路由器归入共同所有权。

扣池费后的毛价差 0.002866070181226265 ETH，gas 0.000972496905296097 ETH，直接向区块 fee recipient 支付 0.001828100586247377 ETH，净现金流 0.000065472689682791 ETH。非 WETH 代币净库存为零，池流量层面的 WETH 盈余也与该毛价差精确一致。

| 池地址 | 输入合约 / 数量 | 输出合约 / 数量 | Swap log index |
|---|---|---|---|
| `0x811beed0119b4afce20d2583eb608c6f7af1954f` | `0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce` / 263597153.258982257484624477 | `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` / 0.52717082604113128 | [575] |
| `0xcf6daab95c476106eca715d48de4b13287ffdeaa` | `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` / 0.524304755859905015 | `0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce` / 263597153.258982257484624477 | [573] |

上表按池的净流量列出经济腿；同一池可多次调用，不能将净腿顺序误作 EVM 回调顺序。精确的执行顺序、交易前后储备、V3 sqrtPrice/tick/活跃流动性、原始来源路径见 [完整 JSON](A2_arbitrage.json) 和 [图 3 交互附表](../figures/fig03_transaction_reconstruction.html)。

所有代币数量按历史 RPC decimals 处理；池 token0/token1/factory 及 V3 fee tier 来自归档的历史合约调用。V3 重建是交易前后价格及活跃流动性状态，不代表已经重新计算全部 tick bitmap、fee growth、LP 头寸及协议债务。

判定依据是实际库存闭合、跨池有向闭环、正净现金流和同区块同池反向关联。没有把全部净利润因果归到目标兑换；没有用钱包所有者或品牌的推测替代地址级收支。池费已经包含在实际输出里，不能再从净收益重复扣除。