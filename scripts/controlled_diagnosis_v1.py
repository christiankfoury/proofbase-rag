"""AD2 saved-observation harness and prospective budget. No live execution mode."""
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import json
import socket
from unittest.mock import patch
from scripts import application_diagnosis_v1 as traces
from scripts.evaluation_reliability_inventory import ROOT, OUT, OLD, read, save, sha

CASES=('dev-01','dev-03','dev-05','dev-06','dev-07','dev-08','dev-09','dev-10','dev-11','dev-12')
PRICES={'application':('0.40','1.60'),'embedding':('0.02','0')}


def core(row):
    """Source context is the intervention; every other causal input is fixed."""
    return dict(original_question=row['original_question'],history=row['history'],scope=row['scope'],expected=row['expected'],
                runtime_commit=row['runtime_commit'],profile=row['profile'],
                corpus_binding=row['corpus_binding'],profile_binding=row['profile_binding'])


def profile_binding(row):
    configs=[]
    for call in row['calls']:
        raw=read(ROOT/call['path']); body=raw['request']
        configs.append(dict(stage=call['stage'],model=body['model'],settings=call['settings'],
                            system_messages=[m for m in body['messages'] if m['role']=='system'],
                            schema=body['response_format']))
    return traces.fingerprint(configs)


def check_authorized(sources,scope):
    ids=[s['chunk_id'] for s in sources]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate source ID')
    if any(scope['role'] not in s['access_roles'] or s['project_id']!=scope['project_id'] or
           (scope['department_id'] is not None and s['department_id']!=scope['department_id']) for s in sources):
        raise ValueError('Unauthorized source')


def verified_call(call):
    path=ROOT/call['path']
    if sha(path)!=call['sha256']: raise ValueError('Stage custody changed')
    raw=read(path)
    settings={k:raw['request'][k] for k in ('temperature','reasoning_effort','max_completion_tokens') if k in raw['request']}
    if (raw['status']!='received' or traces.parsed(raw)!=call['response'] or
            traces.charge(raw)!=Decimal(call['cost_usd']) or settings!=call['settings'] or
            raw['request']['model']!=call['model'] or
            raw['request']['response_format']['json_schema']['name']!=call['stage']):
        raise ValueError('Stage snapshot differs from receipt')
    return raw


def observe(spec,row,arm):
    """Accept only the captured reference input; never transplant model output."""
    if arm not in ('reference','normal_retrieval'): raise ValueError('Unknown arm')
    if core(spec)!=core(row): raise ValueError('Question/history/scope/runtime/profile/corpus differs')
    check_authorized(row['authorized_sources'],row['scope'])
    if arm=='normal_retrieval':
        # This version has only controlled-retrieval custody adapters. A caller's
        # boolean cannot turn an old fixture response into a normal-index capture.
        return dict(status='not_executed',reason='Saved run used controlled retrieval; no normal-index observation.')
    if traces.fingerprint(row['authorized_sources'])!=spec['source_binding']:
        raise ValueError('Context changed; saved output cannot measure this arm')
    # Read-only custody check for every referenced stage, not just the final answer.
    if sha(ROOT/row['case_path'])!=row['case_sha256']: raise ValueError('Case custody changed')
    saved=read(ROOT/row['case_path'])
    turn=next(t for t in saved['turns'] if t['turn']==row['turn'])
    if (turn['final_response']!=row['delivered'] or turn['question']!=row['original_question'] or
            saved['authorized_evidence']!=row['authorized_sources']):
        raise ValueError('Observation differs from captured content')
    for call in row['calls']:
        verified_call(call)
    return dict(status='executed_saved_evidence',case_path=row['case_path'],case_sha256=row['case_sha256'],
                input_binding=traces.fingerprint(core(row)),source_binding=spec['source_binding'],
                delivered=row['delivered'],diagnostic_dimensions=row['diagnostic_dimensions'],
                latency_ms=row['request_latency_ms'],historical_application_cost_usd=row['historical_application_cost_usd'])


