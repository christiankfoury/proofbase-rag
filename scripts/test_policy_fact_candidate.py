"""Offline plumbing judgments are synthetic, never semantic-accuracy evidence."""
import copy
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.test_application_reliability import OfflineCase
from scripts.test_reliability_remediation_v3 import fake, Client, captured
from scripts.test_phase53_evidence_assessment import _request_assessment
from scripts.policy_fact_candidate_support import invoke, authorized_sources
from apps.api.app.reasoning import evidence_assessment as ea, post_generation_validation as pv
from apps.api.app.core.config import get_settings

FOLDER = ROOT / 'data/evaluation/policy-fact-candidate'


def stage(body):
    name = body.get('response_format', {}).get('json_schema', {}).get('name', '')
    if name.startswith('request_assessment'): return 'request'
    if name.startswith('evidence_assessment'): return 'evidence'
    if name.startswith('post_generation_validation'): return 'validation'
    return 'generation'


def mock_response(body, case, suite):
    which = stage(body)
    if which == 'request': return captured(0)
    if which == 'evidence':
        return fake(dict(request_coverage='complete', policy_facts=case['expected_facts'], assessment_confidence=.95))
    if which == 'generation':
        facts = [f for f in case['expected_facts'] if f['availability'] == 'available']
        sources = {s.chunk_id: s for s in authorized_sources(suite, case)}
        citations = []
        for f in facts:
            w = f['witnesses'][0]; s = sources[w['chunk_id']]
            citations.append(dict(document_id=s.document_id, document_title=s.document_title,
                section_heading=s.section_heading, chunk_id=s.chunk_id, citation_text=w['quote']))
        payload = dict(response_type='answer', answer=' '.join(f['policy_statement'] for f in facts),
            citations=citations, supported_claims=[f['policy_statement'] for f in facts],
            unsupported_claims=[], validation_notes='Offline fixture')
        response = fake(payload)
        if body.get('stream'):
            return iter([SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(
                content=response.choices[0].message.content))], usage=response.usage)])
        return response
    inputs = json.loads(body['messages'][1]['content'])
    cid = inputs['authorized_evidence'][0]['chunk_id']
    units = inputs['candidate_units']
    return fake(dict(claims=[dict(**u, claim_type='exact', support_status='supported', evidence_chunk_ids=[cid]) for u in units],
        citation_checks=[dict(citation_chunk_id=cid, supports_claims=True, supported_claim_ids=[u['claim_id'] for u in units])],
        source_instruction_followed=False, source_instruction_evidence_chunk_ids=[], unresolved_conflict=False,
        numeric_context=[], scope_checks=[dict(claim_id=u['claim_id'], preserves_scope=True, explanation='Offline judgment') for u in units]))


