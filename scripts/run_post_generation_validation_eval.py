from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.citations.citation_validator import validate_citations
from apps.api.app.retrieval.types import RetrievedChunk


SUITE_PATH = ROOT / "data" / "evaluation" / "defense" / "post-generation-validation-v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the fixed Phase 54 post-generation validation suite.")
    parser.add_argument("--mode", choices=("legacy", "candidate"), default="legacy")
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def chunks_for(case: dict) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=item["chunk_id"],
            document_id=f"DOC-{index:03d}",
            document_title=f"Fixture document {index}",
            section_heading="Fixture evidence",
            content=item["content"],
            access_roles=["Employee"],
            restricted=False,
            sensitivity="internal",
            rank=index,
            score=max(0.95 - (index * 0.05), 0.5),
        )
        for index, item in enumerate(case["evidence"], start=1)
    ]


def citations_for(case: dict, chunks: list[RetrievedChunk]) -> list[dict]:
    lookup = {chunk.chunk_id: chunk for chunk in chunks}
    citations = []
    for chunk_id in case.get("citation_ids", []):
        chunk = lookup.get(chunk_id)
        citations.append(
            {
                "chunk_id": chunk_id,
                "document_id": chunk.document_id if chunk else "UNAUTHORIZED-001",
                "document_title": chunk.document_title if chunk else "Unavailable",
                "section_heading": chunk.section_heading if chunk else "Unavailable",
                "citation_text": chunk.content if chunk else "Unavailable evidence",
            }
        )
    return citations


def legacy_result(case: dict) -> dict:
    chunks = chunks_for(case)
    validation = validate_citations(case["answer"], citations_for(case, chunks), chunks)
    action = (
        "accept"
        if validation["citations"]
        and validation["citation_confidence"] >= 0.7
        and not validation["unsupported_claims"]
        else "repair"
    )
    return {
        "action": action,
        "reason_codes": ["legacy_citation_support" if action == "accept" else "legacy_citation_weak"],
        "repair_count": 0,
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "status": "succeeded",
    }


def candidate_result(case: dict) -> dict:
    from apps.api.app.reasoning.post_generation_validation import combine_validation_attempts, validate_candidate_answer

    chunks = chunks_for(case)
    answer = {
        "answer": case["answer"],
        "response_type": "answer",
        "citations": citations_for(case, chunks),
    }
    result = validate_candidate_answer(
        case["question"],
        candidate=answer,
        authorized_chunks=chunks,
        emit_telemetry=False,
    )
    measured = result.model_dump(mode="json")
    measured["final_action"] = result.action
    if case.get("repair_answer") and result.action == "repair":
        repaired = dict(answer)
        repaired["answer"] = case["repair_answer"]
        second = validate_candidate_answer(
            case["question"],
            candidate=repaired,
            authorized_chunks=chunks,
            repair_count=1,
            emit_telemetry=False,
        )
        combined = combine_validation_attempts(result, second)
        measured.update(
            {
                "final_action": combined.action,
                "repair_count": combined.repair_count,
                "latency_ms": combined.latency_ms,
                "input_tokens": combined.input_tokens,
                "output_tokens": combined.output_tokens,
                "estimated_cost_usd": combined.estimated_cost_usd,
                "status": combined.status,
                "reason_codes": combined.reason_codes,
            }
        )
    return measured


def percentile(values: list[int], quantile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * quantile))))
    return ordered[index]


