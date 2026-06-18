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

DASHBOARD_PATH = ROOT / "data/evaluation/dashboard-summary.json"
RUNS_DIR = ROOT / "data/evaluation/eval-runs"
FAILED_DIR = ROOT / "data/evaluation/failed-questions"
PROMPT_EXPERIMENT_DIR = ROOT / "data/evaluation/prompt-experiments"
PROMPT_COMPARISON_PATH = PROMPT_EXPERIMENT_DIR / "prompt-comparison.json"
MULTI_DOC_EVAL_PATH = ROOT / "data/evaluation/multi-doc-eval.json"

REQUIRED_REPORTS = [
    PHASE6_RESULTS,
    PHASE7_RESULTS,
    PHASE7_FAILED,
    PHASE8_RESULTS,
    PHASE9_RESULTS,
    PHASE9_FAILED,
]
EXPECTED_RUN_COUNT = 8


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
        "notes": "Permission metrics measure restricted benchmark refusals and authorized source access.",
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
        "notes": "Memory is session-level only and is used for query rewriting, not source evidence.",
    }


def _prompt_experiment_runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not PROMPT_EXPERIMENT_DIR.exists():
        return runs
    for path in sorted(PROMPT_EXPERIMENT_DIR.glob("*-answer-generation-*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        summary = result["summary"]
        failed_questions = [item["question_id"] for item in result.get("failed_questions", [])]
        question_filter = summary.get("question_filter")
        run_id = summary["experiment_id"]
        run_name = summary["run_name"]
        if question_filter and question_filter != "all":
            run_id = path.stem
            run_name = f"{run_name}-{question_filter}"
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
        if question_filter is not None:
            run["question_filter"] = question_filter
        if summary.get("source_question_count") is not None:
            run["source_question_count"] = summary.get("source_question_count")
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
    path = PROMPT_EXPERIMENT_DIR / f"{run['run_id']}.json"
    if not path.exists():
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


def _prompt_comparison() -> dict[str, Any]:
    if not PROMPT_COMPARISON_PATH.exists():
        return {"best": {}, "comparisons": [], "prompt_versions": []}
    return json.loads(PROMPT_COMPARISON_PATH.read_text(encoding="utf-8"))


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

    current_answer_run = _current_answer_run(runs)
    failed_questions = (
        _prompt_experiment_failed_items(current_answer_run)
        if current_answer_run
        else _failed_items(phase7_failed, "phase-7") + _failed_items(phase9_failed, "phase-9")
    )
    prompt_comparison = _prompt_comparison()
    multi_doc_comparison = _multi_doc_comparison()
    dashboard = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "docs/phase-6 through docs/phase-16",
        "runs": runs,
        "overview": _overview(runs, current_answer_run),
        "comparisons": _comparisons(runs),
        "prompt_comparison": prompt_comparison,
        "multi_doc_comparison": multi_doc_comparison,
        "failed_questions": failed_questions,
        "notes": [
            "All dashboard values are exported from existing evaluation result files.",
            "Estimated cost is calculated from configured chat model pricing where token counts are available.",
            "Answer-quality metrics use deterministic and heuristic scoring, not a human judge.",
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