class PolicyFactTests(OfflineCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.dict(os.environ, {'EVIDENCE_ASSESSMENT_PROMPT_VERSION':'v6',
            'POST_GENERATION_VALIDATION_PROMPT_VERSION':'v4', 'REQUEST_ASSESSMENT_MODE':'semantic_all_remaining'}))
        get_settings.cache_clear(); self.addCleanup(get_settings.cache_clear)
        self.suite = json.loads((FOLDER/'cases.json').read_bytes())

    def assess(self, case, payload=None, original=None):
        client = Client(fake(payload or dict(request_coverage='complete', policy_facts=case['expected_facts'], assessment_confidence=.95)))
        result = ea.assess_evidence(case['question'], original_question=original or case['question'],
            request_assessment=_request_assessment(), authorized_chunks=authorized_sources(self.suite, case),
            multi_document=False, client=client, emit_telemetry=False)
        return result, client.requests

    def test_captured_baseline_reproduces_missing_and_contradiction_promotion(self):
        case = self.suite['cases'][0]
        with patch.dict(os.environ, {'EVIDENCE_ASSESSMENT_PROMPT_VERSION':'v4'}):
            get_settings.cache_clear()
            result = ea.assess_evidence(case['question'], request_assessment=_request_assessment(),
                authorized_chunks=authorized_sources(self.suite, case), multi_document=False,
                client=Client(captured(7)), emit_telemetry=False)
            self.assertEqual(result.recommended_action, 'not_found')
            cid = case['source_ids'][0]
            old = ea.SemanticEvidenceDecision(answerability='sufficient', required_facts=[dict(
                fact_id='false', description='Office supplies limit is USD 217', support='contradicted', supporting_chunk_ids=[cid])],
                conflicts=[], missing_information=[], supporting_chunk_ids=[cid], assessment_confidence=.9)
            normalized, _ = ea._complete_semantic_decision(old, source_plan=[], authorized_chunks=authorized_sources(self.suite, case))
            self.assertEqual(normalized.required_facts[0].support, 'supported')
        get_settings.cache_clear()
        result, _ = self.assess(case)
        self.assertEqual(result.recommended_action, 'answer')
        self.assertTrue(all(f.premise_relation == 'contradicted' for f in result.policy_facts))
        self.assertNotIn('217', result.required_facts[0].description)

    def test_sync_and_stream_routing_with_all_five_boundaries(self):
        from openai.resources.chat.completions import Completions
        for streaming in [False, True]:
            for case in self.suite['cases']:
                calls = []
                def respond(resource, **body):
                    calls.append(stage(body)); return mock_response(body, case, self.suite)
                with self.subTest(case=case['id'], streaming=streaming), patch.object(Completions, 'create', respond):
                    row = invoke(self.suite, case, streaming=streaming)
                    self.assertEqual(row['final_response']['response_type'], case['expected_action'])
                    self.assertEqual(calls.count('evidence'), 1)
                    if case['expected_action'] != 'answer':
                        self.assertNotIn('generation', calls)
                        self.assertNotIn('validation', calls)
                    else:
                        self.assertEqual(calls.count('generation'), 1)
                        self.assertEqual(calls.count('validation'), 1)
                    if case['kind'] == 'inaccessible':
                        self.assertNotIn('policy-private', [s['chunk_id'] for s in row['authorized_evidence']])
                        self.assertNotIn('720', json.dumps(row))

    def test_quotes_and_ids_cannot_promote_non_entailing_or_missing_facts(self):
        case = copy.deepcopy(self.suite['cases'][3])
        result, _ = self.assess(case)
        self.assertEqual(result.recommended_action, 'not_found')
        case['expected_facts'][0].update(availability='available', policy_statement='The handling fee is EUR 35.')
        result, _ = self.assess(case)  # Exact authorized quote still has not_established judgment.
        self.assertEqual(result.status, 'failed_safe')

    def test_invalid_provenance_coverage_conflict_and_false_certainty_fail_closed(self):
        original = self.suite['cases'][1]
        changes = [dict(witnesses=[dict(chunk_id='private',quote='hidden')]),
            dict(witnesses=[dict(chunk_id='policy-book-a',quote='invented rule')]),
            dict(premise_quote='only in memory'), dict(witnesses=[]),
            dict(availability='missing'), dict(availability='conflicting'), dict(policy_statement=None)]
        for change in changes:
            case = copy.deepcopy(original); case['expected_facts'][0].update(change)
            result, _ = self.assess(case); self.assertEqual(result.status, 'failed_safe', change)
        for coverage in ['incomplete','uncertain']:
            result, _ = self.assess(original, dict(request_coverage=coverage, policy_facts=original['expected_facts'], assessment_confidence=1))
            self.assertEqual(result.status, 'failed_safe')

    def test_complete_original_and_contradiction_preserved_without_scenario_proposal(self):
        case = self.suite['cases'][1]; original = ('context ' * 650) + case['question']
        result, calls = self.assess(case, original=original)
        self.assertEqual(json.loads(calls[0]['messages'][1]['content'])['current_request'], original)
        self.assertEqual(result.policy_facts[0].premise_relation, 'contradicted')
        self.assertIsNone(result.scenario)
        self.assertNotIn('policy_facts', result.model_dump())  # Default public schema unchanged.

    def test_partial_and_conflicting_available_facts_do_not_override_missing_or_conflicts(self):
        case = copy.deepcopy(self.suite['cases'][1])
        case['question'] += ' What is the handling fee?'
        case['expected_facts'].append(copy.deepcopy(self.suite['cases'][3]['expected_facts'][0]))
        case['expected_facts'][-1].update(premise_quote=None, premise_relation='not_asserted')
        result, _ = self.assess(case); self.assertEqual(result.recommended_action, 'partial_answer')
        case['source_ids'].append('policy-book-b')
        case['expected_facts'][-1] = copy.deepcopy(self.suite['cases'][4]['expected_facts'][0])
        case['expected_facts'][-1]['fact_id'] = 'dispute'
        result, _ = self.assess(case); self.assertEqual(result.recommended_action, 'clarify')
        self.assertEqual(result.supporting_chunk_ids, [])


if __name__ == '__main__': unittest.main()
