from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.experiments.config import ExperimentConfig, prompt_experiment_config
from apps.api.app.experiments.runner import run_prompt_experiment


OUTPUT_DIR = ROOT / "data/evaluation/expanded-baseline"
EVAL_RUN_DIR = ROOT / "data/evaluation/eval-runs"
PHASE_DIR = ROOT / "docs/phase-38"
OUTPUT_JSON = OUTPUT_DIR / "phase38-answer-quality-remediation-v8.json"
EVAL_RUN_JSON = EVAL_RUN_DIR / "phase38-answer-quality-remediation-v8.json"
REPORT_PATH = PHASE_DIR / "answer-quality-remediation-results.md"
BASELINE_RUN_PATH = EVAL_RUN_DIR / "phase35-citation-alignment-v7.json"
BASELINE_DETAIL_PATH = OUTPUT_DIR / "phase35-citation-alignment-v7.json"
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The Phase 38 answer-quality run sends benchmark questions and retrieved synthetic source snippets to "
    "external OpenAI embeddings and chat-completion APIs. Re-run with --allow-external-ai only after explicit approval."
)


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


def _citation_failure_counts(failed_questions: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in failed_questions:
        for category in item.get("citation_failure_categories") or []:
            counts[str(category)] += 1
    return dict(sorted(counts.items()))


def _dashboard_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    failed_question_ids = [item["question_id"] for item in result.get("failed_questions", [])]
    return {
        "run_id": summary["experiment_id"],
        "run_name": summary["run_name"],
        "phase": "phase-38",
        "run_type": "prompt_experiment",
        "timestamp": result["generated_at"],
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
        "reranker": result["config"].get("reranker"),
        "rerank_candidate_limit": result["config"].get("rerank_candidate_limit"),
        "prompt_version": summary["prompt_version"],
        "model": summary["model"],
        "total_questions": summary["question_count"],
        "source_question_count": summary["source_question_count"],
        "question_filter": summary["question_filter"],
        "metrics": {
            "any_source_hit": summary.get("any_source_hit"),
            "all_sources_hit": summary.get("all_sources_hit"),
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
        },
        "failed_questions": failed_question_ids,
        "category_breakdown": _category_breakdown(result.get("rows") or []),
        "failure_reason_counts": _failure_reason_counts(result.get("failed_questions") or []),
        "citation_failure_category_counts": _citation_failure_counts(result.get("failed_questions") or []),
        "notes": (
            "Phase 38 answer-quality remediation over benchmark v1.1. Uses answer_generation v8, "
            "memory-aware prompt-experiment retrieval, targeted ambiguity guards, and adversarial source-content handling. "
            "Expected answers, expected behavior, and expected sources are unchanged."
        ),
        "sample_size": summary["question_count"],
        "passed_count": summary["question_count"] - len(failed_question_ids),
        "failed_count": len(failed_question_ids),
        "benchmark_version": "1.1",
        "run_timestamp": result["generated_at"],
    }


def _metric(metrics: dict[str, Any], key: str) -> Any:
    return metrics.get(key)


def _write_report(result: dict[str, Any], dashboard_run: dict[str, Any]) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_run = json.loads(BASELINE_RUN_PATH.read_text(encoding="utf-8")) if BASELINE_RUN_PATH.exists() else {}
    baseline_detail = json.loads(BASELINE_DETAIL_PATH.read_text(encoding="utf-8")) if BASELINE_DETAIL_PATH.exists() else {}
    baseline_metrics = baseline_run.get("metrics", {})
    current_metrics = dashboard_run["metrics"]
    baseline_failures = baseline_detail.get("failed_questions") or []
    current_failures = result.get("failed_questions") or []
    baseline_failure_counts = _failure_reason_counts(baseline_failures)
    current_failure_counts = _failure_reason_counts(current_failures)
    all_failure_types = sorted(set(baseline_failure_counts) | set(current_failure_counts))
    lines = [
        "# Phase 38 Answer-Quality Remediation Results",
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
        f"- Reranker: `{dashboard_run.get('reranker')}`",
        f"- Rerank candidate limit: `{dashboard_run.get('rerank_candidate_limit')}`",
        f"- Prompt version: `{dashboard_run['prompt_version']}`",
        f"- Model: `{dashboard_run['model']}`",
        f"- Estimated chat cost: `{current_metrics.get('estimated_cost')}`",
        "",
        "## Before / After",
        "",
        "| Metric | Phase 35 Current | Phase 38 Candidate |",
        "|---|---:|---:|",
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
        "estimated_cost",
    ]:
        lines.append(f"| {metric} | `{_metric(baseline_metrics, metric)}` | `{_metric(current_metrics, metric)}` |")
    lines.extend(
        [
            "",
            "## Failure Buckets",
            "",
            "| Failure type | Phase 35 Current | Phase 38 Candidate |",
            "|---|---:|---:|",
        ]
    )
    for failure_type in all_failure_types:
        lines.append(
            f"| {failure_type} | `{baseline_failure_counts.get(failure_type, 0)}` | `{current_failure_counts.get(failure_type, 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Failed Questions",
            "",
            f"- Failed count: `{dashboard_run['failed_count']}`",
            f"- Failed IDs: `{', '.join(dashboard_run.get('failed_questions') or []) or 'None'}`",
            "",
            "## Notes",
            "",
            "- Benchmark expected answers, expected behavior, and expected sources were not changed.",
            "- Permission filtering still happens before generation and before citation validation/backfill.",
            "- Phase 39 still owns deeper multi-document orchestration and generalized ambiguity planning.",
            "- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _config(args: argparse.Namespace) -> ExperimentConfig:
    base = prompt_experiment_config(args.prompt_version)
    return ExperimentConfig(
        experiment_id="phase38-answer-quality-remediation-v8",
        run_name="answer-quality-remediation-v8",
        phase="phase-38",
        retrieval_mode=args.retrieval_mode,
        chunking_strategy="section_based",
        top_k=args.top_k,
        reranker="lexical" if args.retrieval_mode == "vector_lexical_rerank" else None,
        rerank_candidate_limit=args.rerank_candidate_limit,
        prompt_name=base.prompt_name,
        prompt_version=base.prompt_version,
        model=base.model,
        temperature=base.temperature,
        notes="Phase 38 answer-quality remediation candidate.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 38 answer-quality remediation candidate.")
    parser.add_argument("--prompt-version", default="v8")
    parser.add_argument("--retrieval-mode", default="vector_lexical_rerank", choices=["vector_lexical_rerank", "vector_only"])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rerank-candidate-limit", type=int, default=20)
    parser.add_argument("--budget-usd", type=float, default=2.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Confirm explicit approval to send benchmark questions and retrieved snippets to external AI APIs.",
    )
    args = parser.parse_args()
    config = _config(args)

    if args.dry_run:
        print(json.dumps({"config": config.to_dict(), "would_write": [str(OUTPUT_JSON), str(EVAL_RUN_JSON), str(REPORT_PATH)]}, indent=2))
        return
    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_RUN_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)

    result = run_prompt_experiment(config, question_filter="all", budget_usd=args.budget_usd)
    dashboard_run = _dashboard_run(result)
    OUTPUT_JSON.write_text(json.dumps({**result, "dashboard_run": dashboard_run}, indent=2), encoding="utf-8")
    EVAL_RUN_JSON.write_text(json.dumps(dashboard_run, indent=2), encoding="utf-8")
    _write_report(result, dashboard_run)

    print(json.dumps({"summary": result["summary"], "dashboard_run": dashboard_run}, indent=2))
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {EVAL_RUN_JSON}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
