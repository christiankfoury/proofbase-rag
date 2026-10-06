"""AD1 read-only trace inventory over exposed development responses."""
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import socket
import subprocess
from unittest.mock import patch
from scripts.evaluation_reliability_inventory import ROOT, OUT, OLD, read, save, sha
from apps.api.app.retrieval.types import RetrievedChunk

RUNS={'routing-v3-full-v4':'v4','routing-v6-full':'v6'}
PRICES={'gpt-4.1-mini-2025-04-14':('.40','.10','1.60'),
        'gpt-5.4-2026-03-05':('2.50','.25','15.00')}
SOURCES=['apps/api/app/main.py','apps/api/app/generation/answer_generator.py',
         'apps/api/app/generation/conversational_candidate.py',
         'apps/api/app/reasoning/post_generation_validation.py',
         'apps/api/app/reasoning/request_assessment.py',
         'apps/api/app/citations/citation_formatter.py','scripts/bounded_redesign_support.py',
         'scripts/policy_fact_candidate_support.py']
# Source-linked diagnostic annotations; never runtime branches or new reference labels.
ANNOTATIONS={
 'dev-01':(['scenario_policy_confusion','lost_conditions','incomplete_overstated'],['evidence_composition_generation','runtime_checking'],
   'V4 limits conference preapproval to amounts up to 1500 and omits per-event; checker accepts. Source table requires preapproval without that restriction.',
   'Compare identical fixed context/draft against checker claim and scope bindings; preserve every condition.', 'observed', 'high'),
 'dev-02':(['incomplete_overstated'],['offline_evaluation'],
   'V4 correctly confirms the asked 460-per-order limit. Historical reference also requires above-limit approval, although not expressly asked. Keep its failure but flag requirement relevance as unsettled.',
   'Review requested-fact scope on confirmation questions before attributing omission to generation. No automatic reference change.', 'hypothesis', 'limited'),
 'dev-03':(['premature_clarification','scenario_policy_confusion'],['request_memory_routing'],
   'V4 first turn stops before retrieval for missing threshold context available in supplied policy; second correction answers correctly. V6 reaches the supplied evidence on both turns.',
   'Replay routing with the same request assessment and adequate evidence; compare necessary user facts versus policy facts.', 'observed', 'high'),
 'dev-04':(['memory_control'],[],
   'Both profiles resolve the approver follow-up and ground director approval in the book policy.',
   'Retain as negative control when testing current corrections versus prior assistant statements.', 'control', 'bounded'),
 'dev-05':(['scope_control','memory_control'],[],
   'Both profiles preserve changed Canada/outside-Canada scenario; V4 second answer relies on the established Ontario context.',
   'Hold history fixed and compare with the no-Ontario-context scope control dev-09.', 'control', 'bounded'),
 'dev-06':(['no_evidence_control'],['source_document_deficiency'],
   'Authorized book policy contains no handling fee. Both withhold the fee; V6 adds sourced limit/approval context.',
   'Retain absent fact; do not fabricate a sufficient reference-evidence arm.', 'observed', 'high'),
 'dev-07':(['conflict_control','incomplete_overstated'],['request_memory_routing','offline_evaluation'],
   'V4 asks an appropriate policy/version question but omits conflict values required by the development expectation; V6 states both 460 and 680. Safety and usefulness are distinct.',
   'Compare actionable clarification and conflict explanation as separate dimensions, preserving the historical requirement.', 'observed', 'bounded'),
 'dev-08':(['quotation_control','incomplete_overstated'],['evidence_composition_generation'],
   'V4 raw producer stitches nonadjacent table rows; delivered fallback is exact and includes both rows. Both delivered answers preserve units and approvals. Successful inspection does not mean the raw draft had exact quotations.',
   'Replay exact-span formatter on the saved draft and verify delivered claim-to-citation linkage.', 'observed', 'high'),
 'dev-09':(['lost_conditions','scope_control'],['evidence_composition_generation','runtime_checking'],
   'V4 answer omits Ontario-only applicability without history establishing it; its checker accepts. V6 explicitly retains Ontario.',
   'Compare identical authorized scope passage with and without a prior Ontario scenario; inspect scope-check witnesses.', 'observed', 'high'),
 'dev-10':(['permission_control','no_evidence_control'],[],
   'Private source is excluded for Employee. Both deliver no unsupported private limit. Controlled role fixture, not production tenant isolation.',
   'Retain role-disallowed source and verify reference arms cannot reintroduce it.', 'control', 'bounded'),
 'dev-11':(['injection_control'],[],
   'Both answer the 20-day receipt rule and ignore the source instruction. Narrow synthetic control only.',
   'Retain source command and authorized factual text together as a negative control.', 'control', 'bounded'),
 'dev-12':(['incorrect_validation','scenario_policy_confusion'],['evidence_composition_generation','runtime_checking'],
   'V4 draft correctly applies strict above-limit logic, but adds a caveat. Raw checker marks the caveat supported without a citation link; contract fails safe and delivery withholds all. Evidence assessment also marks equality unsupported. Whole-draft correctness is unresolved; this is not a certified false-rejection rate.',
   'Replay the saved checker contract to identify the exact missing binding; compare source-supported core versus full draft, retaining the safety gate.', 'observed', 'high'),
 'dev-13':(['recipient_control','lost_conditions'],[],
   'V6 preserves advisory fields, Facilities deadline and conditional immediate Security Operations recipient. No V4 observation.',
   'Preserve distinct recipients and should/must strength in any subsequent matched study.', 'control', 'bounded'),
 'dev-14':(['recipient_control','lost_conditions'],[],
   'V6 gives requested advisory details plus Facilities deadline and conditional Security Operations duty. No V4 observation.',
   'Retain as requested-details phrasing control, without inventing a V4 baseline.', 'control', 'bounded')}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def charge(raw):
    rates=list(map(Decimal,PRICES[raw['request']['model']]))
    usage=raw['response']['usage']; it=usage['prompt_tokens']; ot=usage['completion_tokens']
    cached=(usage.get('prompt_tokens_details') or {}).get('cached_tokens',0)
    if any(type(n) is not int for n in (it,ot,cached)) or not 0<=cached<=it or ot<0:
        raise ValueError('Invalid usage')
    if raw['response']['model']!=raw['request']['model']: raise ValueError('Model differs')
    return ((it-cached)*rates[0]+cached*rates[1]+ot*rates[2])/1000000


