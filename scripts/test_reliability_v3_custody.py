"""Run unchanged live-v2 receipt checks against hash-verified frozen source files.

No checkout, historical writes, provider access or relaxed report assertions.
Git's normalized text is restored only to the exact recorded LF/CRLF digest.
"""
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.test_reliability_live_v2_evidence import Evidence, report


class FrozenEvidence(Evidence):
    @classmethod
    def setUpClass(cls):
        prepared = report.read(report.FOLDER / 'preflight.json')
        suite = report.read(report.FOLDER / 'cases.json')
        paths = dict(prepared['runtime_files_sha256'])
        paths['scripts/application_reliability_live_v2.py'] = prepared['runner_sha256']
        paths['scripts/reliability_payload_budget.py'] = prepared['estimator_sha256']
        for case in suite['cases']:
            paths.update({s['path']: s['sha256'] for s in case['sources']})
        archive = subprocess.check_output(['git', 'archive', '--format=zip', prepared['runtime_commit'], *paths], cwd=ROOT)
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for name, expected in paths.items():
                blob = z.read(name)
                normalized = blob.replace(b'\r\n', b'\n')
                variants = (blob, normalized, normalized.replace(b'\n', b'\r\n'))
                content = next((b for b in variants if hashlib.sha256(b).hexdigest() == expected), None)
                if content is None:
                    raise AssertionError(f'Frozen Git source cannot reproduce recorded hash: {name}')
                target = Path(temp.name) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
        cls.enterClassContext(patch.object(report, 'ROOT', Path(temp.name)))

    def test_exact_published_summary(self):
        self.assertEqual(report.replay(), report.read(report.FOLDER / 'receipt-summary.json'))


if __name__ == '__main__':
    # Load only the subclass, not the imported historical TestCase a second time.
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FrozenEvidence))
    sys.exit(not result.wasSuccessful())