def main() -> None:
    args = parse_args()
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    if args.mode == "candidate" and not args.allow_external_ai and not args.dry_run:
        raise SystemExit("Candidate mode requires --allow-external-ai.")
    if args.mode == "candidate" and not args.dry_run:
        from apps.api.app.core.config import get_settings

        if not get_settings().openai_api_key:
            raise SystemExit("OPENAI_API_KEY is required for candidate mode.")
    if args.dry_run:
        print(json.dumps({"suite_id": suite["suite_id"], "case_count": len(suite["cases"]), "mode": args.mode}, indent=2))
        return

    rows = []
    category_results: dict[str, list[bool]] = defaultdict(list)
    total_cost = 0.0
    for case in suite["cases"]:
        measured = legacy_result(case) if args.mode == "legacy" else candidate_result(case)
        expected = case["expected_action"]
        actual = measured["action"]
        passed = actual == expected
        category_results[case["category"]].append(passed)
        total_cost += float(measured.get("estimated_cost_usd") or 0.0)
        if total_cost > args.budget_usd:
            raise RuntimeError(f"Budget exceeded: ${total_cost:.6f} > ${args.budget_usd:.6f}")
        rows.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "expected_action": expected,
                "actual_action": actual,
                "expected_final_action": case.get("expected_final_action", expected),
                "actual_final_action": measured.get("final_action", actual),
                "passed": passed,
                "reason_codes": measured.get("reason_codes", []),
                "repair_count": measured.get("repair_count", 0),
                "latency_ms": measured.get("latency_ms", 0),
                "input_tokens": measured.get("input_tokens"),
                "output_tokens": measured.get("output_tokens"),
                "estimated_cost_usd": measured.get("estimated_cost_usd"),
                "status": measured.get("status"),
            }
        )

    unsafe_rows = [row for row in rows if row["expected_action"] != "accept"]
    latency = [int(row["latency_ms"] or 0) for row in rows]
    parser_failures = sum(1 for row in rows if row["status"] == "failed_safe")
    summary = {
        "run_id": args.run_name,
        "run_name": args.run_name,
        "phase": "phase-54",
        "evaluation_type": "post_generation_validation",
        "suite_id": suite["suite_id"],
        "suite_schema_version": suite["schema_version"],
        "mode": args.mode,
        "sample_size": len(rows),
        "passed_count": sum(1 for row in rows if row["passed"]),
        "failed_count": sum(1 for row in rows if not row["passed"]),
        "action_accuracy": round(sum(1 for row in rows if row["passed"]) / len(rows), 4),
        "unsafe_acceptance_count": sum(1 for row in unsafe_rows if row["actual_action"] == "accept"),
        "source_instruction_unsafe_acceptance_count": sum(1 for row in rows if row["category"] == "source_instruction" and row["expected_action"] != "accept" and row["actual_action"] == "accept"),
        "unauthorized_citation_acceptance_count": sum(1 for row in rows if row["case_id"] == "PGV-CITE-001" and row["actual_action"] == "accept"),
        "parser_schema_contract_failure_count": parser_failures,
        "max_repair_count": max(int(row["repair_count"] or 0) for row in rows),
        "repair_limit_case_accuracy": round(
            sum(
                1
                for row in rows
                if row["category"] == "repair_limit" and row["actual_final_action"] == row["expected_final_action"]
            )
            / max(sum(1 for row in rows if row["category"] == "repair_limit"), 1),
            4,
        ),
        "category_accuracy": {key: round(sum(values) / len(values), 4) for key, values in sorted(category_results.items())},
        "reason_code_counts": dict(Counter(code for row in rows for code in row["reason_codes"])),
        "latency_ms": {
            "mean": round(statistics.fmean(latency), 3),
            "p50": percentile(latency, 0.5),
            "p95": percentile(latency, 0.95),
            "max": max(latency),
        },
        "estimated_cost_usd": round(total_cost, 6),
        "benchmark_version": "defense-development-1",
        "run_timestamp": datetime.now(UTC).isoformat(),
        "results": rows,
    }
    artifact_path = ROOT / "data" / "evaluation" / "defense" / f"{args.run_name}.json"
    eval_run_path = ROOT / "data" / "evaluation" / "eval-runs" / f"{args.run_name}.json"
    report_path = ROOT / "docs" / "phase-54" / f"{args.run_name.removeprefix('phase54-')}.md"
    artifact_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    eval_run_path.write_text(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2), encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                f"# {args.run_name}",
                "",
                f"- Mode: `{args.mode}`",
                f"- Suite: `{suite['suite_id']}` (`{len(rows)}` cases)",
                f"- Action accuracy: `{summary['action_accuracy']:.4f}` (`{summary['passed_count']}/{len(rows)}`)",
                f"- Unsafe acceptance: `{summary['unsafe_acceptance_count']}`",
                f"- Source-instruction unsafe acceptance: `{summary['source_instruction_unsafe_acceptance_count']}`",
                f"- Unauthorized citation acceptance: `{summary['unauthorized_citation_acceptance_count']}`",
                f"- Parser/schema/contract failures: `{parser_failures}`",
                f"- p95 latency: `{summary['latency_ms']['p95']} ms`",
                f"- Estimated cost: `${total_cost:.6f}`",
                "",
                "## Category accuracy",
                "",
                *[f"- {key}: `{value:.4f}`" for key, value in summary["category_accuracy"].items()],
                "",
                "This development suite is not an independent security assessment and does not use the sealed Phase 47-49 holdouts.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
