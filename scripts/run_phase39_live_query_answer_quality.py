from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
from apps.api.app.evaluation.answer_metrics import score_answer
from apps.api.app.evaluation.failed_question_report import failed_question_item
from apps.api.app.evaluation.metrics import (
    all_sources_hit,
    any_source_hit,
    expected_source_recall,
    precision_at_k,
    reciprocal_rank,
)
from apps.api.app.main import app
from apps.api.app.memory.session_store import add_message, create_session
from apps.api.app.retrieval.types import RetrievedChunk


BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
OUTPUT_DIR = ROOT / "data/evaluation/expanded-baseline"
EVAL_RUN_DIR = ROOT / "data/evaluation/eval-runs"
PHASE_DIR = ROOT / "docs/phase-39"
RUN_ID = "phase39-live-query-answer-quality-v8"
OUTPUT_JSON = OUTPUT_DIR / f"{RUN_ID}.json"
EVAL_RUN_JSON = EVAL_RUN_DIR / f"{RUN_ID}.json"
REPORT_PATH = PHASE_DIR / "live-query-answer-quality-results.md"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000002706"
EVALUATION_EXCLUDED_DOCUMENT_PREFIXES = ["UPLOAD-"]
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The Phase 39 live query answer-quality run sends benchmark questions and permission-filtered retrieved "
    "synthetic source snippets to external OpenAI embeddings and chat-completion APIs through POST /query. "
    "Re-run with --allow-external-ai only after explicit approval."
)


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def _load_benchmark() -> dict[str, Any]:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _questions(benchmark: dict[str, Any], question_filter: str) -> list[dict[str, Any]]:
    questions = [question for question in benchmark["questions"] if isinstance(question, dict)]
    if question_filter == "all":
        return questions
    return [question for question in questions if question.get("question_type") == question_filter]


