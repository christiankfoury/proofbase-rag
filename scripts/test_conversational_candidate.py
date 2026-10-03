"""Offline integration contracts, not semantic accuracy measurements."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.test_application_reliability import OfflineCase
from scripts.policy_fact_candidate_support import invoke, authorized_sources
from scripts.test_phase53_evidence_assessment import _request_assessment
from scripts.test_reliability_remediation_v3 import captured
from apps.api.app.generation import conversational_candidate as c
from apps.api.app.core.config import get_settings


def response(value, model=c.MINI, finish='stop'):
    return NS(model=model, usage=NS(prompt_tokens=100, completion_tokens=50,
        prompt_tokens_details=NS(cached_tokens=40)), choices=[NS(finish_reason=finish,
        message=NS(content=json.dumps(value), refusal=None))])


def accepted():
    return dict(decision='accept', reason='Supported in this offline fixture.',
        **{k:True for k in c.Check.model_fields if k not in {'decision','reason'}})


class CandidateTests(OfflineCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.dict(os.environ, CONVERSATIONAL_CANDIDATE_ENABLED='true'))
        get_settings.cache_clear(); self.addCleanup(get_settings.cache_clear)
        self.telemetry=self.enterContext(patch.object(c,'submit_auxiliary_telemetry'))
        self.suite=json.loads((ROOT/'data/evaluation/bounded-redesign/development.json').read_bytes())
        self.case=dict(self.suite['cases'][1], question=self.suite['cases'][1]['turns'][0])
        self.chunks=authorized_sources(self.suite,self.case)
        self.draft=dict(answer='The limit is EUR 460 per order.', response_type='answer',
            citations=[dict(chunk_id=self.chunks[0].chunk_id,citation_text=self.chunks[0].content)])

    def run_candidate(self, values, *, chunks=None, history=None):
        self.calls=[]; self.output={}
        def create(**body):
            self.calls.append(body)
            item=values[len(self.calls)-1]
            if isinstance(item,Exception): raise item
            return item
        client=NS(chat=NS(completions=NS(create=create)))
        return c.run(self.case['question'], 'retrieval question', self.chunks if chunks is None else chunks,
            history or [], request_assessment=_request_assessment(),effective_role='Employee',
            project_id=self.suite['project_id'],department_id=None,output=self.output,client=client)

    def test_correction_history_is_reference_and_payload_shared(self):
        history=[dict(role='user',content='Old assumption EUR 217'),dict(role='assistant',content='Unsupported old assertion')]
        self.run_candidate([response(self.draft),response(accepted())],history=history)
        a,b=[json.loads(x['messages'][1]['content']) for x in self.calls]
        b.pop('candidate'); self.assertEqual(a,b)
        self.assertEqual(a['original_question'],self.case['question'])
        self.assertEqual(a['conversation_reference_only'],history)
        self.assertEqual(len(self.calls),2)
        self.assertEqual(self.output['response_type'],'answer')
        self.assertEqual(self.output['final_confidence'],0)

    def test_citation_tampering_and_numeric_substring_cannot_be_quoted(self):
        for change in [dict(chunk_id='private'),dict(citation_text='EUR 46 per order')]:
            draft=json.loads(json.dumps(self.draft));draft['citations'][0].update(change)
            with self.assertRaises(RuntimeError):self.run_candidate([response(draft)])
            self.assertEqual(len(self.calls),1)

    def test_permission_and_project_boundaries_precede_calls(self):
        from dataclasses import replace
        for altered in [replace(self.chunks[0],access_roles=['HR Admin']),replace(self.chunks[0],project_id='other')]:
            with self.assertRaises(RuntimeError):self.run_candidate([],chunks=[altered])
            self.assertEqual(self.calls,[])

    def test_rejection_uncertainty_malformed_and_timeout_never_repair(self):
        checks=[response(dict(accepted(),decision='reject')),response(dict(accepted(),decision='uncertain')),
            response(dict(accepted(),numerical_application=False)),response({}),TimeoutError()]
        checks += [response(dict(accepted(), **{name:False})) for name in c.Check.model_fields
                   if name not in {'decision','reason','numerical_application'}]
        for check in checks:
            with self.assertRaises(RuntimeError):self.run_candidate([response(self.draft),check])
            self.assertEqual(len(self.calls),2);self.assertNotIn('answer',self.output)
            self.assertIsNotNone(self.output['candidate_stages']['producer']['estimated_cost_usd'])
            self.assertEqual(self.telemetry.call_args.kwargs['status'],'failed')
        for draft in [response({}),response(self.draft,finish='length')]:
            with self.assertRaises(RuntimeError):self.run_candidate([draft])
            self.assertEqual(len(self.calls),1)

    def test_absence_of_sources_is_checked_and_no_canned_answer(self):
        draft=dict(answer='The accessible sources do not provide this fee.',response_type='not_found',citations=[])
        self.run_candidate([response(draft),response(accepted())],chunks=[])
        self.assertEqual(len(self.calls),2);self.assertEqual(self.output['response_type'],'not_found')

    def test_cache_receipts_and_unknown_usage(self):
        self.run_candidate([response(self.draft),response(accepted())])
        self.assertAlmostEqual(self.output['estimated_cost_usd'],.000108)
        x=response(self.draft);x.usage=None
        self.assertIsNone(c.usage_receipt(x,c.MINI,0)['estimated_cost_usd'])
        self.assertAlmostEqual(self.telemetry.call_args.kwargs['estimated_cost_usd'],.000108)

    def test_pinned_profiles_and_bounded_history(self):
        body=c.request_body('producer',{},c.CHALLENGER)
        self.assertEqual(body['reasoning_effort'],'low')
        self.assertNotIn('temperature',body)
        history=[dict(role='user',content='x'*4000) for _ in range(10)]
        self.run_candidate([response(self.draft),response(accepted())],history=history)
        sent=json.loads(self.calls[0]['messages'][1]['content'])['conversation_reference_only']
        self.assertEqual(len(sent),6);self.assertTrue(all(len(t['content'])==2000 for t in sent))

    def test_http_and_sse_share_path_and_buffer_rejection(self):
        from openai.resources.chat.completions import Completions
        from fastapi.testclient import TestClient
        original_post=TestClient.post
        for accept in [True,False]:
            finals=[]
            for streaming in [False,True]:
                calls=[]
                responses=[]
                def post(client,*args,**kwargs):
                    result=original_post(client,*args,**kwargs);responses.append(result);return result
                def create(resource,**body):
                    name=body['response_format']['json_schema']['name'];calls.append(name)
                    if name.startswith('request_assessment'):return captured(0)
                    return response(self.draft if name.endswith('producer') else dict(accepted(),decision='accept' if accept else 'reject'))
                with patch.object(Completions,'create',create),patch.object(TestClient,'post',post):
                    if accept:finals.append(invoke(self.suite,self.case,streaming=streaming)['final_response'])
                    else:
                        with self.assertRaises(ValueError):invoke(self.suite,self.case,streaming=streaming)
                        self.assertNotIn(self.draft['answer'],responses[0].text)
                        self.assertNotIn('event: answer_delta',responses[0].text)
                self.assertEqual(calls,['request_assessment_v1','conversational_producer','conversational_checker'])
            if accept:
                for key in ['answer','citations','response_type','evidence_assessment']:
                    self.assertEqual(finals[0][key],finals[1][key])
                self.assertIsNone(finals[0]['evidence_assessment'])


if __name__=='__main__':unittest.main()
