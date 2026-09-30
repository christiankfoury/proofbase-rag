import json
from pathlib import Path
import tempfile
import unittest

from scripts.report_phase73_v5_capture import snapshot, digest


class CapturePublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        (self.folder / 'run').mkdir()
        self.cases = [{'case_id': f'fresh-{i:03d}', 'question': f'Question {i}',
                       'project_id': 'scope', 'department_id': None, 'category': 'test'}
                      for i in range(1, 4)]
        self.write('holdout.json', {'cases': self.cases})
        for case in self.cases[:2]:
            self.write('run/' + case['case_id'] + '.json', {
                'case_id': case['case_id'], 'request': case,
                'raw_response': {'answer': 'Synthetic'}, 'latency_ms': 10,
                'status': 'complete' if case == self.cases[0] else 'captured'})
        self.manifest = {'status': 'interrupted', 'expected_cases': 3, 'completed_cases': 1,
                         'suite_sha256': digest(self.folder / 'holdout.json'),
                         'rows': {'fresh-001': digest(self.folder / 'run/fresh-001.json')}}
        self.write('run/manifest.json', self.manifest)

    def write(self, name, data):
        (self.folder / name).write_text(json.dumps(data), encoding='utf-8')

    def test_partial_denominators(self):
        result = snapshot(self.folder)
        self.assertEqual((result['completed_cases'], result['captured_cases']), (1, 2))
        self.assertEqual(result['ungraded_captured_cases'], ['fresh-002'])
        self.assertEqual(result['unexecuted_cases'], ['fresh-003'])
        self.assertEqual(result['latency_ms']['count'], 2)

    def test_ungraded_response_tampering_changes_inventory(self):
        original = snapshot(self.folder)
        path = self.folder / 'run/fresh-002.json'
        row = json.loads(path.read_bytes())
        row['raw_response']['answer'] = 'Changed'
        self.write('run/fresh-002.json', row)
        self.assertNotEqual(original, snapshot(self.folder))

    def test_wrong_scope_is_rejected(self):
        path = self.folder / 'run/fresh-002.json'
        row = json.loads(path.read_bytes())
        row['request']['project_id'] = 'foreign'
        self.write('run/fresh-002.json', row)
        with self.assertRaisesRegex(ValueError, 'sealed scope'):
            snapshot(self.folder)

    def test_running_attempt_is_rejected(self):
        self.manifest['status'] = 'running'
        self.write('run/manifest.json', self.manifest)
        with self.assertRaisesRegex(ValueError, 'finished attempt'):
            snapshot(self.folder)


if __name__ == '__main__':
    unittest.main()
