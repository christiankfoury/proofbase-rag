from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.db.session import get_connection
from apps.api.app.evaluation.permission_metrics import (
    authorized_retrieval_accuracy,
    blocked_answer_accuracy,
    permission_leakage,
    restricted_citation_leakage,
    unauthorized_chunk_exposure,
)
from apps.api.app.generation.answer_generator import generate_answer
from apps.api.app.permissions.access_control import role_can_access, unauthorized_chunks_reached_generation
from apps.api.app.retrieval.config import default_retrieval_config
from apps.api.app.retrieval.retriever import retrieve_chunks


BENCHMARK_PATH = Path("data/evaluation/benchmark-questions.json")
REPORT_PATH = Path("docs/phase-8/permission-evaluation-results.md")
PHASE33_REPORT_PATH = Path("docs/phase-33/permission-candidate-results.md")
EXTERNAL_EMBEDDINGS_APPROVAL_MESSAGE = (
    "The Phase 33 vector_lexical_rerank permission run sends benchmark question text to the external embeddings API. "
    "Re-run with --allow-external-embeddings only after explicit user approval."
)


def _load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _average(values: list[float | None]) -> str:
    real_values = [value for value in values if value is not None]
    if not real_values:
        return "pending"
    return f"{mean(real_values):.3f}"


