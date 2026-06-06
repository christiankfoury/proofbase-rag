from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.prompt_comparison import (
    best_prompt_summary,
    compare_to_baseline,
    load_prompt_experiment_results,
)
from apps.api.app.costing.estimator import estimate_chat_cost


EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
COMPARISON_PATH = EXPERIMENT_DIR / "prompt-comparison.json"
RESULTS_DOC = ROOT / "docs/phase-11/prompt-experiment-results.md"
REGRESSION_DOC = ROOT / "docs/phase-11/prompt-regression-analysis.md"


def _fmt(value) -> str:
    if value is None:
        return "pending"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _cost(summary: dict) -> float | None:
    return summary.get("estimated_cost") or estimate_chat_cost(
        model=summary.get("model"),
        input_tokens=summary.get("input_tokens"),
        output_tokens=summary.get("output_tokens"),
    )["estimated_cost_usd"]


def _write_results_doc(results: list[dict], best: dict) -> None:
    RESULTS_DOC.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11 Prompt Experiment Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Best overall prompt: `{best.get('best_overall', 'pending')}`",
        f"- Best citation accuracy: `{best.get('best_citations', 'pending')}`",
        f"- Lowest hallucination rate: `{best.get('lowest_hallucination', 'pending')}`",
        "- Metrics are produced by the deterministic Phase 7 answer-quality scoring pipeline.",
        "- Estimated cost uses configured chat model pricing and excludes embedding/ingestion cost.",
        "",
        "## Prompt Version Metrics",
        "",
        "| Prompt | Status | Model | Temp | Answer | Citation | Hallucination | Response Type | Confidence | Failed | Input Tokens | Output Tokens | Est. Cost |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in sorted(results, key=lambda item: item["summary"]["prompt_version"]):
        summary = result["summary"]
        prompt = result["prompt"]
        lines.append(
            "| {version} | {status} | {model} | {temperature} | {answer} | {citation} | {hallucination} | {response_type} | {confidence} | {failed} | {input_tokens} | {output_tokens} | {estimated_cost} |".format(
                version=summary["prompt_version"],
                status=prompt["prompt_status"],
                model=summary["model"],
                temperature=_fmt(summary["temperature"]),
                answer=_fmt(summary["answer_accuracy"]),
                citation=_fmt(summary["citation_accuracy"]),
                hallucination=_fmt(summary["hallucination_rate"]),
                response_type=_fmt(summary["response_type_accuracy"]),
                confidence=_fmt(summary["final_confidence"]),
                failed=_fmt(summary["failed_question_count"]),
                input_tokens=_fmt(summary["input_tokens"]),
                output_tokens=_fmt(summary["output_tokens"]),
                estimated_cost=_fmt(_cost(summary)),
            )
        )
    lines.extend(
        [
            "",
            "## Experiment Notes",
            "",
        ]
    )
    for result in sorted(results, key=lambda item: item["summary"]["prompt_version"]):
        summary = result["summary"]
        lines.append(f"- `{summary['prompt_version']}`: {summary['prompt_change_notes']}")
    RESULTS_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_regression_doc(comparisons: list[dict]) -> None:
    REGRESSION_DOC.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 11 Prompt Regression Analysis",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "Prompt changes are compared against `v1`, the current Phase 7/9 production prompt.",
        "",
    ]
    for comparison in comparisons:
        lines.extend(
            [
                f"## {comparison['candidate_version']} vs {comparison['baseline_version']}",
                "",
                f"- Fixed questions: {', '.join(comparison['fixed_questions']) if comparison['fixed_questions'] else 'None'}",
                f"- Broken questions: {', '.join(comparison['broken_questions']) if comparison['broken_questions'] else 'None'}",
                f"- Still failing: {', '.join(comparison['still_failing']) if comparison['still_failing'] else 'None'}",
                "",
            ]
        )
    REGRESSION_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results = load_prompt_experiment_results(EXPERIMENT_DIR)
    if not results:
        raise SystemExit("No prompt experiment results found. Run `python scripts/run_prompt_experiment.py` first.")
    for result in results:
        result["summary"]["estimated_cost"] = _cost(result["summary"])
    by_version = {result["summary"]["prompt_version"]: result for result in results}
    baseline = by_version.get("v1")
    if not baseline:
        raise SystemExit("Baseline prompt result v1 is required for comparison.")

    comparisons = [
        compare_to_baseline(baseline, result).to_dict()
        for version, result in sorted(by_version.items())
        if version != "v1"
    ]
    best = best_prompt_summary(results)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "best": best,
        "comparisons": comparisons,
        "prompt_versions": [result["summary"] for result in sorted(results, key=lambda item: item["summary"]["prompt_version"])],
    }
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_results_doc(results, best)
    _write_regression_doc(comparisons)
    print(json.dumps({"prompt_versions": len(results), "comparisons": len(comparisons), "best": best}, indent=2))
    print(f"Wrote {COMPARISON_PATH}")
    print(f"Wrote {RESULTS_DOC}")
    print(f"Wrote {REGRESSION_DOC}")


if __name__ == "__main__":
    main()
