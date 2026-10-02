"""Offline spending controls for the small diagnostic; no real client calls."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.application_reliability_live import Ledger, Stop, reservation, read


BODY = {'model': 'gpt-4.1-mini', 'messages': [{'role':'user','content':'Synthetic policy?'}],
        'max_completion_tokens': 2048}


def response(*, embedding=False, tokens=100, cached=0, model=None):
    data = {'model': model or ('text-embedding-3-small' if embedding else 'gpt-4.1-mini-2025-04-14'),
            'usage': {'prompt_tokens': tokens, 'completion_tokens': 0 if embedding else 10,
                      'prompt_tokens_details': {'cached_tokens': cached}}}
    return SimpleNamespace(model_dump=lambda **kw: data)


class Bounds(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.journal = Mock()
        self.ledger = Ledger(self.folder, self.journal)
        self.ledger.begin_case('diag-01')

    def test_cache_aware_settlement_and_raw_receipt(self):
        self.ledger.call(lambda **kw: response(cached=50), BODY, 'chat')
        self.assertEqual(self.ledger.spent, Decimal('.000041'))
        raw = read(self.folder/'raw/call-000.json')
        self.assertEqual(raw['request'], BODY)
        self.assertEqual(self.journal.reserve.call_count, 1)
        self.assertEqual(self.journal.finish.call_count, 1)

    def test_actual_single_item_embedding_payload(self):
        body = {'model':'text-embedding-3-small','input':['Synthetic query']}
        self.ledger.call(lambda **kw: response(embedding=True), body, 'embedding')
        self.assertEqual(self.ledger.spent, Decimal('.000002'))

    def test_per_case_chat_cap_blocks_before_provider(self):
        provider = Mock(side_effect=lambda **kw: response())
        for _ in range(7):
            self.ledger.call(provider, BODY, 'chat')
        with self.assertRaises(Stop):
            self.ledger.call(provider, BODY, 'chat')
        self.assertEqual(provider.call_count, 7)
        self.assertTrue(self.ledger.data['stopped'])

    def test_per_case_embedding_cap_blocks_fourth(self):
        provider = Mock(side_effect=lambda **kw: response(embedding=True))
        body = {'model':'text-embedding-3-small','input':['Synthetic query']}
        for _ in range(3):
            self.ledger.call(provider, body, 'embedding')
        with self.assertRaises(Stop):
            self.ledger.call(provider, body, 'embedding')
        self.assertEqual(provider.call_count, 3)

    def test_timeout_preserves_reservation_and_blocks_any_followup(self):
        provider = Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):
            self.ledger.call(provider, BODY, 'chat')
        self.assertEqual(self.ledger.spent, reservation(BODY,'chat')[2])
        self.assertTrue(self.ledger.data['unknown_outcome'])
        with self.assertRaises(Stop):
            self.ledger.call(provider, BODY, 'chat')
        self.assertEqual(provider.call_count, 1)
        self.assertTrue(self.journal.finish.call_args.kwargs['uncertain'])

    def test_invalid_usage_or_model_preserves_uncertain_response(self):
        with self.assertRaises(RuntimeError):
            self.ledger.call(lambda **kw: response(model='unpriced'), BODY, 'chat')
        self.assertEqual(read(self.folder/'raw/call-000.json')['response']['model'], 'unpriced')
        self.assertTrue(self.ledger.data['unknown_outcome'])

    def test_global_dollar_limit_and_shared_envelope_stop(self):
        provider = Mock()
        with patch('scripts.application_reliability_live.ALLOCATION', Decimal('.000001')):
            with self.assertRaises(Stop):
                self.ledger.call(provider, BODY, 'chat')
        provider.assert_not_called()
        self.journal.reserve.assert_not_called()

    def test_existing_ledger_and_case_cannot_resume(self):
        self.ledger.call(lambda **kw: response(), BODY, 'chat')
        with self.assertRaises(Stop):
            self.ledger.begin_case('diag-01')
        with self.assertRaises(Stop):
            Ledger(self.folder, self.journal)

    def test_request_rejection_does_not_truncate_or_call_provider(self):
        bad = [dict(BODY, model='gpt-5.4'), dict(BODY, stream=True),
               dict(BODY, tools=[{}]), dict(BODY, max_completion_tokens=2049),
               dict(BODY, messages=[{'role':'user','content':'x'*17000}]),
               dict(BODY, messages=[{'role':'user','content':[{}]}])]
        for body in bad:
            original = deepcopy(body)
            with self.subTest(body=str(body)[:90]), self.assertRaises(Stop):
                reservation(body, 'chat')
            self.assertEqual(body, original)
        with self.assertRaises(Stop):
            reservation({'model':'text-embedding-3-small','input':['a','b']}, 'embedding')
        with self.assertRaises(Stop):
            reservation(BODY, 'grader')

    def test_sdk_no_retries_and_caps_before_real_transport(self):
        from openai import OpenAI
        observed = []
        def fake_call(create, body, operation):
            observed.append((body, operation))
            return response()
        with patch.object(self.ledger, 'call', side_effect=fake_call), self.ledger.intercept():
            client = OpenAI(api_key='offline-placeholder', max_retries=8)
            self.assertEqual(client.max_retries, 0)
            client.chat.completions.create(model='gpt-4.1-mini', messages=BODY['messages'])
        self.assertEqual(observed[0][0]['max_completion_tokens'], 2048)
        self.assertEqual(observed[0][1], 'chat')


class SavedEvidence(unittest.TestCase):
    def test_offline_receipt_and_source_replay(self):
        import httpx
        from scripts.report_application_reliability_live import replay, source_diagnostics
        with patch.object(httpx.HTTPTransport, 'handle_request', side_effect=AssertionError('No network')):
            summary = replay()
            details = source_diagnostics()
        self.assertEqual(summary['calls'], {'chat':35,'embedding':18})
        self.assertEqual(summary['charged_usd'], '0.02573086')
        self.assertEqual(sum(r['measurement_status']=='blocked_by_local_input_bound' for r in summary['rows']),3)
        self.assertEqual(details['network_calls'],0)

    def test_tampered_receipt_is_rejected(self):
        import shutil
        from scripts.application_reliability_live import FOLDER
        from scripts.report_application_reliability_live import replay
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp)/'evidence'
            shutil.copytree(FOLDER,copied)
            with (copied/'run/raw/call-000.json').open('a',encoding='utf-8') as handle:
                handle.write(' ')
            with self.assertRaises(AssertionError):
                replay(copied)


if __name__ == '__main__':
    unittest.main()
