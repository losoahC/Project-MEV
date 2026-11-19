"""Refresh current verification metadata without treating scientific unknowns as completed facts."""
from datetime import datetime,timezone
import json,subprocess
import xml.etree.ElementTree as ET
from src.visualization.common import ROOT
from src.ingestion.evidence import read_json


def build():
    path=ROOT/'reports/validation.json';v=read_json(path)
    suites=list(ET.parse(ROOT/'reports/pytest-results.xml').getroot().iter('testsuite'))
    for key,attr in [('test_count','tests'),('failures','failures'),('errors','errors'),('skipped','skipped')]:v[key]=sum(int(s.get(attr,0)) for s in suites)
    audit=read_json(ROOT/'reports/acceptance_audit.json');inv=read_json(ROOT/'data/processed/asset_inventory.json')
    v.update({'phase':'M1–M6 bounded research outputs audited; reviewed Canva draft awaits required approval','coverage':read_json(ROOT/'data/processed/coverage.json'),'evidence_objects':len(read_json(ROOT/'data/raw/manifest.json')['objects']),'acceptance_audit':{'requirements_checked':len(audit['requirements']),'status_counts':audit['status_counts'],'path':'reports/acceptance_audit.json'},'academic_report':'reports/final_research_report.md','full_goal_complete':False,'remaining_requirements':['Explicit approval before committing the14-page revised Canva design; see reviewPDF and companion source notes'],'known_data_limits':['Exact fresh Etherscan numbered labels0/16; all16HTTP403; historical leads retained','Independent incident-source corroboration15/16; wallet13unverified,9sourceArbitrum-specific','Full multi-chain theft/recovery/beneficial ownership inventory and causal MEV share unestablished','Historical time-eligible losing auction book and full THOR/no-MEV price-impact counterfactual unavailable'],'milestone1_acceptance':'Bounded pipeline and source investigations complete; exact numbered explorer labels and wallet13corroboration not established','presentation_review':{'pages':14,'status':'reviewed draft awaiting explicit approval tosave','review_pdf':'reports/presentation/presentation_review.pdf','exact_notes':'reports/presentation/presenter_notes.md','render_review':'14available600pxCanva previews inspected,PDFium14page roundtrip inspected;not full-resolution or PowerPoint application test','changes':['unsupported slide4illustration removed in draft','slide6exact-value reference points to companion notes','slide14reports1024ledgers and52tests'],'Canva_internal_notes':'Generic generated notes remain; exact authoritative sources are supplied in per-slide companion notes. Notes-edit operations were not accepted by connector.'}})
    presentation=read_json(ROOT/'reports/presentation/canva_draft_review.json')
    saved=bool(presentation.get('commit_performed') and presentation.get('user_approval_received'))
    if saved:
        v.update(phase='M1–M6 bounded research outputs audited; approved presentation saved and verified',full_goal_complete=True,remaining_requirements=[],goal_wait_status='resolved: approved revision saved')
        v['presentation_review'].update(status='saved_revision_verified',url=presentation['url'],saved_verification=presentation['saved_verification'])
        v['presentation_review']['changes']=[x.replace('in draft','in saved design') for x in v['presentation_review']['changes']]
    if not audit['full_goal_complete']:
        v.update(full_goal_complete=False,phase='Expanded comprehensive MEV research in progress; previous presentation saved',goal_wait_status='active research; no user approval pending',remaining_requirements=[x['requirement'] for x in audit.get('expanded_objective',{}).get('requirements',[]) if x['status']!='complete'])
        objective=audit.get('expanded_objective',{})
        if objective.get('status')=='awaiting_presentation_save_approval':
            latest=read_json(ROOT/'reports/mev_expansion/expanded_requirements_audit.json')['test_result'];v.update(phase='Observed research computations verified; updated Canva copy awaits post-preview save approval',academic_report='reports/mev_expansion/完整套利与MEV核验报告.md',baseline_test_count=v['test_count'],test_count=latest['tests'],failures=latest['failures'],errors=latest['errors'],skipped=latest['skipped'],goal_wait_status='updated 14-page rendered preview available; final save approval required by Canva tool',remaining_requirements=[objective['pending_action']],expanded_delivery_audit=audit.get('expanded_delivery_audit'))
            v['presentation_review'].update(status='original_saved_updated_copy_reviewed_pending_commit',updated_design_id='DAHbVfFZRn0',updated_preview='reports/presentation/completion_revision/review.html',exact_updated_notes='reports/presentation/completion_revision/speaker_notes_zh.md',expanded_results_in_saved_deck=False)
    elif audit.get('expanded_delivery_audit',{}).get('ready_for_delivery'):
        review=read_json(ROOT/'reports/mev_expansion/expanded_requirements_audit.json');latest=review['test_result'];v.update(phase='Expanded bounded arbitrage/MEV research delivered; scientific limits explicit',academic_report='reports/mev_expansion/完整套利与MEV核验报告.md',full_goal_complete=True,baseline_test_count=v['test_count'],test_count=latest['tests'],failures=latest['failures'],errors=latest['errors'],skipped=latest['skipped'],expanded_delivery_audit=audit['expanded_delivery_audit'],goal_wait_status='delivery complete; no approval pending',remaining_requirements=[])
        v['presentation_review']['expanded_results_in_saved_deck']=False
        saved_copy_path=ROOT/'reports/presentation/completion_revision/saved_verification.json'
        if saved_copy_path.exists():
            saved_copy=read_json(saved_copy_path);assert saved_copy['commit']['status']=='committed' and all(saved_copy['checks'].values())
            v['presentation_review'].update(status='updated_copy_saved_and_readback_verified',updated_design_id=saved_copy['revised_copy_design_id'],expanded_results_in_saved_deck=True,url=saved_copy['saved']['design_metadata']['urls']['edit_url'],saved_verification='reports/presentation/completion_revision/saved_verification.json',exact_updated_notes='reports/presentation/completion_revision/speaker_notes_zh.md')
    event_path=ROOT/'data/processed/event_allocation/validation.json'
    if event_path.exists():
        event=read_json(event_path)
        if event.get('all_checks_passed'):
            summary=read_json(ROOT/'data/processed/event_allocation/summary.json');suites=list(ET.parse(ROOT/'reports/event_allocation/pytest.xml').getroot().iter('testsuite'));tests={k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']};assert tests['failures']==tests['errors']==0
            v.update(phase='Unified event-window reference allocation and actual settlement ledgers delivered and reconciled',academic_report='reports/event_allocation/全事件统一分配报告.md',full_goal_complete=True,test_count=tests['tests'],failures=tests['failures'],errors=tests['errors'],skipped=tests['skipped'],goal_wait_status='Defined project deliverable complete; no approval pending',remaining_requirements=[],event_allocation_delivery={'validation':'reports/event_allocation/validation.json','html':'reports/event_allocation/全事件统一分配核验.html','staged_ledger':'reports/event_allocation/all_stages_allocation.csv.gz','counts':summary['counts'],'independent_checks':len(event['checks']),'price_and_scope_limits_explicit':True,'whole_incident_causal_MEV_or_historical_firm_profit_established':False})
            v['presentation_review'].update(event_allocation_revision_in_saved_deck=False,event_allocation_note='Previously approved 14-page Canva copy retained. This new event allocation is delivered in project HTML, CSV, Chinese report and figures.')
    v['milestone6'].update({'raw_sweep_assets':inv['asset_count'],'expanded_wallet_asset_rows':inv['wallet_asset_rows'],'expanded_balanced_rows':inv['balanced_rows'],'raw_inventory_report':'reports/initial_asset_inventory.md','expanded_offline_replay':'reports/expanded_inventory_offline_replay.json'})
    v['milestone45']['anomaly_coverage']=read_json(ROOT/'data/processed/anomaly_coverage.json')
    node=subprocess.run(['node',str(ROOT/'tests/html_filter_smoke.mjs')],text=True,capture_output=True,check=True)
    result=json.loads(node.stdout);(ROOT/'reports/html_filter_smoke.json').write_text(json.dumps(result,indent=2));v['figure1_extension_logic_review']=result
    v['data_query_tables']=len(read_json(ROOT/'data/processed/catalog.json'))
    v['raw_public_records']=len(read_json(ROOT/'data/raw/public_index.json'))
    path.write_text(json.dumps(v,indent=2));print('Validation metadata refreshed:',v['test_count'],'tests;',len(audit['requirements']),'audited requirements; presentation',v['presentation_review']['status'])

if __name__=='__main__':build()