def chain(row):
    for call in row['calls']: verified_call(call)
    producers=[c for c in row['calls'] if c['stage'] in ('generated_answer_v1','conversational_producer')]
    checkers=[c for c in row['calls'] if c['stage'] in ('post_generation_validation_v1','conversational_checker')]
    if not producers or not checkers:
        return dict(status='missing_stages',reason='Route did not produce both a model draft and checker receipt.',
                    delivered=row['delivered']['answer'])
    bound=[]
    for checker in checkers:
        raw=read(ROOT/checker['path']); payload=json.loads(raw['request']['messages'][1]['content'])
        draft=payload['candidate']
        matching=[p for p in producers if p['response']['answer']==draft['answer']]
        if len(matching)!=1: raise ValueError('Checker not bound to exactly one saved draft')
        producer=matching[0]
        # V4's formatter can alter citation excerpts before semantic checking.
        bound.append(dict(producer_path=producer['path'],checker_path=checker['path'],
                          checked_candidate=draft,checker_output=checker['response'],
                          raw_draft_citations=producer['response'].get('citations',[]),
                          checked_citations=draft.get('citations',[]),
                          producer_response_type=producer['response'].get('response_type'),
                          checked_response_type=draft.get('response_type'),
                          delivered_answer_unchanged=draft['answer']==row['delivered']['answer'],
                          delivered=row['delivered']['answer'],
                          final_validation=row['delivered'].get('post_generation_validation')))
    return dict(status='executed_saved_evidence',comparisons=bound,
                correct_draft_false_rejection=None,incorrect_draft_acceptance=None,
                reason='No independently labeled complete draft cohort; source-inspected findings remain in AD1.')


def proposal(rows):
    # One fixed V4 profile, 12 frozen turn contexts, two repetitions of BOTH arms.
    # Later turns use saved history in both arms, not divergent newly generated history.
    v4=[r for r in rows if r['profile']=='v4']; turns=len(v4); reps=2
    requests=turns*2*reps
    suite=read(OLD/'development-v2.json'); stages=[]
    def reserve(stage,count,model,input_cap,output_cap,price):
        ri,ro=map(Decimal,PRICES[price]); amount=(input_cap*ri+output_cap*ro)/1000000
        stages.append(dict(stage=stage,calls=count,model=model,input_cap=input_cap,output_cap=output_cap,
                           per_call_reservation_usd=str(amount),total_reservation_usd=str(amount*count)))
    for stage,n in [('request_assessment',1),('evidence_assessment',1),('generation_including_one_repair',2),('checker_including_repair_check',2)]:
        reserve(stage,requests*n,'gpt-4.1-mini-2025-04-14',16384,2048,'application')
    reserve('query_embedding_normal_arm',turns*reps,'text-embedding-3-small',8192,0,'embedding')
    reserve('corpus_embedding_unique_chunks',len(suite['sources']),'text-embedding-3-small',8192,0,'embedding')
    cap=sum((Decimal(s['total_reservation_usd']) for s in stages),Decimal(0))
    empirical=sum((Decimal(r['historical_application_cost_usd']) for r in v4),Decimal(0))*2*reps
    embedding=sum((Decimal(s['total_reservation_usd']) for s in stages if 'embedding' in s['stage']),Decimal(0))
    reference_receipts=[r['request_latency_ms'] for r in v4]
    return dict(status='proposal_only_not_authorized',provider_execution_available=False,profile_name='v4_only',
        runtime_basis='dad278eb; future launch must freeze code/config/index/corpus and recheck all bindings',
        sampling=dict(frozen_turn_contexts=turns,repetitions_per_arm=reps,arms=2,application_requests=requests,
                      ordering='For each turn run reference then normal on repetition 1, normal then reference on repetition 2.',
                      history='Freeze each saved V4 turn history for both arms; do not chain new assistant responses.',
                      inference_limit='Two paired draws are diagnostics, not a stable causal effect or model score.'),
        profile=dict(model='gpt-4.1-mini-2025-04-14',generation_temperature=0.2,semantic_stage_temperature=0,
                     request_assessment_mode='semantic_all_remaining',
                     request_assessment_prompt='v2',evidence_prompt='v4',checker_prompt='v4',generation_prompt='v1',
                     candidate_enabled=False,multi_doc_mode='off',top_k=5,retrieval_mode='vector_lexical_rerank',
                     provider_retries=0,repair_limit=1,telemetry=False),
        stages=stages,evaluator_calls=0,evaluator_reason='Unqualified live evaluator cannot supply acceptance labels; proposed diagnostic requires separate source inspection, with provenance and unresolved labels.',
        reference_inputs=[dict(case_id=r['case_id'],turn=r['turn'],core=core(r),expected=r['expected'],
                              sources=r['authorized_sources'],source_binding=traces.fingerprint(r['authorized_sources'])) for r in v4],
        corpus=dict(path='data/evaluation/conversation-continuation/development-v2.json',sha256=sha(OLD/'development-v2.json'),
                    chunks=len(suite['sources']),case_source_selection={c['id']:c['source_ids'] for c in suite['cases'] if c['id'] in CASES},
                    policy='Isolated per-case corpus snapshot of declared source IDs before role filtering; immutable source text/metadata. No production corpus replacement. Private-source control stays in index and is role-filtered.',
                    limitation='Tiny selected corpora test routing/context delivery; not large-corpus recall or ranking. Broader retrieval study requires a separately scoped corpus.'),
        expected_application_cost_usd=str(empirical),embedding_full_reservation_usd=str(embedding),
        expected_total_planning_usd=str(empirical+embedding),hard_stage_cap_usd=str(cap),
        maximum_provider_calls=sum(s['calls'] for s in stages),
        expected_timing_seconds=sum(reference_receipts)/1000*2*reps,
        timing_limit='Scaled historical request durations only; index/setup latency and model variability unknown. Timeout budget 30 seconds per call, no retries.',
        maximum_sequential_provider_wait_seconds=sum(s['calls'] for s in stages)*30,
        pricing_basis='Historical pinned price tables, not a current provider quote; must revalidate pricing before any separately authorized launch.',
        remaining_untouched_usd='8.10754050',final_launch_floor_usd='4.50',
        headroom_after_diagnostic_cap_and_final_floor_usd=str(Decimal('8.10754050')-cap-Decimal('4.50')),
        later_release_path=dict(qualification='Not ready: comparison.v1 has no live qualification adapter and unresolved semantic correspondence.',
            historical_qualification_planning_estimate_usd='3.694425',fresh16_and_fresh60='Not authorized; final floor is not a guarantee or hard cap.',
            illustrative_diagnostic_plus_qualification_plus_floor_usd=str(cap+Decimal('3.694425')+Decimal('4.50')),
            funded_acceptance_claim=False),
        stop_conditions=['No paid launch without new explicit scope/budget approval and frozen executor review.',
            'Stop before submission if pricing/input/token/total reservation exceeds any bound; do not truncate to fit.',
            'Stop on unknown request outcome, transport failure or unexpected call; zero retries.',
            'Stop on unauthorized evidence/citation, source/index drift or altered frozen history.',
            'Keep missing arms and unresolved labels; no selective rerun, reference change or release credit.'],
        recommended_now=False)


