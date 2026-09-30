"""Filesystem fault injection proves recovery never retries provider requests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletion
from scripts import quality_completion_durable as durable
from scripts import quality_v15_local_recovery as recovery
from scripts import quality_eval_transport_v15 as transport


class LocalRecovery(unittest.TestCase):
    def response_fixture(self):
        raw = json.loads((recovery.ORIGINAL/'supported-answer-without-citation/claims.json').read_bytes())
        return raw, ChatCompletion.model_validate(raw['response'])

    def test_saved_response_is_reused_without_calling_provider(self):
        raw, _ = self.response_fixture()
        raw['status'] = 'received'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'claims.json'
            durable.write_json_atomic(path, raw)
            create = Mock(side_effect=AssertionError('Provider must not be called'))
            result = recovery.saved_or_call(transport, create, None, raw['request'], path)
            self.assertIn('claims', result)
            create.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'not reusable'):
                recovery.saved_or_call(transport, create, None, {}, path)

    def test_local_settlement_retry_calls_provider_once(self):
        raw, response = self.response_fixture()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            ledger = durable.Ledger.initialize(folder/'ledger.json')
            ledger.begin_stage('test', 1, transport.reserve(raw['request'])['reserved_usd'])
            create = Mock(return_value=response)
            original_replace = durable.os.replace
            failures = []
            def blocked_once(source, dest):
                if Path(dest) == ledger.path and create.called and not failures:
                    failures.append(True)
                    raise PermissionError('transient sharing violation')
                return original_replace(source, dest)
            with patch.object(durable.os, 'replace', side_effect=blocked_once), patch.object(durable.time, 'sleep'):
                ledger.call(create, raw['request'], folder/'response.json')
            self.assertEqual(create.call_count, 1)
            self.assertEqual(len(failures), 1)
            self.assertEqual(ledger.data['calls'][-1]['status'], 'completed')
            self.assertFalse(ledger.data['unknown_outcome'])

    def test_exhausted_local_retry_preserves_unknown_and_never_retries_provider(self):
        raw, response = self.response_fixture()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            ledger = durable.Ledger.initialize(folder/'ledger.json')
            ledger.begin_stage('test', 1, transport.reserve(raw['request'])['reserved_usd'])
            create = Mock(return_value=response)
            original_replace = durable.os.replace
            failures = []
            def blocked_five(source, dest):
                if Path(dest) == ledger.path and create.called and len(failures) < 5:
                    failures.append(True)
                    raise PermissionError('persistent sharing violation')
                return original_replace(source, dest)
            with patch.object(durable.os, 'replace', side_effect=blocked_five), patch.object(durable.time, 'sleep'):
                with self.assertRaises(PermissionError):
                    ledger.call(create, raw['request'], folder/'response.json')
            self.assertEqual(create.call_count, 1)
            self.assertEqual(len(failures), 5)
            self.assertTrue(ledger.data['unknown_outcome'])
            self.assertIsNotNone(json.loads((folder/'response.json').read_bytes())['response'])
            with self.assertRaises(durable.BudgetStop):
                durable.Ledger(ledger.path)


if __name__ == '__main__':
    unittest.main()
