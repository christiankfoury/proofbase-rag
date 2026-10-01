"""No-network full standard confirmation replay using saved development outputs."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from openai.types.chat import ChatCompletion
from scripts import quality_confirmation_standard_v23 as runner
from scripts import test_quality_cost_control as fixtures
from scripts.quality_eval_calibration_v12 import load_suite


class StandardConfirmation(unittest.TestCase):
    def test_full_sixteen_case_standard_execution_and_replay(self):
        fixture = fixtures.CostControls(methodName='runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        cases = deepcopy(load_suite()['cases'][:16])
        responses = []
        for case in cases:
            folder = runner.ROOT / 'data/evaluation/quality-completion-v1/v18-calibration'
            saved = runner.read(folder / (case['id'] + '.json'))
            case['expected_fact_statuses'] = {f['fact_id']: f['status'] for f in saved['grade']['facts']}
            responses.extend(runner.read(folder / case['id'] / (purpose + '.json')) for purpose in ['claims','coverage','review'])
        raw = iter(responses)
        def create(**body):
            saved = next(raw)
            self.assertTrue(body['messages'][0]['content'].startswith(saved['request']['messages'][0]['content']))
            compared = deepcopy(body); compared['messages'][0] = saved['request']['messages'][0]
            if body['response_format']['json_schema']['name'] == 'quality_claims':
                import json
                value = json.loads(compared['messages'][1]['content']); value.pop('source_metadata')
                compared['messages'][1]['content'] = json.dumps(value, ensure_ascii=False)
            self.assertEqual(compared, saved['request'])
            return ChatCompletion.model_validate(saved['response'])
        client = SimpleNamespace(max_retries=0, chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        prefix = fixture.folder/'prefix.json'
        runner.write(prefix, fixture.journal.load())
        with patch.object(runner,'PREFIX',prefix), patch.object(runner,'OUT',fixture.folder/'run'), patch.object(runner,'POLICY',fixture.policy_path), \
             patch.object(runner,'SpendJournal',return_value=fixture.journal), \
             patch.object(runner,'live_policy',return_value=(fixture.policy,Decimal(10))), \
             patch.object(runner,'retained_entries',return_value={}), \
             patch.object(runner,'SEAL',fixture.policy_path), \
             patch.object(runner,'custody',return_value=({'cases':cases},fixture.bindings)):
            runner.execute(client)
            report=runner.replay()
            self.assertEqual((report['count'],report['matched'],report['calls']),(16,16,48))
            self.assertFalse(report['semantic_validation_passed'])
            with self.assertRaisesRegex(ValueError,'spending differs|repeated attempt'):
                runner.execute(client)

    def test_failed_development_blocks_before_fresh_content(self):
        with patch.object(runner.previous,'readiness',side_effect=ValueError('not ready')), \
             patch.object(runner.previous.original,'load_suite') as load:
            with self.assertRaisesRegex(ValueError,'not ready'):
                runner.custody()
            load.assert_not_called()

    def test_reference_scope_review_is_required(self):
        suite = runner.read(runner.ROOT/'data/evaluation/phase73-successor-v1/confirmation-challenges-v1.json')
        with self.assertRaisesRegex(ValueError, 'scope review'):
            runner.check_references(suite, {'case_reviews': [{}]}, {})

    def test_title_mapping_is_checked_before_seal(self):
        suite = runner.read(runner.ROOT/'data/evaluation/phase73-successor-v1/confirmation-challenges-v1.json')
        suite['cases'][0]['inputs']['source_metadata'] = [{'source_id': 'R1', 'document_id': 'invented', 'document_title': 'Invented'}]
        with self.assertRaisesRegex(ValueError, 'title mapping'):
            runner.check_references(suite, {}, {})


if __name__ == '__main__':
    unittest.main()
