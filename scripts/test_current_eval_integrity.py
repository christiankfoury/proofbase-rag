"""Offline checks for the new budget ledger and exact grader-call replay."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from scripts.current_eval_budget import Ledger, BudgetStop
from scripts.current_dimension_grader import grade_response
from scripts.report_current_eval import replay_grader

ROOT = Path(__file__).resolve().parents[1]


class CurrentIntegrityTests(unittest.TestCase):
    def ledger(self, folder):
        path = Path(folder)/'ledger.json'
        data = json.loads((ROOT/'data/evaluation/dimension-reanalysis-v1/api-ledger.json').read_text(encoding='utf-8'))
        data.update(limit_usd=2.0, budget_authorization='User approved USD 2 cumulative ceiling on 2026-09-14')
        path.write_text(json.dumps(data),encoding='utf-8')
        return path,data

    def test_cannot_start_without_historical_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                Ledger(Path(folder)/'absent.json')

    def test_changed_history_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path,data = self.ledger(folder)
            data['calls'][0]['charged_usd'] = 0
            path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(ValueError):
                Ledger(path)

    def test_no_increase_beyond_authorized_ceiling(self):
        with tempfile.TemporaryDirectory() as folder:
            path,_ = self.ledger(folder)
            with self.assertRaises(ValueError):
                Ledger(path,limit=2.01)

    def test_budget_reservation_stops_before_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            path,_ = self.ledger(folder)
            ledger = Ledger(path)
            called = []
            with self.assertRaises(BudgetStop):
                ledger.invoke('chat',lambda *a,**k:called.append(True),None,(),{'model':'gpt-4.1-2025-04-14','messages':[{'role':'user','content':'x'*1_000_000}]})
            self.assertEqual([],called)

    def replay_fixture(self):
        cal = json.loads((ROOT/'data/evaluation/current-runtime-v3/calibration-attempt-1.json').read_text(encoding='utf-8'))['results'][0]
        inputs, grade = cal['inputs'],cal['grade']
        calls = []
        def create(**kwargs):
            keys = kwargs['response_format']['json_schema']['schema']['required']
            content = json.dumps({key:grade[key] for key in keys})
            response = {'id':'test','object':'chat.completion','created':0,'model':'gpt-4.1-2025-04-14','choices':[{'index':0,'message':{'role':'assistant','content':content,'refusal':None},'finish_reason':'stop'}]}
            calls.append({'request':kwargs,'response':response})
            return SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(refusal=None,content=content))])
        self.assertEqual(grade,grade_response(SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),inputs))
        return {'raw_grader_responses':calls,'grade':grade},inputs

    def test_saved_grader_calls_replay_without_provider(self):
        row,inputs = self.replay_fixture()
        replay_grader(row,inputs)

    def test_changed_actual_grader_input_rejected(self):
        row,inputs = self.replay_fixture()
        row['raw_grader_responses'][0]['request']['messages'][1]['content'] += 'changed'
        with self.assertRaises(ValueError):
            replay_grader(row,inputs)

    def test_changed_output_rejected(self):
        row,inputs = self.replay_fixture()
        row['grade'] = copy.deepcopy(row['grade'])
        row['grade']['all_claims_assessed'] = False
        with self.assertRaises(ValueError):
            replay_grader(row,inputs)

    def test_invalid_json_is_preserved_as_unresolved_without_retry(self):
        row,inputs = self.replay_fixture()
        row['raw_grader_responses'] = row['raw_grader_responses'][:1]
        row['raw_grader_responses'][0]['response']['choices'][0]['message']['content'] = '{invalid'
        row.update(grade=None,grading_error='invalid_or_incomplete_grade')
        replay_grader(row,inputs)

    def test_extra_grader_call_is_rejected(self):
        row,inputs = self.replay_fixture()
        row['raw_grader_responses'].append(copy.deepcopy(row['raw_grader_responses'][-1]))
        with self.assertRaises(ValueError):
            replay_grader(row,inputs)


if __name__ == '__main__':
    unittest.main()
