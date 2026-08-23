from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.independent_generalization_common import load_suite, validate_suite_payload
from scripts.run_independent_generalization_eval import _score_response


def test_valid_development_suite() -> None:
    result = validate_suite_payload(load_suite("development"), expected_split="development")
    assert result["valid"], result["errors"]
    assert result["case_count"] == 70
    assert len(result["coverage"]["documents"]) == 19
    assert result["coverage"]["permission_pair_count"] == 5


def test_duplicate_id_is_rejected() -> None:
    payload = copy.deepcopy(load_suite("development"))
    payload["cases"][1]["case_id"] = payload["cases"][0]["case_id"]
    result = validate_suite_payload(payload, expected_split="development")
    assert not result["valid"]
    assert any("duplicate case IDs" in error for error in result["errors"])


def test_missing_quote_is_rejected() -> None:
    payload = copy.deepcopy(load_suite("development"))
    target = next(case for case in payload["cases"] if case["expected_source_sections_or_quotes"])
    target["expected_source_sections_or_quotes"][0]["quote"] = "This quote is deliberately absent."
    result = validate_suite_payload(payload, expected_split="development")
    assert not result["valid"]
    assert any("expected quote not found" in error for error in result["errors"])


def test_permission_pair_parity_is_required() -> None:
    payload = copy.deepcopy(load_suite("development"))
    target = next(case for case in payload["cases"] if case.get("permission_pair_id"))
    target["question"] += " changed intent"
    result = validate_suite_payload(payload, expected_split="development")
    assert not result["valid"]
    assert any("materially equivalent intent" in error for error in result["errors"])


def test_explicit_restricted_source_expectation_can_replace_a_pair() -> None:
    payload = copy.deepcopy(load_suite("development"))
    pair_id = next(case["permission_pair_id"] for case in payload["cases"] if case.get("permission_pair_id"))
    for case in payload["cases"]:
        if case.get("permission_pair_id") == pair_id:
            case["permission_pair_id"] = None
            case["restricted_source_expectation"] = True
    result = validate_suite_payload(payload, expected_split="development")
    assert result["valid"], result["errors"]


def test_exposure_uses_chunk_access_roles_not_narrow_expected_document_list() -> None:
    case = {
        "case_id": "TEST-PERMISSION-SCORING",
        "split": "development",
        "category": "permission_scope_pairs",
        "difficulty": "medium",
        "user_role": "Employee",
        "project_id": None,
        "department_id": None,
        "previous_turns": [],
        "question": "What is accessible?",
        "expected_behavior": "answer",
        "required_facts": ["accessible evidence"],
        "forbidden_facts": [],
        "expected_source_documents": ["FIN-001"],
        "allowed_documents": [],
    }
    payload = {
        "response_type": "answer",
        "answer": "Accessible evidence is available.",
        "citations": [{"document_id": "FIN-001", "citation_text": "Accessible evidence"}],
        "retrieved_chunks": [{"document_id": "FIN-001", "access_roles": ["Employee", "Manager"]}],
        "permission_check": {"unauthorized_chunks_reached_generation": False},
    }
    row = _score_response(case, payload, latency_ms=1.0)
    assert row["unauthorized_chunk_exposure"] == 0.0
    assert row["restricted_citation_leakage"] == 0.0

    payload["retrieved_chunks"][0]["access_roles"] = ["Manager"]
    restricted = _score_response(case, payload, latency_ms=1.0)
    assert restricted["unauthorized_chunk_exposure"] == 1.0
    assert restricted["restricted_citation_leakage"] == 1.0


def main() -> None:
    test_valid_development_suite()
    test_duplicate_id_is_rejected()
    test_missing_quote_is_rejected()
    test_permission_pair_parity_is_required()
    test_explicit_restricted_source_expectation_can_replace_a_pair()
    test_exposure_uses_chunk_access_roles_not_narrow_expected_document_list()
    print("Phase 47 independent generalization validator tests passed.")


if __name__ == "__main__":
    main()