def build():
    data=read(OUT/'ad1/v1/traces.json')
    for item in data['files']:
        if sha(ROOT/item['path'])!=item['sha256']: raise ValueError('AD1 binding changed')
    rows=deepcopy([r for r in data['rows'] if r['case_id'] in CASES]); reports=[]; specs=[]
    for row in rows:
        suite=OLD/('development-v2.json' if row['profile']=='v4' else 'development-v3.json')
        row.update(corpus_binding=sha(suite),profile_binding=profile_binding(row))
        spec=dict(core(row),source_binding=traces.fingerprint(row['authorized_sources']),case_id=row['case_id'],turn=row['turn'],
                  expected=row['expected'],selected_passages=row['authorized_sources'],
                  selection_rationale=row['annotation']['observation'],
                  sufficiency='absent requested fact; preserve no-answer' if row['case_id'] in ('dev-06','dev-10') else
                    'conflicting rules; sufficient for clarification only' if row['case_id']=='dev-07' else
                    'source-inspected sufficient for requested core; historical expectations retained')
        specs.append(spec)
        reports.append(dict(run=row['run'],case_id=row['case_id'],turn=row['turn'],profile=row['profile'],
                            reference=observe(spec,row,'reference'),normal_retrieval=observe(spec,row,'normal_retrieval'),
                            draft_checker_delivery=chain(row)))
    return dict(version='ad2.v1',source_sha256=sha(OUT/'ad1/v1/traces.json'),
                selected_cases=list(CASES),paired_input_manifest=specs,comparisons=reports,
                arm_counts={arm:dict(Counter(r[arm]['status'] for r in reports)) for arm in ('reference','normal_retrieval','draft_checker_delivery')},
                diagnostic_measures=[dict(profile=profile,turns=len(group),
                    dimension_counts={k:dict(Counter(r['diagnostic_dimensions'][k] for r in group)) for k in group[0]['diagnostic_dimensions']},
                    historical_application_cost_usd=str(sum((Decimal(r['historical_application_cost_usd']) for r in group),Decimal(0))),
                    latency_ms=[r['request_latency_ms'] for r in group],
                    provenance='AD1 agent annotations and deterministic source/citation checks; unlabeled values remain explicit.')
                    for profile in ('v4','v6') for group in [[r for r in rows if r['profile']==profile]]],
                observed_normal_reference_pairs=0,causal_retrieval_effect=None,
                proposal=proposal(rows),new_model_calls=0,new_cost_usd='0',release_eligible=False,target_credit=False)


if __name__=='__main__':
    import sys
    with patch.object(socket.socket,'connect',side_effect=AssertionError('Offline only')):
        result=build(); path=OUT/'ad2/v1/comparisons.json'
        if '--write' in sys.argv: save(path,result)
        elif read(path)!=result: raise ValueError('Comparison replay differs')
        print(json.dumps(dict(arm_counts=result['arm_counts'],budget={k:result['proposal'][k] for k in
              ('hard_stage_cap_usd','expected_total_planning_usd','maximum_provider_calls','expected_timing_seconds','headroom_after_diagnostic_cap_and_final_floor_usd','later_release_path')}),indent=2))
