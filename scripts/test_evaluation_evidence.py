"""Offline report checks, including corrupt and incomplete evidence rejection."""
from copy import deepcopy
import json
import unittest

from scripts.build_evaluation_evidence import (
    EVAL, HOLDOUT, REPORT, ROOT, build_report, holdout_summary, metric, regression, unique_rows, verify_holdout,
)


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.questions = unique_rows(read(EVAL + "benchmark-questions.json")["questions"], "question_id")
        cls.regression = read(EVAL + "expanded-baseline/phase50-manual-findings-regression.json")
        cls.final = read(HOLDOUT + "final.json")
        cls.manifest = read(HOLDOUT + "manifest.json")
        cls.records = [read(path.relative_to(ROOT).as_posix()) for path in sorted((ROOT / HOLDOUT / "cases").glob("*.json"))]
        cls.events = [json.loads(line) for line in (ROOT / HOLDOUT / "journal.jsonl").read_text().splitlines()]

    def test_published_report_matches(self) -> None:
        self.assertEqual(build_report(), read(REPORT))

    def test_null_exclusion_and_partial_credit_are_explicit(self) -> None:
        self.assertEqual(metric([1, 0.5, None]), {
            "scored_cases": 2, "excluded_cases": 1, "score_sum": 1.5, "mean": 0.75,
        })
        self.assertIsNone(metric([None])["mean"])
        with self.assertRaises(ValueError):
            metric([float("nan")])

    def test_wrong_denominator_and_duplicate_cases_fail(self) -> None:
        artifact = deepcopy(self.regression)
        artifact["rows"].pop()
        with self.assertRaisesRegex(ValueError, "complete benchmark"):
            regression(artifact, self.questions)
        artifact["rows"].append(artifact["rows"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            regression(artifact, self.questions)

    def test_changed_answer_citation_and_summary_fail(self) -> None:
        for field, value in (("answer", "unsupported"), ("citations", [])):
            artifact = deepcopy(self.regression)
            artifact["rows"][0][field] = value
            with self.assertRaisesRegex(ValueError, "disagrees with scorer"):
                regression(artifact, self.questions)
        artifact = deepcopy(self.regression)
        artifact["summary"]["answer_accuracy"] = 0.5
        with self.assertRaisesRegex(ValueError, "Summary mismatch"):
            regression(artifact, self.questions)

    def test_missing_and_tampered_holdout_records_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing or extra"):
            verify_holdout(self.final, self.manifest, self.records[:-1], self.events)
        records = deepcopy(self.records)
        records[0]["row"]["passed"] = False
        with self.assertRaisesRegex(ValueError, "Corrupt case"):
            verify_holdout(self.final, self.manifest, records, self.events)

    def test_journal_tampering_fails(self) -> None:
        events = deepcopy(self.events)
        events[1]["case_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "Corrupt journal"):
            verify_holdout(self.final, self.manifest, self.records, events)

    def test_summary_pass_count_tampering_fails(self) -> None:
        final = deepcopy(self.final)
        final["summary"]["passed_count"] = 30
        with self.assertRaisesRegex(ValueError, "pass count mismatch"):
            holdout_summary(final)


if __name__ == "__main__":
    unittest.main()
