"""Synthetic reducer checks, evidence isolation and frozen component reuse."""
from copy import deepcopy
from decimal import Decimal
import json
import socket
import unittest
from unittest.mock import patch

from scripts import structured_blind_evaluator_v1 as evaluator
from scripts import structured_blind_budget_v1 as budget
from scripts import conversation_ordering_v2 as references
from scripts import quality_eval_contract_v35 as legacy
from scripts.bounded_redesign_run import read, digest


def fixture(name='paraphrase-preserves-conditions', stage='calibration'):
    case = deepcopy(next(c for c in references.cases(stage) if c['id'] == name))
    grade = read(references.legacy.FOLDER / ('grader-v35-'+stage) / 'run' / (name+'.json'))['grade']
    return case, deepcopy(grade)


def packet(grade):
    """Synthetic wrapper only; never a claimed model interpretation/replay."""
    result = deepcopy(grade)
    result['claims'] = [dict(text=c['text'], readings=[dict(
        kind='literal', meaning=c['text'], plausible=True,
        context_reason='Synthetic non-ordering assertion.', context_spans=[],
        **{k: deepcopy(v) for k, v in c.items() if k != 'text'})]) for c in grade['claims']]
    return result


def ambiguous():
    case, grade = fixture('answer-injection-award-pass')
    value = packet(grade)
    action = value['claims'][0]['readings'][0]
    action.update(kind='action_order', meaning='Perform the reporting action before payment.',
                  context_spans=[dict(id='A', span=grade['claims'][0]['text'])])
    presentation = deepcopy(action)
    presentation.update(kind='presentation_order', meaning='Reporting is the first item being explained.',
                        factual_status='supported', citation_status='supported',
                        source_spans=[dict(id='R1', span=case['inputs']['factual_sources'][0]['text'])],
                        citation_spans=[dict(id='C1', span=case['inputs']['cited_sources'][0]['text'])])
    value['claims'][0]['readings'].append(presentation)
    return case, value


def compare(case, first, second=None):
    return evaluator.compare(case['inputs'], case['payload'], case['evidence'],
                             case['safety_flags'], first, deepcopy(first) if second is None else second)


class StructuredBlindTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline only')))

    def test_all_controls_plan_four_blind_requests_with_unchanged_coverage(self):
        for stage in ('diagnostic', 'calibration'):
            for case in references.cases(stage) + references.probes(stage):
                original = dict(evaluator.transport.initial_requests(case['inputs']))
                plan = evaluator.request_plan(case['inputs'])
                self.assertEqual([(r['judge'], r['purpose']) for r in plan],
                                 [('a', 'claims'), ('a', 'coverage'), ('b', 'claims'), ('b', 'coverage')])
                for item in plan:
                    body = item['body']
                    evaluator.transport.reserve(body)
                    self.assertEqual(body['messages'][1], original[item['purpose']]['messages'][1])
                    self.assertEqual(body['max_completion_tokens'], 8192 if item['purpose']=='claims' else 4096)
                    if item['purpose']=='coverage': self.assertEqual(body, original['coverage'])
                plan[0]['body']['messages'][1]['content'] = 'CONTAMINATION'
                self.assertNotIn('CONTAMINATION', plan[2]['body']['messages'][1]['content'])

    def test_gold_candidate_and_prior_review_cannot_enter_plan(self):
        case, _ = fixture()
        for field in ('candidate', 'expected', 'rationale', 'review', 'case_id', 'candidate_judgments'):
            with self.assertRaises(ValueError):
                evaluator.request_plan(dict(case['inputs'], **{field: 'pass'}))

    def test_ambiguity_is_reduced_by_code_and_omission_still_fails(self):
        case, value = ambiguous()
        before = deepcopy(value)
        result = compare(case, value)
        self.assertEqual(result['status'], 'agreement_only')
        self.assertEqual(result['dimensions']['citation_support'], 'unresolved')
        self.assertEqual(result['dimensions']['completeness'], 'fail')
        self.assertEqual(result['dimensions']['overall'], 'fail')
        claim = result['projected_grades'][0]['claims'][0]
        self.assertEqual((claim['factual_status'], claim['citation_status']), ('unknown', 'unknown'))
        self.assertEqual(claim['source_spans'] + claim['citation_spans'], [])
        self.assertEqual(value, before)
        self.assertFalse(result['target_credit'])
        for key in (*legacy.DIMENSIONS, 'quotation_fidelity', 'overall'):
            self.assertEqual(result['dimensions'][key],case['expected'][key])

    def test_complete_ambiguous_answer_still_has_no_success(self):
        _,value=ambiguous()
        case=deepcopy(next(c for c in references.cases('calibration') if c['id']=='ambiguous-complete-order'))
        claim=value['claims'][0]; claim['text']='First, report the missing Ibis token to reception.'
        for r in claim['readings']:
            r['context_spans']=[dict(id='A',span=claim['text'])]
            if r['factual_status']=='supported':
                r['source_spans']=[dict(id='R1',span=case['inputs']['factual_sources'][0]['text'])]
                r['citation_spans']=[dict(id='C1',span=case['inputs']['cited_sources'][0]['text'])]
        fee=dict(text='Pay a 3-credit fee.',factual_status='supported',citation_status='supported',
            source_spans=[dict(id='R1',span='pay a 3-credit fee')],
            citation_spans=[dict(id='C1',span='pay a 3-credit fee')],reason='Synthetic fee control.')
        extra=packet(dict(claims=[fee]))['claims'][0]
        value['claims'].append(extra)
        for fact,span in zip(value['facts'],[claim['text'],fee['text']]):
            fact.update(status='covered',answer_spans=[span])
        value.update(actual_behavior='answer',behavior_span=case['inputs']['answer'])
        result=compare(case,value)
        self.assertEqual(result['dimensions']['overall'],'unresolved')
        self.assertEqual(result['dimensions']['completeness'],'pass')
        self.assertFalse(result['candidate_pass'])

    def test_no_hardcoded_answer_or_case_name(self):
        case, value = ambiguous()
        old = value['claims'][0]['text']; new = 'To begin, inform the service desk of the lost token.'
        case['inputs']['answer'] = case['payload']['answer'] = new
        value['claims'][0]['text'] = new
        value['behavior_span'] = new
        value['facts'][0]['answer_spans'] = [new]
        for r in value['claims'][0]['readings']: r['context_spans'] = [dict(id='A', span=new)]
        self.assertNotEqual(new, old)
        self.assertEqual(compare(case, value)['dimensions']['citation_support'], 'unresolved')

    def test_explicit_unsupported_order_is_not_automatically_unknown_citation(self):
        case, value = ambiguous()
        excluded = value['claims'][0]['readings'][1]
        excluded.update(plausible=False, factual_status='unknown', citation_status='unknown',
                        source_spans=[], citation_spans=[])
        result = compare(case, value)
        self.assertEqual(result['dimensions']['citation_support'], 'fail')
        self.assertEqual(result['projected_grades'][0]['claims'][0]['citation_status'], 'missing')

    def test_supported_presentation_or_supported_order_can_project_support(self):
        for excluded_kind in ('action_order', 'presentation_order'):
            case, value = ambiguous()
            readings = value['claims'][0]['readings']
            supported = deepcopy(readings[1])
            for r in readings:
                if r['kind'] == excluded_kind:
                    r.update(plausible=False, factual_status='unknown', citation_status='unknown', source_spans=[], citation_spans=[])
                else:
                    for k in ('factual_status', 'citation_status', 'source_spans', 'citation_spans'): r[k] = deepcopy(supported[k])
            self.assertEqual(compare(case, value)['dimensions']['citation_support'], 'pass')

    def test_same_label_readings_cannot_create_uncertainty_to_hide_failure(self):
        case, value = ambiguous()
        for r in value['claims'][0]['readings']:
            r.update(factual_status='unknown', citation_status='missing', source_spans=[], citation_spans=[])
        self.assertEqual(compare(case, value)['dimensions']['citation_support'], 'fail')

    def test_missing_readings_or_invalid_context_fail_closed(self):
        for mutation in ('drop', 'duplicate', 'all_excluded', 'bad_id', 'bad_span', 'no_witness', 'excluded_verdict'):
            case, value = ambiguous(); readings=value['claims'][0]['readings']
            if mutation=='drop': readings.pop()
            elif mutation=='duplicate': readings.append(deepcopy(readings[0]))
            elif mutation=='all_excluded':
                for r in readings: r['plausible']=False
            elif mutation=='bad_id': readings[0]['context_spans'][0]['id']='R1'
            elif mutation=='bad_span': readings[0]['context_spans'][0]['span']='invented context'
            elif mutation=='no_witness': readings[0]['context_spans']=[]
            else: readings[1]['plausible']=False
            result=compare(case,value)
            self.assertEqual(result['status'],'invalid',mutation)
            self.assertFalse(result['candidate_pass'])

    def test_unknown_or_excluded_reading_cannot_smuggle_positive_witnesses(self):
        case,value=ambiguous()
        value['claims'][0]['readings'][0]['source_spans']=deepcopy(value['claims'][0]['readings'][1]['source_spans'])
        self.assertEqual(compare(case,value)['status'],'invalid')

    def test_interpretation_disagreement_survives_matching_projected_labels(self):
        case,value=ambiguous(); other=deepcopy(value)
        # Both project unknown/missing, but their interpretation decisions differ.
        for p in (value,other):
            for r in p['claims'][0]['readings']:
                r.update(factual_status='unknown',citation_status='missing',source_spans=[],citation_spans=[])
        other['claims'][0]['readings'][1].update(plausible=False,citation_status='unknown')
        result=compare(case,value,other)
        self.assertEqual(result['status'],'disagreement')
        self.assertEqual(result['disputed_dimensions'],['citation_support','factual_support'])
        self.assertEqual(result['dimensions']['completeness'],'fail')

    def test_omitted_extra_claim_and_fact_disagreement_remain_visible(self):
        case,grade=fixture('unsupported-extra-benefit'); first=packet(grade); second=deepcopy(first)
        second['claims'].pop()
        self.assertIn('factual_support',compare(case,first,second)['disputed_dimensions'])
        case,grade=fixture('contradicted-quantity'); first=packet(grade); second=deepcopy(first)
        second['facts'][0].update(status='missing',answer_spans=[])
        self.assertIn('completeness',compare(case,first,second)['disputed_dimensions'])

    def test_schema_witness_and_metadata_errors_never_pass(self):
        for mutation in ('schema','witness','metadata','incomplete','duplicate'):
            case,grade=fixture(); value=packet(grade)
            if mutation=='schema': value['unexpected']='pass'
            elif mutation=='witness': value['claims'][0]['readings'][0]['source_spans'][0]['id']='UNAUTHORIZED'
            elif mutation=='metadata': case['inputs']['source_metadata']=[dict(source_id='R1',document_id='invented',document_title='invented')]
            elif mutation=='incomplete': value['all_claims_assessed']=False
            else: value['claims'].append(deepcopy(value['claims'][0]))
            self.assertEqual(compare(case,value)['status'],'invalid',mutation)

    def test_safety_and_quotation_gates_cannot_be_voted_away(self):
        for mutation in ('permission','quote','document','response_type'):
            case,grade=fixture(); value=packet(grade)
            if mutation=='permission': case['safety_flags']=['permission_leak']
            elif mutation=='quote': case['payload']['citations'][0]['citation_text']='invented quote'
            elif mutation=='document': case['payload']['citations'][0]['document_id']='wrong document'
            else: case['payload']['response_type']='refuse_no_access'
            result=compare(case,value)
            self.assertFalse(result['candidate_pass'])
            self.assertFalse(result['target_credit'])

    def test_agreement_even_on_supported_answer_is_not_release_acceptance(self):
        case,grade=fixture(); result=compare(case,packet(grade))
        self.assertTrue(result['candidate_pass'])
        self.assertFalse(result['release_eligible'])
        self.assertFalse(result['target_credit'])

    def test_saved_nonordering_labels_round_trip_without_new_accuracy_claim(self):
        for stage,count in (('diagnostic',16),('calibration',21)):
            for case in references.cases(stage)[:count]:
                _,grade=fixture(case['id'],stage)
                result=compare(case,packet(grade))
                self.assertEqual(result['grader_errors'],[[],[]],case['id'])
                for key in evaluator.KEYS:
                    self.assertEqual(result['dimensions'][key],legacy.candidate_judgments(case['inputs'],grade)[key])

    def test_all_original_probe_errors_detected_after_blind_judgment(self):
        # Probes reuse known raw inputs; synthetic packets wrap the source-reviewed
        # saved judgments, never their intentionally incorrect probe candidates.
        for stage in ('diagnostic','calibration'):
            cases=references.cases('calibration')
            for probe in references.probes(stage):
                source=next((c for c in cases if c['inputs']==probe['inputs']),None)
                if source:
                    _,grade=fixture(source['id'])
                else:
                    # The pure-refusal probe has no saved blind judgment.
                    # Construct its known software-control labels explicitly.
                    grade=dict(claims=[],all_claims_assessed=True,actual_behavior='unknown',
                        behavior_span=probe['inputs']['answer'],behavior_reason='Synthetic generic refusal.',
                        relevance=dict(status='pass',reason='Refuses the requested task.'),forbidden_assertion='absent',
                        facts=[dict(fact_id=f['fact_id'],status='missing',answer_spans=[],reason='No policy facts in refusal.')
                               for f in probe['inputs']['required_facts']])
                value=packet(grade)
                result=evaluator.probe_review(probe['inputs'],probe['payload'],probe['evidence'],
                    probe['safety_flags'],value,deepcopy(value),probe['candidate'])
                self.assertEqual(sorted(k for k in evaluator.KEYS if result[k]=='dispute'),
                                 sorted(probe['expected_disputes']))

    def test_frozen_coverage_only_reusable_for_one_side(self):
        case,_=fixture('answer-injection-award-pass')
        receipt=budget.reusable_coverage(case,'calibration')
        self.assertEqual((receipt['judge'],receipt['purpose']),('a','coverage'))
        self.assertFalse(receipt['acceptance_reused'])
        changed=deepcopy(case);changed['inputs']['answer']+=' Changed input.'
        self.assertIsNone(budget.reusable_coverage(changed,'calibration'))
        self.assertIsNone(budget.reusable_coverage(references.cases('calibration')[22],'calibration'))

    def test_replay_rejects_copying_receipts_or_anchored_requests(self):
        case,grade=fixture(); value=packet(grade); receipts={}
        for item in evaluator.request_plan(case['inputs']):
            key=item['judge']+'.'+item['purpose']
            schema=item['body']['response_format']['json_schema']['schema']
            content={k:deepcopy(value[k]) for k in schema['properties']}
            receipts[key]=dict(status='received',request=deepcopy(item['body']),response=dict(
                id='synthetic-'+key,model=item['body']['model'],choices=[dict(finish_reason='stop',
                message=dict(content=json.dumps(content),refusal=None))]))
        self.assertEqual(evaluator.replay_packets(case['inputs'],receipts),(value,value))
        for mutation in ('copy','anchor','unknown','truncate','missing'):
            bad=deepcopy(receipts)
            if mutation=='copy': bad['b.claims']=deepcopy(bad['a.claims'])
            elif mutation=='anchor': bad['b.claims']['request']['messages'][1]['content']=json.dumps(dict(candidate=grade))
            elif mutation=='unknown': bad['b.claims']['status']='unknown'
            elif mutation=='truncate': bad['b.claims']['response']['choices'][0]['finish_reason']='length'
            else: bad.pop('b.claims')
            with self.assertRaises(ValueError): evaluator.replay_packets(case['inputs'],bad)

    def test_complete_path_stays_blocked_even_with_all_valid_component_reuse(self):
        result=budget.assessment()
        self.assertEqual(result['status'],'budget_blocked')
        self.assertEqual(result['accounted_usd'],'10.90614776')
        self.assertEqual(result['remaining_usd'],'5.86432750')
        self.assertEqual(result['qualification_headroom_usd'],'1.36432750')
        self.assertEqual(len(result['reusable_components']),38)
        self.assertEqual([s['new_requests'] for s in result['stages']],[60,118,64])
        self.assertEqual(result['stage_acceptances_reused'],0)
        self.assertGreater(Decimal(result['qualification_proxy_usd']),Decimal(result['qualification_headroom_usd']))
        self.assertFalse(result['paid_execution_authorized'])
        self.assertEqual(result['final']['grader_requests'],240)
        self.assertEqual(result['final']['required_successes'],48)
        for item in result['reusable_components']:
            self.assertEqual(item['raw_sha256'],digest(budget.ROOT/item['raw_path']))


if __name__=='__main__':
    unittest.main()
