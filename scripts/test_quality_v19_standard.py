"""Offline request, replay, early-stop and shared/stage-cost regressions."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletion
from scripts import quality_development_v19 as runner
from scripts import test_quality_cost_control as fixtures
from scripts.quality_completion_durable import write_json_atomic as write


class Development(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CostControls(methodName='runTest'); self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_full_calibration_replays_same_saved_semantics_with_new_prompts(self):
        cases = runner.cases('calibration'); probes = runner.probes('calibration')
        saved = runner.ROOT/'data/evaluation/quality-completion-v1/v18-calibration'
        records = [runner.read(saved/c['id']/(p+'.json')) for c in cases for p in ['claims','coverage','review']]
        records += [runner.read(saved/(c['id']+'-raw.json')) for c in probes]
        raw = iter(records)
        def create(**body):
            old = next(raw)
            self.assertTrue(body['messages'][0]['content'].startswith(old['request']['messages'][0]['content']))
            copy = deepcopy(body); copy['messages'][0] = old['request']['messages'][0]
            self.assertEqual(copy, old['request'])
            return ChatCompletion.model_validate(old['response'])
        client = SimpleNamespace(max_retries=0, chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        prefix = self.fixture.folder/'prefix.json'; write(prefix, self.fixture.journal.load())
        spec = {'maximum_calls': 75, 'prefix_path': 'prefix.json'}
        with patch.object(runner, 'ROOT', self.fixture.folder), patch.object(runner, 'FOLDER', self.fixture.folder), \
             patch.object(runner, 'POLICY', self.fixture.policy_path), patch.object(runner, 'plan', return_value=spec), \
             patch.object(runner, 'SpendJournal', return_value=self.fixture.journal), \
             patch.object(runner, 'cases', return_value=cases), patch.object(runner, 'probes', return_value=probes):
            runner.execute('calibration', client)
            report = runner.replay('calibration')
            self.assertEqual((report['matched'], report['matching_probes'], report['calls']), (24,3,75))
            self.assertFalse(report['semantic_validation_passed'])
            with self.assertRaisesRegex(runner.transport.BudgetStop, 'exists'):
                runner.execute('calibration', client)

    def test_stage_cap_stops_before_provider_and_preserves_shared_prefix(self):
        body = runner.transport.initial_requests(runner.cases('diagnostic')[0]['inputs'])[0][1]
        ledger = runner.StageLedger(self.fixture.folder/'stage', self.fixture.journal, 3, Decimal('.000001'))
        provider = Mock()
        with self.assertRaisesRegex(runner.transport.BudgetStop, 'stage spending'):
            ledger.call(provider, body, ledger.folder/'one.json')
        provider.assert_not_called()
        self.assertEqual(self.fixture.journal.load()['entries'], {})
        self.assertEqual(runner.read(ledger.path)['calls'], [])

    def test_diagnostic_stops_on_first_mismatch_without_probes(self):
        cases = deepcopy(runner.cases('calibration')[:2])
        cases[0]['expected']['factual_support'] = 'fail'
        saved = runner.ROOT/'data/evaluation/quality-completion-v1/v18-calibration'/cases[0]['id']
        raw = iter(runner.read(saved/(p+'.json')) for p in ['claims','coverage','review'])
        provider = Mock(side_effect=lambda **body: ChatCompletion.model_validate(next(raw)['response']))
        client = SimpleNamespace(max_retries=0, chat=SimpleNamespace(completions=SimpleNamespace(create=provider)))
        with patch.object(runner, 'FOLDER', self.fixture.folder), \
             patch.object(runner, 'plan', return_value={'maximum_calls': 6}), \
             patch.object(runner, 'SpendJournal', return_value=self.fixture.journal), \
             patch.object(runner, 'cases', return_value=cases), patch.object(runner, 'probes') as probes:
            runner.execute('diagnostic', client)
            manifest = runner.read(runner.output('diagnostic')/'manifest.json')
            self.assertEqual(manifest['status'], 'early_stopped')
            self.assertEqual(len(manifest['rows']), 1)
            self.assertEqual(provider.call_count, 3)
            probes.assert_not_called()

    def test_new_reference_and_probe_contracts_are_valid(self):
        from scripts.quality_confirmation_fact_checks import check_fact_references
        check_fact_references(runner.read(runner.CONTROLS))
        self.assertEqual(len(runner.cases('diagnostic')), 12)
        self.assertEqual(len(runner.probes('diagnostic')), 3)
        for case in runner.probes('diagnostic'):
            self.assertEqual(runner.contract.validate(case['candidate'], case['inputs']), [])


if __name__ == '__main__':
    unittest.main()
