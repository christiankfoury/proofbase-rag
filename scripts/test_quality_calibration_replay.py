from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import report_quality_calibration as report


class CalibrationReplayTests(unittest.TestCase):
    def test_saved_failed_calibration_replays_honestly(self):
        result = report.replay()
        self.assertEqual(result["matching_judgments"], 3)
        self.assertEqual(result["case_count"], 24)
        self.assertEqual(result["matching_review_probes"], 1)
        self.assertFalse(result["semantic_validation_passed"])
        self.assertEqual(result["cumulative_cost_usd"], "1.34856592")

    def test_replay_uses_frozen_ledger_not_later_live_state(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            shutil.copytree(report.FOLDER / "calibration-v7-01", folder / "calibration-v7-01")
            (folder / "api-ledger.json").write_text("invalid later live ledger")
            with patch.object(report, "FOLDER", folder):
                self.assertEqual(report.replay()["matching_judgments"], 3)

    def test_changed_raw_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            shutil.copytree(report.FOLDER / "calibration-v7-01", folder / "calibration-v7-01")
            path = folder / "calibration-v7-01/paraphrase-preserves-conditions/claims.json"
            path.write_bytes(path.read_bytes() + b" ")
            with patch.object(report, "FOLDER", folder), self.assertRaisesRegex(ValueError, "Raw ledger binding changed"):
                report.replay()


if __name__ == "__main__":
    unittest.main()
