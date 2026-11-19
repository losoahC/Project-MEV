"""Recompute the delivered event tables from archived inputs by default."""
import argparse

def run(stage):
    if stage=='collect':
        from . import tron_scope,tron_evidence,tron_operator_history,tron_failed_receipts,tron_encoding,prices
        tron_scope.run();tron_evidence.transactions();tron_evidence.receipts();prices.fetch_primary();prices.fetch_binance();prices.fetch_secondary();prices.fetch_supplemental();prices.fetch_hyperliquid();tron_operator_history.run();tron_failed_receipts.run();tron_encoding.collect_unresolved()
    elif stage=='reconstruct':
        from . import ethereum_journal,tron_journal,history_merge,position_rights
        ethereum_journal.run();tron_journal.run();history_merge.run();position_rights.run()
    elif stage=='analysis':
        from . import allocate,proposer,block_settlements,combined_ledger,diagnostics,market_crosscheck,tron_encoding,audit,report
        tron_encoding.run();allocate.run();allocate.run(mode='stable1');proposer.run();block_settlements.run();combined_ledger.run();diagnostics.run();market_crosscheck.run();audit.run();report.run()
    elif stage=='audit':
        from . import audit
        audit.run()
    elif stage=='report':
        from . import report
        report.run()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['analysis','reconstruct','collect','audit','report'],default='analysis');run(p.parse_args().stage)