def _expected_docs(question: dict[str, Any]) -> list[str]:
    if question["question_type"] in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def _average(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return round(mean(real_values), 3)


def _sum(values: list[int | None]) -> int | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return sum(real_values)


def _sum_cost(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return None
    return round(sum(real_values), 6)


def _category_breakdown(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        question_type = row.get("question_type")
        if question_type:
            counts[str(question_type)] = counts.get(str(question_type), 0) + 1
    return dict(sorted(counts.items()))


def _failure_reason_counts(failed_questions: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in failed_questions:
        counts[str(item.get("failure_type") or "unknown")] += 1
    return dict(sorted(counts.items()))


def _has_submetric_issue(row: dict[str, Any]) -> bool:
    full_credit_metrics = [
        "answer_accuracy",
        "citation_accuracy",
        "response_type_accuracy",
        "refusal_accuracy",
        "not_found_accuracy",
        "clarification_accuracy",
        "all_sources_hit",
        "expected_source_recall",
    ]
    has_issue = any(row.get(metric) is not None and row[metric] < 1.0 for metric in full_credit_metrics)
    if row.get("hallucination_rate") is not None and row["hallucination_rate"] > 0.0:
        has_issue = True
    return has_issue


def _submetric_issue_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["question_id"] for row in rows if _has_submetric_issue(row)]


def _submetric_issue_breakdown(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    breakdown = {
        "actionable": {"count": 0, "ids": []},
        "memory_response_type_diagnostic": {"count": 0, "ids": []},
        "clarification_source_coverage_diagnostic": {"count": 0, "ids": []},
    }
    for row in rows:
        if not _has_submetric_issue(row):
            continue
        question_id = row["question_id"]
        expected_behavior = row.get("expected_behavior")
        is_memory_behavior_diagnostic = (
            expected_behavior == "answer_with_memory"
            and row.get("behavior") == "answer"
            and row.get("response_type_accuracy") is not None
            and row.get("response_type_accuracy") < 1.0
        )
        is_clarification_source_diagnostic = (
            expected_behavior == "ask_clarifying_question"
            and row.get("clarification_accuracy") == 1.0
            and (
                (row.get("all_sources_hit") is not None and row.get("all_sources_hit") < 1.0)
                or (row.get("expected_source_recall") is not None and row.get("expected_source_recall") < 1.0)
            )
        )
        actionable_metrics = [
            "answer_accuracy",
            "citation_accuracy",
            "refusal_accuracy",
            "not_found_accuracy",
            "clarification_accuracy",
        ]
        has_actionable_failure = any(
            row.get(metric) is not None and row.get(metric) < 1.0
            for metric in actionable_metrics
        )
        if row.get("hallucination_rate") is not None and row["hallucination_rate"] > 0.0:
            has_actionable_failure = True
        if (
            expected_behavior in {"answer", "answer_with_memory"}
            and not is_memory_behavior_diagnostic
            and (
                (row.get("all_sources_hit") is not None and row.get("all_sources_hit") < 1.0)
                or (row.get("expected_source_recall") is not None and row.get("expected_source_recall") < 1.0)
            )
        ):
            has_actionable_failure = True

        if is_memory_behavior_diagnostic:
            breakdown["memory_response_type_diagnostic"]["ids"].append(question_id)
        if is_clarification_source_diagnostic:
            breakdown["clarification_source_coverage_diagnostic"]["ids"].append(question_id)
        if has_actionable_failure and not is_clarification_source_diagnostic:
            breakdown["actionable"]["ids"].append(question_id)

    for item in breakdown.values():
        item["ids"] = sorted(set(item["ids"]))
        item["count"] = len(item["ids"])
    return breakdown


def _diagnostic_submetric_note_count(breakdown: dict[str, dict[str, Any]]) -> int:
    diagnostic_ids: set[str] = set()
    for key, value in breakdown.items():
        if key == "actionable":
            continue
        diagnostic_ids.update(value.get("ids") or [])
    return len(diagnostic_ids)


def _citation_failure_counts(failed_questions: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in failed_questions:
        for category in item.get("citation_failure_categories") or []:
            counts[str(category)] += 1
    return dict(sorted(counts.items()))


def _chunk_from_payload(item: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(item.get("chunk_id") or ""),
        document_id=str(item.get("document_id") or ""),
        document_title=str(item.get("document_title") or ""),
        section_heading=str(item.get("section_heading") or ""),
        content=str(item.get("content") or item.get("content_preview") or ""),
        access_roles=list(item.get("access_roles") or []),
        restricted=bool(item.get("restricted")),
        sensitivity=str(item.get("sensitivity") or "internal"),
        rank=int(item.get("rank") or 0),
        score=float(item.get("score") or 0.0),
        project_id=item.get("project_id"),
        department_id=item.get("department_id"),
        vector_score=item.get("vector_score"),
        keyword_score=item.get("keyword_score"),
        hybrid_score=item.get("hybrid_score"),
        retrieval_source=str(item.get("retrieval_source") or "api-query"),
    )


def _session_for_question(question: dict[str, Any]) -> str | None:
    previous_turns = question.get("previous_turns") or []
    if not previous_turns:
        return None
    session_id = create_session(question["user_role"], user_id=None)
    for turn in previous_turns:
        add_message(
            session_id=session_id,
            role=turn["role"],
            content=turn["content"],
        )
    return session_id


def _query_payload(question: dict[str, Any], args: argparse.Namespace, session_id: str | None) -> dict[str, Any]:
    return {
        "question": question["question"],
        "user_role": question["user_role"],
        "session_id": session_id,
        "retrieval_mode": args.retrieval_mode,
        "top_k": args.top_k,
        "prompt_version": args.prompt_version,
        "multi_doc_mode": args.multi_doc_mode,
        "evaluation_excluded_document_prefixes": EVALUATION_EXCLUDED_DOCUMENT_PREFIXES,
    }


def _run_query(client: TestClient, question: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    session_id = _session_for_question(question)
    started = time.perf_counter()
    response = client.post(
        "/query",
        headers={DEMO_USER_HEADER: ADMIN_USER_ID},
        json=_query_payload(question, args, session_id),
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    response.raise_for_status()
    return response.json(), latency_ms


def _row(question: dict[str, Any], response: dict[str, Any], latency_ms: int, top_k: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    chunks = [_chunk_from_payload(item) for item in response.get("retrieved_chunks") or []]
    expected_docs = _expected_docs(question)
    answer_result = {
        "response_type": response["response_type"],
        "behavior": response["behavior"],
        "answer": response["answer"],
        "citations": response.get("citations") or [],
        "citation_confidence": response.get("citation_confidence"),
        "answer_confidence": response.get("answer_confidence"),
        "final_confidence": response.get("final_confidence"),
        "supported_claims": response.get("supported_claims") or [],
        "unsupported_claims": response.get("unsupported_claims") or [],
        "retrieved_chunks": response.get("retrieved_chunks") or [],
        "retrieved_chunks_raw": chunks,
    }
    scores = score_answer(question, answer_result)
    row_for_scoring = {
        "question_id": question["question_id"],
        "question": question["question"],
        "question_type": question["question_type"],
        "expected_behavior": question["expected_behavior"],
        "response_type": response["response_type"],
        "behavior": response["behavior"],
        "answer": response["answer"],
        "citations": response.get("citations") or [],
        "retrieved_chunks": response.get("retrieved_chunks") or [],
        "retrieved_chunks_raw": chunks,
        "any_source_hit": any_source_hit(expected_docs, chunks),
        "all_sources_hit": all_sources_hit(expected_docs, chunks),
        "expected_source_recall": expected_source_recall(expected_docs, chunks),
        "precision_at_k": precision_at_k(expected_docs, chunks, top_k),
        "mrr": reciprocal_rank(expected_docs, chunks),
        "latency_ms": latency_ms,
        "citation_confidence": response.get("citation_confidence"),
        "answer_confidence": response.get("answer_confidence"),
        "final_confidence": response.get("final_confidence"),
        "input_tokens": response.get("input_tokens"),
        "output_tokens": response.get("output_tokens"),
        "input_cost_usd": response.get("input_cost_usd"),
        "output_cost_usd": response.get("output_cost_usd"),
        "estimated_cost_usd": response.get("estimated_cost_usd"),
        "pricing_status": response.get("pricing_status"),
        "prompt_version": response.get("prompt_version"),
        "model": response.get("model"),
        "temperature": response.get("temperature"),
        "multi_doc_used": response.get("multi_doc_used"),
        "multi_doc_mode": response.get("multi_doc_mode"),
        "original_question": response.get("memory", {}).get("original_question"),
        "rewritten_question": response.get("memory", {}).get("rewritten_question"),
        "is_followup": response.get("memory", {}).get("is_followup"),
        "memory_used": response.get("memory", {}).get("memory_used"),
        "rewrite_strategy": response.get("memory", {}).get("rewrite_strategy"),
        "permission_check": response.get("permission_check"),
        **scores,
    }
    failed_item = failed_question_item(question, row_for_scoring, scores)
    row = {key: value for key, value in row_for_scoring.items() if key != "retrieved_chunks_raw"}
    return row, failed_item


def _summary(
    *,
    rows: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    benchmark: dict[str, Any],
    args: argparse.Namespace,
    started_at: str,
) -> dict[str, Any]:
    submetric_issue_ids = _submetric_issue_ids(rows)
    submetric_issue_breakdown = _submetric_issue_breakdown(rows)
    return {
        "experiment_id": RUN_ID,
        "run_name": "live-query-answer-quality-v8",
        "phase": "phase-39",
        "prompt_name": "answer_generation",
        "prompt_version": args.prompt_version,
        "model": next((row.get("model") for row in rows if row.get("model")), None),
        "retrieval_mode": args.retrieval_mode,
        "chunking_strategy": "section_based",
        "top_k": args.top_k,
        "multi_doc_mode": args.multi_doc_mode,
        "evaluation_excluded_document_prefixes": EVALUATION_EXCLUDED_DOCUMENT_PREFIXES,
        "question_filter": args.question_filter,
        "question_count": len(rows),
        "source_question_count": benchmark.get("question_count"),
        "failed_question_count": len(failed),
        "submetric_issue_count": len(submetric_issue_ids),
        "submetric_issue_ids": submetric_issue_ids,
        "submetric_issue_breakdown": submetric_issue_breakdown,
        "actionable_submetric_issue_count": submetric_issue_breakdown["actionable"]["count"],
        "diagnostic_submetric_note_count": _diagnostic_submetric_note_count(submetric_issue_breakdown),
        "any_source_hit": _average([row["any_source_hit"] for row in rows]),
        "all_sources_hit": _average([row["all_sources_hit"] for row in rows]),
        "expected_source_recall": _average([row["expected_source_recall"] for row in rows]),
        "precision_at_k": _average([row["precision_at_k"] for row in rows]),
        "mrr": _average([row["mrr"] for row in rows]),
        "answer_accuracy": _average([row["answer_accuracy"] for row in rows]),
        "citation_accuracy": _average([row["citation_accuracy"] for row in rows]),
        "faithfulness": _average([row["faithfulness"] for row in rows]),
        "hallucination_rate": _average([row["hallucination_rate"] for row in rows]),
        "response_type_accuracy": _average([row["response_type_accuracy"] for row in rows]),
        "refusal_accuracy": _average([row["refusal_accuracy"] for row in rows]),
        "not_found_accuracy": _average([row["not_found_accuracy"] for row in rows]),
        "clarification_accuracy": _average([row["clarification_accuracy"] for row in rows]),
        "final_confidence": _average([row["final_confidence"] for row in rows]),
        "input_tokens": _sum([row.get("input_tokens") for row in rows]),
        "output_tokens": _sum([row.get("output_tokens") for row in rows]),
        "estimated_cost": _sum_cost([row.get("estimated_cost_usd") for row in rows]),
        "pricing_status": "estimated",
        "started_at": started_at,
    }


def _dashboard_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    failed_question_ids = [item["question_id"] for item in result.get("failed_questions", [])]
    return {
        "run_id": summary["experiment_id"],
        "run_name": summary["run_name"],
        "phase": summary["phase"],
        "run_type": "live_query_eval",
        "timestamp": result["generated_at"],
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
        "prompt_name": summary["prompt_name"],
        "prompt_version": summary["prompt_version"],
        "multi_doc_mode": summary["multi_doc_mode"],
        "evaluation_excluded_document_prefixes": summary.get("evaluation_excluded_document_prefixes") or [],
        "model": summary["model"],
        "total_questions": summary["question_count"],
        "source_question_count": summary["source_question_count"],
        "question_filter": summary["question_filter"],
        "metrics": {
            "any_source_hit": summary.get("any_source_hit"),
            "all_sources_hit": summary.get("all_sources_hit"),
            "expected_source_recall": summary.get("expected_source_recall"),
            "precision_at_k": summary.get("precision_at_k"),
            "mrr": summary.get("mrr"),
            "answer_accuracy": summary.get("answer_accuracy"),
            "citation_accuracy": summary.get("citation_accuracy"),
            "faithfulness": summary.get("faithfulness"),
            "hallucination_rate": summary.get("hallucination_rate"),
            "response_type_accuracy": summary.get("response_type_accuracy"),
            "refusal_accuracy": summary.get("refusal_accuracy"),
            "not_found_accuracy": summary.get("not_found_accuracy"),
            "clarification_accuracy": summary.get("clarification_accuracy"),
            "final_confidence": summary.get("final_confidence"),
            "input_tokens": summary.get("input_tokens"),
            "output_tokens": summary.get("output_tokens"),
            "estimated_cost": summary.get("estimated_cost"),
            "failed_question_count": summary.get("failed_question_count"),
            "submetric_issue_count": summary.get("submetric_issue_count"),
            "actionable_submetric_issue_count": summary.get("actionable_submetric_issue_count"),
            "diagnostic_submetric_note_count": summary.get("diagnostic_submetric_note_count"),
        },
        "failed_questions": failed_question_ids,
        "submetric_issue_ids": summary.get("submetric_issue_ids") or [],
        "submetric_issue_breakdown": summary.get("submetric_issue_breakdown") or {},
        "category_breakdown": _category_breakdown(result.get("rows") or []),
        "failure_reason_counts": _failure_reason_counts(result.get("failed_questions") or []),
        "citation_failure_category_counts": _citation_failure_counts(result.get("failed_questions") or []),
        "notes": (
            "Phase 39 live /query answer-quality evaluation over benchmark v1.1. Exercises API query orchestration, "
            "memory session loading, auto multi-document detection, permission-filtered retrieval, generation, "
            "citation validation, and the API response payload. Uploaded-document fixtures are excluded from this "
            "benchmark run before generation. Expected answers, expected behavior, expected sources, prompts, and "
            "retrieval ranking logic are unchanged."
        ),
        "sample_size": summary["question_count"],
        "passed_count": summary["question_count"] - len(failed_question_ids),
        "failed_count": len(failed_question_ids),
        "benchmark_version": result["benchmark_version"],
        "run_timestamp": result["generated_at"],
    }


def _write_report(result: dict[str, Any], dashboard_run: dict[str, Any]) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    metrics = dashboard_run["metrics"]
    failures = result.get("failed_questions") or []
    lines = [
        "# Phase 39 Live Query Answer-Quality Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Candidate",
        "",
        f"- Run ID: `{dashboard_run['run_id']}`",
        f"- Questions: `{dashboard_run['total_questions']}`",
        f"- Benchmark version: `{dashboard_run['benchmark_version']}`",
        f"- Retrieval mode: `{dashboard_run['retrieval_mode']}`",
        f"- Top K: `{dashboard_run['top_k']}`",
        f"- Prompt version: `{dashboard_run['prompt_version']}`",
        f"- Multi-doc mode: `{dashboard_run['multi_doc_mode']}`",
        f"- Excluded document prefixes: `{', '.join(dashboard_run.get('evaluation_excluded_document_prefixes') or []) or 'None'}`",
        f"- Estimated chat cost: `{metrics.get('estimated_cost')}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for metric in [
        "answer_accuracy",
        "citation_accuracy",
        "faithfulness",
        "hallucination_rate",
        "response_type_accuracy",
        "refusal_accuracy",
        "not_found_accuracy",
        "clarification_accuracy",
        "failed_question_count",
        "submetric_issue_count",
        "actionable_submetric_issue_count",
        "diagnostic_submetric_note_count",
        "estimated_cost",
    ]:
        lines.append(f"| {metric} | `{metrics.get(metric)}` |")
    lines.extend(
        [
            "",
            "## Failed Questions",
            "",
            f"- Failed count: `{dashboard_run['failed_count']}`",
            f"- Failed IDs: `{', '.join(dashboard_run.get('failed_questions') or []) or 'None'}`",
            f"- Failure buckets: `{json.dumps(_failure_reason_counts(failures), sort_keys=True)}`",
            f"- Submetric issue count: `{metrics.get('submetric_issue_count')}`",
            f"- Actionable submetric issue count: `{metrics.get('actionable_submetric_issue_count')}`",
            f"- Diagnostic submetric note count: `{metrics.get('diagnostic_submetric_note_count')}`",
            f"- Submetric issue IDs: `{', '.join(dashboard_run.get('submetric_issue_ids') or []) or 'None'}`",
            f"- Submetric issue breakdown: `{json.dumps(dashboard_run.get('submetric_issue_breakdown') or {}, sort_keys=True)}`",
            "",
            "## Notes",
            "",
            "- This runner calls `POST /query` instead of the prompt-experiment retrieval/generation helper.",
            "- Permission filtering happens inside the normal API retrieval path before generation.",
            "- Uploaded-document fixtures are excluded from benchmark retrieval before generation.",
            "- Memory benchmark rows are represented as local eval sessions with their previous turns inserted before the live query.",
            "- Memory `answer_with_memory` response-type half-credit is retained for historical comparability but reported as a diagnostic note when answer and citation behavior are otherwise correct.",
            "- Correct clarification responses with incomplete source coverage are reported as diagnostic notes instead of answer/citation failures.",
            "- Benchmark expected answers, expected behavior, and expected sources were not changed.",
        ]
    )
    _write_text_atomic(REPORT_PATH, "\n".join(lines) + "\n")


def run_live_query_eval(args: argparse.Namespace) -> dict[str, Any]:
    benchmark = _load_benchmark()
    questions = _questions(benchmark, args.question_filter)
    client = TestClient(app)
    rows: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    started_at = datetime.now(UTC).isoformat()
    cumulative_cost = 0.0

    for index, question in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] {question['question_id']} /query", flush=True)
        response, latency_ms = _run_query(client, question, args)
        row, failed_item = _row(question, response, latency_ms, args.top_k)
        rows.append(row)
        if failed_item:
            failed.append(failed_item)
        if row.get("estimated_cost_usd") is not None:
            cumulative_cost += float(row["estimated_cost_usd"])
        if args.budget_usd is not None and cumulative_cost >= args.budget_usd:
            raise RuntimeError(
                f"Experiment budget stop reached: ${cumulative_cost:.6f} >= ${args.budget_usd:.2f}."
            )
        print(
            f"  response={row['response_type']} answer_acc={row['answer_accuracy']} "
            f"citation_acc={row['citation_accuracy']} multi_doc={row['multi_doc_used']}",
            flush=True,
        )

    summary = _summary(
        rows=rows,
        failed=failed,
        benchmark=benchmark,
        args=args,
        started_at=started_at,
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark_version": benchmark.get("benchmark_version") or "not available",
        "config": {
            "run_id": RUN_ID,
            "retrieval_mode": args.retrieval_mode,
            "top_k": args.top_k,
            "prompt_version": args.prompt_version,
            "multi_doc_mode": args.multi_doc_mode,
            "question_filter": args.question_filter,
        },
        "summary": summary,
        "rows": rows,
        "failed_questions": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 39 full answer-quality through POST /query.")
    parser.add_argument("--prompt-version", default="v8")
    parser.add_argument("--retrieval-mode", default="vector_lexical_rerank", choices=["vector_lexical_rerank", "vector_only"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--multi-doc-mode", default="auto", choices=["auto", "off", "force"])
    parser.add_argument("--question-filter", default="all")
    parser.add_argument("--budget-usd", type=float, default=2.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Confirm explicit approval to send benchmark questions and source snippets to external AI APIs.",
    )
    args = parser.parse_args()
    benchmark = _load_benchmark()
    questions = _questions(benchmark, args.question_filter)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_id": RUN_ID,
                    "question_count": len(questions),
                    "benchmark_version": benchmark.get("benchmark_version"),
                    "config": {
                        "retrieval_mode": args.retrieval_mode,
                        "top_k": args.top_k,
                        "prompt_version": args.prompt_version,
                        "multi_doc_mode": args.multi_doc_mode,
                        "question_filter": args.question_filter,
                    },
                    "would_write": [str(OUTPUT_JSON), str(EVAL_RUN_JSON), str(REPORT_PATH)],
                    "external_ai_required": True,
                },
                indent=2,
            )
        )
        return
    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_RUN_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    result = run_live_query_eval(args)
    dashboard_run = _dashboard_run(result)
    _write_text_atomic(OUTPUT_JSON, json.dumps({**result, "dashboard_run": dashboard_run}, indent=2))
    _write_text_atomic(EVAL_RUN_JSON, json.dumps(dashboard_run, indent=2))
    _write_report(result, dashboard_run)

    print(json.dumps({"summary": result["summary"], "dashboard_run": dashboard_run}, indent=2))
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {EVAL_RUN_JSON}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