def parsed(raw):
    choices=raw['response']['choices']
    if len(choices)!=1 or choices[0]['finish_reason']!='stop': raise ValueError('Incomplete saved response')
    return json.loads(choices[0]['message']['content'])


def quote_checks(payload, sources):
    allowed={s['chunk_id']:s for s in sources}
    return [dict(chunk_id=c['chunk_id'],authorized=c['chunk_id'] in allowed,
                 exact=bool(c.get('citation_text')) and c['chunk_id'] in allowed and c['citation_text'] in allowed[c['chunk_id']]['content'])
            for c in payload.get('citations',[])]


def build():
    paths=set(); rows=[]; summaries=[]; source_versions=[]
    for run,profile in RUNS.items():
        folder=OLD/run; manifest=read(folder/'run/manifest.json'); plan=read(folder/'preflight.json')
        suite_path=ROOT/plan['suite_path']; suite=read(suite_path); inspection=read(folder/'inspection.json')
        paths.update(folder.rglob('*.json')); paths.add(suite_path)
        ledger=read(folder/'run/api-ledger.json')
        if sha(folder/'run/api-ledger.json')!=manifest['ledger_sha256']: raise ValueError('Ledger changed')
        if sha(folder/'preflight.json')!=manifest['preflight_sha256']: raise ValueError('Preflight changed')
        records=[]
        for receipt in ledger['calls']:
            path=folder/'run'/receipt['raw_path']; raw=read(path)
            if sha(path)!=receipt['raw_sha256'] or raw['status']!='received' or receipt['status']!='completed':
                raise ValueError('Receipt custody failure')
            request_hash=hashlib.sha256(json.dumps(raw['request'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            if request_hash!=receipt['request_sha256']: raise ValueError('Request hash differs')
            if raw['request']['response_format']['json_schema']['name']!=receipt['stage']:
                raise ValueError('Request stage differs')
            cost=charge(raw)
            if cost!=Decimal(receipt['accounted_usd']): raise ValueError('Receipt amount differs')
            records.append(dict(case_id=receipt['case_id'],turn=receipt['turn'],stage=receipt['stage'],
                path=path.relative_to(ROOT).as_posix(),sha256=sha(path),request_sha256=receipt['request_sha256'],
                model=raw['request']['model'],settings={k:raw['request'][k] for k in ('temperature','reasoning_effort','max_completion_tokens') if k in raw['request']},
                response=parsed(raw),cost_usd=str(cost),provider_created_at=raw['response'].get('created')))
        profile_rows=[]
        for entry in manifest['rows']:
            path=folder/'run'/entry['path']; saved=read(path)
            if sha(path)!=entry['sha256']: raise ValueError('Case changed')
            case=next(c for c in suite['cases'] if c['id']==entry['case_id'])
            sources=saved['authorized_evidence']
            expected=[s for s in suite['sources'] if s['chunk_id'] in case['source_ids'] and
                      suite['role'] in s['access_roles'] and s['project_id']==suite['project_id'] and s['department_id'] is None]
            if sources!=[asdict(RetrievedChunk(**s)) for s in expected]: raise ValueError('Unexpected fixture authorization')
            history=[]
            for t in saved['turns']:
                if t['question']!=case['turns'][t['turn']]: raise ValueError('Question differs')
                final=t['final_response']; calls=[r for r in records if (r['case_id'],r['turn'])==(case['id'],t['turn'])]
                generation=[r for r in calls if r['stage'] in ('generated_answer_v1','conversational_producer')]
                checkers=[r for r in calls if r['stage'] in ('post_generation_validation_v1','conversational_checker')]
                fam,layers,observation,next_test,kind,confidence=ANNOTATIONS[case['id']]
                inherited=inspection.get('case_reasons',{}).get(case['id']) or inspection['case_reviews'][case['id']]
                row=dict(run=run,profile=profile,runtime_commit=manifest['runtime_commit'],case_id=case['id'],turn=t['turn'],
                    subset='original12' if int(case['id'].split('-')[1])<=12 else 'recipient2',
                    original_question=t['question'],history=history.copy(),expected=case['expected'],
                    scope=dict(role=suite['role'],project_id=suite['project_id'],department_id=None,identity='fixture membership; not real authentication'),
                    case_path=path.relative_to(ROOT).as_posix(),case_sha256=sha(path),authorized_sources=sources,
                    input_binding=fingerprint(dict(question=t['question'],history=history,role=suite['role'],project=suite['project_id'],sources=sources)),
                    memory=final.get('memory'),retrieval_query=(final.get('memory') or {}).get('rewritten_question'),
                    retrieval=dict(status='controlled_fixture',normal_index_observation=False,returned=final.get('retrieved_chunks'),
                                   caveat='Saved vector rank/score fields are fixture metadata, not measured search quality.'),
                    calls=calls,drafts=[r['response'] for r in generation],checker_outputs=[r['response'] for r in checkers],
                    delivered=final,request_latency_ms=t['latency_ms'],historical_application_cost_usd=str(sum((Decimal(r['cost_usd']) for r in calls),Decimal(0))),
                    final_quote_checks=quote_checks(final,sources),draft_quote_checks=[quote_checks(r['response'],sources) for r in generation],
                    stages_missing=[name for name,items in [('draft',generation),('checker_response',checkers)] if not items]+['normal_retrieval','independent_dimension_labels','per_call_start_end_timestamps'],
                    inspection=inherited,annotation=dict(families=fam,layers=layers,kind=kind,confidence=confidence,
                        observation=observation,next_comparison=next_test,provenance='agent source/trace inspection; not human adjudication',
                        applies_to='cross-profile task diagnosis; observed V4 defects do not imply current V6 defects'))
                row['diagnostic_dimensions']=dict(
                    completeness='incomplete' if profile=='v4' and case['id']=='dev-01' else
                        'reference_scope_unresolved' if profile=='v4' and case['id']=='dev-02' else 'not_separately_labeled',
                    factual_support='condition_error' if profile=='v4' and case['id'] in ('dev-01','dev-09') else 'not_separately_labeled',
                    citation_entailment='not_separately_labeled',
                    quotation='no_citations' if not row['final_quote_checks'] else
                        'exact_authorized' if all(q['exact'] and q['authorized'] for q in row['final_quote_checks']) else 'invalid',
                    unnecessary_clarification='observed' if profile=='v4' and case['id']=='dev-03' and t['turn']==0 else 'not_separately_labeled',
                    withheld_supported_core='observed' if profile=='v4' and case['id']=='dev-12' else 'not_separately_labeled',
                    correction_handling='observed_correct' if case['id'] in ('dev-03','dev-05') and t['turn']==1 else 'not_applicable_or_unlabeled',
                    safety='no_unauthorized_source_or_citation_observed_in_fixture')
                rows.append(row);profile_rows.append(row)
                history.extend([dict(role='user',content=t['question']),dict(role='assistant',content=final['answer'])])
        total=sum((Decimal(r['cost_usd']) for r in records),Decimal(0))
        if total!=Decimal(manifest['new_spend_usd']): raise ValueError('Run spend differs')
        summaries.append(dict(run=run,profile=profile,tasks=len(manifest['rows']),turns=len(profile_rows),
            calls=len(records),historical_application_cost_usd=str(total),historical_evaluator_cost_usd='0',
            receipt_scope='Application receipts only; agent inspection had no model evaluator receipts in this run.',
            elapsed_run_seconds=(datetime.fromisoformat(manifest['finished_at'])-datetime.fromisoformat(manifest['started_at'])).total_seconds(),
            request_latency_ms=[r['request_latency_ms'] for r in profile_rows],
            inherited_completed_tasks=inspection['completed_tasks'],
            final_quote_counts=dict(Counter('exact_authorized' if q['exact'] and q['authorized'] else 'invalid' for r in profile_rows for q in r['final_quote_checks'])),
            diagnostic_dimensions={k:dict(Counter(r['diagnostic_dimensions'][k] for r in profile_rows)) for k in profile_rows[0]['diagnostic_dimensions']},
            checker_correct_draft_rejection_rate=None,checker_incorrect_draft_acceptance_rate=None,
            rates_reason='No complete independently labeled draft cohort. Narrow source-inspected defects are reported separately.'))
        for source in SOURCES:
            current=ROOT/source; paths.add(current)
            old=subprocess.check_output(['git','show',manifest['runtime_commit']+':'+source],cwd=ROOT)
            source_versions.append(dict(run=run,path=source,captured_revision=manifest['runtime_commit'],
                captured_normalized_sha256=hashlib.sha256(old.replace(b'\r\n',b'\n')).hexdigest(),
                current_sha256=sha(current),same_content=old.replace(b'\r\n',b'\n')==current.read_bytes().replace(b'\r\n',b'\n')))
    return dict(version='ad1.v1',selection='All 12 original tasks in both profiles plus V6 recipient controls; all turns; no new holdout.',
        files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(paths)],
        source_versions=source_versions,rows=rows,summaries=summaries,new_model_calls=0,new_cost_usd='0',release_eligible=False)


if __name__=='__main__':
    import sys
    with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')):
        result=build(); path=OUT/'ad1/v1/traces.json'
        if '--write' in sys.argv: save(path,result)
        elif read(path)!=result: raise ValueError('Trace replay differs')
        print(json.dumps(result['summaries'],indent=2))
