"""Cost/custody failures must stop before another provider submission."""
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from scripts import policy_fact_candidate_diagnostic as diag
from scripts.test_reliability_remediation_v3 import captured


class DiagnosticBounds(unittest.TestCase):
    def test_only_dynamic_routing_context_can_vary_in_assessment_payload(self):
        body = dict(messages=[dict(content='fixed prompt'),dict(content=json.dumps(dict(
            current_request='original',authorized_retrieved_chunks=['source'],
            request_assessment_for_routing_context_only={'topic':'old'})))])
        changed = json.loads(json.dumps(body)); data = json.loads(changed['messages'][1]['content'])
        data['request_assessment_for_routing_context_only']['topic']='new'
        changed['messages'][1]['content']=json.dumps(data)
        self.assertTrue(diag.same_assessment_payload(changed, body, 'evidence'))
        data['authorized_retrieved_chunks']=['different']
        changed['messages'][1]['content']=json.dumps(data)
        self.assertFalse(diag.same_assessment_payload(changed, body, 'evidence'))

    def body(self):
        raw = json.loads((diag.ROOT/'data/evaluation/application-reliability-live-v2/run/raw/call-003.json').read_bytes())
        return raw['request']

    def ledger(self, folder, journal=None):
        return diag.Ledger(folder, journal or Mock(), dict(prepared_stages=[]))

    def test_duplicate_stage_and_case_cannot_charge_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = self.ledger(folder); ledger.begin('case')
            provider = Mock(return_value=captured(3))
            ledger.call(provider, self.body())
            with self.assertRaises(ValueError): ledger.call(provider, self.body())
            self.assertEqual(provider.call_count, 1)
            with self.assertRaises(ValueError): ledger.begin('case')

    def test_unknown_outcome_reserves_and_blocks_later_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            journal = Mock(); ledger = self.ledger(folder, journal); ledger.begin('case')
            provider = Mock(side_effect=TimeoutError('test'))
            with self.assertRaises(TimeoutError): ledger.call(provider, self.body())
            with self.assertRaises(ValueError): ledger.call(provider, self.body())
            self.assertEqual(provider.call_count, 1)
            self.assertTrue(journal.finish.call_args.kwargs['uncertain'])
            self.assertGreater(Decimal(ledger.data['calls'][0]['charged_usd']), 0)

    def test_unpriced_payload_or_changed_assessment_never_submitted(self):
        for change in [dict(model='unpriced-model'), dict(stream=True), dict(tools=[{}])]:
            with tempfile.TemporaryDirectory() as folder:
                ledger = self.ledger(folder); ledger.begin('case'); provider = Mock()
                with self.assertRaises(ValueError): ledger.call(provider, dict(self.body(), **change))
                provider.assert_not_called(); ledger.journal.reserve.assert_not_called()
        with tempfile.TemporaryDirectory() as folder:
            ledger = self.ledger(folder); ledger.begin('case'); provider = Mock()
            body = self.body(); body['response_format'] = dict(json_schema=dict(name='evidence_assessment_v6'))
            with self.assertRaises(ValueError): ledger.call(provider, body)
            provider.assert_not_called(); ledger.journal.reserve.assert_not_called()

    def test_absolute_call_and_dollar_bounds_prevent_submission(self):
        for rows in [[dict(case_id='prior',stage='generation',charged_usd='0')]*24,
                     [dict(case_id='prior',stage='generation',charged_usd='.50')]]:
            with tempfile.TemporaryDirectory() as folder:
                ledger = self.ledger(folder); ledger.begin('case'); ledger.data['calls'] = rows
                provider = Mock()
                with self.assertRaises(ValueError): ledger.call(provider, self.body())
                provider.assert_not_called(); ledger.journal.reserve.assert_not_called()


if __name__ == '__main__': unittest.main()
