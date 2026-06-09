from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FAILED_PATH = ROOT / "data/evaluation/failed-questions/failed-questions.json"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
PROMPT_RUN_PATH = ROOT / "data/evaluation/prompt-experiments/phase11-answer-generation-v1.json"
V5_FOCUSED_RUN_PATH = ROOT / "data/evaluation/prompt-experiments/phase11-answer-generation-v5-failed-subset.json"
V5_FULL_RUN_PATH = ROOT / "data/evaluation/prompt-experiments/phase11-answer-generation-v5.json"
SUMMARY_PATH = ROOT / "data/evaluation/failed-questions/failure-cause-summary.json"
REPORT_PATH = ROOT / "docs/phase-17/failed-question-cause-analysis.md"

CAUSE_MAP = {
    "retrieval_miss": "retrieval_miss",
    "wrong_citation": "citation_mismatch",
    "incomplete_answer": "answer_completeness",
    "answer_not_generated": "confidence_threshold_downgrade",
    "multi_document_failure": "multi_doc_synthesis_issue",
    "unsupported_answer": "answer_support_issue",
}

CAUSE_LABELS = {
    "retrieval_miss": "Retrieval miss",
    "citation_mismatch": "Citation mismatch",
    "answer_completeness": "Answer completeness",
    "confidence_threshold_downgrade": "Confidence threshold downgrade",
    "multi_doc_synthesis_issue": "Multi-document synthesis issue",
    "answer_support_issue": "Answer support issue",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_by_id() -> dict[str, dict]:
    benchmark = _load_json(BENCHMARK_PATH)
    return {question["question_id"]: question for question in benchmark["questions"]}


def _prompt_rows_by_id() -> dict[str, dict]:
    if not PROMPT_RUN_PATH.exists():
        return {}
    run = _load_json(PROMPT_RUN_PATH)
    return {row["question_id"]: row for row in run.get("rows", [])}


def _cause_bucket(failure_type: str | None) -> str:
    return CAUSE_MAP.get(failure_type or "", failure_type or "unknown")


def _doc_ids(items: list[dict]) -> list[str]:
    return list(dict.fromkeys(item.get("document_id") for item in items if item.get("document_id")))


def _retrieved_docs(row: dict | None) -> list[str]:
    if not row:
        return []
    return _doc_ids(row.get("retrieved_chunks") or [])


def _citation_docs(row: dict | None, fallback: dict) -> list[str]:
    if row:
        docs = _doc_ids(row.get("citations") or [])
        if docs:
            return docs
    return _doc_ids(fallback.get("actual_citations") or [])


def _enriched_failures() -> list[dict]:
    failed_items = _load_json(FAILED_PATH)
    benchmark = _benchmark_by_id()
    rows = _prompt_rows_by_id()
    enriched = []
    for item in failed_items:
        question_id = item["question_id"]
        question = benchmark.get(question_id, {})
        row = rows.get(question_id)
        cause_bucket = _cause_bucket(item.get("failure_type"))
        enriched.append(
            {
                "phase": item.get("phase"),
                "question_id": question_id,
                "question_type": question.get("question_type"),
                "user_role": question.get("user_role"),
                "question": question.get("question"),
                "expected_behavior": item.get("expected_behavior"),
                "actual_response_type": item.get("actual_response_type"),
                "failure_type": item.get("failure_type"),
                "cause_bucket": cause_bucket,
                "cause_label": CAUSE_LABELS.get(cause_bucket, cause_bucket),
                "expected_source_document": question.get("expected_source_document") or [],
                "actual_citation_documents": _citation_docs(row, item),
                "retrieved_documents": _retrieved_docs(row),
                "answer_accuracy": row.get("answer_accuracy") if row else None,
                "citation_accuracy": row.get("citation_accuracy") if row else None,
                "hallucination_rate": row.get("hallucination_rate") if row else None,
                "citation_confidence": item.get("citation_confidence"),
                "answer_confidence": item.get("answer_confidence"),
                "recommended_fix": item.get("recommended_fix"),
            }
        )
    return enriched


def _summary(enriched: list[dict]) -> dict:
    by_bucket = Counter(item["cause_bucket"] for item in enriched)
    by_failure_type = Counter(item["failure_type"] for item in enriched)
    bucket_items: dict[str, list[str]] = defaultdict(list)
    for item in enriched:
        bucket_items[item["cause_bucket"]].append(item["question_id"])
    largest_bucket = by_bucket.most_common(1)[0][0] if by_bucket else None
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_failed_questions": str(FAILED_PATH.relative_to(ROOT)),
        "joined_prompt_run": str(PROMPT_RUN_PATH.relative_to(ROOT)),
        "failed_question_count": len(enriched),
        "bucket_counts": dict(sorted(by_bucket.items(), key=lambda pair: (-pair[1], pair[0]))),
        "failure_type_counts": dict(sorted(by_failure_type.items(), key=lambda pair: (-pair[1], pair[0]))),
        "largest_bucket": largest_bucket,
        "largest_bucket_label": CAUSE_LABELS.get(largest_bucket or "", largest_bucket),
        "target_question_ids": bucket_items.get(largest_bucket or "", []),
        "prompt_run_results": _prompt_run_results(),
        "failures": enriched,
    }


