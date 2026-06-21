from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.run_benchmark import run_benchmark
from apps.api.app.retrieval.config import RetrievalConfig, default_retrieval_config


OUTPUT_DIR = ROOT / "data/evaluation/expanded-baseline"
PHASE_DIR = ROOT / "docs/phase-33"
REPORT_PATH = PHASE_DIR / "precision-candidate-results.md"
SUMMARY_PATH = PHASE_DIR / "precision-candidate-runbook.md"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"


def _run_id(top_k: int) -> str:
    return f"phase33-vector-lexical-rerank-top{top_k}"


def _result_json(top_k: int) -> Path:
    return OUTPUT_DIR / f"{_run_id(top_k)}.json"


def _avg(values: list[float | None]) -> float | None:
    real = [value for value in values if value is not None]
    return round(mean(real), 3) if real else None


def _benchmark_questions_by_id() -> dict[str, dict[str, Any]]:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return {
        str(question.get("question_id") or question.get("id")): question
        for question in benchmark["questions"]
        if question.get("question_id") or question.get("id")
    }


def _category_breakdown(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        question_type = row.get("question_type")
        if question_type:
            counts[str(question_type)] = counts.get(str(question_type), 0) + 1
    return dict(sorted(counts.items()))


def _retrieval_expected_documents(question: dict[str, Any] | None) -> list[str]:
    if not question:
        return []
    if question.get("question_type") in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def _dashboard_run(summary: dict[str, Any], generated_at: str, config: RetrievalConfig) -> dict[str, Any]:
    results = summary.get("results") or []
    questions = _benchmark_questions_by_id()
    failed = [
        row["question_id"]
        for row in results
        if _retrieval_expected_documents(questions.get(row["question_id"]))
        and row.get("all_sources_hit") is not None
        and row.get("all_sources_hit") < 1.0
    ]
    return {
        "run_id": _run_id(config.top_k),
        "run_name": f"precision-candidate-vector-lexical-rerank-top{config.top_k}",
        "phase": "phase-33",
        "run_type": "retrieval_eval",
        "timestamp": generated_at,
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
        "reranker": config.reranker,
        "rerank_candidate_limit": config.rerank_candidate_limit,
        "prompt_version": None,
        "model": None,
        "total_questions": summary["question_count"],
        "source_question_count": summary["question_count"],
        "metrics": {
            "any_source_hit": _avg([row.get("any_source_hit") for row in results]),
            "all_sources_hit": _avg([row.get("all_sources_hit") for row in results]),
            "expected_source_recall": _avg([row.get("expected_source_recall") for row in results]),
            "precision_at_k": _avg([row.get("precision_at_k") for row in results]),
            "mrr": _avg([row.get("mrr") for row in results]),
            "average_latency_ms": _avg([row.get("latency_ms") for row in results]),
            "failed_question_count": len(failed),
        },
        "failed_questions": failed,
        "category_breakdown": _category_breakdown(results),
        "notes": (
            "Phase 33 retrieval-only candidate over benchmark v1.1. Uses the opt-in vector_lexical_rerank "
            "mode with permission-filtered vector candidates reranked deterministically before top-k trimming. "
            "This run is only publishable as an improvement if the permission safety suite also remains at zero leakage."
        ),
    }


def _write_runbook(config: RetrievalConfig, dry_run: bool) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 33 Precision Candidate Runbook",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Candidate Config",
        "",
        f"- Run ID: `{_run_id(config.top_k)}`",
        f"- Retrieval mode: `{config.retrieval_mode}`",
        f"- Chunking strategy: `{config.chunking_strategy}`",
        f"- Top K: `{config.top_k}`",
        f"- Reranker: `{config.reranker}`",
        f"- Rerank candidate limit: `{config.rerank_candidate_limit}`",
        "",
        "## Required Live Commands",
        "",
        "```powershell",
        "python scripts/run_phase33_precision_candidate.py",
        "python scripts/run_permission_eval.py",
        "python scripts/export_dashboard_data.py",
        "```",
        "",
        "## Gates",
        "",
        "- Precision@k must be `>= 0.75`.",
        "- Expected-source recall must be `>= 0.95`.",
        "- MRR must be `>= 0.95`.",
        "- Permission leakage must remain `0.000`.",
        "",
        "## Current Status",
        "",
        "- Dry run only." if dry_run else "- Live run completed; inspect `precision-candidate-results.md` and exported dashboard data.",
        "- OpenAI-backed retrieval sends benchmark questions to the embedding API; run only with explicit approval.",
        "",
    ]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def _write_result_summary(dashboard_run: dict[str, Any]) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    metrics = dashboard_run["metrics"]
    gates = {
        "precision_at_k": (metrics.get("precision_at_k") or 0) >= 0.75,
        "expected_source_recall": (metrics.get("expected_source_recall") or 0) >= 0.95,
        "mrr": (metrics.get("mrr") or 0) >= 0.95,
    }
    lines = [
        "# Phase 33 Precision Candidate Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        f"- Run ID: `{dashboard_run['run_id']}`",
        f"- Questions: `{dashboard_run['total_questions']}`",
        f"- Retrieval mode: `{dashboard_run['retrieval_mode']}`",
        f"- Top K: `{dashboard_run['top_k']}`",
        f"- Reranker: `{dashboard_run.get('reranker')}`",
        f"- Candidate limit: `{dashboard_run.get('rerank_candidate_limit')}`",
        "",
        "## Metrics",
        "",
        f"- Any-source hit: `{metrics.get('any_source_hit')}`",
        f"- All-sources hit: `{metrics.get('all_sources_hit')}`",
        f"- Expected-source recall: `{metrics.get('expected_source_recall')}`",
        f"- Precision@k: `{metrics.get('precision_at_k')}`",
        f"- MRR: `{metrics.get('mrr')}`",
        f"- Average latency ms: `{metrics.get('average_latency_ms')}`",
        f"- Failed source-coverage questions: `{metrics.get('failed_question_count')}`",
        "",
        "## Retrieval Gates",
        "",
        f"- Precision target: `{'pass' if gates['precision_at_k'] else 'fail'}`",
        f"- Recall gate: `{'pass' if gates['expected_source_recall'] else 'fail'}`",
        f"- MRR gate: `{'pass' if gates['mrr'] else 'fail'}`",
        "",
        "Permission safety must be verified separately before Phase 33 can be marked complete.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def _config(top_k: int, candidate_limit: int) -> RetrievalConfig:
    return default_retrieval_config(
        run_name=_run_id(top_k),
        retrieval_mode="vector_lexical_rerank",
        chunking_strategy="section_based",
        top_k=top_k,
        rerank_candidate_limit=candidate_limit,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 33 vector lexical rerank retrieval candidate.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--candidate-limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true", help="Write the runbook and print config without calling retrieval.")
    args = parser.parse_args()

    config = _config(top_k=args.top_k, candidate_limit=args.candidate_limit)
    _write_runbook(config, dry_run=args.dry_run)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "run_id": _run_id(config.top_k),
                    "retrieval_mode": config.retrieval_mode,
                    "top_k": config.top_k,
                    "reranker": config.reranker,
                    "rerank_candidate_limit": config.rerank_candidate_limit,
                    "runbook": str(SUMMARY_PATH),
                    "result_json": str(_result_json(config.top_k)),
                },
                indent=2,
            )
        )
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    summary = run_benchmark(
        retrieval_only=True,
        config=config,
        report_path=REPORT_PATH,
        write_report=True,
        include_results=True,
    )
    dashboard_run = _dashboard_run(summary, generated_at, config)
    result_json = _result_json(config.top_k)
    result_json.write_text(
        json.dumps({"generated_at": generated_at, "summary": summary, "dashboard_run": dashboard_run}, indent=2),
        encoding="utf-8",
    )
    _write_result_summary(dashboard_run)
    print(json.dumps({"dashboard_run": dashboard_run, "result_json": str(result_json)}, indent=2))


if __name__ == "__main__":
    main()
