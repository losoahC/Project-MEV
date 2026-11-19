"""Investigate retained bid timing without inventing the proposer's selection cutoff."""
from collections import defaultdict
from decimal import Decimal
import json

import pandas as pd

from src.ingestion.evidence import read_json
from src.visualization.common import ROOT


def run():
    submissions=read_json(ROOT/'data/processed/auction_submissions.json')
    outcomes={o['case_id']:o for o in read_json(ROOT/'data/processed/auction_outcomes.json')}
    groups=defaultdict(list)
    for s in submissions:
        groups[(s['case_id'],s['relay'])].append(s)
    rows=[]
    for (case_id,relay),bids in sorted(groups.items()):
        winner=outcomes[case_id]
        slot_start_ms=(1606824023+winner['slot']*12)*1000
        timed=[b for b in bids if b.get('timestamp_ms') is not None]
        delivered=[int(b['timestamp_ms']) for b in timed if b['delivered_block_hash_match']]
        others=[b for b in bids if not b['delivered_block_hash_match']]
        highest=max(others,key=lambda b:int(b['value'])) if others else None
        prior=[b for b in others if b.get('timestamp_ms') is not None and delivered and int(b['timestamp_ms'])<=min(delivered)]
        rows.append({'case_id':case_id,'relay':relay,'slot':winner['slot'],'observed_rows':len(bids),'timed_rows':len(timed),
            'delivered_value_wei':winner['delivered_value_wei'],
            'first_delivered_payload_submission_offset_ms':min(delivered)-slot_start_ms if delivered else None,
            'max_other_value_wei':highest['value'] if highest else None,
            'max_other_submission_offset_ms':int(highest['timestamp_ms'])-slot_start_ms if highest and highest.get('timestamp_ms') is not None else None,
            'max_other_tx_block_hash':highest['block_hash'] if highest else None,
            'observed_other_above_delivered_rows':sum(int(b['value'])>int(winner['delivered_value_wei']) for b in others),
            'max_other_before_first_delivered_candidate_wei':str(max(int(b['value']) for b in prior)) if prior else None,
            'selection_cutoff_ms':None,
            'interpretation':'Relay-declared receipt timestamps only. First retained delivered-payload submission is not the proposer selection time. Higher non-delivered submissions do not by themselves establish auction failure.'})
    (ROOT/'data/processed/auction_timing_assessment.json').write_text(json.dumps(rows,indent=2))
    pd.DataFrame(rows).to_parquet(ROOT/'reports/tables/fig05_bid_timing.parquet',index=False)
    print(f'Investigated retained arrival timing in {len(rows)} nonempty relay/slot groups; proposer cutoff remains unobserved')


if __name__=='__main__':
    run()