def _prompt_run_result(path: Path) -> dict | None:
    if not path.exists():
        return None
    run = _load_json(path)
    summary = run.get("summary", {})
    failed = run.get("failed_questions", [])
    by_bucket = Counter(_cause_bucket(item.get("failure_type")) for item in failed)
    return {
        "path": str(path.relative_to(ROOT)),
        "question_filter": summary.get("question_filter"),
        "question_count": summary.get("question_count"),
        "failed_question_count": summary.get("failed_question_count"),
        "answer_accuracy": summary.get("answer_accuracy"),
        "citation_accuracy": summary.get("citation_accuracy"),
        "hallucination_rate": summary.get("hallucination_rate"),
        "response_type_accuracy": summary.get("response_type_accuracy"),
        "estimated_cost": summary.get("estimated_cost"),
        "bucket_counts": dict(sorted(by_bucket.items(), key=lambda pair: (-pair[1], pair[0]))),
        "failed_question_ids": [item.get("question_id") for item in failed],
    }


def _prompt_run_results() -> dict:
    return {
        "v5_failed_subset": _prompt_run_result(V5_FOCUSED_RUN_PATH),
        "v5_full": _prompt_run_result(V5_FULL_RUN_PATH),
    }


def _write_report(summary: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 17 Failed-Question Cause Analysis",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Failed questions analyzed: {summary['failed_question_count']}",
        f"- Largest bucket: {summary['largest_bucket_label']}",
        f"- Target question IDs: {', '.join(summary['target_question_ids']) or 'None'}",
        "",
        "## Bucket Counts",
        "",
        "| Cause Bucket | Count | Question IDs |",
        "|---|---:|---|",
    ]
    failures_by_bucket: dict[str, list[dict]] = defaultdict(list)
    for item in summary["failures"]:
        failures_by_bucket[item["cause_bucket"]].append(item)
    for bucket, count in summary["bucket_counts"].items():
        ids = ", ".join(item["question_id"] for item in failures_by_bucket[bucket])
        lines.append(f"| {CAUSE_LABELS.get(bucket, bucket)} | {count} | {ids} |")

    lines.extend(
        [
            "",
            "## Detailed Failures",
            "",
            "| Question ID | Type | Cause | Expected Sources | Citations | Retrieved Documents | Recommended Fix |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in summary["failures"]:
        lines.append(
            "| {question_id} | {question_type} | {cause_label} | {expected} | {citations} | {retrieved} | {fix} |".format(
                question_id=item["question_id"],
                question_type=item.get("question_type") or "",
                cause_label=item["cause_label"],
                expected=", ".join(item.get("expected_source_document") or []) or "-",
                citations=", ".join(item.get("actual_citation_documents") or []) or "-",
                retrieved=", ".join(item.get("retrieved_documents") or []) or "-",
                fix=item.get("recommended_fix") or "-",
            )
        )

    prompt_results = summary.get("prompt_run_results") or {}
    focused = prompt_results.get("v5_failed_subset")
    full = prompt_results.get("v5_full")
    lines.extend(["", "## V5 Evaluation Results", ""])
    if focused or full:
        lines.extend(
            [
                "| Run | Questions | Failed | Answer Accuracy | Citation Accuracy | Hallucination Rate | Response Type Accuracy | Est. Cost |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for label, result in [("v5 failed subset", focused), ("v5 full benchmark", full)]:
            if not result:
                continue
            lines.append(
                "| {label} | {question_count} | {failed_question_count} | {answer_accuracy} | {citation_accuracy} | {hallucination_rate} | {response_type_accuracy} | {estimated_cost} |".format(
                    label=label,
                    **result,
                )
            )
    else:
        lines.append("V5 evaluation has not been run yet.")

    if full:
        target_before = summary["bucket_counts"].get("answer_support_issue", 0)
        target_after = full["bucket_counts"].get("answer_support_issue", 0)
        lines.extend(
            [
                "",
                f"- Target bucket changed from {target_before} to {target_after} on the full v5 run.",
                f"- Full v5 remaining failed IDs: {', '.join(full['failed_question_ids']) or 'None'}",
            ]
        )

    lines.extend(
        [
            "",
            "## First Fix Target",
            "",
            "The first implementation target is the largest measured bucket. For this run, that means reducing unsupported-answer cases by making the prompt omit weakly supported claims, cite only directly supporting chunks, and prefer partial answers when only part of the expected answer is supported.",
            "",
            "## Regression Gate",
            "",
            "- Run a focused prompt experiment against these failed IDs before a full benchmark.",
            "- Promote the prompt only if the target bucket decreases without increasing permission leakage, not-found failures, or hallucination rate.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    enriched = _enriched_failures()
    summary = _summary(enriched)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_report(summary)
    print(json.dumps({key: summary[key] for key in ["failed_question_count", "bucket_counts", "largest_bucket", "target_question_ids"]}, indent=2))
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
