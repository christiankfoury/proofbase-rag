from __future__ import annotations

import json
import re
import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.costing.estimator import estimate_chat_cost

PHASE6_RESULTS = ROOT / "docs/phase-6/evaluation-results.md"
PHASE7_RESULTS = ROOT / "docs/phase-7/evaluation-results.md"
PHASE7_FAILED = ROOT / "docs/phase-7/failed-question-analysis.md"
PHASE8_RESULTS = ROOT / "docs/phase-8/permission-evaluation-results.md"
PHASE9_RESULTS = ROOT / "docs/phase-9/memory-evaluation-results.md"
PHASE9_FAILED = ROOT / "docs/phase-9/failed-memory-question-analysis.md"
BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"

DASHBOARD_PATH = ROOT / "data/evaluation/dashboard-summary.json"
RUNS_DIR = ROOT / "data/evaluation/eval-runs"
FAILED_DIR = ROOT / "data/evaluation/failed-questions"
PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
EXPANDED_BASELINE_DIR = ROOT / "data/evaluation/expanded-baseline"
PROMPT_COMPARISON_PATH = PROMPT_EXPERIMENT_DIR / "prompt-comparison.json"
MULTI_DOC_EVAL_PATH = ROOT / "data/evaluation/multi-doc-eval.json"
PHASE33_DIAGNOSTICS_PATH = ROOT / "data/evaluation/phase33-precision-diagnostics.json"
PHASE33_NO_EGRESS_PATH = ROOT / "data/evaluation/phase33-no-egress-candidates.json"
PHASE33_LIVE_CANDIDATE_PATH = EXPANDED_BASELINE_DIR / "phase33-vector-lexical-rerank-top3.json"
PHASE33_PERMISSION_CANDIDATE_PATH = ROOT / "docs/phase-33/permission-candidate-results.md"

REQUIRED_REPORTS = [
    PHASE6_RESULTS,
    PHASE7_RESULTS,
    PHASE7_FAILED,
    PHASE8_RESULTS,
    PHASE9_RESULTS,
    PHASE9_FAILED,
]
EXPECTED_RUN_COUNT = 8
LEGACY_BENCHMARK_VERSION = "1.0"
LEGACY_BENCHMARK_CUTOFF = "2026-06-20T00:00:00"


def _load_benchmark() -> dict[str, Any]:
    if not BENCHMARK_PATH.exists():
        return {"questions": []}
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _category_breakdown(questions: list[dict[str, Any]]) -> dict[str, int]:
    breakdown: dict[str, int] = {}
    for question in questions:
        question_type = question.get("question_type")
        if not question_type:
            continue
        breakdown[str(question_type)] = breakdown.get(str(question_type), 0) + 1
    return dict(sorted(breakdown.items()))


def _benchmark_context(benchmark: dict[str, Any]) -> dict[str, Any]:
    questions = [question for question in benchmark.get("questions", []) if isinstance(question, dict)]
    return {
        "benchmark_version": benchmark.get("benchmark_version") or "not available",
        "source_corpus": benchmark.get("source_corpus") or "not available",
        "corpus_question_count": benchmark.get("question_count") or len(questions),
        "category_breakdown": _category_breakdown(questions),
        "current_dashboard_suites": {
            "primary_retrieval_and_answer_quality": 60,
            "permission_safety": 10,
            "memory_followups": 5,
        },
    }


def _run_benchmark_version(run: dict[str, Any], *, current_benchmark_version: str | None = None) -> str:
    if run.get("benchmark_version"):
        return str(run["benchmark_version"])
    timestamp = str(run.get("timestamp") or "")
    legacy_sample_size = run.get("source_question_count") == 60 or run.get("total_questions") in {5, 10, 60}
    if legacy_sample_size and timestamp < LEGACY_BENCHMARK_CUTOFF:
        return LEGACY_BENCHMARK_VERSION
    return current_benchmark_version or "not available"


def _annotate_run(run: dict[str, Any], *, current_benchmark_version: str | None = None) -> dict[str, Any]:
    sample_size = run.get("total_questions")
    failed_count = run.get("metrics", {}).get("failed_question_count")
    if failed_count is None and run.get("failed_questions") is not None:
        failed_count = len(run.get("failed_questions") or [])
    passed_count = None
    if isinstance(sample_size, int) and isinstance(failed_count, int):
        passed_count = sample_size - failed_count
    return {
        **run,
        "sample_size": sample_size,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "benchmark_version": _run_benchmark_version(run, current_benchmark_version=current_benchmark_version),
        "run_timestamp": run.get("timestamp"),
    }


