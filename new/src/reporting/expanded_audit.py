"""Review expanded deliverables without certifying unidentified all-incident quantities."""
import json,csv,hashlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from decimal import Decimal
from datetime import datetime,timezone
from src.arbitrage.discover import ROOT

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ['a','img']:self.links += [v for k,v in attrs if k in ['href','src']]

def run():
    p=ROOT/'data/processed/mev_full_window';t=ROOT/'data/processed/mev_tron';out=ROOT/'reports/mev_expansion';read=lambda name:json.loads((p/name).read_text());tr=lambda name:json.loads((t/name).read_text());checks=[]
    def check(name,condition,refs,finding):checks.append({'requirement':name,'passed':bool(condition),'evidence':refs,'finding':finding})
    s=read('summary.json');check('完整可用 Ethereum 窗口扫描',s['blocks']==3311 and s['receipts']==751258 and s['failures']==0,['data/processed/mev_full_window/summary.json'],'完整原始窗口，不声称全历史／全链。')
    units=read('strategy_units.json');candidates=read('candidates.json');hashes=[tx['tx_hash'] for u in units for tx in u['txs']];check('去重单元与区间成本腿',len(hashes)==len(set(hashes))==12967 and {h for u in units for h in u['candidate_hashes']}=={r['tx_hash'] for r in candidates},['data/processed/mev_full_window/strategy_units.json'],'12,249 个单元；12,841 候选；含 126 笔补入成本腿。')
    sender=read('sender_accounting_summary.json');check('完整窗口其他成本上下文',sender['transactions']==137013 and sender['failures']==0,['data/processed/mev_full_window/all_sender_accounting.jsonl'],'包括 124,172 笔非直接候选；窗口外成本仍未知。')
    affected=read('affected_pool_scope_summary.json');check('不局限目标附近五块',affected['scope_transactions']==71434 and affected['discovery_cutoff_blocks'] is None,['data/processed/mev_full_window/affected_pool_scope.jsonl'],'160 池完整窗口活动；不把活动都认作 MEV。')
    route=read('full_route_summary.json');check('逐笔路线与明确 MEV 判据',route['candidate_transactions']==12841 and route['swap_event_rows']==49922 and not route['gas_used_as_sufficient_MEV_test'],['reports/mev_expansion/全部候选池路径.csv','reports/mev_expansion/全部操作单元与判据.csv','docs/MEV判定标准.md'],'每个单元有机制条件；相邻、盈利或高 Gas 均非单独充分条件。')
    terminal=read('terminal_cycle_summary.json');terminal_rows=read('terminal_cycle_profits.json');check('资产闭合、费用和负净额保留',terminal['verified_disjoint_cycle_units']==len(terminal_rows)==2685 and terminal['fully_priced_units']==sum(r['net_reference_USD'] is not None for r in terminal_rows) and terminal['nonpositive_after_cost_units']==sum(r['net_reference_positive'] is False for r in terminal_rows)>0,['data/processed/mev_full_window/terminal_cycle_profits.json'],'逐币数量与有效价格分开；缺价不填零；闭合子集不是全事件利润。')
    money=read('covered_surplus_distribution.json');tot={k:Decimal(v) for k,v in money['totals_ETH'].items()};check('排序费用分拆与严格中转路径',tot['gross']==sum(tot[k] for k in ['burn','priority','direct','indirect','retained']),['data/processed/mev_full_window/covered_surplus_distribution.json','src/arbitrage/indirect_payments.py'],'2391 个 ETH/WETH 正收益单元；不将 proposer 二次付款重复扣除。')
    addresses=read('covered_cycle_address_changes.json');check('实际逐地址留存分解',addresses['all_joint_boundaries_reconciled'] and len(addresses['rows'])==4733,['reports/mev_expansion/闭合循环逐地址净变化.csv'],'联合操作边界分到真实地址净变化，不冒充最终余额／控制人。')
    vr=read('victim_replays.json')['rows'];check('目标条件影响与参考差额分开',len(vr)==22 and all(r['status']=='verified_fixed_call_victim_intervention' and all(e['inputs_unchanged'] for e in r['victim_effects']) for r in vr),['data/processed/mev_full_window/victim_replays.json','reports/mev_expansion/victim_intervention_index.md'],'固定调用删除前腿；实际前缀先复现；不同干预不相加。')
    comet=read('comet_resolver_equity.json');check('订单借款不冒充利润',int(comet['position_equity_change_raw']['0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'])==-int(comet['states']['after']['borrow_raw']),['data/processed/mev_full_window/comet_resolver_equity.json'],'抵押加回、新债务扣除；诊断查询 Gas 不算真实成本。')
    partition=read('order_reference_shortfall_partition.json');check('最大订单损失去向精确对平',partition['partition_reconciles_exactly'] and not partition['MEV_incremental_loss_proven'],['data/processed/mev_full_window/order_reference_shortfall_partition.json'],'$6.966M 参考差额拆为权益、区块付款、第三方结算和 Gas，不称因果 MEV。')
    cp=read('order_counterparty_redistribution.json');check('九笔订单实际对手方地址',len(cp['rows'])==199 and all(r['known_price_asset_partition_reconciles_exactly'] for r in cp['summary_by_order']),['reports/mev_expansion/九笔订单逐地址分配.csv'],'3 笔全部地址资产可估值，6 笔有未估值资产；池托管余额不是 LP 钱包利润。')
    sig=tr('all_named_signature_audit.json');ta=tr('all_named_bot_accounting.json');check('四个 TRON 地址完整分页和签名主体',ta['fully_collected_named_bots'] and len(ta['rows'])==3541 and sig['all_txid_verified'] and sig['owner_signer_matches']==3541,['data/processed/mev_tron/all_named_bot_accounting.json','data/processed/mev_tron/canonical_transaction_overrides.json'],'包括失败尝试；23 笔索引字节偏差以 solidified canonical body 修正，原文保留。')
    jl=tr('justlend_position_adjustments.json');check('TRON 库存与借贷仓位分开',len(jl['rows'])==15 and all(r['complete_for_principal_conversion'] for r in jl['rows']),['data/processed/mev_tron/justlend_position_adjustments.json'],'Mint/Redeem 份额与实际资产本金相对，Borrow 增负债；旧持仓利息和重估仍未知。')
    tm=tr('pool_metadata_current.json');check('TRON 当前 metadata 不冒充历史状态',len(tm)==143 and all(r['current_factory_lookup_matches_pool'] and not r['historical_identity_proven'] for r in tm),['data/processed/mev_tron/pool_metadata_current.json'],'143 池当前 factory 匹配，54 仍未命名；历史金额来自回执。')
    target=tr('target_owner_summary.json');check('TRON 17笔目标与窗口外试单',target['all_positive_TRX_USDT_input_swaps']==17 and target['priced_all_swap_rows']==17 and target['all_swap_reference_shortfall_USD'] is not None and not target['unpriced_all_swap_hashes'],['data/processed/mev_tron/target_owner_accounting.json'],'17/17 已估值；100USDT 试单位于原bot窗口之后，未塞进窗口比较。')
    profiles=read('named_address_profiles.json');check('Bitquery 口径比较与未复现差异',len(profiles['summary'])==13 and next(r for r in profiles['summary'] if r['address'].startswith('0x0cdd'))['simple_ETH_stable_trades']==100,['reports/mev_expansion/完整套利与MEV核验报告.md','data/processed/mev_full_window/named_address_profiles.json'],'对照原表，不将接近数字、单腿和不同边界当精确复现。')
    parser=Links();parser.feed((out/'完整套利与MEV核验报告.html').read_text());broken=[]
    for link in parser.links:
        u=urlsplit(link)
        if not u.scheme and u.path and not (out/unquote(u.path)).resolve().exists():broken.append(link)
    check('中文报告、本地图和下载链接',not broken and len(parser.links)>50,['reports/mev_expansion/完整套利与MEV核验报告.html'],'静态 HTML 链接／图片引用核对；四张 PNG 已目视审查。浏览器 access host 不可用，未声称完成浏览器页面视觉检查。')
    xml=ET.parse(out/'completion-pytest.xml').getroot();suites=list(xml.iter('testsuite'));tests={k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']};check('完整检查',tests['tests']>=87 and tests['failures']==tests['errors']==tests['skipped']==0,['reports/mev_expansion/completion-pytest.xml'],'当前完整检查；原52及76项XML保留为旧快照，不冒充新结果。')
    complete=read('complete_pool_surplus_distributions.json');check('全部分配差额已复算对平',complete['summary']['previous_gap_units']==complete['summary']['fully_reconciled']==471 and complete['summary']['still_not_reconciled']==0,['data/processed/mev_full_window/complete_pool_surplus_distributions.json','reports/mev_expansion/完整池收益逐地址分配.csv'],'471单元、1322地址记录；ETH/WETH现金与V4底层凭证分开；不合并受益人。')
    transfers=read('transfer_audit_summary.json');check('真实转账与Etherscan复核入口',transfers['transactions']==34397 and transfers['movement_rows']==397776 and not transfers['failures'] and (out/'真实收支核对入口.html').exists(),['reports/mev_expansion/逐笔真实转账与Etherscan链接.csv.gz','reports/mev_expansion/逐交易逐地址实际收支.csv.gz','reports/mev_expansion/真实收支核对入口.html'],'批量数量来自回执和成功调用树；浏览器页面仅提供人工复核链接，不虚称已逐页抓取。')
    auctions=read('full_auction_allocation.json');check('全窗口实际proposer付款',auctions['summary']['onchain_proposer_amount_matches']==auctions['summary']['unique_observed_delivery_blocks']==2939 and not auctions['summary']['amount_mismatches'],['data/processed/mev_full_window/full_auction_allocation.json'],'2939/2939交付金额和链上实际收款一致；native builder余额代理与公司利润分开。')
    joint=read('joint_front_replays.json');hashes=[e['target'] for r in joint['rows'] for e in r.get('target_effects',[])];check('扩大执行干预并去重',len(joint['rows'])==319 and len(hashes)==len(set(hashes))==372 and all(r['status']=='verified_joint_block_intervention' for r in joint['rows']),['data/processed/mev_full_window/expanded_front_replays.json','data/processed/mev_full_window/joint_front_replays.json'],'每块联合删除前腿，目标只计一次。各块父状态独立，不冒充连续全事件无MEV反事实。')
    recovery=read('recovered_target_removals.json');check('旧六项失败的具体诊断',recovery['funding_infeasible_after_target_removal']==6 and recovery['unexplained_transport_or_execution_errors']==0,['data/processed/mev_full_window/recovered_target_removals.json'],'删除目标后剩余调用资金不足，情景不可执行；未伪造余额或填零收益。')
    pm=read('pool_metadata_full_summary.json');check('所有普通池历史资产身份',pm['historical_asset_identities_verified']==pm['pools']==1097 and pm['factory_matches']==1096,['data/processed/mev_full_window/complete_factory_membership_audit.json','data/processed/ammalgam_historical_identity.json'],'1096历史factory目录匹配；另一个历史implementation及underlyingTokens确认Ammalgam借贷池，保留不同协议风险。')
    principal=read('position_principal_ledger.json');check('所有仓位单元本金分账',principal['summary']['position_or_NFT_units']==200 and principal['summary']['decoded_events']==1025 and principal['summary']['loan_collateral_rows']==167,['data/processed/mev_full_window/position_principal_ledger.json'],'所有200单元的现金、借贷与流动性本金分开；借入和释放旧本金不称利润。')
    csvrows={}
    for path in out.glob('*.csv'):
        with path.open() as f:csvrows[path.name]=sum(1 for _ in csv.DictReader(f))
    expected={'全部候选池路径.csv':49922,'全部操作单元与判据.csv':12249,'闭合循环逐地址净变化.csv':4733,'TRON逐笔池路径.csv':1722,'九笔订单逐地址分配.csv':199,'完整池收益逐地址分配.csv':1322,'逐笔真实转账与Etherscan链接.csv':397776,'逐交易逐地址实际收支.csv':500996,'全窗口拍卖与实际付款.csv':2939};check('交付明细数量',all(csvrows.get(k)==v for k,v in expected.items()),['reports/mev_expansion/'],'不同CSV分别对应事件、资产、地址或交易，跨表不能混加为事件数。')
    digests={}
    for path in sorted(out.iterdir()):
        if path.is_file() and path.suffix in ['.md','.html','.png','.svg','.csv','.xml']:
            h=hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
            digests[str(path.relative_to(ROOT))]=h.hexdigest()
    doc={'updated_utc':datetime.now(timezone.utc).isoformat(),'scope':'Research computations and review artifacts over the bounded observed evidence; not a certificate of all-incident causal or beneficial-owner identification.','ready_for_delivery':all(c['passed'] for c in checks),'checks':checks,'failed_checks':[c['requirement'] for c in checks if not c['passed']],'test_result':tests,'csv_data_rows':csvrows,'broken_local_report_links':broken,'artifact_sha256':digests,'scientific_unknowns':{'all_incident_causal_MEV_loss_USD':None,'all_incident_firm_wide_arbitrage_profit_USD':None,'ultimate_beneficial_owners_complete':False,'unresolved_external_distribution_units':complete['summary']['still_not_reconciled'],'unpriced_terminal_cycle_units':terminal['verified_disjoint_cycle_units']-terminal['fully_priced_units'],'orders_with_unpriced_counterparty_assets':sum(not r['all_address_assets_priced'] for r in cp['summary_by_order']),'TRON_historical_state_replay_proven':False,'exact_Bitquery_global_replication':False},'presentation':'Original approved 14-page Canva remains saved. Updated 14-page copied design DAHbVfFZRn0 has concrete rendered review pages; commit requires the Canva tools explicit approval after this new preview. See reports/presentation/completion_revision/review.html.'};(out/'expanded_requirements_audit.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False));print(json.dumps({'ready_for_delivery':doc['ready_for_delivery'],'checks':len(checks),'failed':doc['failed_checks'],'tests':tests,'csv_rows':csvrows,'broken_links':broken},indent=2))
    saved_path=ROOT/'reports/presentation/completion_revision/saved_verification.json'
    if saved_path.exists():
        saved=json.loads(saved_path.read_text());assert saved['commit']['status']=='committed' and saved['post_preview_user_approval_received'] and all(saved['checks'].values())
        doc['presentation']='Updated 14-page copy DAHbVfFZRn0 saved after explicit post-preview approval and independently read back; original DAHbT7iYK6M preserved. All 14 restored renders pixel-identical to the approved preview. Exact sources remain in the Chinese companion narration.'
        doc['updated_presentation_saved_and_verified']=True;doc['presentation_verification']='reports/presentation/completion_revision/saved_verification.json';(out/'expanded_requirements_audit.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False))
if __name__=='__main__':run()
