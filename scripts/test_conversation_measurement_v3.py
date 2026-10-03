"""Offline final-run reservation, embedding, isolation and call-bound checks."""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from openai.types import CreateEmbeddingResponse
from scripts import conversation_measurement_v3 as m


class MeasurementTests(unittest.TestCase):
    def setup_ledger(self,spent='1.50'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        self.enterContext(patch.object(m.grading,'ROOT',root));self.enterContext(patch.object(m.grading,'FOLDER',root))
        plan=dict(prefix=dict(spent_usd=spent,ledger_sha256={}),maximum_calls=2100,case_ids=['fresh-001'])
        ledger=m.MeasurementLedger(root/'final/run',plan);ledger.begin_case('fresh-001')
        self.enterContext(patch.object(m.grading,'prefix',side_effect=lambda:dict(spent_usd=str(ledger.accounted),ledger_sha256={'final/run/api-ledger.json':m.digest(ledger.folder/'api-ledger.json')})))
        ledger.mode='application';return ledger

    def test_embedding_is_reserved_before_submission_and_fully_settled(self):
        ledger=self.setup_ledger();body=dict(model='text-embedding-3-small',input=['Synthetic uploaded knowledge'])
        def create(**kw):
            self.assertEqual(kw,body)
            self.assertEqual(m.read(ledger.folder/'api-ledger.json')['calls'][0]['status'],'reserved')
            return CreateEmbeddingResponse.model_validate(dict(model='text-embedding-3-small',object='list',data=[],usage=dict(prompt_tokens=100,total_tokens=100)))
        ledger.call(create,body,ledger.folder/'raw/application/fresh-001/embedding.json')
        self.assertEqual(ledger.accounted,Decimal('1.500002'))
        self.assertEqual(ledger.case_calls['fresh-001']['application'],1)

    def test_model_output_input_and_per_case_limits_fail_before_network(self):
        ledger=self.setup_ledger()
        body=dict(model='gpt-5.4-2026-03-05',reasoning_effort='low',max_completion_tokens=1600,messages=[])
        _,limits=ledger.prepare_request(body);self.assertEqual(limits['output_cap'],1600)
        for extra in [dict(max_completion_tokens=2049),dict(model='unpriced'),dict(reasoning_effort='medium'),dict(messages=[dict(role='user',content='x'*140000)])]:
            with self.assertRaises(m.grading.transport.BudgetStop):ledger.prepare_request(dict(body,**extra))
        ledger.case_calls['fresh-001']['application']=32
        provider=Mock()
        with self.assertRaises(m.grading.transport.BudgetStop):ledger.call(provider,body,ledger.folder/'over.json')
        provider.assert_not_called();self.assertTrue(ledger.data['budget_exhausted'])

    def test_ceiling_blocks_application_call_with_prior_grader_spend(self):
        ledger=self.setup_ledger('12.49999');provider=Mock()
        with self.assertRaises(m.grading.transport.BudgetStop):
            ledger.call(provider,dict(model='gpt-5.4-2026-03-05',reasoning_effort='low',max_completion_tokens=1600,messages=[]),ledger.folder/'over.json')
        provider.assert_not_called();self.assertEqual(ledger.accounted,Decimal('12.49999'))

    def test_no_unsealed_or_repeated_case_and_unchanged_grader_caps(self):
        ledger=self.setup_ledger()
        for cid in ('fresh-001','unsealed'):
            with self.assertRaises(ValueError):ledger.begin_case(cid)
        ledger.mode='grading'
        body=m.grading.transport.initial_requests(m.grading.cases('calibration')[0]['inputs'])[0][1]
        self.assertEqual(ledger.prepare_request(body)[1]['output_cap'],8192)
        ledger.case_calls['fresh-001']['grading']=3
        with self.assertRaises(m.grading.transport.BudgetStop):ledger.prepare_request(body)


    def test_operator_stop_prevents_next_submission_without_unknown_charge(self):
        ledger=self.setup_ledger();provider=Mock()
        m.write(ledger.folder.parent/'stop-request.json',dict(reason='Source review finding'))
        with self.assertRaises(m.grading.transport.BudgetStop):
            ledger.call(provider,dict(model='gpt-5.4-2026-03-05',reasoning_effort='low',max_completion_tokens=1600,messages=[]),ledger.folder/'next.json')
        provider.assert_not_called();self.assertTrue(ledger.data['stopped'])
        self.assertFalse(ledger.data['unknown_outcome']);self.assertEqual(ledger.accounted,Decimal('1.50'))
        self.assertEqual(ledger.data['calls'],[])

    def test_partial_case_receipts_replay_without_case_credit(self):
        import shutil
        from scripts import conversation_grader as old
        source=m.grading.ROOT/'data/evaluation/conversation-continuation/final-v1'
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        folder=Path(tmp.name)/'partial';shutil.copytree(source,folder)
        manifest=m.read(folder/'run/manifest.json');manifest['rows'].pop('fresh-001')
        m.write(folder/'run/manifest.json',manifest)
        with patch.object(m,'FOLDER',folder),patch.object(m,'custody',return_value=(m.read(source/'freeze.json'),m.read(source/'holdout.json'),{})),patch.object(m.grading,'versioned',side_effect=old.versioned),patch('builtins.print'):
            m.report()
        result=m.read(folder/'report.json')
        self.assertEqual(result['completed_cases'],1)
        self.assertEqual(result['unresolved_or_unexecuted'],59)
        self.assertEqual(result['calls'],16)
        self.assertEqual(result['new_spend_usd'],'0.24155986')
        self.assertFalse(result['measurement_gate_passed']);self.assertFalse(result['activation_allowed'])


if __name__=='__main__':unittest.main()
