from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.run_benchmark import run_benchmark
from apps.api.app.experiments.config import ExperimentConfig, prompt_experiment_config
from apps.api.app.experiments.runner import run_prompt_experiment
from apps.api.app.retrieval.config import default_retrieval_config


OUTPUT_DIR = ROOT / "data/evaluation/expanded-baseline"
PHASE_DIR = ROOT / "docs/phase-32"
RETRIEVAL_REPORT = PHASE_DIR / "expanded-retrieval-baseline.md"
SUMMARY_REPORT = PHASE_DIR / "expanded-baseline-results.md"
RETRIEVAL_JSON = OUTPUT_DIR / "phase32-expanded-retrieval.json"
ANSWER_JSON = OUTPUT_DIR / "phase32-expanded-answer-generation-v5.json"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"


def _avg(values: list[float | None]) -> float | None:
    real = [value for value in values if value is not None]
    return round(mean(real), 3) if real else None


def _category_breakdown(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        question_type = row.get("question_type")
        if question_type:
            counts[str(question_type)] = counts.get(str(question_type), 0) + 1
    return dict(sorted(counts.items()))


def _benchmark_questions_by_id() -> dict[str, dict]:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return {
        str(question.get("question_id") or question.get("id")): question
        for question in benchmark["questions"]
        if question.get("question_id") or question.get("id")
    }


def _retrieval_expected_documents(question: dict | None) -> list[str]:
    if not question:
        return []
    if question.get("question_type") in {"permission_restricted", "missing_information"}:
        return []
    return question.get("expected_source_document") or []


def _retrieval_dashboard_run(summary: dict, generated_at: str) -> dict:
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
        "run_id": "phase32-expanded-retrieval",
        "run_name": "expanded-retrieval-baseline",
        "phase": "phase-32",
        "run_type": "retrieval_eval",
        "timestamp": generated_at,
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
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
        "notes": "Expanded Phase 32 retrieval-only baseline over benchmark v1.1. Answer quality and cost metrics are pending for this run type.",
    }


def _answer_dashboard_run(result: dict) -> dict:
    summary = result["summary"]
    return {
        "run_id": summary["experiment_id"],
        "run_name": summary["run_name"],
        "phase": "phase-32",
        "run_type": "prompt_experiment",
        "timestamp": result["generated_at"],
        "retrieval_mode": summary["retrieval_mode"],
        "chunking_strategy": summary["chunking_strategy"],
        "top_k": summary["top_k"],
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
        "failed_questions": [item["question_id"] for item in result.get("failed_questions", [])],
        "category_breakdown": _category_breakdown(result.get("rows") or []),
        "notes": "Expanded Phase 32 answer baseline over benchmark v1.1 using the current v5 answer-generation prompt.",
    }


def _write_summary(retrieval_run: dict | None, answer_run: dict | None, budget_usd: float) -> None:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 32 Expanded Baseline Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        f"Budget guardrail: ${budget_usd:.2f}",
        "",
    ]
    if retrieval_run:
        lines.extend(
            [
                "## Retrieval Baseline",
                "",
                f"- Run ID: `{retrieval_run['run_id']}`",
                f"- Questions: {retrieval_run['total_questions']}",
                f"- All-sources hit: `{retrieval_run['metrics'].get('all_sources_hit')}`",
                f"- Precision@k: `{retrieval_run['metrics'].get('precision_at_k')}`",
                f"- MRR: `{retrieval_run['metrics'].get('mrr')}`",
                f"- Failed source-coverage questions: {retrieval_run['metrics'].get('failed_question_count')}",
                f"- Failed source-coverage IDs: `{', '.join(retrieval_run.get('failed_questions') or []) or 'None'}`",
                "",
            ]
        )
    if answer_run:
        lines.extend(
            [
                "## Answer Baseline",
                "",
                f"- Run ID: `{answer_run['run_id']}`",
                f"- Questions: {answer_run['total_questions']}",
                f"- Answer accuracy: `{answer_run['metrics'].get('answer_accuracy')}`",
                f"- Citation accuracy: `{answer_run['metrics'].get('citation_accuracy')}`",
                f"- Hallucination rate: `{answer_run['metrics'].get('hallucination_rate')}`",
                f"- Response type accuracy: `{answer_run['metrics'].get('response_type_accuracy')}`",
                f"- Estimated chat cost: `${answer_run['metrics'].get('estimated_cost')}`",
                f"- Failed questions: {answer_run['metrics'].get('failed_question_count')}",
                "- Failed-question details are exported to `data/evaluation/failed-questions/failed-questions.json`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Notes",
            "",
            "- This is a baseline on the expanded benchmark, not a claimed improvement.",
            "- Chat cost is estimated from model pricing and excludes embedding and infrastructure cost.",
            "- Retrieval metrics and answer-quality metrics are separated so future tuning can compare like with like.",
            "",
        ]
    )
    SUMMARY_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 32 expanded benchmark baselines.")
    parser.add_argument("--budget-usd", type=float, default=10.0)
    parser.add_argument("--skip-retrieval", action="store_true")
    parser.add_argument("--skip-answer", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    retrieval_run = None
    answer_run = None

    if not args.skip_retrieval:
        retrieval_config = default_retrieval_config(
            run_name="phase32-expanded-retrieval",
            retrieval_mode="vector_only",
            chunking_strategy="section_based",
        )
        retrieval_summary = run_benchmark(
            retrieval_only=True,
            config=retrieval_config,
            report_path=RETRIEVAL_REPORT,
            write_report=True,
            include_results=True,
        )
        retrieval_run = _retrieval_dashboard_run(retrieval_summary, generated_at)
        RETRIEVAL_JSON.write_text(
            json.dumps({"generated_at": generated_at, "summary": retrieval_summary, "dashboard_run": retrieval_run}, indent=2),
            encoding="utf-8",
        )

    if not args.skip_answer:
        base = prompt_experiment_config("v5")
        config = ExperimentConfig(
            experiment_id="phase32-expanded-answer-generation-v5",
            run_name="expanded-answer-generation-v5",
            phase="phase-32",
            retrieval_mode=base.retrieval_mode,
            chunking_strategy=base.chunking_strategy,
            top_k=base.top_k,
            prompt_name=base.prompt_name,
            prompt_version=base.prompt_version,
            model=base.model,
            temperature=base.temperature,
            notes="Expanded Phase 32 baseline using the current strongest answer-generation prompt.",
        )
        answer_result = run_prompt_experiment(config, question_filter="all", budget_usd=args.budget_usd)
        answer_run = _answer_dashboard_run(answer_result)
        ANSWER_JSON.write_text(
            json.dumps({**answer_result, "dashboard_run": answer_run}, indent=2),
            encoding="utf-8",
        )

    _write_summary(retrieval_run, answer_run, args.budget_usd)
    print(json.dumps({"retrieval_run": retrieval_run, "answer_run": answer_run}, indent=2))
    print(f"Wrote {SUMMARY_REPORT}")


if __name__ == "__main__":
    main()
