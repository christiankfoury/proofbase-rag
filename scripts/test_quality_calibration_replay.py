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

    def test_windows_source_newlines_do_not_change_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            for name in report.CODE:
                source = (report.ROOT / "scripts" / name).read_text(encoding="utf-8")
                (root / "scripts" / name).write_bytes(source.replace("\n", "\r\n").encode("utf-8"))
            with patch.object(report, "ROOT", root):
                self.assertEqual(report.replay()["matching_judgments"], 3)


if __name__ == "__main__":
    unittest.main()


class CalibrationV8ReplayTests(unittest.TestCase):
    def test_v8_replays_without_overstating_readiness(self):
        from scripts.report_quality_calibration_v8 import replay
        result = replay()
        self.assertEqual(result["matching_judgments"], 17)
        self.assertEqual(result["matching_review_probes"], 3)
        self.assertFalse(result["semantic_validation_passed"])
        self.assertEqual(result["cumulative_cost_usd"], "1.53666792")
