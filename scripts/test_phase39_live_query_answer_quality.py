from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.run_phase39_live_query_answer_quality as runner
import scripts.export_dashboard_data as dashboard_export
from apps.api.app.main import current_demo_user


def test_query_payload_uses_live_multi_doc_auto_mode() -> None:
    args = Namespace(
        retrieval_mode="vector_lexical_rerank",
        top_k=5,
        prompt_version="v8",
        multi_doc_mode="auto",
    )
    question = {
        "question": "Compare vacation carryover and sick leave.",
        "user_role": "Employee",
    }

    payload = runner._query_payload(question, args, session_id="session-1")

    assert payload["retrieval_mode"] == "vector_lexical_rerank"
    assert payload["prompt_version"] == "v8"
    assert payload["multi_doc_mode"] == "auto"
    assert payload["session_id"] == "session-1"
    assert payload["evaluation_excluded_document_prefixes"] == ["UPLOAD-"]


def test_row_scores_api_response_and_preserves_multi_doc_flag() -> None:
    question = {
        "question_id": "TEST-001",
        "question": "Can employees carry over unused vacation days?",
        "question_type": "simple_factual",
        "expected_behavior": "answer",
        "expected_answer": "Employees may carry over up to 5 unused vacation days into the next calendar year.",
        "expected_source_document": ["HR-002"],
        "expected_source_section_or_quote": [
            {
                "document_id": "HR-002",
                "section": "Vacation Entitlement",
                "quote": "Employees may carry over up to 5 unused vacation days into the next calendar year.",
            }
        ],
        "user_role": "Employee",
    }
    response = {
        "response_type": "answer",
        "behavior": "answer",
        "answer": "Employees may carry over up to 5 unused vacation days into the next calendar year.",
        "citations": [
            {
                "document_id": "HR-002",
                "section_heading": "Vacation Entitlement",
                "chunk_id": "chunk-1",
                "confidence": 0.95,
            }
        ],
        "retrieved_chunks": [
            {
                "chunk_id": "chunk-1",
                "document_id": "HR-002",
                "document_title": "PTO and Leave Policy",
                "section_heading": "Vacation Entitlement",
                "content": "Employees may carry over up to 5 unused vacation days.",
                "access_roles": ["Employee"],
                "restricted": False,
                "sensitivity": "internal",
                "rank": 1,
                "score": 0.91,
                "retrieval_source": "vector_lexical_rerank",
            }
        ],
        "citation_confidence": 0.95,
        "answer_confidence": 0.95,
        "final_confidence": 0.94,
        "supported_claims": ["Employees may carry over up to 5 unused vacation days."],
        "unsupported_claims": [],
        "input_tokens": 100,
        "output_tokens": 50,
        "estimated_cost_usd": 0.001,
        "pricing_status": "estimated",
        "prompt_version": "v8",
        "model": "gpt-4.1-mini",
        "temperature": 0.0,
        "multi_doc_used": True,
        "multi_doc_mode": "auto",
        "memory": {
            "original_question": "Can employees carry over unused vacation days?",
            "rewritten_question": "Can employees carry over unused vacation days?",
            "is_followup": False,
            "memory_used": False,
            "rewrite_strategy": None,
        },
        "permission_check": {
            "unauthorized_chunks_reached_generation": False,
        },
    }

    row, failed_item = runner._row(question, response, latency_ms=123, top_k=5)

    assert failed_item is None
    assert row["answer_accuracy"] == 1.0
    assert row["citation_accuracy"] == 1.0
    assert row["all_sources_hit"] == 1.0
    assert row["multi_doc_used"] is True
    assert row["retrieved_chunks"][0]["document_id"] == "HR-002"


