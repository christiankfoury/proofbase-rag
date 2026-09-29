"""Checks for the reference gate; no provider or application calls."""
from copy import deepcopy
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts.quality_confirmation_reference_checks import check_references, derived_behavior
from scripts.quality_eval_contract_v8 import candidate_judgments


class ReferenceChecks(unittest.TestCase):
    def test_precedence_matches_unchanged_reducer_for_all_combinations(self):
        for expected, actual, status in itertools.product(
            ["answer", "clarify", "not_found", "refuse_no_access"],
            ["answer", "partial_answer", "clarify", "not_found", "refuse_no_access", "refuse_instruction", "unknown"],
            ["covered", "missing", "contradicted", "unknown"]):
            grade = {"actual_behavior": actual, "facts": [{"status": status}], "claims": [],
                     "relevance": {"status": "pass"}, "forbidden_assertion": "absent"}
            result = candidate_judgments({"expected_behavior": expected}, grade)
            self.assertEqual(derived_behavior(expected, actual, result["completeness"]), result["response_behavior"])

    def test_prior_sealed_defect_is_rejected_without_changing_it(self):
        path = Path(__file__).resolve().parents[1]/"data/evaluation/quality-completion-v1/confirmation-challenges-v2.json"
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "confirmation-v2-08:behavior_precedence"):
            check_references(json.loads(before))
        self.assertEqual(path.read_bytes(), before)

    def test_failure_cannot_be_masked_by_unresolved_composite(self):
        case = {"id": "test", "inputs": {"expected_behavior": "answer", "required_facts": [{}], "forbidden_assertions": []},
                "payload": {"citations": []}, "evidence": [], "safety_flags": [],
                "expected": {"actual_behavior": "unknown", "completeness": "fail", "response_behavior": "fail",
                             "factual_support": "not_applicable", "citation_support": "not_applicable", "relevance": "pass",
                             "quotation_fidelity": "not_applicable", "overall": "unresolved"}}
        with self.assertRaisesRegex(ValueError, "composite_precedence"):
            check_references({"cases": [case]})
        fixed = deepcopy(case); fixed["expected"]["overall"] = "fail"
        self.assertEqual(check_references({"cases": [fixed]}), 1)

    def test_failed_preflight_never_calls_provider_or_opens_run(self):
        from scripts import quality_confirmation_replacement as runner
        with patch.object(runner, "readiness", return_value="ready"), patch.object(runner, "preflight", side_effect=ValueError("labels")):
            with self.assertRaisesRegex(ValueError, "labels"):
                runner.execute(lambda **kwargs:self.fail("Provider must not run"), None)


if __name__ == "__main__":
    unittest.main()
