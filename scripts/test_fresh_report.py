import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.report_fresh_eval import reconstruct
from scripts.run_fresh_eval import summarize
from scripts.fresh_eval_calibration import fixtures
from scripts.fresh_eval_grader import verdict


class ReportTests(unittest.TestCase):
    def test_saved_verdict_replay_and_tamper_detection(self):
        fixture = fixtures()[0]
        case = dict(fixture["case"], case_id="fresh-001", category="factual", difficulty="easy")
        grade = {"behavior_correct": True, "facts": [{"fact_id": "F1", "status": "correct", "reason": "supported"}],
                 "claims": [{"text": fixture["payload"]["answer"], "kind": "factual", "supported": True, "citation_ids": ["C1"], "reason": "supported"}],
                 "all_factual_claims_enumerated": True, "all_citations_relevant": True, "forbidden_assertion_present": False,
                 "uncertain": False, "reason": "supported"}
        row = dict(case_id=case["case_id"], category="factual", status="complete", raw_response=fixture["payload"],
                   authorized_evidence=fixture["evidence"], safety_flags=[], grade=grade,
                   **verdict(case, fixture["payload"], fixture["evidence"], grade, []))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "run-v1").mkdir()
            values = {"freeze.json": {"commit": "frozen"}, "holdout.json": {"cases": [case]},
                      "api-ledger.json": {"calls": [{"charged_usd": .1}]},
                      "summary.json": dict(summarize([case], [row]), cost_usd_including_calibration=.1),
                      "run-v1/fresh-001.json": row}
            for name, value in values.items():
                (root / name).write_text(json.dumps(value))
            with patch("scripts.report_fresh_eval.FOLDER", root), patch("scripts.report_fresh_eval.verify_custody", return_value=({}, {"cases": [case]})):
                report = reconstruct()
                self.assertEqual(report["full_response"]["rate"], 1)
                self.assertTrue(report["safety_gate_met"])
                row["safety_flags"] = ["http_error"]
                row.update(verdict(case, fixture["payload"], fixture["evidence"], grade, row["safety_flags"]))
                (root / "run-v1/fresh-001.json").write_text(json.dumps(row))
                (root / "summary.json").write_text(json.dumps(dict(summarize([case], [row]), cost_usd_including_calibration=.1)))
                self.assertFalse(reconstruct()["safety_gate_met"])
                row["raw_response"]["citations"][0]["citation_text"] = "invented quote"
                (root / "run-v1/fresh-001.json").write_text(json.dumps(row))
                with self.assertRaisesRegex(ValueError, "Stored verdict"):
                    reconstruct()


if __name__ == "__main__":
    unittest.main()
