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

from apps.api.app.retrieval.reranker import rerank_chunks
from apps.api.app.retrieval.types import RetrievedChunk


BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
BASELINE_PATH = ROOT / "data/evaluation/expanded-baseline/phase32-expanded-retrieval.json"
OUTPUT_PATH = ROOT / "data/evaluation/phase33-precision-diagnostics.json"
REPORT_PATH = ROOT / "docs/phase-33/precision-diagnostics.md"
CHECKLIST_PATH = ROOT / "docs/phase-33/checklist.md"
VERIFICATION_PATH = ROOT / "docs/phase-33/verification.md"

EXCLUDED_TYPES = {"permission_restricted", "missing_information"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _average(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def _expected_documents(question: dict[str, Any]) -> list[str]:
    if question.get("question_type") in EXCLUDED_TYPES:
        return []
    return list(question.get("expected_source_document") or [])


def _result_rows(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows = baseline.get("summary", {}).get("results") or []
    if not isinstance(rows, list):
        raise ValueError("Phase 32 baseline artifact does not contain summary.results")
    return rows


def _benchmark_by_id(benchmark: dict[str, Any]) -> dict[str, dict[str, Any]]:
    questions = benchmark.get("questions") or []
    return {str(question["question_id"]): question for question in questions}


def _metrics_for_k(rows: list[dict[str, Any]], questions: dict[str, dict[str, Any]], k: int) -> dict[str, Any]:
    precision_values: list[float] = []
    all_hit_values: list[float] = []
    any_hit_values: list[float] = []
    recall_values: list[float] = []
    mrr_values: list[float] = []
    failed_questions: list[str] = []
    by_type: dict[str, dict[str, Any]] = {}

    for row in rows:
        question = questions[row["question_id"]]
        expected = set(_expected_documents(question))
        if not expected:
            continue

        chunks = row.get("retrieved_chunks") or []
        top_chunks = chunks[:k]
        retrieved_documents = [chunk["document_id"] for chunk in top_chunks]
        matched_documents = expected.intersection(retrieved_documents)
        question_type = str(question.get("question_type") or "unknown")

        precision = sum(1 for document_id in retrieved_documents if document_id in expected) / k
        any_hit = 1.0 if matched_documents else 0.0
        all_hit = 1.0 if matched_documents == expected else 0.0
        recall = len(matched_documents) / len(expected)
        reciprocal_rank = 0.0
        for rank, document_id in enumerate(retrieved_documents, start=1):
            if document_id in expected:
                reciprocal_rank = 1.0 / rank
                break

        precision_values.append(precision)
        any_hit_values.append(any_hit)
        all_hit_values.append(all_hit)
        recall_values.append(recall)
        mrr_values.append(reciprocal_rank)

        bucket = by_type.setdefault(
            question_type,
            {
                "question_count": 0,
                "precision_values": [],
                "all_hit_values": [],
                "recall_values": [],
                "mrr_values": [],
                "failed_questions": [],
            },
        )
        bucket["question_count"] += 1
        bucket["precision_values"].append(precision)
        bucket["all_hit_values"].append(all_hit)
        bucket["recall_values"].append(recall)
        bucket["mrr_values"].append(reciprocal_rank)
        if not all_hit:
            failed_questions.append(row["question_id"])
            bucket["failed_questions"].append(row["question_id"])

    type_summary = {
        question_type: {
            "question_count": bucket["question_count"],
            "precision_at_k": _average(bucket["precision_values"]),
            "all_sources_hit": _average(bucket["all_hit_values"]),
            "expected_source_recall": _average(bucket["recall_values"]),
            "mrr": _average(bucket["mrr_values"]),
            "failed_question_count": len(bucket["failed_questions"]),
            "failed_questions": bucket["failed_questions"],
        }
        for question_type, bucket in sorted(by_type.items())
    }

    return {
        "top_k": k,
        "source_question_count": len(precision_values),
        "any_source_hit": _average(any_hit_values),
        "all_sources_hit": _average(all_hit_values),
        "expected_source_recall": _average(recall_values),
        "precision_at_k": _average(precision_values),
        "mrr": _average(mrr_values),
        "failed_question_count": len(failed_questions),
        "failed_questions": failed_questions,
        "by_question_type": type_summary,
        "phase33_gate": {
            "precision_target_met": _average(precision_values) >= 0.75,
            "recall_gate_met": _average(recall_values) >= 0.95,
            "mrr_gate_met": _average(mrr_values) >= 0.95,
        },
    }


def _query_with_memory(question: dict[str, Any]) -> str:
    previous_turns = question.get("previous_turns") or []
    if not previous_turns:
        return str(question["question"])
    context = "\n".join(f"{turn['role']}: {turn['content']}" for turn in previous_turns)
    return f"Previous conversation:\n{context}\n\nFollow-up question:\n{question['question']}"


def _chunk_from_saved(row: dict[str, Any]) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(row["chunk_id"]),
        document_id=str(row["document_id"]),
        document_title=str(row.get("document_title") or row["document_id"]),
        section_heading=str(row.get("section_heading") or ""),
        content=str(row.get("content") or row.get("content_preview") or ""),
        access_roles=list(row.get("access_roles") or []),
        restricted=bool(row.get("restricted")),
        sensitivity=str(row.get("sensitivity") or "internal"),
        rank=int(row.get("rank") or 0),
        score=float(row.get("score") or 0.0),
        vector_score=float(row.get("vector_score") or row.get("score") or 0.0),
        keyword_score=row.get("keyword_score"),
        hybrid_score=row.get("hybrid_score"),
        retrieval_source=str(row.get("retrieval_source") or "vector"),
    )


def _metrics_for_saved_rerank(rows: list[dict[str, Any]], questions: dict[str, dict[str, Any]], k: int) -> dict[str, Any]:
    reranked_rows: list[dict[str, Any]] = []
    for row in rows:
        question = questions[row["question_id"]]
        chunks = [_chunk_from_saved(chunk) for chunk in row.get("retrieved_chunks") or []]
        reranked = rerank_chunks(_query_with_memory(question), chunks)
        reranked_rows.append(
            {
                **row,
                "retrieved_chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "document_title": chunk.document_title,
                        "section_heading": chunk.section_heading,
                        "access_roles": chunk.access_roles,
                        "restricted": chunk.restricted,
                        "sensitivity": chunk.sensitivity,
                        "rank": chunk.rank,
                        "score": chunk.score,
                        "vector_score": chunk.vector_score,
                        "keyword_score": chunk.keyword_score,
                        "hybrid_score": chunk.hybrid_score,
                        "retrieval_source": chunk.retrieval_source,
                    }
                    for chunk in reranked
                ],
            }
        )
    metrics = _metrics_for_k(reranked_rows, questions, k)
    metrics["method"] = "saved_top5_lexical_rerank"
    return metrics


