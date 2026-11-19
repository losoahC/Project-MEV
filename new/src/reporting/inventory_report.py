"""Report the complete raw-token universe of observed sweeps without ticker valuation."""
from decimal import Decimal,localcontext
import json
from src.visualization.common import ROOT

def build():
    d=json.loads((ROOT/'data/processed/asset_inventory.json').read_text())
    lines=['# Observed initial sweeps and expanded asset inventory','',f"**Observed scope:** {d['asset_count']} assets in {len(d['initial_tx_hashes'])} exchange-address-to-lead transactions, {d['initial_edges']} distinct transfer events. Historical opening/closing snapshots cover every one of these assets at all 16 address leads: {d['balanced_rows']}/{d['wallet_asset_rows']} raw-unit ledgers reconcile exactly, with {d['missing_balance_calls']} failed balance calls.",'',f"Source address: `{d['exchange_source_address']}`. Opening block {d['opening_block']:,}; closing block {d['closing_block']:,}. This raw-token inventory expands beyond the four-asset USD snapshot. It does not combine amounts across currencies or imply that every recipient shares an owner.",'','## Sweep transactions','']
    for h in d['initial_tx_hashes']:lines.append(f'- [Ethereum transaction {h}](https://etherscan.io/tx/{h})')
    lines += ['','These are the three observed sweeps from the stated source address. Other incident source addresses, other chains, custody-account USDC and intermediate conversion inflows are not silently relabeled as part of these three sweeps. The total event theft remains unresolved.','',
    '## Asset-by-asset raw accounting','', '| Exact token identity | Display symbol¹ | Historical decimals | Three-sweep input quantity | Closing quantity across 16 leads | Raw ledger residual |','|---|---|---:|---:|---:|---:|']
    for r in d['assets']:
        n=r['decimals']
        def q(key):
            if n is None or r[key] is None:return 'unresolved'
            with localcontext() as ctx:
                ctx.prec=100
                return str(Decimal(r[key])/Decimal(10)**n)
        lines.append(f"| `{r['token']}` | {r['symbol_from_legacy_metadata_only'] or 'unknown'} | {n} | {q('initial_exchange_sweep_in_raw')} | {q('observed_closing_raw')} | {q('unexplained_change_raw')} |")
    lines += ['', '¹ Display symbols are carried from legacy metadata only. Exact contract address is the identity; no symbol-only price match is permitted. Decimals and balances are historical RPC results, not inferred from symbols.','',
    'Closing balance may include other inflows, intermediate swaps, debt proceeds and conversions during the window. It is therefore not the same as “remaining original stolen units”. Likewise, a zero closing balance inside these leads does not prove funds were recovered or economically destroyed; transfers to other addresses need separate provenance.','',
    '## Verification and reproducibility','',
    'Read-only Ethereum historical calls use Multicall3 aggregate3 to return all 16 balances plus decimals per token/block. Both endpoint bytecodes, exact ABI-encoded requests, returned bytes and acquisition timestamps are retained. Deployment source: [official Multicall3 repository](https://github.com/mds1/multicall3). Overlapping four-asset rows are checked against the independently requested direct-RPC snapshots; disagreement raises an error. This is not a cryptographic state proof.','',
    'Supporting datasets: `data/processed/asset_inventory.json`, `asset_inventory.parquet`, `initial_sweep_assets.parquet`. Each row includes exact opening/closing RPC evidence and all contributing transfer edge IDs; each asset lists the original sweep events.','',
    '```bash','python -m src.reconciliation.inventory --online  # only if raw objects are missing','python -m src.reconciliation.inventory           # cached, read-only offline reconstruction','python -m src.reporting.inventory_report','```','',
    'The four-asset USD ledger and observed USDT/USDC blacklist snapshot remain separate: [M6 reconciliation](milestone6_report.md). The wider inventory does not replace missing price or recovery observations with invented USD values.']
    (ROOT/'reports/initial_asset_inventory.md').write_text('\n'.join(lines)+'\n');print('Wrote 64-asset raw inventory report with 1024 snapshot reconciliations')

if __name__=='__main__':build()
