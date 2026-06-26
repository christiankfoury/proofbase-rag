from datetime import UTC, datetime
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.configs import phase6_retrieval_configs
from apps.api.app.evaluation.run_benchmark import run_benchmark


REPORT_PATH = Path("docs/phase-6/evaluation-results.md")
EXTERNAL_EMBEDDINGS_APPROVAL_MESSAGE = (
    "The legacy retrieval experiments call external OpenAI embeddings for each benchmark query. "
    "Re-run with --allow-external-embeddings only after explicit approval."
)


def _requires_external_embeddings_approval(
    *,
    dry_run: bool,
    allow_external_embeddings: bool,
    allow_external_ai: bool,
) -> bool:
    return not dry_run and not (allow_external_embeddings or allow_external_ai)


def _metric_tuple(result: dict) -> tuple[float, float, float, float]:
    return (
        result["all_sources_hit"] if result["all_sources_hit"] is not None else -1.0,
        result["expected_source_recall"] if result["expected_source_recall"] is not None else -1.0,
        result["mrr"] if result["mrr"] is not None else -1.0,
        result["precision_at_k"] if result["precision_at_k"] is not None else -1.0,
    )


def _answerable_results(summary: dict) -> dict[str, dict]:
    return {
        result["question_id"]: result
        for result in summary["results"]
        if result["all_sources_hit"] is not None
    }


def _compare_runs(baseline: dict, candidate: dict) -> tuple[list[str], list[str], list[str]]:
    baseline_results = _answerable_results(baseline)
    candidate_results = _answerable_results(candidate)
    improved: list[str] = []
    regressed: list[str] = []
    unchanged: list[str] = []

    for question_id, baseline_result in baseline_results.items():
        candidate_result = candidate_results.get(question_id)
        if not candidate_result:
            continue
        baseline_score = _metric_tuple(baseline_result)
        candidate_score = _metric_tuple(candidate_result)
        if candidate_score > baseline_score:
            improved.append(question_id)
        elif candidate_score < baseline_score:
            regressed.append(question_id)
        else:
            unchanged.append(question_id)

    return improved, regressed, unchanged


def _failed_questions(summary: dict) -> list[str]:
    failed = []
    for result in _answerable_results(summary).values():
        if result["all_sources_hit"] != 1.0:
            failed.append(result["question_id"])
    return failed


def _write_report(summaries: list[dict]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    by_name = {summary["run_name"]: summary for summary in summaries}
    baseline = by_name["vector-section"]
    hybrid = by_name["hybrid-section-0.5"]
    improved, regressed, unchanged = _compare_runs(baseline, hybrid)

    lines = [
        "# Phase 6 Evaluation Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Configurations Tested",
        "",
        "| Run | Mode | Chunking | Top K | Vector Weight | Keyword Weight |",
        "|---|---|---|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append(
            "| {run_name} | {retrieval_mode} | {chunking_strategy} | {top_k} | {vector_weight} | {keyword_weight} |".format(
                **summary
            )
        )

    lines.extend(
        [
            "",
            "## Retrieval Metrics",
            "",
            "| Run | Any Source | All Sources | Source Recall | Precision@k | MRR | Avg Latency ms | Failed Questions |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for summary in summaries:
        failed = ", ".join(_failed_questions(summary)) or "None"
        lines.append(
            "| {run_name} | {any_source_hit} | {all_sources_hit} | {expected_source_recall} | {precision_at_k} | {mrr} | {average_latency_ms} | {failed} |".format(
                failed=failed,
                **summary,
            )
        )

    lines.extend(
        [
            "",
            "## Hybrid vs Vector Baseline",
            "",
            f"- Baseline: `vector-section`",
            f"- Candidate: `hybrid-section-0.5`",
            f"- Improved questions: {', '.join(improved) if improved else 'None'}",
            f"- Regressed questions: {', '.join(regressed) if regressed else 'None'}",
            f"- Unchanged answerable questions: {len(unchanged)}",
            "",
            "A question is considered improved when all-sources hit, source recall, MRR, or Precision@k improves in that order. It is considered regressed when the same ordered metric tuple gets worse.",
            "",
            "## Pending Metrics",
            "",
            "- Answer accuracy: pending human or judge evaluation.",
            "- Faithfulness: pending human or judge evaluation.",
            "- Hallucination rate: pending human or judge evaluation.",
            "- Token usage and cost: pending model-call instrumentation.",
            "",
            "## Notes",
            "",
            "- These are retrieval-only runs to avoid unnecessary chat-completion cost.",
            "- Permission-restricted and missing-information questions are excluded from retrieval averages because they have no expected retrievable source for the requesting role.",
            "- Azure AI Search, reranking, and semantic chunking remain deferred.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the legacy Phase 6 retrieval experiments.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-embeddings",
        action="store_true",
        help="Confirm explicit approval to send benchmark questions to external embedding APIs.",
    )
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Alias for --allow-external-embeddings for consistency with answer-generating evaluators.",
    )
    args = parser.parse_args()
    configs = phase6_retrieval_configs()
    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_count": len(configs),
                    "configs": [config.__dict__ for config in configs],
                    "would_write": [str(REPORT_PATH)],
                    "external_embeddings_required": True,
                },
                indent=2,
            )
        )
        return
    if _requires_external_embeddings_approval(
        dry_run=args.dry_run,
        allow_external_embeddings=args.allow_external_embeddings,
        allow_external_ai=args.allow_external_ai,
    ):
        raise SystemExit(EXTERNAL_EMBEDDINGS_APPROVAL_MESSAGE)
    summaries = []
    for config in configs:
        print(f"Running {config.run_name}...")
        summary = run_benchmark(
            retrieval_only=True,
            config=config,
            write_report=False,
            include_results=True,
        )
        summaries.append(summary)
        print(
            f"  any={summary['any_source_hit']} all={summary['all_sources_hit']} "
            f"recall={summary['expected_source_recall']} precision={summary['precision_at_k']} "
            f"mrr={summary['mrr']} latency_ms={summary['average_latency_ms']}"
        )
    _write_report(summaries)
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
