"""No-network audit of the interrupted-history to Batch accounting handoff."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import phase73_eval_history as history
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_cost_control import read, digest, MODEL


class Prefix(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.policy = read(history.POLICY)
        self.baseline = self.root / self.policy['baseline_ledger_path']
        write(self.baseline, read(history.ROOT / self.policy['baseline_ledger_path']))
        resolution = self.root / self.policy['prior_outcome_resolution']['path']
        write(resolution, {'fixture': True})
        self.policy_path = self.root / 'policy.json'; write(self.policy_path, self.policy)
        self.c = SimpleNamespace(OUT=self.root / 'batch', REPORT=self.root / 'report.json',
            GATE=self.root / 'gate.json', REVIEW=self.root / 'review.md', readiness=Mock(), batch=Mock())
        self.c.REVIEW.write_text('Synthetic review fixture')
        write(self.c.OUT / 'additional-spend.json', {'fixture': True})
        total = Decimal(0)
        def verify(folder):
            count = 32 if folder.name == 'initial' else 16
            return {}, {'status': 'complete'}, [{'custom_id': str(i), 'body': {'fixture': i}} for i in range(count)]
        self.c.batch.verify.side_effect = verify
        for wave in ['initial', 'review']:
            folder = self.c.OUT / wave
            for request in verify(folder)[2]:
                response = {'model': MODEL, 'usage': {'prompt_tokens': 100, 'completion_tokens': 5,
                    'prompt_tokens_details': {'cached_tokens': 80}}}
                amount = history.charge(response, 'batch'); total += amount
                write(folder / 'responses' / (request['custom_id'] + '.json'),
                      {'request': request['body'], 'response': response, 'cache_aware_cost_usd': str(amount)})
        write(self.c.REPORT, {'matched': 16, 'calls': 48, 'cost_usd': str(total)})
        write(self.c.GATE, {'status': 'approved', 'unresolved_semantic_findings': 0,
            'human_adjudication': False, 'report_sha256': digest(self.c.REPORT),
            'source_review_sha256': digest(self.c.REVIEW)})
        for name, value in [('ROOT', self.root), ('POLICY', self.policy_path), ('confirmation', self.c)]:
            p = patch.object(history, name, value); p.start(); self.addCleanup(p.stop)
        p = patch.object(history, 'live_policy', return_value=(self.policy, Decimal(10)))
        p.start(); self.addCleanup(p.stop)

    def test_preserves_original_rows_reservation_and_all_batch_costs(self):
        original = read(self.baseline)
        prefix = history.build_prefix()
        self.c.readiness.assert_called_once()
        self.assertEqual(prefix['calls'][:len(original['calls'])], original['calls'])
        self.assertEqual(len(prefix['calls']), len(original['calls']) + 48)
        self.assertEqual(prefix['resolved_rejection_indices'], [2594])
        self.assertEqual(Decimal(prefix['prior_spend_usd']), Decimal('10.85570077') + Decimal(prefix['batch_cost_usd']))
        path = self.root / 'prior.json'; write(path, prefix)
        self.assertEqual(history.PriorLedger(path).resolved_rejections, {2594})
        self.assertEqual(read(self.baseline), original)

    def test_unqualified_evaluator_blocks_before_history_access(self):
        self.c.readiness.side_effect = ValueError('Not ready')
        with self.assertRaisesRegex(ValueError, 'Not ready'):
            history.build_prefix()
        self.c.batch.verify.assert_not_called()

    def test_another_unknown_or_changed_rejection_is_not_waived(self):
        data = read(self.baseline); data['calls'][-2]['status'] = 'unknown'; write(self.baseline, data)
        with self.assertRaisesRegex(ValueError, 'Historical rejection'):
            history.build_prefix()

    def test_changed_prefix_and_batch_response_are_rejected(self):
        prefix = history.build_prefix(); path = self.root / 'prior.json'; write(path, prefix)
        corrupt = deepcopy(prefix); corrupt['calls'][-1]['charged_usd'] = '0'; write(path, corrupt)
        with self.assertRaisesRegex(ValueError, 'prefix changed'):
            history.PriorLedger(path)
        write(path, prefix)
        raw_path = self.c.OUT / 'initial/responses/0.json'
        raw = read(raw_path); raw['response']['usage']['completion_tokens'] += 1; write(raw_path, raw)
        with self.assertRaisesRegex(ValueError, 'row changed'):
            history.PriorLedger(path)


if __name__ == '__main__':
    unittest.main()
