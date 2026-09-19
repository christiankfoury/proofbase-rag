import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import quality_eval_confirmation as confirmation


class ConfirmationTests(unittest.TestCase):
    def test_full_independently_checked_suite_and_bound(self):
        from decimal import Decimal
        plan = confirmation.preflight(SimpleNamespace(spent=Decimal("2")))
        self.assertEqual(plan["case_count"], 16)
        self.assertEqual(len(plan["cases"]),16)
        self.assertTrue(plan["headroom_passed"])
        self.assertEqual(len(confirmation.load_suite()["cases"]),16)

    def test_expectation_validation_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"validation.json"
            data=json.loads(confirmation.VALIDATION.read_bytes())
            data["case_reviews"][0]["accept"]=False
            path.write_text(json.dumps(data))
            with patch.object(confirmation,"VALIDATION",path), self.assertRaisesRegex(ValueError,"expectation validation"):
                confirmation.preflight(SimpleNamespace())

    def test_failed_development_gate_prevents_calls_and_attempt_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(confirmation,"FOLDER",Path(temp)), patch.object(confirmation,"readiness",side_effect=ValueError("gate failed")):
                with self.assertRaisesRegex(ValueError,"gate failed"):
                    confirmation.execute(lambda **kwargs:self.fail("No call allowed"),SimpleNamespace())
                self.assertEqual(list(Path(temp).iterdir()),[])


if __name__=="__main__":
    unittest.main()