def _document_access_roles() -> dict[str, list[str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            select external_document_id, access_roles
            from documents
            where status = 'active'
            """
        ).fetchall()
    return {row["external_document_id"]: list(row["access_roles"]) for row in rows}


def _authorized_role_for_documents(document_ids: list[str], role_by_doc: dict[str, list[str]]) -> str | None:
    if not document_ids:
        return None
    candidate_roles = set(role_by_doc.get(document_ids[0], []))
    for document_id in document_ids[1:]:
        candidate_roles &= set(role_by_doc.get(document_id, []))
    preferred_order = ["Manager", "HR Admin", "IT Admin", "Sales Representative", "Employee", "IT/Admin"]
    for role in preferred_order:
        if role in candidate_roles:
            return "IT Admin" if role == "IT/Admin" else role
    return None


def _retrieved_document_ids(chunks) -> list[str]:
    return list(dict.fromkeys(chunk.document_id for chunk in chunks))


def _write_report(summary: dict, unauthorized_rows: list[dict], authorized_rows: list[dict], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    title = (
        "Phase 33 Permission Candidate Results"
        if summary["retrieval_mode"] == "vector_lexical_rerank"
        else "Phase 8 Permission Evaluation Results"
    )
    lines = [
        f"# {title}",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Run Summary",
        "",
        f"- Restricted benchmark questions tested: {summary['restricted_question_count']}",
        f"- Authorized source-access tests: {summary['authorized_test_count']}",
        f"- Retrieval mode: {summary['retrieval_mode']}",
        f"- Chunking strategy: {summary['chunking_strategy']}",
        f"- Top K: {summary['top_k']}",
        f"- Reranker: {summary['reranker']}",
        f"- Rerank candidate limit: {summary['rerank_candidate_limit']}",
        f"- Permission leakage rate: {summary['permission_leakage_rate']}",
        f"- Blocked-answer accuracy: {summary['blocked_answer_accuracy']}",
        f"- Unauthorized chunk exposure rate: {summary['unauthorized_chunk_exposure_rate']}",
        f"- Restricted citation leakage rate: {summary['restricted_citation_leakage_rate']}",
        f"- Unauthorized chunks reached generation rate: {summary['unauthorized_chunks_reached_generation_rate']}",
        f"- Authorized retrieval accuracy: {summary['authorized_retrieval_accuracy']}",
        f"- Authorized answer accuracy: {summary['authorized_answer_accuracy']}",
        "",
        "## Unauthorized Restricted Questions",
        "",
        "| Question ID | Role | Expected Restricted Docs | Retrieved Docs | Response | Chunk Exposure | Citation Leak | Permission Leak |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in unauthorized_rows:
        lines.append(
            "| {question_id} | {user_role} | {expected_documents} | {retrieved_documents} | {response_type} | {unauthorized_chunk_exposure} | {restricted_citation_leakage} | {permission_leakage} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Authorized Source-Access Tests",
            "",
            "| Source Question | Authorized Role | Expected Docs | Retrieved Docs | Retrieval Accuracy | Answer Accuracy |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for row in authorized_rows:
        lines.append(
            "| {question_id} | {authorized_role} | {expected_documents} | {retrieved_documents} | {authorized_retrieval_accuracy} | {authorized_answer_accuracy} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Unauthorized chunk exposure is measured by checking whether the expected restricted source document appears in retrieved chunks for the unauthorized role.",
            "- Restricted citation leakage is measured by checking whether unauthorized responses cite expected restricted source documents.",
            "- Authorized retrieval accuracy confirms the expected restricted source can be retrieved by at least one role with access.",
            "- Authorized answer accuracy is pending by default to avoid extra chat-completion cost; run with `--include-authorized-generation` to score it.",
            "- Audit logs are written to `audit_logs` and do not include source text.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _default_run_name(retrieval_mode: str) -> str:
    if retrieval_mode == "vector_lexical_rerank":
        return "phase33-vector-lexical-rerank-permission-eval"
    return "phase-8-permission-eval"


def _default_report_path(retrieval_mode: str) -> Path:
    if retrieval_mode == "vector_lexical_rerank":
        return PHASE33_REPORT_PATH
    return REPORT_PATH


def _requires_external_embeddings_approval(retrieval_mode: str) -> bool:
    return retrieval_mode == "vector_lexical_rerank"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retrieval-mode",
        default="vector_only",
        choices=["vector_only", "vector_lexical_rerank", "keyword_only", "hybrid"],
    )
    parser.add_argument("--chunking-strategy", default="section_based")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rerank-candidate-limit", type=int, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--report-path", type=Path, default=None)
    parser.add_argument("--include-authorized-generation", action="store_true")
    parser.add_argument(
        "--allow-external-embeddings",
        action="store_true",
        help="Confirm explicit approval to send benchmark question text to the external embeddings API.",
    )
    args = parser.parse_args()

    if _requires_external_embeddings_approval(args.retrieval_mode) and not args.allow_external_embeddings:
        raise SystemExit(EXTERNAL_EMBEDDINGS_APPROVAL_MESSAGE)

    benchmark = _load_benchmark()
    run_name = args.run_name or _default_run_name(args.retrieval_mode)
    report_path = args.report_path or _default_report_path(args.retrieval_mode)
    config = default_retrieval_config(
        run_name=run_name,
        retrieval_mode=args.retrieval_mode,
        chunking_strategy=args.chunking_strategy,
        top_k=args.top_k,
        rerank_candidate_limit=args.rerank_candidate_limit,
    )
    role_by_doc = _document_access_roles()
    permission_questions = [
        question
        for question in benchmark["questions"]
        if question["question_type"] == "permission_restricted"
    ]

    unauthorized_rows = []
    authorized_rows = []

    for question in permission_questions:
        expected_documents = question.get("expected_source_document") or []
        chunks = retrieve_chunks(question["question"], question["user_role"], config)
        answer = generate_answer(
            question["question"],
            chunks,
            expected_behavior=question["expected_behavior"],
            user_role=question["user_role"],
        )
        unauthorized_rows.append(
            {
                "question_id": question["question_id"],
                "user_role": question["user_role"],
                "expected_documents": ", ".join(expected_documents),
                "retrieved_documents": ", ".join(_retrieved_document_ids(chunks)) or "None",
                "response_type": answer["response_type"],
                "unauthorized_chunk_exposure": unauthorized_chunk_exposure(question, chunks),
                "restricted_citation_leakage": restricted_citation_leakage(question, answer["citations"]),
                "permission_leakage": permission_leakage(question, chunks, answer["citations"]),
                "blocked_answer_accuracy": blocked_answer_accuracy(answer["response_type"]),
                "unauthorized_chunks_reached_generation": 1.0
                if unauthorized_chunks_reached_generation(chunks, question["user_role"])
                else 0.0,
            }
        )

        authorized_role = _authorized_role_for_documents(expected_documents, role_by_doc)
        if not authorized_role:
            continue
        if not all(role_can_access(role_by_doc.get(document_id, []), authorized_role) for document_id in expected_documents):
            continue
        authorized_chunks = retrieve_chunks(question["question"], authorized_role, config)
        authorized_answer_accuracy = "pending"
        if args.include_authorized_generation:
            authorized_answer = generate_answer(
                question["question"],
                authorized_chunks,
                expected_behavior="answer",
                user_role=authorized_role,
            )
            authorized_answer_accuracy = (
                "1.0"
                if authorized_answer["response_type"] in {"answer", "partial_answer"}
                else "0.0"
            )
        authorized_rows.append(
            {
                "question_id": question["question_id"],
                "authorized_role": authorized_role,
                "expected_documents": ", ".join(expected_documents),
                "retrieved_documents": ", ".join(_retrieved_document_ids(authorized_chunks)) or "None",
                "authorized_retrieval_accuracy": authorized_retrieval_accuracy(expected_documents, authorized_chunks),
                "authorized_answer_accuracy": authorized_answer_accuracy,
            }
        )

    authorized_answer_values = [
        float(row["authorized_answer_accuracy"])
        for row in authorized_rows
        if row["authorized_answer_accuracy"] != "pending"
    ]
    summary = {
        "restricted_question_count": len(unauthorized_rows),
        "authorized_test_count": len(authorized_rows),
        "retrieval_mode": config.retrieval_mode,
        "chunking_strategy": config.chunking_strategy,
        "top_k": config.top_k,
        "reranker": config.reranker,
        "rerank_candidate_limit": config.rerank_candidate_limit,
        "permission_leakage_rate": _average([row["permission_leakage"] for row in unauthorized_rows]),
        "blocked_answer_accuracy": _average([row["blocked_answer_accuracy"] for row in unauthorized_rows]),
        "unauthorized_chunk_exposure_rate": _average([row["unauthorized_chunk_exposure"] for row in unauthorized_rows]),
        "restricted_citation_leakage_rate": _average([row["restricted_citation_leakage"] for row in unauthorized_rows]),
        "unauthorized_chunks_reached_generation_rate": _average(
            [row["unauthorized_chunks_reached_generation"] for row in unauthorized_rows]
        ),
        "authorized_retrieval_accuracy": _average([row["authorized_retrieval_accuracy"] for row in authorized_rows]),
        "authorized_answer_accuracy": _average(authorized_answer_values),
    }
    _write_report(summary, unauthorized_rows, authorized_rows, report_path=report_path)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
