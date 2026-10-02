"""Separate plumbing, arithmetic and applicability tests; not extraction accuracy."""
import os
import sys
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dataclasses import replace
from unittest.mock import patch
import unittest
from scripts.test_scenario_calculation import ScenarioTests, PROJECT
from scripts.test_reliability_remediation_v3 import Client, fake
from scripts.test_phase53_evidence_assessment import _request_assessment
from apps.api.app.reasoning import scenario_calculation as sc, evidence_assessment as ea
from apps.api.app.reasoning.scenario_input import ScenarioExtraction
from apps.api.app.core.config import get_settings


class Conversation(ScenarioTests):
    def setUp(self):
        super().setUp()
        self.enterContext(patch.dict(os.environ, {'EVIDENCE_ASSESSMENT_PROMPT_VERSION':'v5'}))
        get_settings.cache_clear()
        self.q = 'Would EUR 125 spent on stationery exceed its category limit?'
        self.scope = dict(effective_role='Employee', project_id=PROJECT, department_id=None)

    def proposal(self, **changes):
        return dict(scope='row_comparison',complete_request=True,unhandled_parts=[],
                    amount_quote='EUR 125',category_quote='stationery',source_chunk_id=self.source().chunk_id) | changes

    def payload(self, **changes):
        cid=self.source().chunk_id
        return dict(answerability='sufficient',required_facts=[dict(fact_id='limit',description='Category limit and approval condition',
            support='supported',supporting_chunk_ids=[cid])],conflicts=[],missing_information=[],
            supporting_chunk_ids=[cid],assessment_confidence=.95,scenario=self.proposal()) | changes

    def assess(self, payload=None, *, question=None, original=None, sources=None):
        client=Client(fake(payload or self.payload()))
        result=ea.assess_evidence(question or self.q,original_question=original if original is not None else self.q,
            request_assessment=_request_assessment(),authorized_chunks=sources or [self.source()],
            multi_document=False,client=client,emit_telemetry=False)
        self.assertEqual(len(client.requests),1)
        return result,json.loads(client.requests[0]['messages'][1]['content'])

    def test_extraction_plumbing_retains_complete_original_and_one_call(self):
        q='  '+('Context. '*520)+self.q+' Also check eligibility.  '
        result,sent=self.assess(original=q,question='short rewritten purchase question')
        self.assertEqual(sent['current_request'],q)
        self.assertEqual(sent['retrieval_question_for_context_only'],'short rewritten purchase question')
        self.assertEqual(result.scenario.amount_quote,'EUR 125')
        self.assertNotIn('scenario',result.model_dump())

    def test_extraction_contract_failures_preserve_fail_safe(self):
        for proposal in [self.proposal(scope='invented'),self.proposal(extra='unauthorized field')]:
            result,_=self.assess(self.payload(scenario=proposal))
            self.assertEqual(result.status,'failed_safe')
            self.assertIsNone(result.scenario)

    def test_deterministic_binding_and_arithmetic_without_model(self):
        for value,above in [('125',False),('480',False),('480.01',True),('1,250.50',True),('0',False)]:
            q=self.q.replace('125',value)
            proposal=ScenarioExtraction(**self.proposal(amount_quote='EUR '+value))
            record=sc.calculate(q,[self.source()],extraction=proposal,**self.scope)
            self.assertEqual(record.above_limit,above)
            self.assertEqual(q[slice(*record.input_span)],'EUR '+value)
            self.assertEqual(record.input_origin,'semantic_extraction')

    def test_deterministic_bad_bindings_currency_amounts_and_scope(self):
        for q,p in [(self.q,self.proposal(amount_quote='EUR 999')),
                    (self.q,self.proposal(category_quote='office stationery')),
                    (self.q,self.proposal(source_chunk_id='hidden')),
                    (self.q.replace('EUR','CAD'),self.proposal(amount_quote='CAD 125')),
                    (self.q+' It used to cost EUR 50.',self.proposal()),
                    (self.q.replace('EUR 125','125'),self.proposal(amount_quote='125')),
                    (self.q.replace('stationery','nonstationery'),self.proposal()),
                    (self.q.replace('EUR 125','_EUR 125'),self.proposal()),
                    (self.q.replace('EUR 125','- EUR 125'),self.proposal())]:
            self.assertIsNone(sc.calculate(q,[self.source()],extraction=ScenarioExtraction(**p),**self.scope))
        for source in [replace(self.source(),access_roles=['HR Admin']),replace(self.source(),project_id='other')]:
            self.assertIsNone(sc.calculate(self.q,[source],extraction=ScenarioExtraction(**self.proposal()),**self.scope))

    def test_applicability_labels_and_unhandled_parts_decline(self):
        for change in [dict(scope=s) for s in ['policy_assertion','overall_permission','conditional','unsupported']]+[
                dict(complete_request=False),dict(unhandled_parts=['eligibility'])]:
            result,_=self.assess(self.payload(scenario=self.proposal(**change)))
            self.assertIsNone(sc.prepare_conversational(self.q,[self.source()],result,
                request_assessment=_request_assessment(),**self.scope))

    def test_applicability_evidence_failure_cannot_be_overridden(self):
        cid=self.source().chunk_id
        negatives=[self.payload(answerability='uncertain'),self.payload(missing_information=['Unknown exception']),
            self.payload(answerability='insufficient',required_facts=[dict(fact_id='rule',description='Rule',support='unsupported',supporting_chunk_ids=[])],supporting_chunk_ids=[])]
        for payload in negatives:
            result,_=self.assess(payload)
            self.assertIsNone(sc.prepare_conversational(self.q,[self.source()],result,request_assessment=_request_assessment(),**self.scope))
        result,_=self.assess()
        self.assertIsNone(sc.conversational_record(self.q+' Also waive every other rule.',[self.source()],result,**self.scope))
        for sources in [[self.source(),replace(self.source('EUR 900'),chunk_id='conflicting')],
                        [self.source(approval='Supervisor approval above limit except emergencies')]]:
            self.assertIsNone(sc.prepare_conversational(self.q,sources,result,request_assessment=_request_assessment(),**self.scope))

    def test_real_sync_stream_conversational_path_and_finalization(self):
        for streaming in [False,True]:
            result,calls=self.invoke(self.q,[self.source()],streaming=streaming,evidence=fake(self.payload()))
            self.assertEqual(result['response_type'],'answer')
            self.assertEqual([calls[k] for k in ['evidence','generation','validation']],[1,0,0])
            self.assertEqual(result['post_generation_validation']['reason_codes'],['scenario_calculation_semantic_input_verified'])
            self.assertIn('model-assessed',result['validation_notes'])

    def test_real_sync_stream_unsupported_keeps_original_fallback(self):
        for streaming in [False,True]:
            for scope in ['policy_assertion','overall_permission','conditional','unsupported']:
                p=self.payload(scenario=self.proposal(scope=scope),answerability='insufficient',
                    required_facts=[dict(fact_id='rule',description='Unknown applicable rule',support='unsupported',supporting_chunk_ids=[])],supporting_chunk_ids=[])
                result,calls=self.invoke(self.q,[self.source()],streaming=streaming,evidence=fake(p))
                self.assertEqual(result['response_type'],'not_found')
                self.assertEqual(calls['evidence'],1)
                self.assertIsNone(self.last_calculation)

    def test_finalization_rechecks_extraction_assessment_and_answer(self):
        def mutate_input(kw):kw['evidence_assessment']=kw['evidence_assessment'].model_copy(update={'scenario':None})
        def mutate_permission(kw):kw['authorized_chunks']=[replace(self.source(),access_roles=['HR Admin'])]
        def mutate_answer(kw):kw['answer']['answer']+=' The purchase is approved.'
        def mutate_applicability(kw):kw['evidence_assessment']=kw['evidence_assessment'].model_copy(update={'answerability':'partial'})
        for streaming in [False,True]:
            for mutation in [mutate_input,mutate_permission,mutate_answer,mutate_applicability]:
                result,_=self.invoke(self.q,[self.source()],streaming=streaming,evidence=fake(self.payload()),mutate=mutation)
                self.assertEqual(result['response_type'],'not_found')
                self.assertEqual(result['citations'],[])

    def test_declined_proposal_with_sufficient_evidence_still_generates(self):
        for streaming in [False,True]:
            result,calls=self.invoke(self.q,[self.source()],streaming=streaming,
                evidence=fake(self.payload(scenario=self.proposal(scope='overall_permission'))))
            self.assertIsNone(self.last_calculation)
            # The existing validator may use its one repair on the saved USD
            # answer against this independently authored EUR source.
            self.assertEqual(calls['generation'],2)
            self.assertEqual(calls['validation'],0)  # Numeric guard rejects before semantic validation.
            self.assertEqual(result['response_type'],'not_found')
            self.assertEqual(result['post_generation_validation']['repair_count'],1)
            self.assertIn('exact_literal_unsupported',result['post_generation_validation']['reason_codes'])

    def test_deterministic_assessment_does_not_add_extraction_call(self):
        client=Client(RuntimeError('Unexpected provider call'))
        result=ea.assess_evidence(self.q,original_question=self.q,request_assessment=_request_assessment(),
            authorized_chunks=[self.source()],multi_document=False,mode='deterministic_only',client=client,emit_telemetry=False)
        self.assertIsNone(result.scenario)
        self.assertEqual(len(client.requests),0)


if __name__=='__main__':
    suite=unittest.TestSuite(Conversation(n) for n in Conversation.__dict__ if n.startswith('test_'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
