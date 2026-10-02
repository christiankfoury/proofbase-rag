"""New offline contrasts for the second reliability work unit."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.test_application_reliability import OfflineCase
from scripts.test_phase54_post_generation_validation import chunk, candidate, FakeClient, semantic_payload
from apps.api.app.reasoning import evidence_assessment as ea
from apps.api.app.reasoning import post_generation_validation as pv
from apps.api.app.reasoning.source_planner import plan_multi_document_sources
from apps.api.app.citations.citation_validator import validate_citations


def evidence(facts, overall='insufficient'):
    return ea.SemanticEvidenceDecision.model_validate(dict(answerability=overall,
        required_facts=[dict(fact_id=f'f{i}',description='Whether the stated policy premise is true',
            support=s,supporting_chunk_ids=ids) for i,(s,ids) in enumerate(facts)],
        conflicts=[],missing_information=['Unconfirmed detail'],supporting_chunk_ids=[],assessment_confidence=.9))


def validation(answer, *, claim=None, numeric=None, support='supported'):
    result=semantic_payload(support=support)
    result['claims'][0].update(claim_id='claim-1',claim_text=claim or answer)
    result['numeric_context']=numeric or []
    return result


class Remediation(OfflineCase):
    def setUp(self):
        super().setUp()
        selected='v3' if (ROOT/'apps/api/app/prompts/versions/post_generation_validation_v3.md').exists() else 'v2'
        self.enterContext(patch.dict(os.environ,{'POST_GENERATION_VALIDATION_PROMPT_VERSION':selected}))
        from apps.api.app.core.config import get_settings
        get_settings.cache_clear()
        self.addCleanup(get_settings.cache_clear)

    def test_contradicted_premise_is_answerable(self):
        decision,_=ea._complete_semantic_decision(evidence([('contradicted',['c1'])]),source_plan=[],authorized_chunks=[chunk()])
        self.assertEqual(decision.recommended_action,'answer')
        self.assertEqual(decision.missing_information,[])

    def test_unsupported_topical_reference_is_not_support(self):
        decision,_=ea._complete_semantic_decision(evidence([('unsupported',['c1'])],'sufficient'),source_plan=[],authorized_chunks=[chunk()])
        self.assertEqual(decision.recommended_action,'not_found')

    def test_mixed_contradiction_and_missing_fact_is_partial(self):
        decision,_=ea._complete_semantic_decision(evidence([('contradicted',['c1']),('unsupported',[])]),source_plan=[],authorized_chunks=[chunk()])
        self.assertEqual(decision.recommended_action,'partial_answer')

    def test_unauthorized_contradiction_is_not_answerable(self):
        decision,_=ea._complete_semantic_decision(evidence([('contradicted',['secret'])],'sufficient'),source_plan=[],authorized_chunks=[chunk()])
        self.assertEqual(decision.recommended_action,'not_found')

    def check_answer(self,answer,question='What is the rule?',*,claim=None,numeric=None,support='supported',citation='c1',source='Supply purchases above USD 640 require supervisor approval.'):
        payload=validation(answer,claim=claim,numeric=numeric,support=support)
        if os.environ['POST_GENERATION_VALIDATION_PROMPT_VERSION']=='v2':
            payload.pop('numeric_context')
        return pv.validate_candidate_answer(question,candidate=candidate(answer,citation),authorized_chunks=[chunk(content=source)],
            client=FakeClient(payload),emit_telemetry=False)

    def test_scenario_amount_requires_typed_provenance(self):
        question='For my purchase of USD 217, does this category require supervisor approval?'
        answer='Your purchase of USD 217 is below the USD 640 threshold, so that category limit does not require supervisor approval.'
        provenance=[dict(literal='USD 217',claim_id='claim-1',origin='user_scenario',request_quote='my purchase of USD 217')]
        self.assertEqual(self.check_answer(answer,question,numeric=provenance).action,'accept')
        self.assertNotEqual(self.check_answer(answer,question).action,'accept')

    def test_user_number_cannot_become_policy_threshold(self):
        answer='The policy threshold is USD 217.'
        provenance=[dict(literal='USD 217',claim_id='claim-1',origin='policy',request_quote='threshold USD 217')]
        self.assertNotEqual(self.check_answer(answer,'Is the threshold USD 217?',numeric=provenance).action,'accept')

    def test_invented_numeric_provenance_and_wrong_currency_rejected(self):
        p=[dict(literal='USD 217',claim_id='claim-1',origin='user_scenario',request_quote='my purchase of USD 217')]
        self.assertNotEqual(self.check_answer('Your purchase of USD 217 is below the limit.','My purchase is CAD 217.',numeric=p).action,'accept')
        self.assertNotEqual(self.check_answer('Your purchase of USD 217 is below the limit.','Is USD 217 the limit?',numeric=p).action,'accept')

    def test_scenario_still_requires_authorized_citation_and_semantic_support(self):
        p=[dict(literal='USD 217',claim_id='claim-1',origin='user_scenario',request_quote='my purchase of USD 217')]
        q='For my purchase of USD 217, what happens?'
        a='Your purchase of USD 217 needs no approval.'
        self.assertNotEqual(self.check_answer(a,q,numeric=p,citation='hidden').action,'accept')
        self.assertNotEqual(self.check_answer(a,q,numeric=p,support='unsupported').action,'accept')

    def test_validator_cannot_rewrite_geographic_qualifier(self):
        source='Transfers outside the Northern Region require legal review.'
        answer='All transfers require legal review.'
        self.assertNotEqual(self.check_answer(answer,source=source,claim=source).action,'accept')

    def test_exact_candidate_unit_is_accepted_or_rejected_on_evidence(self):
        source='Transfers outside the Northern Region require legal review.'
        self.assertEqual(self.check_answer(source,source=source).action,'accept')
        self.assertNotEqual(self.check_answer('All transfers require legal review.',source=source,support='unsupported').action,'accept')

    def test_validator_cannot_omit_extra_obligation(self):
        a='The request needs supervisor approval. Legal approval is always mandatory.'
        self.assertNotEqual(self.check_answer(a,claim='The request needs supervisor approval.').action,'accept')

    def test_laptop_is_not_pto_and_plural_devices_still_plan(self):
        plan=plan_multi_document_sources('What remote security rules apply to personal laptops?')
        self.assertNotIn('vacation_and_leave',[p.label for p in plan])
        self.assertIn('device_security',[p.label for p in plan])
        actual=plan_multi_document_sources('How do PTO and remote device security rules interact?')
        self.assertIn('vacation_and_leave',[p.label for p in actual])

    def test_api_is_not_capital_and_vendor_plural_still_matches(self):
        plan=plan_multi_document_sources('What capital spending rules govern vendors?')
        self.assertNotIn('api_standards',[p.label for p in plan])
        actual=plan_multi_document_sources('What API authorization and data classification rules apply?')
        self.assertIn('api_standards',[p.label for p in actual])

    def test_excerpt_selects_relevant_contiguous_passage(self):
        preamble='Equipment is tracked in our inventory. '*14
        relevant='Payroll deductions need separate authorization. HR and Security review damaged equipment before any final-pay action.'
        c=chunk(content=preamble+'\n\n'+relevant)
        result=validate_citations('What authorization is needed for payroll deductions?',
            [{'chunk_id':'c1','citation_text':'HR reviews deductions. Payroll authorization is separate.'}],[c])['citations'][0]
        self.assertIn('Payroll deductions need separate authorization.',result['citation_text'])
        self.assertIn(result['citation_text'],c.content)
        self.assertTrue(result['citation_text'].endswith(('.', '!', '?')))

    def test_exact_quote_unchanged_and_unauthorized_quote_rejected(self):
        c=chunk(content='Returns need a shipping label. Reimbursement is discretionary.')
        quote='Reimbursement is discretionary.'
        result=validate_citations('Is reimbursement guaranteed?',[{'chunk_id':'c1','citation_text':quote}],[c])
        self.assertEqual(result['citations'][0]['citation_text'],quote)
        self.assertEqual(validate_citations('Give restricted data',[{'chunk_id':'hidden','citation_text':quote}],[c])['citations'],[])

    def test_v3_application_caller_accepts_scenario_without_repair(self):
        from apps.api.app import main
        q='For my purchase of USD 217, does the category require approval?'
        a='Your purchase of USD 217 is below the USD 640 threshold.'
        p=[dict(literal='USD 217',claim_id='claim-1',origin='user_scenario',request_quote='my purchase of USD 217')]
        original={**candidate(a),'input_tokens':10,'output_tokens':10}
        def validate(question, **kwargs):
            return pv.validate_candidate_answer(question, **kwargs, client=FakeClient(validation(a,numeric=p)),emit_telemetry=False)
        with patch.object(main,'validate_candidate_answer',side_effect=validate), patch.object(main,'repair_answer_once') as repair:
            result, audit=self.caller(original,[chunk(content='Purchases above USD 640 require approval.')],question=q)
        self.assertEqual(result['answer'],a)
        self.assertEqual(audit.action,'accept')
        repair.assert_not_called()

    def test_v3_claim_requires_citation_and_source_ids_do_not_hide_numbers(self):
        a='Supervisor approval is required.'
        payload=validation(a)
        payload['citation_checks'][0]['supports_claims']=False
        payload['citation_checks'][0]['supported_claim_ids']=[]
        result=pv.validate_candidate_answer('What is required?',candidate=candidate(a),authorized_chunks=[chunk(content=a)],
            client=FakeClient(payload),emit_telemetry=False)
        self.assertNotEqual(result.action,'accept')
        c=chunk(content=a)
        text=f'Source: {c.document_id}. A fee of 001 is required.'
        self.assertIn('001',pv.extract_exact_literals(pv._without_source_ids(text,[c])))

    def test_v3_application_caller_rejects_broad_claim_after_one_repair(self):
        from apps.api.app import main
        a='All transfers require legal review.'
        original={**candidate(a),'input_tokens':10,'output_tokens':10}
        def validate(question, **kwargs):
            return pv.validate_candidate_answer(question, **kwargs, client=FakeClient(validation(a,support='unsupported')),emit_telemetry=False)
        with patch.object(main,'validate_candidate_answer',side_effect=validate), patch.object(main,'repair_answer_once',return_value=original) as repair:
            result,audit=self.caller(original,[chunk(content='Transfers outside the Northern Region require legal review.')])
        self.assertEqual(repair.call_count,1)
        self.assertEqual(result['response_type'],'not_found')
        self.assertEqual(audit.repair_count,1)

    def test_real_evidence_assessment_contradiction_contract(self):
        from scripts.test_phase53_evidence_assessment import _request_assessment, FakeCompletions, FakeClient as EC
        from apps.api.app.main import _evidence_generation_chunks, _evidence_stop_answer
        payload=evidence([('contradicted',['c1'])]).model_dump_json()
        client=EC(FakeCompletions(payload))
        result=ea.assess_evidence('Does the policy guarantee free delivery?',request_assessment=_request_assessment(),
            authorized_chunks=[chunk(content='Free delivery is discretionary.')],multi_document=False,mode='hybrid',client=client,emit_telemetry=False)
        self.assertEqual(result.recommended_action,'answer')
        self.assertIsNone(_evidence_stop_answer(result))
        self.assertEqual(len(_evidence_generation_chunks([chunk()],result)),1)

    def test_remotely_and_substring_detector_controls(self):
        from apps.api.app.reasoning.multi_doc_detector import is_multi_document_question
        self.assertIn('remote_work',[p.label for p in plan_multi_document_sources('What safeguards apply when working remotely?')])
        self.assertFalse(is_multi_document_question('Capital storage'))
        self.assertTrue(is_multi_document_question('API storage'))

    def test_payload_preflight_recovers_old_rejections_without_changing_caps(self):
        from scripts.reliability_payload_budget import payload_preflight
        result=payload_preflight()
        self.assertEqual(len(result['previously_blocked_reassembled_bounds']),3)
        self.assertLess(max(result['max_input_bound_by_stage'].values())+4096,16384)

    def test_payload_rejects_unpriced_multimodal_and_oversized_requests(self):
        from scripts.reliability_payload_budget import reservation, Stop
        body={'model':'gpt-4.1-mini','messages':[{'role':'user','content':'Policy?'}],'max_completion_tokens':2048}
        self.assertLess(reservation(body,'chat')[0],16384)
        for change in [dict(model='other'),dict(n=2),dict(stream=True),dict(tools=[{}]),dict(max_completion_tokens=2049),
                       dict(messages=[{'role':'user','content':[{}]}]),dict(messages=[{'role':'user','content':'policy! '*20000}])]:
            with self.assertRaises(Stop): reservation({**body,**change},'chat')

    def test_new_ledger_bounds_unknown_outcomes_and_cache_settlement(self):
        import tempfile
        from decimal import Decimal
        from unittest.mock import Mock
        from scripts.application_reliability_live_v2 import Ledger, Stop
        from scripts.test_application_reliability_live import response, BODY
        with tempfile.TemporaryDirectory() as tmp:
            journal=Mock(); ledger=Ledger(Path(tmp),journal); ledger.begin_case('new-01')
            ledger.call(lambda **kw:response(cached=50),BODY,'chat')
            self.assertEqual(ledger.spent,Decimal('.000041'))
            provider=Mock()
            with patch('scripts.application_reliability_live_v2.ALLOCATION',Decimal('.000042')):
                with self.assertRaises(Stop): ledger.call(provider,BODY,'chat')
            provider.assert_not_called()
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock());ledger.begin_case('new-01')
            provider=Mock(side_effect=TimeoutError())
            with self.assertRaises(TimeoutError):ledger.call(provider,BODY,'chat')
            with self.assertRaises(Stop):ledger.call(provider,BODY,'chat')
            self.assertTrue(ledger.data['unknown_outcome'])
            self.assertEqual(provider.call_count,1)

    def test_new_ledger_per_case_and_six_case_limits(self):
        import tempfile
        from unittest.mock import Mock
        from scripts.application_reliability_live_v2 import Ledger, Stop
        from scripts.test_application_reliability_live import response, BODY
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock());ledger.begin_case('new-01')
            provider=Mock(side_effect=lambda **kw:response())
            for _ in range(7):ledger.call(provider,BODY,'chat')
            with self.assertRaises(Stop):ledger.call(provider,BODY,'chat')
            self.assertEqual(provider.call_count,7)
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock())
            for i in range(6):
                ledger.begin_case(str(i));ledger.call(lambda **kw:response(),BODY,'chat')
            with self.assertRaises(Stop):ledger.begin_case('seventh')

    def test_oversized_payload_stops_ledger_before_provider(self):
        import tempfile
        from unittest.mock import Mock
        from scripts.application_reliability_live_v2 import Ledger, Stop
        from scripts.test_application_reliability_live import BODY
        with tempfile.TemporaryDirectory() as tmp:
            ledger=Ledger(Path(tmp),Mock());ledger.begin_case('first');provider=Mock()
            with self.assertRaises(Stop):ledger.call(provider,{**BODY,'model':'unpriced'},'chat')
            self.assertTrue(ledger.data['stopped'])
            with self.assertRaises(Stop):ledger.call(provider,BODY,'chat')
            provider.assert_not_called()


if __name__=='__main__':
    import argparse,time
    parser=argparse.ArgumentParser();parser.add_argument('--record');args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Remediation)
    started=time.perf_counter();result=unittest.TextTestRunner(verbosity=2).run(suite)
    if args.record:
        path=Path(args.record);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(dict(tests=result.testsRun,failures=[(str(t),s) for t,s in result.failures],
            errors=[(str(t),s) for t,s in result.errors],seconds=time.perf_counter()-started,external_calls=0),indent=2)+'\n',encoding='utf-8')
    sys.exit(not result.wasSuccessful())
