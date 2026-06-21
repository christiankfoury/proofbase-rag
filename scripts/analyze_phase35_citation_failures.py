from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.citation_failures import CITATION_FAILURE_LABELS, citation_failure_summary


BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
DEFAULT_RUN_PATH = ROOT / "data/evaluation/expanded-baseline/phase34-answer-grounding-v6.json"
OUTPUT_JSON = ROOT / "data/evaluation/phase35-citation-failures.json"
REPORT_PATH = ROOT / "docs/phase-35/citation-failure-analysis.md"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _benchmark_by_id() -> dict[str, dict[str, Any]]:
    benchmark = _load_json(BENCHMARK_PATH)
    return {question["question_id"]: question for question in benchmark.get("questions", [])}


def _doc_ids(items: list[dict[str, Any]]) -> list[str]:
    return list(dict.fromkeys(str(item.get("document_id")) for item in items if item.get("document_id")))


def _analyze(run_path: Path) -> dict[str, Any]:
    run_path = run_path.resolve()
    run = _load_json(run_path)
    questions = _benchmark_by_id()
    failures = []
    category_counts: Counter[str] = Counter()
    for row in run.get("rows") or []:
        question = questions.get(row.get("question_id"))
        if not question:
            continue
        summary = citation_failure_summary(question, row)
        categories = summary["citation_failure_categories"]
        if not categories:
            continue
        for category in categories:
            category_counts[category] += 1
        failures.append(
            {
                "question_id": row.get("question_id"),
                "question_type": row.get("question_type"),
                "expected_sources": question.get("expected_source_document") or [],
                "citation_documents": _doc_ids(row.get("citations") or []),
                "retrieved_documents": _doc_ids(row.get("retrieved_chunks") or []),
                "citation_accuracy": row.get("citation_accuracy"),
                "answer_accuracy": row.get("answer_accuracy"),
                "hallucination_rate": row.get("hallucination_rate"),
                **summary,
            }
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_run": str(run_path.relative_to(ROOT)),
        "run_id": run.get("summary", {}).get("experiment_id"),
        "run_name": run.get("summary", {}).get("run_name"),
        "citation_accuracy": run.get("summary", {}).get("citation_accuracy"),
        "hallucination_rate": run.get("summary", {}).get("hallucination_rate"),
        "failed_question_count": run.get("summary", {}).get("failed_question_count"),
        "citation_failure_question_count": len(failures),
        "category_counts": dict(sorted(category_counts.items())),
        "failures": failures,
    }


def _write_report(summary: dict[str, Any], report_path: Path) -> None:
    failures_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in summary["failures"]:
        for category in item["citation_failure_categories"]:
            failures_by_category[category].append(item)

    lines = [
        "# Phase 35 Citation Failure Analysis",
        "",
        f"Generated at: {summary['generated_at']}",
        f"Source run: `{summary['source_run']}`",
        "",
        "## Summary",
        "",
        f"- Run ID: `{summary.get('run_id')}`",
        f"- Citation accuracy: `{summary.get('citation_accuracy')}`",
        f"- Hallucination rate: `{summary.get('hallucination_rate')}`",
        f"- Citation-failure questions: `{summary['citation_failure_question_count']}`",
        "",
        "## Category Counts",
        "",
        "| Category | Count | Question IDs |",
        "|---|---:|---|",
    ]
    for category, count in summary["category_counts"].items():
        ids = ", ".join(item["question_id"] for item in failures_by_category[category])
        lines.append(f"| {CITATION_FAILURE_LABELS.get(category, category)} | `{count}` | {ids or '-'} |")

    lines.extend(
        [
            "",
            "## Detailed Failures",
            "",
            "| Question ID | Type | Categories | Expected Sources | Citation Documents | Retrieved Documents | Answer | Citation | Hallucination |",
            "|---|---|---|---|---|---|---:|---:|---:|",
        ]
    )
    for item in summary["failures"]:
        labels = [CITATION_FAILURE_LABELS.get(category, category) for category in item["citation_failure_categories"]]
        lines.append(
            "| {question_id} | {question_type} | {categories} | {expected} | {citations} | {retrieved} | `{answer}` | `{citation}` | `{hallucination}` |".format(
                question_id=item["question_id"],
                question_type=item.get("question_type") or "",
                categories=", ".join(labels) or "-",
                expected=", ".join(item.get("expected_sources") or []) or "-",
                citations=", ".join(item.get("citation_documents") or []) or "-",
                retrieved=", ".join(item.get("retrieved_documents") or []) or "-",
                answer=item.get("answer_accuracy"),
                citation=item.get("citation_accuracy"),
                hallucination=item.get("hallucination_rate"),
            )
        )

    lines.extend(
        [
            "",
            "## Reviewer Notes",
            "",
            "- `Citation missing` means at least one expected source document was not cited, or no citations were returned.",
            "- `Wrong document cited` means the answer cited a document outside the expected source set.",
            "- `Right document but wrong chunk` is section-level evidence: the document matches but the cited section differs from the benchmark expected section.",
            "- `Citation attached to unsupported claim` comes from unsupported claims, low citation confidence, or low per-citation support.",
            "- `Citation from restricted source` means a citation points outside the benchmark allowed document set.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Phase 35 citation failure categories for a saved eval run.")
    parser.add_argument("--run-path", default=str(DEFAULT_RUN_PATH))
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--report-path", default=str(REPORT_PATH))
    args = parser.parse_args()

    output_json = Path(args.output_json)
    report_path = Path(args.report_path)
    summary = _analyze(Path(args.run_path))
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_report(summary, report_path)
    print(json.dumps({key: summary[key] for key in ["run_id", "citation_failure_question_count", "category_counts"]}, indent=2))
    print(f"Wrote {output_json}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
