from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.quality_eval_calibration import (SUITE, AUDITS, load_suite, load_audits, preflight, execute, digest)
from scripts.quality_eval_transport import Ledger, BudgetStop


class CalibrationCustodyTests(unittest.TestCase):
    def validation(self):
        return {"status": "approved", "suite_sha256": digest(SUITE), "case_count": 24, "human_adjudication": False,
                "case_reviews": [{"id": case["id"], "accept": True} for case in load_suite()["cases"]],
                "review_suite_sha256": digest(AUDITS), "review_case_count": 3,
                "review_case_reviews": [{"id": case["id"], "accept": True} for case in load_audits()["cases"]]}

    def test_full_challenges_and_audits_validate_structurally(self):
        self.assertEqual(len(load_suite()["cases"]), 24)
        self.assertEqual(len(load_audits()["cases"]), 3)

    def test_missing_independent_validation_blocks_readiness(self):
        with tempfile.TemporaryDirectory() as temp:
            result = preflight(validation_path=Path(temp) / "absent.json")
        self.assertFalse(result["independently_checked"])
        self.assertFalse(result["headroom_passed"])
        self.assertEqual(result["external_calls"], 0)
        self.assertGreater(Decimal(result["upper_bound_usd"]), Decimal("0.80310608"))

    def test_hash_mismatch_or_rejected_judgment_cannot_approve(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "validation.json"
            accepted = self.validation()
            path.write_text(json.dumps(accepted))
            self.assertTrue(preflight(validation_path=path)["independently_checked"])
            for mutation in ("suite_sha256", "review_suite_sha256", "status", "case_reviews", "review_case_reviews"):
                altered = deepcopy(accepted)
                if mutation.endswith("reviews"):
                    altered[mutation][0]["accept"] = False
                else:
                    altered[mutation] = "wrong"
                path.write_text(json.dumps(altered))
                with self.subTest(mutation=mutation):
                    self.assertFalse(preflight(validation_path=path)["independently_checked"])

    def test_budget_failure_precedes_call_or_attempt_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            validation = folder / "validation.json"
            validation.write_text(json.dumps(self.validation()))
            ledger = Ledger.initialize(folder / "ledger.json")
            before = ledger.path.read_bytes()
            with self.assertRaises(BudgetStop):
                execute("underfunded", lambda **kwargs: self.fail("Must not call API"), ledger,
                        validation_path=validation, folder=folder)
            self.assertFalse((folder / "calibration-underfunded").exists())
            self.assertEqual(before, ledger.path.read_bytes())

    def test_invalid_and_duplicate_suite_id_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "suite.json"
            suite = load_suite()
            for bad in ("../escape", suite["cases"][1]["id"]):
                altered = deepcopy(suite)
                altered["cases"][0]["id"] = bad
                path.write_text(json.dumps(altered))
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    load_suite(path)

    def test_started_attempt_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            out = folder / "calibration-existing"
            out.mkdir()
            marker = out / "preserved.json"
            marker.write_text("old attempt")
            class NoCalls:
                def require_headroom(self, amount):
                    pass
            with patch("scripts.quality_eval_calibration.preflight", return_value={"independently_checked": True, "upper_bound_usd": "0.1"}):
                with self.assertRaises(FileExistsError):
                    execute("existing", lambda **kwargs: self.fail("No API"), NoCalls(), folder=folder)
            self.assertEqual(marker.read_text(), "old attempt")


if __name__ == "__main__":
    unittest.main()
