"""No-network pricing, budget, Batch lifecycle and unchanged-grading regressions."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from scripts import quality_cost_control as costs
from scripts import quality_batch_transport as batch
from scripts import quality_batch_grading as grading
from scripts.quality_completion_durable import write_json_atomic as write
from scripts.quality_eval_transport_v18 import initial_requests
from scripts.quality_eval_calibration_v12 import load_suite


def object_response(**data):
    return SimpleNamespace(**data, model_dump=lambda **kw: deepcopy(data))


class CostControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.policy_path = self.folder / 'policy.json'
        write(self.folder / 'baseline.json', {'prior': 'unchanged'})
        write(self.folder / 'resolution.json', {'status': 'resolved_no_generation',
            'baseline_ledger_sha256': costs.digest(self.folder / 'baseline.json'),
            'evidence_sha256': {'baseline.json': costs.digest(self.folder / 'baseline.json')},
            'provider_error_code': 'project_spend_limit_exceeded'})
        self.policy = {'additional_ceiling_usd': '10', 'external_service_ready': True,
            'baseline_ledger_path': 'baseline.json', 'baseline_ledger_sha256': costs.digest(self.folder / 'baseline.json'),
            'prior_outcome_resolution': {'path': 'resolution.json', 'sha256': costs.digest(self.folder / 'resolution.json')}}
        write(self.policy_path, self.policy)
        self.patch_root = patch.object(costs, 'ROOT', self.folder)
        self.patch_root.start()
        self.addCleanup(self.patch_root.stop)
        self.journal = batch.SpendJournal(self.folder / 'spend', self.policy_path)
        self.cases = load_suite()['cases'][:2]
        self.bindings = {'data/evaluation/quality-completion-v1/v18-freeze.json':
                         costs.digest(batch.ROOT / 'data/evaluation/quality-completion-v1/v18-freeze.json')}
        self.client = SimpleNamespace(max_retries=0, files=Mock(), batches=Mock())
        self.client.files.create.return_value = object_response(id='file-test')
        self.client.batches.create.return_value = object_response(id='batch-test')

    def prepare(self, name='job'):
        job = self.folder / name
        batch.prepare(job, [{'custom_id': 'one', 'body': initial_requests(self.cases[0]['inputs'])[0][1]}], self.bindings)
        self.authorize(job)
        return job

    def authorize(self, job):
        write(job / 'authorization.json', {'status': 'approved', 'plan_sha256': costs.digest(job / 'plan.json'),
              'protocol_bindings': self.bindings, 'human_adjudication': False})

    def terminal(self, job, *, missing=False, duplicate=False, status='completed'):
        requests = [json.loads(line) for line in (job / 'input.jsonl').read_bytes().splitlines()]
        lines = []
        for row in requests:
            if row['custom_id'] == 'one':
                cid, purpose = self.cases[0]['id'], 'claims'
            else:
                cid, purpose = row['custom_id'].rsplit('-', 1)
            raw = costs.read(batch.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration' / cid / (purpose + '.json'))
            self.assertEqual(raw['request'], row['body'])
            lines.append({'custom_id': row['custom_id'], 'error': None,
                'response': {'status_code': 200, 'body': raw['response'], 'request_id': 'mock-request'}})
        if missing:
            lines.pop()
        if duplicate:
            lines.append(deepcopy(lines[0]))
        self.client.files.content.return_value = SimpleNamespace(content=b''.join(batch.encoded(v) + b'\n' for v in reversed(lines)))
        self.client.batches.retrieve.return_value = object_response(id='batch-test', input_file_id='file-test',
            status=status, output_file_id='file-output', error_file_id=None)

    def test_prices_apply_cache_and_batch_without_double_discount(self):
        response = {'model': costs.MODEL, 'usage': {'prompt_tokens': 1000, 'completion_tokens': 100,
                    'prompt_tokens_details': {'cached_tokens': 800}}}
        self.assertEqual(costs.charge(response), Decimal('.0022'))
        self.assertEqual(costs.charge(response, 'batch'), Decimal('.0011'))
        response['usage']['prompt_tokens_details']['cached_tokens'] = 1001
        with self.assertRaises(ValueError):
            costs.charge(response)
        response['model'] = 'unpriced-model'
        with self.assertRaises(ValueError):
            costs.charge(response)

    def test_unselected_cap_quota_and_unresolved_outcome_block_before_network(self):
        job = self.prepare()
        for key, value in [('additional_ceiling_usd', None), ('external_service_ready', False), ('prior_outcome_resolution', None)]:
            policy = dict(self.policy); policy[key] = value; write(self.policy_path, policy)
            with self.assertRaises(ValueError):
                batch.submit(job, self.client, self.journal)
            self.client.files.create.assert_not_called()

    def test_ceiling_covers_reservations_and_blocks_before_upload(self):
        job = self.prepare()
        self.policy['additional_ceiling_usd'] = '.000001'; write(self.policy_path, self.policy)
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            batch.submit(job, self.client, self.journal)
        self.client.files.create.assert_not_called()

    def test_shared_ceiling_accounts_for_prior_settled_calls(self):
        self.journal.reserve('application', Decimal('6'), 'request-hash')
        self.journal.finish('application', Decimal('4'), 'response-hash')
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            self.journal.reserve('batch-next', Decimal('7'), 'plan-hash')
        self.journal.reserve('batch-next', Decimal('6'), 'plan-hash')
        with self.assertRaisesRegex(ValueError, 'Pending'):
            self.journal.reserve('overlap', Decimal('.01'), 'plan-hash')

    def test_sdk_retry_and_missing_authorization_are_blocked_before_upload(self):
        job = self.prepare()
        self.client.max_retries = 2
        with self.assertRaisesRegex(ValueError, 'retries'):
            batch.submit(job, self.client, self.journal)
        self.client.max_retries = 0
        write(job / 'authorization.json', {'status': 'pending'})
        with self.assertRaisesRegex(ValueError, 'authorization'):
            batch.submit(job, self.client, self.journal)
        self.client.files.create.assert_not_called()

    def test_timeout_is_not_resubmitted_and_blocks_other_jobs(self):
        job = self.prepare()
        self.client.batches.create.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            batch.submit(job, self.client, self.journal)
        with self.assertRaisesRegex(ValueError, 'already attempted'):
            batch.submit(job, self.client, self.journal)
        second = self.prepare('other')
        with self.assertRaisesRegex(ValueError, 'unknown|already reserved'):
            batch.submit(second, self.client, self.journal)
        self.assertEqual(self.client.batches.create.call_count, 1)
        entry = next(iter(self.journal.load()['entries'].values()))
        self.assertEqual(entry['accounted_usd'], entry['reserved_usd'])

    def test_pending_collection_and_completed_replay_never_resubmit(self):
        job = self.prepare(); batch.submit(job, self.client, self.journal)
        self.terminal(job, status='in_progress')
        self.assertEqual(batch.collect(job, self.client, self.journal)['status'], 'in_progress')
        self.client.files.content.assert_not_called()
        self.terminal(job)
        result = batch.collect(job, self.client, self.journal)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(batch.collect(job, self.client, self.journal), result)
        self.assertEqual(self.client.batches.create.call_count, 1)
        self.assertEqual(self.client.batches.retrieve.call_count, 2)
        entry = next(iter(self.journal.load()['entries'].values()))
        self.assertLess(Decimal(entry['accounted_usd']), Decimal(entry['reserved_usd']))

    def test_missing_and_duplicate_results_retain_reservation(self):
        for variant in ('missing', 'duplicate'):
            with self.subTest(variant=variant):
                journal = batch.SpendJournal(self.folder / variant, self.policy_path)
                job = self.prepare('job-' + variant); batch.submit(job, self.client, journal)
                self.terminal(job, **{variant: True})
                result = batch.collect(job, self.client, journal)
                self.assertEqual(result['status'], 'unresolved')
                self.assertTrue((job / 'output.jsonl').exists())
                entry = next(iter(journal.load()['entries'].values()))
                self.assertEqual(entry['status'], 'unknown')
                self.assertEqual(entry['accounted_usd'], entry['reserved_usd'])

    def test_changed_request_rejected_before_upload(self):
        job = self.prepare(); (job / 'input.jsonl').write_bytes(b'{}\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            batch.submit(job, self.client, self.journal)
        self.client.files.create.assert_not_called()

    def test_two_wave_saved_outputs_match_frozen_grades_and_reducers(self):
        folder = self.folder / 'grading'
        grading.prepare_initial(folder, load_suite()['cases'], self.bindings)
        for wave in ('initial', 'review'):
            if wave == 'review':
                grading.prepare_review(folder)
            job = folder / wave; self.authorize(job)
            batch.submit(job, self.client, self.journal)
            self.terminal(job)
            self.assertEqual(batch.collect(job, self.client, self.journal)['status'], 'complete')
        report = grading.replay(folder)
        self.assertFalse(report['readiness_approved'])
        for row in report['rows']:
            saved = costs.read(batch.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration' / (row['id'] + '.json'))
            self.assertEqual((row['grade'], row['review'], row['dimensions']), (saved['grade'], saved['review'], saved['dimensions']))
        self.assertEqual(self.client.batches.create.call_count, 2)


if __name__ == '__main__':
    unittest.main()
