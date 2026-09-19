"""Offline contract tests; supplied judgments do not measure a semantic model."""
from copy import deepcopy
import unittest

from scripts.quality_eval_challenges import fixtures
from scripts.quality_eval_contract import dimensions, request_parts, summarize, validate


def evaluate(item):
    return dimensions(item["inputs"], item["grade"], item["payload"], item["evidence"], item["safety_flags"], item["review"])


class QualityContractTests(unittest.TestCase):
    def test_visible_challenges(self):
        cases = fixtures()
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertEqual(len(cases), 22)
        for item in cases:
            with self.subTest(item=item["id"]):
                result = evaluate(item)
                for dimension, expected in item["expected"].items():
                    self.assertEqual(result[dimension], expected, (dimension, result))

    def test_missing_fact_cannot_have_witness(self):
        item = fixtures()[1]
        item["grade"]["facts"][1]["answer_spans"] = [item["inputs"]["answer"]]
        self.assertIn("missing_fact_has_witness", validate(item["grade"], item["inputs"]))

    def test_exact_not_normalized_spans(self):
        item = fixtures()[0]
        item["grade"]["claims"][0]["text"] = item["inputs"]["answer"].lower()
        self.assertIn("claim_answer_span", validate(item["grade"], item["inputs"]))
        item = fixtures()[0]
        item["payload"]["citations"][0]["citation_text"] = item["evidence"][0]["content"].replace(" ", "  ")
        self.assertEqual(evaluate(item)["quotation_fidelity"], "fail")

    def test_duplicate_and_missing_fact_ids(self):
        item = fixtures()[0]
        item["grade"]["facts"][1]["fact_id"] = "F1"
        self.assertIn("fact_coverage", validate(item["grade"], item["inputs"]))

    def test_supported_citations_cannot_contradict_factual_label(self):
        item = fixtures()[0]
        item["grade"]["claims"][0]["factual_status"] = "contradicted"
        self.assertIn("support_labels_conflict", validate(item["grade"], item["inputs"]))

    def test_incomplete_prose_cannot_earn_complete_answer_pass(self):
        item = fixtures()[1]
        item["grade"]["actual_behavior"] = "answer"
        self.assertEqual(validate(item["grade"], item["inputs"]), [])
        result = evaluate(item)
        self.assertEqual(result["response_behavior"], "fail")
        self.assertEqual(result["overall"], "fail")
        self.assertFalse(result["has_unresolved_judgment"])

    def test_nonanswer_cannot_credit_gold(self):
        item = fixtures()[4]
        item["inputs"]["required_facts"] = [{"fact_id": "F1", "text": "The grant is EUR 360."}]
        item["grade"]["facts"] = [{"fact_id": "F1", "status": "covered", "answer_spans": [item["inputs"]["answer"]], "reason": "Invented coverage."}]
        errors = validate(item["grade"], item["inputs"])
        self.assertIn("nonanswer_with_covered_facts", errors)
        self.assertIn("covered_facts_without_claims", errors)

    def test_actual_answer_cannot_differ_from_grader_input(self):
        item = fixtures()[0]
        item["payload"]["answer"] = "I cannot help."
        self.assertIn("answer_input_mismatch", evaluate(item)["grader_errors"])

    def test_cited_input_cannot_substitute_gold_or_another_chunk(self):
        item = fixtures()[0]
        item["inputs"]["cited_sources"][0]["text"] = "Invented supporting text."
        self.assertIn("citation_input_mismatch", evaluate(item)["grader_errors"])
        item = fixtures()[0]
        item["inputs"]["factual_sources"][0]["text"] = "Altered retrieval."
        self.assertIn("retrieval_input_mismatch", evaluate(item)["grader_errors"])

    def test_empty_required_facts_cannot_make_answer_vacuously_pass(self):
        item = fixtures()[0]
        item["inputs"]["required_facts"] = []
        item["grade"]["facts"] = []
        self.assertIn("answer_expectations_missing", evaluate(item)["grader_errors"])

    def test_unmatched_citation_is_hard_failure_even_without_review(self):
        item = fixtures()[0]
        item["payload"]["citations"][0]["document_id"] = "PRIVATE"
        item["review"] = None
        result = evaluate(item)
        self.assertEqual(result["overall"], "fail")
        self.assertEqual(result["quotation_fidelity"], "unresolved")
        self.assertTrue(result["has_unresolved_judgment"])

    def test_missing_or_invalid_grades_remain_unresolved(self):
        for grade in (None, {}, {"all_claims_assessed": "yes"}):
            item = fixtures()[0]
            item["grade"] = grade
            self.assertEqual(evaluate(item)["overall"], "unresolved")

    def test_review_cannot_award_pass_over_failure(self):
        item = fixtures()[1]
        result = evaluate(item)
        self.assertEqual(result["overall"], "fail")
        item["review"]["completeness"] = "dispute"
        result = evaluate(item)
        self.assertFalse(result["target_credit"])
        self.assertTrue(result["has_unresolved_judgment"])

    def test_claim_and_coverage_boundaries(self):
        item = fixtures()[0]
        first, second = request_parts(item["inputs"])
        self.assertEqual(set(first["input"]), {"answer", "factual_sources", "cited_sources"})
        self.assertEqual(set(second["input"]), {"question", "history_not_evidence", "answer", "required_facts", "forbidden_assertions"})
        changed = deepcopy(item["inputs"])
        changed["expected_behavior"] = "not_found"
        changed["response_type"] = "not_found"
        self.assertEqual(request_parts(changed), [first, second])

    def test_summary_requires_semantic_validation_and_full_count(self):
        row = {"case_id": "dev-1", "dimensions": evaluate(fixtures()[0])}
        result = summarize([row])
        self.assertIsNone(result["validated_overall_rate"])
        self.assertFalse(result["complete"])
        self.assertIsNone(summarize([row], 1)["validated_overall_rate"])
        self.assertIsNone(summarize([row], semantic_validation_passed=True)["validated_overall_rate"])
        self.assertEqual(summarize([row], 1, semantic_validation_passed=True)["validated_overall_rate"], 1)

    def test_unresolved_counts_include_cases_with_known_failure(self):
        row = {"case_id": "dev-1", "dimensions": evaluate(fixtures()[16])}
        result = summarize([row], 1, semantic_validation_passed=True)
        self.assertEqual(result["candidate_passes"], 0)
        self.assertEqual(result["unresolved_cases"], 1)
        self.assertIsNone(result["validated_overall_rate"])

    def test_summary_rejects_duplicate_or_excess_rows(self):
        row = {"case_id": "dev-1", "dimensions": evaluate(fixtures()[0])}
        with self.assertRaises(ValueError):
            summarize([row, row])
        with self.assertRaises(ValueError):
            summarize([row], 0)

    def test_evaluation_does_not_mutate_evidence(self):
        item = fixtures()[0]
        before = deepcopy(item)
        evaluate(item)
        self.assertEqual(item, before)


if __name__ == "__main__":
    unittest.main()
