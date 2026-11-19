import copy,json
from decimal import Decimal
from src.arbitrage.classify import classify
from src.arbitrage.discover import ROOT

def test_high_gas_and_builder_payment_alone_do_not_classify_mev():
    c={'tx_hash':'0xexample','block':1,'sender':'a','executor':'b','associations':[],'pool_legs':[],'swap_event_count':0,'gas_wei':str(10**22),'identified_builder_payment_wei':str(10**22),'net_after_gas_and_builder_ETH':'1','other_token_residual_raw':{},'pool_inventory_closed_WETH_cycle':False}
    a=classify(c)
    assert a['mechanism']=='inventory_or_episode_accounting_required'
    assert a['ordering_evidence']=='same_pool_association_only'
    assert not a['mev_causally_established']

def test_discovery_recovers_all_original_cycles_without_selection_fixture():
    rows=json.loads((ROOT/'data/processed/mev_discovery/candidates.json').read_text());byhash={r['tx_hash']:r for r in rows}
    old=json.loads((ROOT/'data/processed/arbitrage_cases.json').read_text())
    assert len(old)==3
    for c in old:
        r=byhash[c['tx_hash']]
        assert r['net_after_gas_and_builder_ETH']==c['net_after_gas_and_builder_ETH']
        assert classify(r)['criteria']['after_target_same_pool_opposite_direction']

def test_episodes_include_negative_legs_and_reconcile_fees():
    rows=json.loads((ROOT/'data/processed/mev_discovery/episodes.json').read_text())
    for e in rows:
        assert Decimal(e['gross_ETH'])-Decimal(e['gas_ETH'])-Decimal(e['direct_builder_ETH'])==Decimal(e['net_ETH'])
    example=next(e for e in rows if e['block']==26302760 and e['sender']=='0xc623b0b546bf3031ba88a583a46d5180df8d67c2')
    assert example['transaction_count']==2
    assert Decimal(example['positive_single_leg_candidate_subtotal_ETH'])>1300
    assert Decimal(example['net_ETH'])<1

def test_route_catalog_preserves_every_swap_and_does_not_invent_dex_names():
    rows=json.loads((ROOT/'data/processed/mev_discovery/ordered_routes.json').read_text())
    assert len(rows)==3210
    for r in rows:
        assert len(r['ordered_swaps'])==r['swap_event_count']
        assert [s['log_index'] for s in r['ordered_swaps']]==sorted(s['log_index'] for s in r['ordered_swaps'])
        for s in r['ordered_swaps']:
            if s['DEX']:assert s['factory_lookup_matches_pool']

def test_episode_price_ledger_includes_loss_leg_instead_of_large_receipt():
    rows=json.loads((ROOT/'data/processed/mev_discovery/episode_valuations.json').read_text())
    r=next(x for x in rows if x['block']==26302760 and x['sender']=='0xc623b0b546bf3031ba88a583a46d5180df8d67c2')
    assert r['transaction_count']==2 and r['valuation_complete']
    assert any(Decimal(t['marked_after_gas_USD'])<0 for t in r['transactions'])
    assert abs(Decimal(r['marked_after_gas_USD']))<100000
    assert r['causal_hacker_loss_USD'] is None

def test_a1_six_rounds_preserve_21_swaps_and_reconcile_pool_surplus():
    rows=json.loads((ROOT/'data/processed/mev_discovery/ordered_routes.json').read_text())
    r=next(x for x in rows if x['tx_hash']=='0x722001ce0a09024d683592474d12df947aa9548befb0292ae098a9db37a0aa7c')
    assert r['swap_event_count']==21 and r['distinct_pools']==14
    assert [(c['first_swap_number'],c['last_swap_number']) for c in r['contiguous_token_cycles']]==[(1,4),(5,7),(8,11),(12,14),(15,18),(19,21)]
    weth='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
    assert all(set(c['pool_flow_surplus_raw'])=={weth} for c in r['contiguous_token_cycles'])
    surplus=sum(int(c['pool_flow_surplus_raw'][weth]) for c in r['contiguous_token_cycles'])
    assert Decimal(surplus)/Decimal(10)**18==Decimal('12.137824203978034597')
