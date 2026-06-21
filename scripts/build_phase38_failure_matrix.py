from __future__ import annotations

import json
import sys
import subprocess
from argparse import ArgumentParser
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_PATH = ROOT / "data/evaluation/failed-questions/failed-questions.json"
OUTPUT_JSON = ROOT / "data/evaluation/phase38-failure-matrix.json"
REPORT_PATH = ROOT / "docs/phase-38/failure-matrix.md"

REMEDIATION_BY_BUCKET = {
    "ambiguity_failure": "Return a clarification before generation when approval context is underspecified.",
    "multi_document_failure": "Keep visible for Phase 39 query decomposition and source-coverage planning.",
    "wrong_citation": "Prefer exact supporting chunks and backfill citations only from retrieved, permission-filtered chunks.",
    "unsupported_answer": "Treat adversarial source instructions as evidence, not assistant instructions.",
    "incomplete_answer": "Prompt for all supported required facts and exact thresholds when evidence is present.",
    "retrieval_miss": "Use the same memory-aware query rewrite path as the live assistant.",
}


def _load_failures(source_ref: str | None = None) -> list[dict[str, Any]]:
    if source_ref:
        git_path = str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/")
        result = subprocess.run(
            ["git", "show", f"{source_ref}:{git_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _bucket_failures(failures: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in failures:
        buckets[str(item.get("failure_type") or "unknown")].append(item)
    return dict(sorted(buckets.items()))


def _matrix(failures: list[dict[str, Any]], source_ref: str | None = None) -> dict[str, Any]:
    buckets = _bucket_failures(failures)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source_revision": source_ref,
        "source_run_id": failures[0].get("run_id") if failures else None,
        "source_benchmark_version": "1.1",
        "source_failed_question_count": len(failures),
        "buckets": [
            {
                "failure_type": failure_type,
                "count": len(items),
                "question_ids": [item["question_id"] for item in items],
                "primary_remediation": REMEDIATION_BY_BUCKET.get(failure_type, "Review manually."),
            }
            for failure_type, items in buckets.items()
        ],
    }


def _write_report(matrix: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 38 Failure Matrix",
        "",
        f"Generated at: {matrix['generated_at']}",
        "",
        f"- Source artifact: `{matrix['source_path']}`",
        f"- Source revision: `{matrix['source_revision'] or 'working tree'}`",
        f"- Source run: `{matrix['source_run_id']}`",
        f"- Benchmark version: `{matrix['source_benchmark_version']}`",
        f"- Failed questions: `{matrix['source_failed_question_count']}`",
        "",
        "| Bucket | Count | Question IDs | Primary remediation |",
        "| --- | ---: | --- | --- |",
    ]
    for bucket in matrix["buckets"]:
        lines.append(
            "| {failure_type} | `{count}` | {question_ids} | {primary_remediation} |".format(
                failure_type=bucket["failure_type"],
                count=bucket["count"],
                question_ids=", ".join(f"`{item}`" for item in bucket["question_ids"]),
                primary_remediation=bucket["primary_remediation"],
            )
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- This matrix is built from the current failed-question artifact before Phase 38 behavior changes.",
            "- Later Phase 38 dashboard exports refresh the failed-question artifact with post-remediation failures.",
            "- Benchmark expected answers, expected behavior, and expected sources are unchanged.",
            "- Multi-document orchestration gaps remain visible for Phase 39 rather than being hidden by benchmark edits.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = ArgumentParser(description="Build the Phase 38 answer-quality failure matrix.")
    parser.add_argument(
        "--source-ref",
        default=None,
        help="Optional Git ref to read data/evaluation/failed-questions/failed-questions.json from.",
    )
    args = parser.parse_args()

    failures = _load_failures(args.source_ref)
    matrix = _matrix(failures, source_ref=args.source_ref)
    OUTPUT_JSON.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    _write_report(matrix)
    print(json.dumps({"source_failed_question_count": len(failures), "bucket_count": len(matrix["buckets"])}, indent=2))
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