def _candidate_summary(metrics_by_k: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "top_k": item["top_k"],
            "precision_at_k": item["precision_at_k"],
            "expected_source_recall": item["expected_source_recall"],
            "all_sources_hit": item["all_sources_hit"],
            "mrr": item["mrr"],
            "failed_question_count": item["failed_question_count"],
            "meets_phase33_precision_target": item["phase33_gate"]["precision_target_met"],
            "meets_phase33_recall_gate": item["phase33_gate"]["recall_gate_met"],
            "meets_phase33_mrr_gate": item["phase33_gate"]["mrr_gate_met"],
        }
        for item in metrics_by_k
    ]


def _write_report(result: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_rows = _candidate_summary(result["top_k_replay"])
    lines = [
        "# Phase 33 Precision Diagnostics",
        "",
        f"Generated at: {result['generated_at']}",
        "",
        "## Scope",
        "",
        "- Input run: `phase32-expanded-retrieval`.",
        "- Input artifact: `data/evaluation/expanded-baseline/phase32-expanded-retrieval.json`.",
        "- Method: local replay of the saved Phase 32 retrieved chunk order with smaller top-k cuts.",
        "- Network/API use: none.",
        "- This is diagnostic evidence only; it does not prove a live retrieval improvement.",
        "",
        "## Top-K Replay",
        "",
        "| Top K | Precision@k | Source Recall | All-Sources Hit | MRR | Failed Source Questions | Precision Target | Recall Gate | MRR Gate |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in candidate_rows:
        lines.append(
            "| {top_k} | {precision_at_k:.3f} | {expected_source_recall:.3f} | {all_sources_hit:.3f} | {mrr:.3f} | {failed_question_count} | {precision} | {recall} | {mrr_gate} |".format(
                top_k=row["top_k"],
                precision_at_k=row["precision_at_k"],
                expected_source_recall=row["expected_source_recall"],
                all_sources_hit=row["all_sources_hit"],
                mrr=row["mrr"],
                failed_question_count=row["failed_question_count"],
                precision="pass" if row["meets_phase33_precision_target"] else "fail",
                recall="pass" if row["meets_phase33_recall_gate"] else "fail",
                mrr_gate="pass" if row["meets_phase33_mrr_gate"] else "fail",
            )
        )

    best_precision = max(candidate_rows, key=lambda row: row["precision_at_k"])
    best_gated = [
        row
        for row in candidate_rows
        if row["meets_phase33_recall_gate"] and row["meets_phase33_mrr_gate"]
    ]
    best_gated_row = max(best_gated, key=lambda row: row["precision_at_k"]) if best_gated else None

    lines.extend(
        [
            "",
            "## Saved Top-5 Lexical Rerank Replay",
            "",
            "This replay applies the Phase 33 lexical reranker to the saved top-5 chunks from Phase 32. It cannot evaluate chunks outside that saved top-5 pool.",
            "",
            "| Top K | Precision@k | Source Recall | All-Sources Hit | MRR | Failed Source Questions | Precision Target | Recall Gate | MRR Gate |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in _candidate_summary(result["saved_top5_lexical_rerank_replay"]):
        lines.append(
            "| {top_k} | {precision_at_k:.3f} | {expected_source_recall:.3f} | {all_sources_hit:.3f} | {mrr:.3f} | {failed_question_count} | {precision} | {recall} | {mrr_gate} |".format(
                top_k=row["top_k"],
                precision_at_k=row["precision_at_k"],
                expected_source_recall=row["expected_source_recall"],
                all_sources_hit=row["all_sources_hit"],
                mrr=row["mrr"],
                failed_question_count=row["failed_question_count"],
                precision="pass" if row["meets_phase33_precision_target"] else "fail",
                recall="pass" if row["meets_phase33_recall_gate"] else "fail",
                mrr_gate="pass" if row["meets_phase33_mrr_gate"] else "fail",
            )
        )

    best_reranked = max(
        _candidate_summary(result["saved_top5_lexical_rerank_replay"]),
        key=lambda row: (
            row["meets_phase33_recall_gate"],
            row["meets_phase33_mrr_gate"],
            row["precision_at_k"],
        ),
    )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"- Highest replayed precision is top-{best_precision['top_k']} at `{best_precision['precision_at_k']:.3f}`, but recall is `{best_precision['expected_source_recall']:.3f}`.",
        ]
    )
    if best_gated_row:
        lines.append(
            f"- Best replayed cut that keeps recall and MRR gates is top-{best_gated_row['top_k']} with Precision@k `{best_gated_row['precision_at_k']:.3f}`."
        )
    lines.extend(
        [
            f"- Saved top-5 lexical rerank replay reaches Precision@k `{best_reranked['precision_at_k']:.3f}` at top-{best_reranked['top_k']} with recall `{best_reranked['expected_source_recall']:.3f}`.",
            "- A top-k-only change does not meet all Phase 33 targets. The next implementation step needs a ranking or filtering change verified by a live retrieval run.",
            "- Permission leakage is not measured by this replay; Phase 33 completion still requires the permission safety check or an equivalent live safety run.",
            "",
            "## Failed Questions At Best Gated Cut",
            "",
        ]
    )
    if best_gated_row:
        best_gated_detail = next(item for item in result["top_k_replay"] if item["top_k"] == best_gated_row["top_k"])
        failed = best_gated_detail["failed_questions"]
        lines.append(", ".join(failed) if failed else "None")
    else:
        lines.append("No replayed cut preserved both recall and MRR gates.")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _write_checklist(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Phase 33 Checklist",
                "",
                "- [x] Start from Phase 32 expanded retrieval baseline.",
                "- [x] Add no-network precision diagnostics for saved baseline artifacts.",
                "- [x] Identify whether top-k-only tuning can satisfy Phase 33 gates.",
                "- [x] Implement an opt-in lexical reranking candidate.",
                "- [ ] Run before/after retrieval evaluation on benchmark v1.1.",
                "- [ ] Verify source recall >= 0.95, MRR >= 0.95, Precision@k >= 0.75, and permission leakage = 0.000.",
                "- [ ] Export dashboard data with measured Phase 33 run IDs.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_verification(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_gated = [
        row
        for row in _candidate_summary(result["top_k_replay"])
        if row["meets_phase33_recall_gate"] and row["meets_phase33_mrr_gate"]
    ]
    best_gated_row = max(best_gated, key=lambda row: row["precision_at_k"]) if best_gated else None
    lines = [
        "# Phase 33 Verification",
        "",
        f"Generated at: {result['generated_at']}",
        "",
        "## Completed Checks",
        "",
        "- `python scripts/test_phase33_reranker.py`",
        "- `python scripts/analyze_phase33_precision.py`",
        "",
        "## Diagnostic Result",
        "",
    ]
    if best_gated_row:
        lines.append(
            f"- Best no-network top-k replay preserving recall and MRR gates: top-{best_gated_row['top_k']} with Precision@k `{best_gated_row['precision_at_k']:.3f}`."
        )
    lines.extend(
        [
            "- Top-k-only replay does not meet the Phase 33 Precision@k target of `0.75` while preserving recall and MRR.",
            "- Saved top-5 lexical rerank replay is included as a deterministic candidate check, but it cannot inspect chunks outside the saved top-5 pool.",
            "- OpenAI-backed live retrieval reruns were skipped because external API use was not approved for this continuation.",
            "- Permission safety was not re-run in this diagnostic-only step.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(output_path: Path = OUTPUT_PATH, report_path: Path = REPORT_PATH) -> dict[str, Any]:
    benchmark = _load_json(BENCHMARK_PATH)
    baseline = _load_json(BASELINE_PATH)
    questions = _benchmark_by_id(benchmark)
    rows = _result_rows(baseline)
    top_k_replay = [_metrics_for_k(rows, questions, k) for k in range(1, 6)]
    saved_top5_lexical_rerank_replay = [_metrics_for_saved_rerank(rows, questions, k) for k in range(1, 6)]
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "benchmark_version": benchmark.get("benchmark_version"),
        "baseline_run": {
            "run_id": baseline.get("dashboard_run", {}).get("run_id") or "phase32-expanded-retrieval",
            "run_name": baseline.get("summary", {}).get("run_name"),
            "retrieval_mode": baseline.get("summary", {}).get("retrieval_mode"),
            "chunking_strategy": baseline.get("summary", {}).get("chunking_strategy"),
            "top_k": baseline.get("summary", {}).get("top_k"),
            "precision_at_k": baseline.get("summary", {}).get("precision_at_k"),
            "expected_source_recall": baseline.get("summary", {}).get("expected_source_recall"),
            "all_sources_hit": baseline.get("summary", {}).get("all_sources_hit"),
            "mrr": baseline.get("summary", {}).get("mrr"),
        },
        "top_k_replay": top_k_replay,
        "saved_top5_lexical_rerank_replay": saved_top5_lexical_rerank_replay,
        "notes": [
            "This diagnostic replays saved Phase 32 result ordering only.",
            "It does not call OpenAI, query Postgres, or prove a live retrieval change.",
            "Lexical rerank replay is limited to chunks already present in the saved top-5 artifact.",
            "Phase 33 completion still requires a measured before/after live retrieval run and permission safety verification.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_report(result, report_path)
    _write_checklist(CHECKLIST_PATH)
    _write_verification(VERIFICATION_PATH, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Phase 33 precision tradeoffs from saved Phase 32 artifacts.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    result = run(output_path=args.output, report_path=args.report)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "report": str(args.report),
                "top_k_replay": _candidate_summary(result["top_k_replay"]),
                "saved_top5_lexical_rerank_replay": _candidate_summary(result["saved_top5_lexical_rerank_replay"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
