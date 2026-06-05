from __future__ import annotations

import json
from pathlib import Path


DASHBOARD_PATH = Path("data/evaluation/dashboard-summary.json")
REPORT_PATH = Path("docs/phase-10/evaluation-results-summary.md")


def _metric(value: object) -> str:
    if value is None:
        return "pending"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def main() -> None:
    if not DASHBOARD_PATH.exists():
        raise SystemExit("Dashboard data is missing. Run `python scripts/export_dashboard_data.py` first.")

    dashboard = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    runs = dashboard["runs"]
    lines = [
        "# Phase 10 Evaluation Results Summary",
        "",
        f"Generated from: `{DASHBOARD_PATH}`",
        "",
        "## Overview",
        "",
        f"- Best retrieval run: {dashboard['overview']['best_retrieval_run']}",
        f"- Retrieval conclusion: {dashboard['overview']['retrieval_conclusion']}",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in dashboard["overview"]["headline_metrics"].items():
        lines.append(f"| {key.replace('_', ' ').title()} | {_metric(value)} |")

    lines.extend(
        [
            "",
            "## Run Comparison",
            "",
            "| Run | Phase | Type | Retrieval | Chunking | Precision@k | MRR | Answer Acc | Citation Acc | Permission Leakage | Memory Acc |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for run in runs:
        metrics = run["metrics"]
        lines.append(
            "| {run_name} | {phase} | {run_type} | {retrieval_mode} | {chunking_strategy} | {precision} | {mrr} | {answer} | {citation} | {permission} | {memory} |".format(
                run_name=run["run_name"],
                phase=run["phase"],
                run_type=run["run_type"],
                retrieval_mode=run.get("retrieval_mode") or "n/a",
                chunking_strategy=run.get("chunking_strategy") or "n/a",
                precision=_metric(metrics.get("precision_at_k")),
                mrr=_metric(metrics.get("mrr")),
                answer=_metric(metrics.get("answer_accuracy")),
                citation=_metric(metrics.get("citation_accuracy")),
                permission=_metric(metrics.get("permission_leakage_rate")),
                memory=_metric(metrics.get("memory_answer_accuracy")),
            )
        )

    lines.extend(
        [
            "",
            "## Comparison Notes",
            "",
        ]
    )
    for comparison in dashboard["comparisons"].values():
        lines.append(f"- {comparison['summary']}")

    lines.extend(
        [
            "",
            "## Failed Questions",
            "",
            f"- Failed question records exported: {len(dashboard['failed_questions'])}",
            "- Use `data/evaluation/failed-questions/failed-questions.json` for dashboard details.",
            "",
            "## Honesty Notes",
            "",
            "- No fake metrics are added by Phase 10.",
            "- Estimated cost remains pending where earlier phases did not calculate it.",
            "- Answer metrics are deterministic or heuristic signals, not a human-grade semantic evaluation.",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
