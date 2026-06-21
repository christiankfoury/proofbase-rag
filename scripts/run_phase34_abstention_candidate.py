from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.experiments.config import ExperimentConfig, prompt_experiment_config
from apps.api.app.experiments.runner import run_prompt_experiment


OUTPUT_DIR = ROOT / "data/evaluation/expanded-baseline"
EVAL_RUN_DIR = ROOT / "data/evaluation/eval-runs"
PHASE_DIR = ROOT / "docs/phase-34"
OUTPUT_JSON = OUTPUT_DIR / "phase34-answer-grounding-v6.json"
EVAL_RUN_JSON = EVAL_RUN_DIR / "phase34-answer-grounding-v6.json"
REPORT_PATH = PHASE_DIR / "answer-grounding-results.md"
BASELINE_RUN_PATH = EVAL_RUN_DIR / "phase32-expanded-answer-generation-v5.json"
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The Phase 34 answer-grounding run sends benchmark questions and retrieved source snippets to external "
    "OpenAI embeddings and chat-completion APIs. Re-run with --allow-external-ai only after explicit approval."
)


def _metric(summary: dict[str, Any], key: str) -> Any:
    return summary.get("metrics", {}).get(key) if "metrics" in summary else summary.get(key)


def _dashboard_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    failed_question_ids = [item["question_id"] for item in result.get("failed_questions", [])]
    return {
        "run_id": summary["experiment_id"],
        "run_name": summary["run_name"],
        "phase": "phase-34",
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
        "notes": (
            "Phase 34 grounded-abstention candidate over benchmark v1.1. Uses answer_generation v6 with "
            "sentence-aware citation validation and the Phase 33 vector_lexical_rerank retrieval candidate."
        ),
        "sample_size": summary["question_count"],
        "passed_count": summary["question_count"] - len(failed_question_ids),
        "failed_count": len(failed_question_ids),
        "benchmark_version": "1.1",
        "run_timestamp": result["generated_at"],
    }


def _category_breakdown(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        question_type = row.get("question_type")
        if question_type:
            counts[str(question_type)] = counts.get(str(question_type), 0) + 1
    return dict(sorted(counts.items()))


def _write_report(result: dict[str, Any], dashboard_run: dict[str, Any]) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(BASELINE_RUN_PATH.read_text(encoding="utf-8")) if BASELINE_RUN_PATH.exists() else {}
    current_metrics = dashboard_run["metrics"]
    baseline_metrics = baseline.get("metrics", {})
    lines = [
        "# Phase 34 Answer Grounding Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Candidate",
        "",
        f"- Run ID: `{dashboard_run['run_id']}`",
        f"- Questions: `{dashboard_run['total_questions']}`",
        f"- Retrieval mode: `{dashboard_run['retrieval_mode']}`",
        f"- Top K: `{dashboard_run['top_k']}`",
        f"- Reranker: `{dashboard_run.get('reranker')}`",
        f"- Rerank candidate limit: `{dashboard_run.get('rerank_candidate_limit')}`",
        f"- Prompt version: `{dashboard_run['prompt_version']}`",
        f"- Model: `{dashboard_run['model']}`",
        "",
        "## Before / After",
        "",
        "| Metric | Phase 32 Baseline | Phase 34 Candidate |",
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
        lines.append(f"| {metric} | `{baseline_metrics.get(metric)}` | `{current_metrics.get(metric)}` |")
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
            "- This run uses external embeddings and chat completions.",
            "- Chat cost is estimated from configured model pricing and excludes embedding and infrastructure cost.",
            "- Permission filtering still happens before generation through the retrieval layer.",
            "- The target is hallucination rate <= `0.08` without answer-accuracy regression.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _config(args: argparse.Namespace) -> ExperimentConfig:
    base = prompt_experiment_config(args.prompt_version)
    return ExperimentConfig(
        experiment_id="phase34-answer-grounding-v6",
        run_name="answer-grounding-v6",
        phase="phase-34",
        retrieval_mode=args.retrieval_mode,
        chunking_strategy="section_based",
        top_k=args.top_k,
        reranker="lexical" if args.retrieval_mode == "vector_lexical_rerank" else None,
        rerank_candidate_limit=args.rerank_candidate_limit,
        prompt_name=base.prompt_name,
        prompt_version=base.prompt_version,
        model=base.model,
        temperature=base.temperature,
        notes="Phase 34 grounded abstention candidate.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 34 grounded-abstention answer candidate.")
    parser.add_argument("--prompt-version", default="v6")
    parser.add_argument("--retrieval-mode", default="vector_lexical_rerank", choices=["vector_lexical_rerank", "vector_only"])
    parser.add_argument("--top-k", type=int, default=3)
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