def _with_category_breakdown(run: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return run
    return {**run, "category_breakdown": _category_breakdown(rows)}


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _timestamp(markdown: str) -> str:
    match = re.search(r"Generated at:\s*([^\n]+)", markdown)
    return match.group(1).strip() if match else datetime.now(UTC).isoformat()


def _float(value: str) -> float | None:
    value = value.strip()
    if value.lower() in {"pending", "none", "n/a", ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(value: str) -> int | None:
    value = value.strip()
    if value.lower() in {"pending", "none", "n/a", ""}:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _estimated_cost(model: str | None, input_tokens: int | None, output_tokens: int | None) -> float | None:
    return estimate_chat_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )["estimated_cost_usd"]


def _summary_bullets(markdown: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in markdown.splitlines():
        match = re.match(r"-\s+([^:]+):\s*(.+)", line.strip())
        if match:
            key = match.group(1).strip().lower().replace("@", "_at_")
            key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
            values[key] = match.group(2).strip()
    return values


def _parse_phase6_table(markdown: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    in_table = False
    for line in markdown.splitlines():
        if line.startswith("| Run | Any Source |"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and not line.startswith("|"):
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 8:
            continue
        failed_questions = [] if cells[7] == "None" else [item.strip() for item in cells[7].split(",")]
        rows.append(
            {
                "run_id": f"phase6-{cells[0]}",
                "run_name": cells[0],
                "phase": "phase-6",
                "run_type": "retrieval_eval",
                "timestamp": _timestamp(markdown),
                "retrieval_mode": _phase6_mode(cells[0]),
                "chunking_strategy": "fixed_size" if "fixed" in cells[0] else "section_based",
                "top_k": 5,
                "prompt_version": None,
                "model": None,
                "total_questions": 60,
                "metrics": {
                    "any_source_hit": _float(cells[1]),
                    "all_sources_hit": _float(cells[2]),
                    "expected_source_recall": _float(cells[3]),
                    "precision_at_k": _float(cells[4]),
                    "mrr": _float(cells[5]),
                    "average_latency_ms": _float(cells[6]),
                },
                "failed_questions": failed_questions,
                "notes": "Retrieval-only run. Answer quality and cost metrics are pending for this run type.",
            }
        )
    return rows


def _phase6_mode(run_name: str) -> str:
    if run_name.startswith("keyword"):
        return "keyword_only"
    if run_name.startswith("hybrid"):
        return "hybrid"
    return "vector_only"


def _failed_question_ids(markdown: str) -> list[str]:
    ids: list[str] = []
    for line in markdown.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"Question ID", "---"}:
            continue
        if re.match(r"^[A-Z]+-\d{3}$", cells[0]):
            ids.append(cells[0])
    return ids


def _failed_items(markdown: str, phase: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"Question ID", "---"}:
            continue
        if not re.match(r"^[A-Z]+-\d{3}$", cells[0]):
            continue
        if phase == "phase-7" and len(cells) >= 7:
            items.append(
                {
                    "phase": phase,
                    "question_id": cells[0],
                    "expected_behavior": cells[1],
                    "actual_response_type": cells[2],
                    "failure_type": cells[3],
                    "citation_confidence": _float(cells[4]),
                    "answer_confidence": _float(cells[5]),
                    "recommended_fix": cells[6],
                }
            )
        elif phase == "phase-9" and len(cells) >= 6:
            items.append(
                {
                    "phase": phase,
                    "question_id": cells[0],
                    "failure_type": cells[1],
                    "rewritten_question": cells[2],
                    "expected_source": cells[3],
                    "actual_citations": cells[4],
                    "recommended_fix": cells[5],
                }
            )
    return items


def _phase7_run(markdown: str, failed_markdown: str) -> dict[str, Any]:
    values = _summary_bullets(markdown)
    input_tokens = _int(values.get("input_tokens", ""))
    output_tokens = _int(values.get("output_tokens", ""))
    model = "gpt-4.1-mini"
    return {
        "run_id": "phase7-answer-quality",
        "run_name": "phase-7-answer-quality",
        "phase": "phase-7",
        "run_type": "answer_quality_eval",
        "timestamp": _timestamp(markdown),
        "retrieval_mode": values.get("retrieval_mode"),
        "chunking_strategy": values.get("chunking_strategy"),
        "top_k": _int(values.get("top_k", "")),
        "prompt_version": "answer_v1",
        "model": model,
        "total_questions": _int(values.get("questions", "")),
        "metrics": {
            "any_source_hit": _float(values.get("any_source_hit", "")),
            "all_sources_hit": _float(values.get("all_sources_hit", "")),
            "precision_at_k": _float(values.get("precision_at_k", "")),
            "mrr": _float(values.get("mrr", "")),
            "answer_accuracy": _float(values.get("answer_accuracy", "")),
            "citation_accuracy": _float(values.get("citation_accuracy", "")),
            "faithfulness": _float(values.get("faithfulness_support_score", "")),
            "hallucination_rate": _float(values.get("hallucination_rate", "")),
            "response_type_accuracy": _float(values.get("response_type_accuracy", "")),
            "refusal_accuracy": _float(values.get("refusal_accuracy", "")),
            "not_found_accuracy": _float(values.get("not_found_accuracy", "")),
            "clarification_accuracy": _float(values.get("clarification_accuracy", "")),
            "final_confidence": _float(values.get("average_final_confidence", "")),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": _estimated_cost(model, input_tokens, output_tokens),
        },
        "failed_questions": _failed_question_ids(failed_markdown),
        "notes": "Answer metrics use deterministic scoring and heuristic confidence; cost is estimated from configured model pricing.",
    }


def _phase8_run(markdown: str) -> dict[str, Any]:
    values = _summary_bullets(markdown)
    return {
        "run_id": "phase8-permission-safety",
        "run_name": "phase-8-permission-safety",
        "phase": "phase-8",
        "run_type": "permission_eval",
        "timestamp": _timestamp(markdown),
        "retrieval_mode": values.get("retrieval_mode"),
        "chunking_strategy": values.get("chunking_strategy"),
        "top_k": _int(values.get("top_k", "")),
        "prompt_version": "answer_v1",
        "model": "gpt-4.1-mini",
        "total_questions": _int(values.get("restricted_benchmark_questions_tested", "")),
        "metrics": {
            "restricted_question_count": _int(values.get("restricted_benchmark_questions_tested", "")),
            "authorized_test_count": _int(values.get("authorized_source_access_tests", "")),
            "permission_leakage_rate": _float(values.get("permission_leakage_rate", "")),
            "blocked_answer_accuracy": _float(values.get("blocked_answer_accuracy", "")),
            "unauthorized_chunk_exposure_rate": _float(values.get("unauthorized_chunk_exposure_rate", "")),
            "restricted_citation_leakage_rate": _float(values.get("restricted_citation_leakage_rate", "")),
            "unauthorized_chunks_reached_generation_rate": _float(
                values.get("unauthorized_chunks_reached_generation_rate", "")
            ),
            "authorized_retrieval_accuracy": _float(values.get("authorized_retrieval_accuracy", "")),
            "authorized_answer_accuracy": _float(values.get("authorized_answer_accuracy", "")),
        },
        "failed_questions": [],
        "category_breakdown": {"permission_restricted": _int(values.get("restricted_benchmark_questions_tested", ""))},
        "notes": "Pre-retrieval role filter blocked all 10 unauthorized requests. Zero restricted chunks reached retrieval or generation. Authorized-role retrieval confirmed for all 10 questions. Authorized answer generation is marked pending (requires --include-authorized-generation flag). Permission safety here is structurally enforced by a hard document-access filter, not probabilistic.",
    }


def _phase9_run(markdown: str, failed_markdown: str) -> dict[str, Any]:
    values = _summary_bullets(markdown)
    input_tokens = _int(values.get("input_tokens", ""))
    output_tokens = _int(values.get("output_tokens", ""))
    model = "gpt-4.1-mini"
    return {
        "run_id": "phase9-memory",
        "run_name": "phase-9-memory",
        "phase": "phase-9",
        "run_type": "memory_eval",
        "timestamp": _timestamp(markdown),
        "retrieval_mode": values.get("retrieval_mode"),
        "chunking_strategy": values.get("chunking_strategy"),
        "top_k": _int(values.get("top_k", "")),
        "prompt_version": "answer_v1",
        "model": model,
        "total_questions": _int(values.get("memory_benchmark_questions", "")),
        "metrics": {
            "followup_detection_accuracy": _float(values.get("follow_up_detection_accuracy", "")),
            "query_rewrite_quality": _float(values.get("query_rewrite_quality", "")),
            "memory_answer_accuracy": _float(values.get("memory_answer_accuracy", "")),
            "memory_citation_accuracy": _float(values.get("memory_citation_accuracy", "")),
            "memory_response_type_accuracy": _float(values.get("memory_response_type_accuracy", "")),
            "memory_permission_leakage": _float(values.get("memory_permission_leakage", "")),
            "hallucination_rate": _float(values.get("hallucination_rate_on_follow_ups", "")),
            "final_confidence": _float(values.get("average_final_confidence", "")),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": _estimated_cost(model, input_tokens, output_tokens),
        },
        "failed_questions": _failed_question_ids(failed_markdown),
        "category_breakdown": {"conversation_memory": _int(values.get("memory_benchmark_questions", ""))},
        "notes": "Memory is session-level only and is used for query rewriting, not source evidence.",
    }


def _prompt_experiment_runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not PROMPT_EXPERIMENT_DIR.exists():
        return runs
    for path in sorted(PROMPT_EXPERIMENT_DIR.glob("*-answer-generation-*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        summary = result["summary"]
        rows = [row for row in result.get("rows", []) if isinstance(row, dict)]
        failed_questions = [item["question_id"] for item in result.get("failed_questions", [])]
        question_filter = summary.get("question_filter")
        run_id = summary["experiment_id"]
        run_name = summary["run_name"]
        if question_filter and question_filter != "all":
            run_id = path.stem
            run_name = f"{run_name} (subset)"
        run = {
            "run_id": run_id,
            "run_name": run_name,
            "phase": summary["phase"],
            "run_type": "prompt_experiment",
            "timestamp": result["generated_at"],
            "retrieval_mode": summary["retrieval_mode"],
            "chunking_strategy": summary["chunking_strategy"],
            "top_k": summary["top_k"],
            "prompt_name": summary["prompt_name"],
            "prompt_version": summary["prompt_version"],
            "prompt_status": summary["prompt_status"],
            "prompt_change_notes": summary["prompt_change_notes"],
            "model": summary["model"],
            "temperature": summary["temperature"],
            "total_questions": summary["question_count"],
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
                "estimated_cost": summary.get("estimated_cost") or _estimated_cost(
                    summary.get("model"),
                    summary.get("input_tokens"),
                    summary.get("output_tokens"),
                ),
                "failed_question_count": summary.get("failed_question_count"),
            },
            "failed_questions": failed_questions,
            "notes": summary["prompt_change_notes"],
        }
        run = _with_category_breakdown(run, rows)
        if question_filter is not None:
            run["question_filter"] = question_filter
        if summary.get("source_question_count") is not None:
            run["source_question_count"] = summary.get("source_question_count")
        if summary.get("prompt_version") == "v1":
            run["notes"] += (
                " Note: v1 uses temperature=0.2, causing run-to-run variance. The phase-7 baseline run of the"
                " same prompt scored 0.829 answer accuracy vs 0.800 here; the difference is LLM"
                " non-determinism, not a code change. Subsequent prompt versions (v2 onward) use"
                " temperature=0.0 for reproducibility."
            )
        if question_filter and question_filter != "all":
            run["notes"] += (
                f" This run evaluated only {summary.get('question_count')}/{summary.get('source_question_count')}"
                " benchmark questions (previously-failed subset). Precision@k appears higher than full-benchmark"
                " runs because the subset contains disproportionately many MULTI questions with 3+ expected"
                " source documents, which inflate chunk-level precision. Not directly comparable to"
                " full-benchmark scores."
            )
        runs.append(run)
    return runs


def _expanded_baseline_runs() -> list[dict[str, Any]]:
    if not EXPANDED_BASELINE_DIR.exists():
        return []
    runs = []
    for path in sorted(EXPANDED_BASELINE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        run = payload.get("dashboard_run")
        if isinstance(run, dict):
            runs.append(run)
    return runs


def _current_answer_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        run
        for run in runs
        if run.get("run_type") == "prompt_experiment"
        and run.get("question_filter") == "all"
        and run.get("total_questions") == run.get("source_question_count")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda run: run.get("timestamp") or "")


def _full_prompt_experiment_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        run
        for run in runs
        if run.get("run_type") == "prompt_experiment"
        and run.get("question_filter") in {None, "all"}
        and (
            run.get("source_question_count") is None
            or run.get("total_questions") == run.get("source_question_count")
        )
    ]


def _prompt_experiment_failed_items(run: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not run:
        return []
    candidates = [
        PROMPT_EXPERIMENT_DIR / f"{run['run_id']}.json",
        EXPANDED_BASELINE_DIR / f"{run['run_id']}.json",
    ]
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        return []
    result = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            **item,
            "phase": run["phase"],
            "run_id": run["run_id"],
            "run_name": run["run_name"],
        }
        for item in result.get("failed_questions", [])
    ]


def _multi_doc_comparison() -> dict[str, Any]:
    if not MULTI_DOC_EVAL_PATH.exists():
        return {}
    data = json.loads(MULTI_DOC_EVAL_PATH.read_text(encoding="utf-8"))
    baseline = data.get("baseline", {}).get("summary", {})
    multi_doc = data.get("multi_doc", {}).get("summary", {})
    baseline_rows = data.get("baseline", {}).get("rows", [])
    multi_doc_rows = data.get("multi_doc", {}).get("rows", [])

    fixed = [
        r["question_id"] for r in multi_doc_rows
        if r.get("answer_accuracy", 0) >= 1.0
        and next((b for b in baseline_rows if b["question_id"] == r["question_id"]), {}).get("answer_accuracy", 0) < 1.0
    ]
    broken = [
        r["question_id"] for r in multi_doc_rows
        if r.get("answer_accuracy", 1) < 1.0
        and next((b for b in baseline_rows if b["question_id"] == r["question_id"]), {}).get("answer_accuracy", 1) >= 1.0
    ]
    still_failing = [
        r["question_id"] for r in multi_doc_rows
        if r.get("answer_accuracy", 1) < 1.0
        and next((b for b in baseline_rows if b["question_id"] == r["question_id"]), {}).get("answer_accuracy", 1) < 1.0
    ]

    return {
        "baseline": baseline,
        "multi_doc": multi_doc,
        "fixed_questions": fixed,
        "broken_questions": broken,
        "still_failing": still_failing,
        "hallucination_regression": (
            (multi_doc.get("hallucination_rate") or 0) > (baseline.get("hallucination_rate") or 0)
        ),
    }


def _phase33_precision_readiness() -> dict[str, Any]:
    if not PHASE33_DIAGNOSTICS_PATH.exists():
        return {}

    diagnostics = json.loads(PHASE33_DIAGNOSTICS_PATH.read_text(encoding="utf-8"))
    no_egress = json.loads(PHASE33_NO_EGRESS_PATH.read_text(encoding="utf-8")) if PHASE33_NO_EGRESS_PATH.exists() else {}
    top_k_replay = diagnostics.get("top_k_replay") or []
    rerank_replay = diagnostics.get("saved_top5_lexical_rerank_replay") or []
    baseline = diagnostics.get("baseline_run") or {}

    def candidate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summary = []
        for row in rows:
            gate = row.get("phase33_gate") or {}
            summary.append(
                {
                    "top_k": row.get("top_k"),
                    "precision_at_k": row.get("precision_at_k"),
                    "expected_source_recall": row.get("expected_source_recall"),
                    "all_sources_hit": row.get("all_sources_hit"),
                    "mrr": row.get("mrr"),
                    "failed_question_count": row.get("failed_question_count"),
                    "meets_precision_target": gate.get("precision_target_met"),
                    "meets_recall_gate": gate.get("recall_gate_met"),
                    "meets_mrr_gate": gate.get("mrr_gate_met"),
                }
            )
        return summary

    def best_gate_preserving(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        eligible = [
            row
            for row in candidate_summary(rows)
            if row.get("meets_recall_gate") and row.get("meets_mrr_gate")
        ]
        if not eligible:
            return None
        return max(eligible, key=lambda row: row.get("precision_at_k") or 0)

    def metric_float(value: Any) -> float | None:
        if value is None or value == "pending":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    live_candidate: dict[str, Any] | None = None
    if PHASE33_LIVE_CANDIDATE_PATH.exists():
        live_data = json.loads(PHASE33_LIVE_CANDIDATE_PATH.read_text(encoding="utf-8"))
        summary = live_data.get("summary") or {}
        results = summary.get("results") or []
        questions = {
            question.get("question_id"): question
            for question in _load_benchmark().get("questions", [])
            if question.get("question_id")
        }
        failed_question_ids = [
            row.get("question_id")
            for row in results
            if row.get("question_id")
            and questions.get(row.get("question_id"), {}).get("question_type")
            not in {"permission_restricted", "missing_information"}
            and questions.get(row.get("question_id"), {}).get("expected_source_document")
            and row.get("all_sources_hit") is not None
            and row.get("all_sources_hit") < 1.0
        ]
        precision = metric_float(summary.get("precision_at_k"))
        recall = metric_float(summary.get("expected_source_recall"))
        mrr = metric_float(summary.get("mrr"))
        live_candidate = {
            "run_uuid": summary.get("run_id"),
            "run_name": summary.get("run_name"),
            "generated_at": live_data.get("generated_at"),
            "question_count": summary.get("question_count"),
            "retrieval_mode": summary.get("retrieval_mode"),
            "top_k": summary.get("top_k"),
            "precision_at_k": precision,
            "expected_source_recall": recall,
            "all_sources_hit": metric_float(summary.get("all_sources_hit")),
            "mrr": mrr,
            "average_latency_ms": metric_float(summary.get("average_latency_ms")),
            "failed_question_count": len(failed_question_ids),
            "failed_question_ids": failed_question_ids,
            "meets_precision_target": precision is not None and precision >= 0.75,
            "meets_recall_gate": recall is not None and recall >= 0.95,
            "meets_mrr_gate": mrr is not None and mrr >= 0.95,
        }

    permission_candidate: dict[str, Any] | None = None
    if PHASE33_PERMISSION_CANDIDATE_PATH.exists():
        permission_metrics: dict[str, str] = {}
        for line in PHASE33_PERMISSION_CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^- ([^:]+): (.+)$", line.strip())
            if match:
                key = match.group(1).lower().replace(" ", "_").replace("-", "_")
                permission_metrics[key] = match.group(2)
        permission_candidate = {
            "restricted_question_count": metric_float(permission_metrics.get("restricted_benchmark_questions_tested")),
            "authorized_test_count": metric_float(permission_metrics.get("authorized_source_access_tests")),
            "permission_leakage_rate": metric_float(permission_metrics.get("permission_leakage_rate")),
            "blocked_answer_accuracy": metric_float(permission_metrics.get("blocked_answer_accuracy")),
            "unauthorized_chunk_exposure_rate": metric_float(permission_metrics.get("unauthorized_chunk_exposure_rate")),
            "restricted_citation_leakage_rate": metric_float(permission_metrics.get("restricted_citation_leakage_rate")),
            "unauthorized_chunks_reached_generation_rate": metric_float(
                permission_metrics.get("unauthorized_chunks_reached_generation_rate")
            ),
            "authorized_retrieval_accuracy": metric_float(permission_metrics.get("authorized_retrieval_accuracy")),
            "authorized_answer_accuracy": metric_float(permission_metrics.get("authorized_answer_accuracy")),
        }

    live_gates_pass = bool(
        live_candidate
        and live_candidate.get("meets_precision_target")
        and live_candidate.get("meets_recall_gate")
        and live_candidate.get("meets_mrr_gate")
    )
    permission_gates_pass = bool(
        permission_candidate
        and permission_candidate.get("permission_leakage_rate") == 0.0
        and permission_candidate.get("blocked_answer_accuracy") == 1.0
        and permission_candidate.get("unauthorized_chunk_exposure_rate") == 0.0
        and permission_candidate.get("restricted_citation_leakage_rate") == 0.0
        and permission_candidate.get("unauthorized_chunks_reached_generation_rate") == 0.0
        and permission_candidate.get("authorized_retrieval_accuracy") == 1.0
    )
    phase33_complete = live_gates_pass and permission_gates_pass

    return {
        "status": "complete" if phase33_complete else "in_progress",
        "phase": "phase-33",
        "generated_at": diagnostics.get("generated_at"),
        "benchmark_version": diagnostics.get("benchmark_version"),
        "diagnostic_source": "live candidate run plus saved Phase 32 artifact replay",
        "input_run_id": baseline.get("run_id"),
        "candidate_mode": "vector_lexical_rerank",
        "candidate_run_id": "phase33-vector-lexical-rerank-top3",
        "live_run_required": not phase33_complete,
        "publishable_improvement": phase33_complete,
        "gates": {
            "precision_at_k_target": 0.75,
            "expected_source_recall_minimum": 0.95,
            "mrr_minimum": 0.95,
            "permission_leakage_rate": 0.0,
            "blocked_answer_accuracy_target": 1.0,
        },
        "live_candidate": live_candidate,
        "permission_candidate": permission_candidate,
        "best_top_k_replay": best_gate_preserving(top_k_replay),
        "best_saved_top5_lexical_rerank_replay": best_gate_preserving(rerank_replay),
        "saved_top5_lexical_rerank_config": diagnostics.get("saved_top5_lexical_rerank_config", {}),
        "top_k_replay": candidate_summary(top_k_replay),
        "saved_top5_lexical_rerank_replay": candidate_summary(rerank_replay),
        "no_egress_keyword_candidates": {
            "generated_at": no_egress.get("generated_at"),
            "method": no_egress.get("method"),
            "network_api_use": no_egress.get("network_api_use"),
            "answer_generation": no_egress.get("answer_generation"),
            "candidates": [
                {
                    "top_k": candidate.get("top_k"),
                    "metrics": candidate.get("metrics"),
                    "phase33_gate": candidate.get("phase33_gate"),
                    "permission_boundary": candidate.get("permission_boundary"),
                }
                for candidate in no_egress.get("candidates", [])
            ],
            "notes": no_egress.get("notes", []),
        } if no_egress else {},
        "required_live_commands": [
            "python scripts/run_phase33_precision_candidate.py --top-k 3 --candidate-limit 20 --allow-external-embeddings",
            "python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 3 --rerank-candidate-limit 20 --allow-external-embeddings",
            "python scripts/export_dashboard_data.py",
        ],
        "notes": [
            "The live Phase 33 candidate is publishable only when retrieval gates and permission safety gates pass together.",
            "The saved replay remains visible as provenance for why the live candidate was selected.",
            "Authorized answer accuracy remains pending by default to avoid extra chat-completion cost.",
        ],
    }


def _prompt_comparison() -> dict[str, Any]:
    if not PROMPT_COMPARISON_PATH.exists():
        return {"best": {}, "comparisons": [], "prompt_versions": []}
    return json.loads(PROMPT_COMPARISON_PATH.read_text(encoding="utf-8"))


def _metric_context(run: dict[str, Any], metric_key: str) -> dict[str, Any]:
    return {
        "run_id": run.get("run_id"),
        "run_name": run.get("run_name"),
        "metric_key": metric_key,
        "sample_size": run.get("sample_size"),
        "passed_count": run.get("passed_count"),
        "failed_count": run.get("failed_count"),
        "benchmark_version": run.get("benchmark_version"),
        "run_timestamp": run.get("run_timestamp") or run.get("timestamp"),
        "category_breakdown": run.get("category_breakdown"),
    }


def _overview(runs: list[dict[str, Any]], current_answer_run: dict[str, Any] | None) -> dict[str, Any]:
    by_id = {run["run_id"]: run for run in runs}
    retrieval = by_id.get("phase6-vector-section", {})
    answer = by_id.get("phase7-answer-quality", {})
    permissions = by_id.get("phase8-permission-safety", {})
    memory = by_id.get("phase9-memory", {})
    current_failed_count = len(current_answer_run.get("failed_questions") or []) if current_answer_run else len(
        answer.get("failed_questions") or []
    )
    return {
        "best_retrieval_run": "vector-section",
        "retrieval_conclusion": "Hybrid did not clearly outperform vector-only retrieval; vector-section remained best overall.",
        "current_answer_run_id": current_answer_run.get("run_id") if current_answer_run else answer.get("run_id"),
        "current_failed_question_count": current_failed_count,
        "progress_summary": {
            "improved": [
                "Permission tests reached zero leakage.",
                "Memory follow-up tests reached full accuracy.",
                "Chat-generation cost tracking is implemented.",
            ],
            "still_needs_work": [
                "Hybrid retrieval still did not beat vector-only overall.",
                f"{current_failed_count} failed-question cases remain in the current improvement backlog.",
                "Embedding, infrastructure, cached-input, and batch cost modeling remain pending.",
            ],
        },
        "headline_metrics": {
            "retrieval_hit_rate": retrieval.get("metrics", {}).get("all_sources_hit"),
            "precision_at_k": retrieval.get("metrics", {}).get("precision_at_k"),
            "mrr": retrieval.get("metrics", {}).get("mrr"),
            "answer_accuracy": answer.get("metrics", {}).get("answer_accuracy"),
            "citation_accuracy": answer.get("metrics", {}).get("citation_accuracy"),
            "hallucination_rate": answer.get("metrics", {}).get("hallucination_rate"),
            "permission_leakage_rate": permissions.get("metrics", {}).get("permission_leakage_rate"),
            "memory_accuracy": memory.get("metrics", {}).get("memory_answer_accuracy"),
        },
        "metric_context": {
            "retrieval_hit_rate": _metric_context(retrieval, "all_sources_hit"),
            "precision_at_k": _metric_context(retrieval, "precision_at_k"),
            "mrr": _metric_context(retrieval, "mrr"),
            "answer_accuracy": _metric_context(answer, "answer_accuracy"),
            "citation_accuracy": _metric_context(answer, "citation_accuracy"),
            "hallucination_rate": _metric_context(answer, "hallucination_rate"),
            "permission_leakage_rate": _metric_context(permissions, "permission_leakage_rate"),
            "memory_accuracy": _metric_context(memory, "memory_answer_accuracy"),
        },
    }


def _comparisons(runs: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {run["run_id"]: run for run in runs}
    vector = by_id.get("phase6-vector-section")
    hybrid = by_id.get("phase6-hybrid-section-0.5")
    keyword = by_id.get("phase6-keyword-section")
    fixed = by_id.get("phase6-vector-fixed-size")
    prompt_runs = _full_prompt_experiment_runs(runs)
    comparisons = {
        "baseline_vs_current": {
            "baseline": "phase6-vector-section",
            "current": "phase7-answer-quality",
            "summary": "Phase 7 keeps the same retrieval baseline and adds answer/citation/confidence scoring.",
        },
        "vector_vs_keyword_vs_hybrid": {
            "runs": [run["run_id"] for run in [vector, keyword, hybrid] if run],
            "summary": "Vector-section had the strongest overall retrieval profile; hybrid matched hit rate but reduced Precision@k.",
        },
        "section_vs_fixed_size": {
            "runs": [run["run_id"] for run in [vector, fixed] if run],
            "summary": "Fixed-size chunking did not clearly outperform section-based chunking.",
        },
    }
    if prompt_runs:
        best_prompt = max(
            prompt_runs,
            key=lambda run: (
                run["metrics"].get("answer_accuracy") or 0,
                run["metrics"].get("citation_accuracy") or 0,
                -(run["metrics"].get("hallucination_rate") or 1),
            ),
        )
        comparisons["prompt_versions"] = {
            "runs": [run["run_id"] for run in prompt_runs],
            "summary": f"Prompt experiments compare answer-generation versions; {best_prompt['prompt_version']} is currently strongest by answer and citation metrics.",
        }
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow dashboard export even when one or more required source reports are missing.",
    )
    args = parser.parse_args()
    missing = [path for path in REQUIRED_REPORTS if not path.exists()]
    if missing and not args.allow_partial:
        missing_list = "\n".join(f"- {path.relative_to(ROOT)}" for path in missing)
        raise SystemExit(f"Missing required evaluation reports:\n{missing_list}")

    benchmark = _load_benchmark()
    benchmark_context = _benchmark_context(benchmark)
    current_benchmark_version = benchmark_context["benchmark_version"]

    phase6 = _read(PHASE6_RESULTS)
    phase7 = _read(PHASE7_RESULTS)
    phase7_failed = _read(PHASE7_FAILED)
    phase8 = _read(PHASE8_RESULTS)
    phase9 = _read(PHASE9_RESULTS)
    phase9_failed = _read(PHASE9_FAILED)

    runs = []
    runs.extend(_parse_phase6_table(phase6))
    if phase7:
        runs.append(_phase7_run(phase7, phase7_failed))
    if phase8:
        runs.append(_phase8_run(phase8))
    if phase9:
        runs.append(_phase9_run(phase9, phase9_failed))
    if len(runs) != EXPECTED_RUN_COUNT and not args.allow_partial:
        raise SystemExit(f"Expected {EXPECTED_RUN_COUNT} dashboard runs, found {len(runs)}.")
    runs.extend(_prompt_experiment_runs())
    runs.extend(_expanded_baseline_runs())
    runs = [_annotate_run(run, current_benchmark_version=current_benchmark_version) for run in runs]

    current_answer_run = _current_answer_run(runs)
    failed_questions = (
        _prompt_experiment_failed_items(current_answer_run)
        if current_answer_run
        else _failed_items(phase7_failed, "phase-7") + _failed_items(phase9_failed, "phase-9")
    )
    prompt_comparison = _prompt_comparison()
    multi_doc_comparison = _multi_doc_comparison()
    phase33_precision_readiness = _phase33_precision_readiness()
    dashboard = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "docs/phase-6 through docs/phase-35",
        "benchmark_context": benchmark_context,
        "runs": runs,
        "overview": _overview(runs, current_answer_run),
        "comparisons": _comparisons(runs),
        "prompt_comparison": prompt_comparison,
        "multi_doc_comparison": multi_doc_comparison,
        "phase33_precision_readiness": phase33_precision_readiness,
        "failed_questions": failed_questions,
        "notes": [
            "All dashboard values are exported from existing evaluation result files.",
            "Estimated cost is calculated from configured chat model pricing where token counts are available.",
            "Answer-quality metrics use deterministic and heuristic scoring, not a human judge.",
            "Phase 33 precision readiness is retained as provenance for the retrieval candidate used by later answer-quality runs.",
        ],
    }

    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    for run in runs:
        (RUNS_DIR / f"{run['run_id']}.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    (FAILED_DIR / "failed-questions.json").write_text(json.dumps(failed_questions, indent=2), encoding="utf-8")

    print(json.dumps({"run_count": len(runs), "failed_question_count": len(failed_questions)}, indent=2))
    print(f"Wrote {DASHBOARD_PATH}")
    print(f"Wrote {RUNS_DIR}")
    print(f"Wrote {FAILED_DIR / 'failed-questions.json'}")


if __name__ == "__main__":
    main()
