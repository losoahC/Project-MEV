"""Refresh source corroboration while keeping exact explorer labels and ownership unresolved."""
from src.ingestion.evidence import read_json
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]


def wallet_record(wallet,observations):
    checks=[o for o in observations if wallet['address'].lower() in o.get('addresses',[])]
    independent=[o for o in checks if o.get('result')=='attribution_observed']
    return {**wallet,'chain':'ethereum','label_status':'legacy_label_not_freshly_verified',
        'identity_confidence':'independently_corroborated' if independent else 'unverified_lead',
        'independent_sources':sorted({o['url'] for o in independent}),
        'independent_scope_notes':[o.get('claim','') for o in independent],
        'ownership_cluster':None,'cluster_note':'Source corroboration of an incident address is not proof of common beneficial ownership or cross-chain account control.'}


def refresh():
    observations=read_json(ROOT/'data/fixtures/identity_observations.json')['observations']
    path=ROOT/'data/processed/wallet_registry.json';rows=[wallet_record(w,observations) for w in read_json(path)]
    path.write_text(json.dumps(rows,indent=2))
    coverage_path=ROOT/'data/processed/coverage.json';coverage=read_json(coverage_path)
    coverage['wallets_independently_corroborated']=sum(w['identity_confidence']=='independently_corroborated' for w in rows)
    coverage['identity_scope_note']='Independent sources corroborate incident-address association, not exact current Etherscan numbering or common ownership. Wallet 9 independent source concerns Arbitrum, not separate Ethereum-control proof.'
    coverage_path.write_text(json.dumps(coverage,indent=2))
    print('Independently source-corroborated incident addresses:',coverage['wallets_independently_corroborated'],'/16; exact freshly read Etherscan labels remain unverified')


if __name__=='__main__':
    refresh()