def test_dashboard_run_marks_live_query_eval() -> None:
    result = {
        "generated_at": "2026-06-26T00:00:00+00:00",
        "benchmark_version": "1.1",
        "summary": {
            "experiment_id": runner.RUN_ID,
            "run_name": "live-query-answer-quality-v8",
            "phase": "phase-39",
            "prompt_name": "answer_generation",
            "prompt_version": "v8",
            "model": "gpt-4.1-mini",
            "retrieval_mode": "vector_lexical_rerank",
            "chunking_strategy": "section_based",
            "top_k": 5,
            "multi_doc_mode": "auto",
            "evaluation_excluded_document_prefixes": ["UPLOAD-"],
            "question_filter": "all",
            "question_count": 1,
            "source_question_count": 1,
            "failed_question_count": 0,
            "submetric_issue_count": 0,
            "submetric_issue_ids": [],
            "answer_accuracy": 1.0,
            "citation_accuracy": 1.0,
            "hallucination_rate": 0.0,
        },
        "rows": [{"question_type": "simple_factual"}],
        "failed_questions": [],
    }

    dashboard_run = runner._dashboard_run(result)

    assert dashboard_run["run_type"] == "live_query_eval"
    assert dashboard_run["run_id"] == runner.RUN_ID
    assert dashboard_run["failed_count"] == 0
    assert dashboard_run["metrics"]["submetric_issue_count"] == 0
    assert dashboard_run["evaluation_excluded_document_prefixes"] == ["UPLOAD-"]
    assert dashboard_run["category_breakdown"] == {"simple_factual": 1}


def test_summary_tracks_submetric_issues_without_failed_questions() -> None:
    rows = [
        {
            "question_id": "MEM-001",
            "answer_accuracy": 1.0,
            "citation_accuracy": 1.0,
            "response_type_accuracy": 0.5,
            "refusal_accuracy": None,
            "not_found_accuracy": None,
            "clarification_accuracy": None,
            "all_sources_hit": 1.0,
            "expected_source_recall": 1.0,
            "any_source_hit": 1.0,
            "precision_at_k": 0.4,
            "mrr": 1.0,
            "faithfulness": 0.9,
            "hallucination_rate": 0.0,
            "final_confidence": 0.9,
            "input_tokens": 10,
            "output_tokens": 5,
            "estimated_cost_usd": 0.001,
        }
    ]
    args = Namespace(
        retrieval_mode="vector_lexical_rerank",
        top_k=5,
        prompt_version="v8",
        multi_doc_mode="auto",
        question_filter="all",
    )

    summary = runner._summary(
        rows=rows,
        failed=[],
        benchmark={"question_count": 1},
        args=args,
        started_at="2026-06-27T00:00:00+00:00",
    )

    assert summary["failed_question_count"] == 0
    assert summary["submetric_issue_count"] == 1
    assert summary["submetric_issue_ids"] == ["MEM-001"]


def test_query_rejects_eval_exclusions_for_non_admin_users() -> None:
    client = TestClient(runner.app)
    runner.app.dependency_overrides[current_demo_user] = lambda: {
        "id": "employee-1",
        "business_role": "Employee",
        "is_admin": False,
        "memberships": [],
    }
    try:
        response = client.post(
            "/query",
            json={
                "question": "What is the vacation carryover policy?",
                "user_role": "Employee",
                "evaluation_excluded_document_prefixes": ["UPLOAD-"],
            },
        )
    finally:
        runner.app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "Evaluation document exclusions" in response.json()["detail"]


def test_dashboard_export_accepts_live_query_eval_as_current_answer_run() -> None:
    older_prompt_run = {
        "run_id": "phase38-answer-quality-remediation-v8",
        "run_type": "prompt_experiment",
        "question_filter": "all",
        "total_questions": 130,
        "source_question_count": 130,
        "timestamp": "2026-06-25T00:00:00+00:00",
    }
    live_query_run = {
        "run_id": runner.RUN_ID,
        "run_type": "live_query_eval",
        "question_filter": "all",
        "total_questions": 130,
        "source_question_count": 130,
        "timestamp": "2026-06-26T00:00:00+00:00",
    }

    current = dashboard_export._current_answer_run([older_prompt_run, live_query_run])

    assert current is live_query_run


def main() -> None:
    test_query_payload_uses_live_multi_doc_auto_mode()
    test_row_scores_api_response_and_preserves_multi_doc_flag()
    test_dashboard_run_marks_live_query_eval()
    test_summary_tracks_submetric_issues_without_failed_questions()
    test_query_rejects_eval_exclusions_for_non_admin_users()
    test_dashboard_export_accepts_live_query_eval_as_current_answer_run()
    print("Phase 39 live query answer-quality evaluator tests passed.")


if __name__ == "__main__":
    main()
