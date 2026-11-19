"""One explicit time and quote policy shared by every chain and category."""
from pathlib import Path
from src.arbitrage.discover import ROOT

START=1793305800  # 2026-10-29 20:30:00 UTC / 16:30 New York
END=1793343600    # 2026-10-30 07:00:00 UTC / 03:00 New York, exclusive
OUT=ROOT/'data/processed/event_allocation'
REPORT=ROOT/'reports/event_allocation'
POLICY={
    'version':'event-allocation-v1',
    'time_window':{'start_utc':'2026-10-29T20:30:00Z','end_utc_exclusive':'2026-10-30T07:00:00Z','start_timestamp':START,'end_timestamp_exclusive':END,'display_timezone':'America/New_York'},
    'primary_price_policy':'The same prior completed minute for every entry in a transaction. Verified-contract Coinbase USD spot; verified secondary venues and actual USDTUSD conversion explicitly recorded. Missing quotes remain unpriced, never zero.',
    'bitquery_comparison_policy':'Separate stablecoin-USD1 sensitivity, retaining the same prior-completed-minute quote clock. Bitquery used same-minute Hyperliquid marks and different chain cutoffs; this is not called exact replication.',
    'deduplication_keys':{'transaction':['chain','tx_hash'],'transfer':['chain','tx_hash','event_or_trace_index','asset','component'],'trade_leg':['chain','tx_hash','pool_key','log_index'],'fee':['chain','tx_hash','fee_kind']},
    'primary_identity':'Signed hacker reference loss after own onchain cost = signed non-hacker asset/position changes + protocol fee burn. Unpriced asset vectors conserve separately. These are reference-value changes, not historical cost-basis or causal MEV profits.',
    'proposer_rule':'Searcher/block-recipient fees appear once in the primary table. Actual proposer payouts are a secondary redistribution and are not added to primary extraction. The event share is not inferred from the whole block payout.',
    'control_rule':'Before the first monitored target at a pool is control. Other calls or pools in the same transaction are execution context. Same-pool activity after a target is association, not proof of incident causation.',
    'universe_rule':'The archived identified target-wallet/order/swap set and every authenticated pool/PoolId touched by those targets in the specified window. Exact reconciliation to Bitquery undisclosed full transaction universe is not asserted. Other-pool routes inside the selected transactions remain visible in the complete actual journal.',
}

def setup():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
