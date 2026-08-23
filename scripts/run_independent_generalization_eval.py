from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.main import app
from apps.api.app.memory.session_store import add_message, create_session
from apps.api.app.permissions.access_control import role_can_access
from scripts.independent_generalization_common import (
    CORPUS_DIR,
    HOLDOUT_PATH,
    PROJECT_ID,
    ROOT as REPO_ROOT,
    USER_IDS,
    file_sha256,
    git_commit,
    load_suite,
    tree_sha256,
    validate_split,
    verify_holdout_preflight,
    write_json_atomic,
)
from scripts.phase48_generalization_scoring import (
    fact_score,
    forbidden_fact_asserted,
    substantive_unsupported_claims,
)


RESULTS_DIR = ROOT / "data/evaluation/independent-generalization/results"
EVAL_RUNS_DIR = ROOT / "data/evaluation/eval-runs"
PHASE_DOCS_DIR = ROOT / "docs/phase-47"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000002706"
DEFAULT_RETRIEVAL_MODE = "vector_lexical_rerank"
DEFAULT_TOP_K = 5
DEFAULT_RERANK_CANDIDATE_LIMIT = 20
DEFAULT_PROMPT_VERSION = "v8"
MAX_ESTIMATED_CASE_COST_USD = 0.02
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "Phase 47 sends authored questions, prior chat turns, uploaded synthetic fixture text, and permission-filtered "
    "retrieved snippets to external OpenAI embedding and chat-completion APIs. Re-run with --allow-external-ai "
    "only after explicit approval."
)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "has", "have", "if", "in",
    "is", "it", "of", "on", "or", "should", "that", "the", "their", "this", "to", "when", "with",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _fact_score(fact: str, text: str) -> float:
    return fact_score(fact, text)


def _average(values: list[float | None]) -> float | None:
    real = [float(value) for value in values if value is not None]
    return round(mean(real), 3) if real else None


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": numerator, "denominator": denominator, "value": round(numerator / denominator, 3) if denominator else None}


def _behavior_match(expected: str, actual: str | None) -> float:
    if expected == "answer":
        return 1.0 if actual in {"answer", "partial_answer"} else 0.0
    return 1.0 if expected == actual else 0.0


def _create_session(case: dict[str, Any]) -> str | None:
    turns = case.get("previous_turns") or []
    if not turns:
        return None
    session_id = create_session(str(case["user_role"]), user_id=str(case["user_id"]))
    for turn in turns:
        add_message(session_id=session_id, role=str(turn["role"]), content=str(turn["content"]))
    return session_id


def _document_ids(items: list[dict[str, Any]] | None) -> list[str]:
    return [str(item.get("document_id")) for item in items or [] if item.get("document_id")]


def _score_response(case: dict[str, Any], payload: dict[str, Any], *, latency_ms: float, status_code: int = 200) -> dict[str, Any]:
    expected_behavior = str(case["expected_behavior"])
    actual_behavior = str(payload.get("response_type") or ("refuse_no_access" if status_code in {401, 403} else "error"))
    answer = str(payload.get("answer") or payload.get("detail") or "")
    citations = payload.get("citations") or []
    retrieved = payload.get("retrieved_chunks") or []
    citation_documents = _document_ids(citations)
    retrieved_documents = _document_ids(retrieved)
    expected_documents = [str(value) for value in case.get("expected_source_documents") or []]
    required_scores = [_fact_score(str(fact), answer) for fact in case.get("required_facts") or []]
    required_fact_completeness = round(mean(required_scores), 3) if required_scores else None
    forbidden_hits = [
        str(fact)
        for fact in case.get("forbidden_facts") or []
        if forbidden_fact_asserted(str(fact), answer)
    ]
    forbidden_fact_violation = 1.0 if forbidden_hits else 0.0
    expected_source_recall = None
    if expected_documents:
        expected_source_recall = round(len(set(expected_documents) & set(retrieved_documents)) / len(set(expected_documents)), 3)
    all_required_sources_retrieved = None if not expected_documents else float(set(expected_documents).issubset(set(retrieved_documents)))
    citation_document_accuracy = None
    if expected_behavior == "answer" and expected_documents:
        citation_document_accuracy = float(set(expected_documents).issubset(set(citation_documents)))

    citation_text = " ".join(str(citation.get("citation_text") or "") for citation in citations)
    claim_support_scores = [_fact_score(str(fact), citation_text) for fact in case.get("required_facts") or []]
    claim_to_citation_support = round(mean(claim_support_scores), 3) if claim_support_scores else None
    unauthorized_documents = sorted(
        {
            str(chunk.get("document_id"))
            for chunk in retrieved
            if chunk.get("document_id")
            and not role_can_access(list(chunk.get("access_roles") or []), str(case["user_role"]))
        }
    )
    access_by_document = {
        str(chunk.get("document_id")): list(chunk.get("access_roles") or [])
        for chunk in retrieved
        if chunk.get("document_id")
    }
    restricted_citations = sorted(
        {
            document_id
            for document_id in citation_documents
            if document_id in access_by_document
            and not role_can_access(access_by_document[document_id], str(case["user_role"]))
        }
    )
    permission_check = payload.get("permission_check") or {}
    unauthorized_reached_generation = bool(permission_check.get("unauthorized_chunks_reached_generation"))
    memory_as_evidence = any("memory" in doc.lower() or "conversation" in doc.lower() for doc in citation_documents)
    unsupported_claims = payload.get("unsupported_claims") or []
    substantive_unsupported = [
        claim
        for claim in substantive_unsupported_claims(unsupported_claims)
        if forbidden_fact_asserted(claim, answer, threshold=0.65)
    ]
    hallucination_flag = bool(forbidden_hits or (substantive_unsupported and actual_behavior in {"answer", "partial_answer"}))
    behavior_accuracy = _behavior_match(expected_behavior, actual_behavior)
    passed = (
        behavior_accuracy == 1.0
        and (required_fact_completeness is None or required_fact_completeness >= 0.7)
        and forbidden_fact_violation == 0.0
        and (citation_document_accuracy is None or citation_document_accuracy == 1.0)
        and not unauthorized_documents
        and not restricted_citations
        and not unauthorized_reached_generation
        and not memory_as_evidence
        and not hallucination_flag
    )
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "category": case["category"],
        "difficulty": case["difficulty"],
        "user_role": case["user_role"],
        "project_id": case.get("project_id"),
        "department_id": case.get("department_id"),
        "conversation_depth": len(case.get("previous_turns") or []),
        "source_count": len(expected_documents),
        "question": case["question"],
        "expected_behavior": expected_behavior,
        "actual_behavior": actual_behavior,
        "status_code": status_code,
        "answer": answer,
        "behavior_accuracy": behavior_accuracy,
        "required_fact_completeness": required_fact_completeness,
        "required_fact_scores": required_scores,
        "forbidden_fact_violation": forbidden_fact_violation,
        "forbidden_fact_hits": forbidden_hits,
        "expected_source_recall": expected_source_recall,
        "all_required_sources_retrieved": all_required_sources_retrieved,
        "citation_document_accuracy": citation_document_accuracy,
        "claim_to_citation_support": claim_to_citation_support,
        "hallucination_flag": float(hallucination_flag),
        "clarification_accuracy": behavior_accuracy if expected_behavior == "clarify" else None,
        "not_found_accuracy": behavior_accuracy if expected_behavior == "not_found" else None,
        "blocked_answer_accuracy": behavior_accuracy if expected_behavior == "refuse_no_access" else None,
        "unauthorized_chunk_exposure": float(bool(unauthorized_documents)),
        "unauthorized_documents": unauthorized_documents,
        "restricted_citation_leakage": float(bool(restricted_citations)),
        "restricted_citation_documents": restricted_citations,
        "unauthorized_chunks_reached_generation": float(unauthorized_reached_generation),
        "memory_source_recovery_quality": expected_source_recall if case["category"] == "multi_turn_memory" else None,
        "memory_as_evidence_violation": float(memory_as_evidence),
        "rewritten_question": (payload.get("memory") or {}).get("rewritten_question"),
        "citation_documents": citation_documents,
        "retrieved_documents": retrieved_documents,
        "citations": citations,
        "unsupported_claims": unsupported_claims,
        "substantive_unsupported_claims": substantive_unsupported,
        "latency_ms": round(latency_ms, 1),
        "input_tokens": payload.get("input_tokens"),
        "output_tokens": payload.get("output_tokens"),
        "estimated_cost_usd": payload.get("estimated_cost_usd") or 0.0,
        "fixture_backed": bool(case.get("fixture_requirements")),
        "passed": passed,
    }


def _run_query_case(client: TestClient, case: dict[str, Any]) -> dict[str, Any]:
    session_id = _create_session(case)
    started = time.perf_counter()
    response = client.post(
        "/query",
        headers={DEMO_USER_HEADER: case["user_id"]},
        json={
            "question": case["question"],
            "session_id": session_id,
            "project_id": case.get("project_id"),
            "department_id": case.get("department_id"),
            "retrieval_mode": DEFAULT_RETRIEVAL_MODE,
            "top_k": DEFAULT_TOP_K,
            "rerank_candidate_limit": DEFAULT_RERANK_CANDIDATE_LIMIT,
            "prompt_version": DEFAULT_PROMPT_VERSION,
        },
    )
    latency_ms = (time.perf_counter() - started) * 1000
    if response.status_code not in {200, 401, 403}:
        response.raise_for_status()
    payload = response.json()
    return _score_response(case, payload, latency_ms=latency_ms, status_code=response.status_code)


def _pdf_bytes(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        b"5 0 obj\n<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for item in objects:
        offsets.append(len(output))
        output.extend(item)
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(output)


def _upload(client: TestClient, *, project_id: str, department_id: str, marker: str) -> dict[str, Any]:
    response = client.post(
        f"/projects/{project_id}/departments/{department_id}/documents/upload",
        headers={DEMO_USER_HEADER: ADMIN_USER_ID},
        data={"title": f"Phase 47 Fixture {marker}", "access_roles": "Employee, Manager, IT Admin", "restricted": "false"},
        files={"file": (f"phase47-{marker.lower()}.pdf", _pdf_bytes(f"Phase 47 fixture policy. Vendor review code: {marker}."), "application/pdf")},
    )
    response.raise_for_status()
    return response.json()["document"]


def _approve(client: TestClient, *, project_id: str, department_id: str, document_id: str) -> dict[str, Any]:
    response = client.post(
        f"/projects/{project_id}/departments/{department_id}/documents/{document_id}/approve-index",
        headers={DEMO_USER_HEADER: ADMIN_USER_ID},
    )
    response.raise_for_status()
    return response.json()["document"]


def _cleanup_fixture(*, document_ids: list[str], project_ids: list[str], source_paths: list[str]) -> None:
    with get_connection() as conn:
        if document_ids:
            conn.execute("delete from ingestion_jobs where document_id = any(%s::uuid[])", (document_ids,))
            conn.execute("update documents set current_version_id = null where id = any(%s::uuid[])", (document_ids,))
            conn.execute("delete from documents where id = any(%s::uuid[])", (document_ids,))
        for project_id in project_ids:
            conn.execute("delete from ingestion_jobs where project_id = %s::uuid", (project_id,))
            conn.execute("update documents set current_version_id = null where project_id = %s::uuid", (project_id,))
            conn.execute("delete from documents where project_id = %s::uuid", (project_id,))
            conn.execute("delete from projects where id = %s::uuid", (project_id,))
    for source_path in source_paths:
        path = Path(source_path)
        resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
        uploads_root = (ROOT / "data/uploads").resolve()
        if resolved.is_relative_to(uploads_root) and resolved.exists():
            resolved.unlink()


def _fixture_case_from_payload(case: dict[str, Any], payload: dict[str, Any], *, latency_ms: float, dynamic_document_id: str | None = None) -> dict[str, Any]:
    adjusted = dict(case)
    if dynamic_document_id:
        adjusted["expected_source_documents"] = [dynamic_document_id if item.startswith("UPLOAD-") else item for item in case.get("expected_source_documents") or []]
        adjusted["allowed_documents"] = [dynamic_document_id if item.startswith("UPLOAD-") else item for item in case.get("allowed_documents") or []]
    return _score_response(adjusted, payload, latency_ms=latency_ms)


def _run_fixture_cases(client: TestClient, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cases:
        return []
    rows: list[dict[str, Any]] = []
    document_ids: list[str] = []
    project_ids: list[str] = []
    source_paths: list[str] = []
    northstar_document: dict[str, Any] | None = None
    northstar_approved: dict[str, Any] | None = None
    operations_id = "00000000-0000-0000-0000-000000002011"
    people_id = "00000000-0000-0000-0000-000000002001"
    try:
        for case in cases:
            scenario = str((case.get("fixture_requirements") or {}).get("scenario") or "")
            if scenario in {"pending_review_not_indexed", "approved_document_retrievable", "strict_department_scope"}:
                if northstar_document is None:
                    northstar_document = _upload(client, project_id=PROJECT_ID, department_id=operations_id, marker="P47-REVIEW-ALPHA")
                    document_ids.append(str(northstar_document["id"]))
                    source_paths.append(str(northstar_document["source_path"]))
                if scenario != "pending_review_not_indexed" and northstar_approved is None:
                    northstar_approved = _approve(
                        client,
                        project_id=PROJECT_ID,
                        department_id=operations_id,
                        document_id=str(northstar_document["id"]),
                    )
                department_id = people_id if scenario == "strict_department_scope" else operations_id
                started = time.perf_counter()
                response = client.post(
                    "/query",
                    headers={DEMO_USER_HEADER: case["user_id"]},
                    json={
                        "question": case["question"],
                        "project_id": PROJECT_ID,
                        "department_id": department_id,
                        "retrieval_mode": DEFAULT_RETRIEVAL_MODE,
                        "top_k": DEFAULT_TOP_K,
                        "rerank_candidate_limit": DEFAULT_RERANK_CANDIDATE_LIMIT,
                        "prompt_version": DEFAULT_PROMPT_VERSION,
                    },
                )
                response.raise_for_status()
                external_id = str((northstar_approved or northstar_document)["external_document_id"])
                rows.append(_fixture_case_from_payload(case, response.json(), latency_ms=(time.perf_counter() - started) * 1000, dynamic_document_id=external_id))
                continue

            if scenario == "cross_project_membership":
                create_project = client.post(
                    "/projects",
                    headers={DEMO_USER_HEADER: ADMIN_USER_ID},
                    json={"name": f"Phase 47 Isolation {uuid.uuid4().hex[:8]}", "description": "Disposable Phase 47 fixture"},
                )
                create_project.raise_for_status()
                isolated_project_id = str(create_project.json()["project"]["id"])
                project_ids.append(isolated_project_id)
                create_department = client.post(
                    f"/projects/{isolated_project_id}/departments",
                    headers={DEMO_USER_HEADER: ADMIN_USER_ID},
                    json={"name": "Isolated Knowledge", "icon": "lock", "color": "rust", "default_access_roles": ["Employee", "IT Admin"]},
                )
                create_department.raise_for_status()
                isolated_department_id = str(create_department.json()["department"]["id"])
                uploaded = _upload(client, project_id=isolated_project_id, department_id=isolated_department_id, marker="P47-ISOLATED-BETA")
                source_paths.append(str(uploaded["source_path"]))
                _approve(client, project_id=isolated_project_id, department_id=isolated_department_id, document_id=str(uploaded["id"]))
                started = time.perf_counter()
                response = client.post(
                    "/query",
                    headers={DEMO_USER_HEADER: case["user_id"]},
                    json={
                        "question": case["question"],
                        "project_id": isolated_project_id,
                        "department_id": isolated_department_id,
                        "retrieval_mode": DEFAULT_RETRIEVAL_MODE,
                        "top_k": DEFAULT_TOP_K,
                        "rerank_candidate_limit": DEFAULT_RERANK_CANDIDATE_LIMIT,
                        "prompt_version": DEFAULT_PROMPT_VERSION,
                    },
                )
                payload = response.json()
                rows.append(_score_response(case, payload, latency_ms=(time.perf_counter() - started) * 1000, status_code=response.status_code))
                continue
            raise ValueError(f"Unsupported fixture scenario for {case['case_id']}: {scenario}")
    finally:
        _cleanup_fixture(document_ids=document_ids, project_ids=project_ids, source_paths=source_paths)
    return rows


def _dimensions(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if key == "scope":
            value = "global" if not row.get("project_id") else ("department" if row.get("department_id") else "project")
        groups[str(value)].append(row)
    return {
        value: {
            "sample_size": len(group),
            "passed_count": sum(1 for row in group if row["passed"]),
            "failed_count": sum(1 for row in group if not row["passed"]),
            "behavior_accuracy": _average([row["behavior_accuracy"] for row in group]),
            "required_fact_completeness": _average([row["required_fact_completeness"] for row in group]),
            "citation_document_accuracy": _average([row["citation_document_accuracy"] for row in group]),
        }
        for value, group in sorted(groups.items())
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in rows if not row["passed"]]
    answer_rows = [row for row in rows if row["expected_behavior"] == "answer"]
    permission_rows = [row for row in rows if row["category"] == "permission_scope_pairs" or row["fixture_backed"]]
    memory_rows = [row for row in rows if row["category"] == "multi_turn_memory"]
    total_cost = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 6)
    total_input = sum(int(row.get("input_tokens") or 0) for row in rows)
    total_output = sum(int(row.get("output_tokens") or 0) for row in rows)
    metrics = {
        "behavior_accuracy": _average([row["behavior_accuracy"] for row in rows]),
        "expected_source_recall": _average([row["expected_source_recall"] for row in answer_rows]),
        "all_required_sources_retrieved": _average([row["all_required_sources_retrieved"] for row in answer_rows]),
        "required_fact_completeness": _average([row["required_fact_completeness"] for row in answer_rows]),
        "forbidden_fact_violation_rate": _average([row["forbidden_fact_violation"] for row in rows]),
        "citation_document_accuracy": _average([row["citation_document_accuracy"] for row in answer_rows]),
        "claim_to_citation_support": _average([row["claim_to_citation_support"] for row in answer_rows]),
        "hallucination_rate": _average([row["hallucination_flag"] for row in rows]),
        "clarification_accuracy": _average([row["clarification_accuracy"] for row in rows]),
        "not_found_accuracy": _average([row["not_found_accuracy"] for row in rows]),
        "blocked_answer_accuracy": _average([row["blocked_answer_accuracy"] for row in rows]),
        "unauthorized_chunk_exposure_rate": _average([row["unauthorized_chunk_exposure"] for row in permission_rows]),
        "restricted_citation_leakage_rate": _average([row["restricted_citation_leakage"] for row in permission_rows]),
        "unauthorized_chunks_reached_generation_rate": _average([row["unauthorized_chunks_reached_generation"] for row in permission_rows]),
        "memory_source_recovery_quality": _average([row["memory_source_recovery_quality"] for row in memory_rows]),
        "memory_as_evidence_violation_rate": _average([row["memory_as_evidence_violation"] for row in memory_rows]),
        "average_latency_ms": round(mean(float(row["latency_ms"]) for row in rows), 1) if rows else None,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "estimated_cost": total_cost,
    }
    denominators = {
        "overall_pass": _rate(len(rows) - len(failed), len(rows)),
        "behavior_accuracy": _rate(sum(row["behavior_accuracy"] == 1.0 for row in rows), len(rows)),
        "permission_leakage": _rate(sum(row["unauthorized_chunk_exposure"] > 0 or row["restricted_citation_leakage"] > 0 for row in permission_rows), len(permission_rows)),
        "memory_as_evidence": _rate(sum(row["memory_as_evidence_violation"] > 0 for row in memory_rows), len(memory_rows)),
    }
    return {
        "sample_size": len(rows),
        "passed_count": len(rows) - len(failed),
        "failed_count": len(failed),
        "failed_case_ids": [row["case_id"] for row in failed],
        "category_counts": dict(sorted(Counter(row["category"] for row in rows).items())),
        "metrics": metrics,
        "numerators_denominators": denominators,
        "breakdowns": {
            "category": _dimensions(rows, "category"),
            "role": _dimensions(rows, "user_role"),
            "difficulty": _dimensions(rows, "difficulty"),
            "scope": _dimensions(rows, "scope"),
            "source_count": _dimensions(rows, "source_count"),
            "conversation_depth": _dimensions(rows, "conversation_depth"),
        },
        "hard_gates": {
            "permission_leakage_zero": all(row["unauthorized_chunk_exposure"] == 0 and row["restricted_citation_leakage"] == 0 for row in permission_rows),
            "unauthorized_chunks_reached_generation_zero": all(row["unauthorized_chunks_reached_generation"] == 0 for row in permission_rows),
            "memory_as_evidence_zero": all(row["memory_as_evidence_violation"] == 0 for row in memory_rows),
        },
        "portfolio_claim_gates": {
            "behavior_accuracy_gte_0_900": (metrics["behavior_accuracy"] or 0) >= 0.9,
            "expected_source_recall_gte_0_900": (metrics["expected_source_recall"] or 0) >= 0.9,
            "required_fact_completeness_gte_0_850": (metrics["required_fact_completeness"] or 0) >= 0.85,
            "citation_accuracy_gte_0_900": (metrics["citation_document_accuracy"] or 0) >= 0.9,
            "hallucination_rate_lte_0_050": metrics["hallucination_rate"] <= 0.05,
        },
    }


def _eval_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    provenance = result["provenance"]
    return {
        "run_id": result["run_id"],
        "run_name": result["run_name"],
        "phase": "phase-47",
        "run_type": "independent_generalization_eval",
        "timestamp": result["completed_at"],
        "benchmark_version": f"independent-generalization-{result['split']}-v1",
        "split": result["split"],
        "total_questions": summary["sample_size"],
        "retrieval_mode": provenance["retrieval_profile"],
        "top_k": provenance["top_k"],
        "prompt_version": provenance["prompt_version"],
        "model": provenance["model"],
        "temperature": provenance["temperature"],
        "metrics": {**summary["metrics"], "failed_question_count": summary["failed_count"]},
        "failed_questions": summary["failed_case_ids"],
        "category_breakdown": summary["category_counts"],
        "provenance": provenance,
        "hard_gates": summary["hard_gates"],
        "portfolio_claim_gates": summary["portfolio_claim_gates"],
        "notes": "Separate Phase 47 evidence. Do not blend with benchmark 1.1 or Phase 45/46 probe metrics.",
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    metrics = summary["metrics"]
    lines = [
        f"# Phase 47 {result['split'].title()} Results",
        "",
        f"Generated at: {result['completed_at']}",
        "",
        "## Provenance",
        "",
        f"- Run ID: `{result['run_id']}`",
        f"- Suite: `independent-generalization-{result['split']}-v1`",
        f"- Evaluation commit: `{result['provenance']['evaluation_commit']}`",
        f"- Frozen runtime commit: `{result['provenance'].get('frozen_runtime_commit') or 'not applicable before holdout freeze'}`",
        f"- Suite hash: `{result['provenance']['suite_hash']}`",
        f"- Corpus hash: `{result['provenance']['corpus_hash']}`",
        f"- Model: `{result['provenance']['model']}`",
        f"- Prompt / retrieval: `{result['provenance']['prompt_version']}` / `{result['provenance']['retrieval_profile']}` top-k `{result['provenance']['top_k']}`",
        "",
        "## Measured Results",
        "",
        f"- Sample size: `{summary['sample_size']}`",
        f"- Passed: `{summary['passed_count']}`",
        f"- Failed: `{summary['failed_count']}`",
        f"- Behavior accuracy: `{metrics['behavior_accuracy']}`",
        f"- Required-source recall: `{metrics['expected_source_recall']}`",
        f"- Required-fact completeness: `{metrics['required_fact_completeness']}`",
        f"- Citation document accuracy: `{metrics['citation_document_accuracy']}`",
        f"- Claim-to-citation support: `{metrics['claim_to_citation_support']}`",
        f"- Hallucination rate (heuristic): `{metrics['hallucination_rate']}`",
        f"- Permission leakage / unauthorized generation / memory-as-evidence hard gates: `{'pass' if all(summary['hard_gates'].values()) else 'fail'}`",
        f"- Estimated OpenAI cost: `${metrics['estimated_cost']:.6f}`",
        f"- Average latency: `{metrics['average_latency_ms']}` ms",
        "",
        "## Failed Cases",
        "",
    ]
    failed_rows = [row for row in result["rows"] if not row["passed"]]
    if not failed_rows:
        lines.append("- None in this run.")
    else:
        lines.extend(["| Case | Category | Expected | Actual | Fact completeness | Citation accuracy |", "| --- | --- | --- | --- | ---: | ---: |"])
        for row in failed_rows:
            lines.append(
                f"| {row['case_id']} | {row['category']} | {row['expected_behavior']} | {row['actual_behavior']} | "
                f"{row['required_fact_completeness']} | {row['citation_document_accuracy']} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "",
            "- This suite is separate from benchmark `1.1` and the Phase 45/46 probes.",
            "- Fact completeness and claim-to-citation support are deterministic token-coverage diagnostics, not semantic proof.",
            "- The hallucination flag is heuristic; human adjudication remains required for holdout evidence.",
            "- Fixture-backed upload/project-isolation rows are identified in the raw artifact and should not be treated as static-corpus cases.",
        ]
    )
    return "\n".join(lines) + "\n"


def _failure_matrix(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": result["run_id"],
        "split": result["split"],
        "failures": [
            {
                "case_id": row["case_id"],
                "category": row["category"],
                "expected_behavior": row["expected_behavior"],
                "actual_behavior": row["actual_behavior"],
                "required_fact_completeness": row["required_fact_completeness"],
                "citation_document_accuracy": row["citation_document_accuracy"],
                "expected_source_recall": row["expected_source_recall"],
                "hallucination_flag": row["hallucination_flag"],
                "permission_flags": {
                    "unauthorized_chunk_exposure": row["unauthorized_chunk_exposure"],
                    "restricted_citation_leakage": row["restricted_citation_leakage"],
                    "unauthorized_chunks_reached_generation": row["unauthorized_chunks_reached_generation"],
                    "memory_as_evidence_violation": row["memory_as_evidence_violation"],
                },
            }
            for row in result["rows"]
            if not row["passed"]
        ],
    }


def _select_cases(args: argparse.Namespace) -> list[dict[str, Any]]:
    suite = load_suite(args.split)
    cases = list(suite["cases"])
    if args.split == "holdout" and (args.case_id or args.category or args.limit):
        raise SystemExit("Partial holdout execution is prohibited; remove --case-id, --category, and --limit.")
    if args.case_id:
        requested = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in requested]
        missing = requested - {case["case_id"] for case in cases}
        if missing:
            raise SystemExit(f"Unknown case IDs: {', '.join(sorted(missing))}")
    if args.category:
        cases = [case for case in cases if case["category"] == args.category]
    if args.limit:
        cases = cases[: args.limit]
    if args.stability_passes:
        if args.split != "development":
            raise SystemExit("Stability mode is development-only.")
        cases = [case for case in cases if case.get("stability_slice")]
        if len(cases) != 20:
            raise SystemExit(f"Stability slice must contain exactly 20 cases; found {len(cases)}")
    return cases


def _run_once(cases: list[dict[str, Any]], *, budget_usd: float) -> list[dict[str, Any]]:
    if len(cases) * MAX_ESTIMATED_CASE_COST_USD > budget_usd:
        raise SystemExit(
            f"Preflight maximum estimate ${len(cases) * MAX_ESTIMATED_CASE_COST_USD:.2f} exceeds budget ${budget_usd:.2f}."
        )
    rows: list[dict[str, Any]] = []
    fixture_cases = [case for case in cases if case.get("fixture_requirements")]
    regular_cases = [case for case in cases if not case.get("fixture_requirements")]
    with TestClient(app) as client:
        for index, case in enumerate(regular_cases, start=1):
            spent = sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows)
            if spent >= budget_usd:
                raise RuntimeError(f"Budget exhausted before case {case['case_id']}: ${spent:.6f} >= ${budget_usd:.2f}")
            print(f"[{index}/{len(cases)}] starting {case['case_id']}", flush=True)
            row = _run_query_case(client, case)
            rows.append(row)
            print(f"[{index}/{len(cases)}] {case['case_id']}: {'PASS' if row['passed'] else 'FAIL'} cost=${float(row['estimated_cost_usd']):.6f}", flush=True)
        fixture_rows = _run_fixture_cases(client, fixture_cases)
        for row in fixture_rows:
            rows.append(row)
            print(f"[{len(rows)}/{len(cases)}] {row['case_id']}: {'PASS' if row['passed'] else 'FAIL'} fixture")
    rows.sort(key=lambda row: row["case_id"])
    spent = sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows)
    if spent > budget_usd:
        raise RuntimeError(f"Run cost ${spent:.6f} exceeded budget ${budget_usd:.2f}")
    return rows


def _stability_result(cases: list[dict[str, Any]], *, passes: int, budget_usd: float) -> dict[str, Any]:
    all_passes: list[list[dict[str, Any]]] = []
    remaining_budget = budget_usd
    for pass_index in range(1, passes + 1):
        print(f"Starting stability pass {pass_index}/{passes}")
        rows = _run_once(cases, budget_usd=remaining_budget)
        all_passes.append(rows)
        remaining_budget -= sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows)
    by_case: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for rows in all_passes:
        for row in rows:
            by_case[row["case_id"]].append(row)
    case_consistency = []
    for case_id, rows in sorted(by_case.items()):
        behavior_values = {row["actual_behavior"] for row in rows}
        source_values = {tuple(row["retrieved_documents"]) for row in rows}
        citation_values = {tuple(row["citation_documents"]) for row in rows}
        case_consistency.append(
            {
                "case_id": case_id,
                "pass_count": sum(1 for row in rows if row["passed"]),
                "pass_consistent": len({row["passed"] for row in rows}) == 1,
                "response_type_consistent": len(behavior_values) == 1,
                "source_consistent": len(source_values) == 1,
                "citation_consistent": len(citation_values) == 1,
                "latency_mean_ms": round(mean(row["latency_ms"] for row in rows), 1),
                "latency_range_ms": [min(row["latency_ms"] for row in rows), max(row["latency_ms"] for row in rows)],
                "cost_mean_usd": round(mean(float(row["estimated_cost_usd"] or 0.0) for row in rows), 6),
                "cost_range_usd": [
                    min(float(row["estimated_cost_usd"] or 0.0) for row in rows),
                    max(float(row["estimated_cost_usd"] or 0.0) for row in rows),
                ],
            }
        )
    return {
        "generated_at": _now(),
        "passes": passes,
        "case_count": len(cases),
        "request_count": len(cases) * passes,
        "estimated_cost": round(sum(float(row.get("estimated_cost_usd") or 0.0) for rows in all_passes for row in rows), 6),
        "case_consistency": case_consistency,
        "pass_consistency_rate": _average([float(item["pass_consistent"]) for item in case_consistency]),
        "response_type_consistency_rate": _average([float(item["response_type_consistent"]) for item in case_consistency]),
        "source_consistency_rate": _average([float(item["source_consistent"]) for item in case_consistency]),
        "citation_consistency_rate": _average([float(item["citation_consistent"]) for item in case_consistency]),
        "raw_passes": all_passes,
    }


def _write_stability_report(result: dict[str, Any]) -> None:
    lines = [
        "# Phase 47 Stability Results",
        "",
        f"Generated at: {result['generated_at']}",
        "",
        f"- Cases: `{result['case_count']}`",
        f"- Passes: `{result['passes']}`",
        f"- Requests: `{result['request_count']}`",
        f"- Pass consistency: `{result['pass_consistency_rate']}`",
        f"- Response-type consistency: `{result['response_type_consistency_rate']}`",
        f"- Source consistency: `{result['source_consistency_rate']}`",
        f"- Citation consistency: `{result['citation_consistency_rate']}`",
        f"- Estimated OpenAI cost: `${result['estimated_cost']:.6f}`",
        "",
        "This is a three-pass development diagnostic. It is not a best-of-three score and does not alter the one-time holdout contract.",
    ]
    path = PHASE_DOCS_DIR / "stability-results.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 47 independent generalization development or holdout split.")
    parser.add_argument("--split", choices=("development", "holdout"), required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--budget-usd", type=float, default=2.0)
    parser.add_argument("--frozen-runtime-commit")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--stability-passes", type=int, choices=(3,))
    args = parser.parse_args()

    validation = validate_split(args.split)
    if not validation["valid"]:
        raise SystemExit("Suite validation failed:\n- " + "\n- ".join(validation["errors"]))
    cases = _select_cases(args)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "split": args.split,
                    "suite_version": "1.0",
                    "case_count": len(cases),
                    "category_counts": dict(sorted(Counter(case["category"] for case in cases).items())),
                    "estimated_maximum_cost_usd": round(len(cases) * MAX_ESTIMATED_CASE_COST_USD * (args.stability_passes or 1), 2),
                    "would_call_external_ai": False,
                    "stability_passes": args.stability_passes,
                },
                indent=2,
            )
        )
        return
    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)
    if args.budget_usd <= 0:
        raise SystemExit("--budget-usd must be positive")

    preflight: dict[str, Any] | None = None
    if args.split == "holdout":
        if not args.frozen_runtime_commit:
            raise SystemExit("Holdout execution requires --frozen-runtime-commit.")
        default_result_path = RESULTS_DIR / "phase47-independent-holdout.json"
        if default_result_path.exists():
            raise SystemExit("A complete Phase 47 holdout artifact already exists; selective or repeated holdout execution is prohibited.")
        preflight = verify_holdout_preflight(args.frozen_runtime_commit)
        if not preflight["valid"]:
            raise SystemExit("Holdout preflight failed:\n- " + "\n- ".join(preflight["errors"]))

    if args.stability_passes:
        stability = _stability_result(cases, passes=args.stability_passes, budget_usd=args.budget_usd)
        write_json_atomic(RESULTS_DIR / "phase47-development-stability.json", stability)
        _write_stability_report(stability)
        print(json.dumps({key: stability[key] for key in ["case_count", "passes", "request_count", "estimated_cost", "pass_consistency_rate", "response_type_consistency_rate", "source_consistency_rate", "citation_consistency_rate"]}, indent=2))
        return

    settings = get_settings()
    started_at = _now()
    rows = _run_once(cases, budget_usd=args.budget_usd)
    completed_at = _now()
    run_id = f"phase47-independent-{args.split}"
    suite_file = HOLDOUT_PATH if args.split == "holdout" else ROOT / "data/evaluation/independent-generalization/development-v1.json"
    result = {
        "run_id": run_id,
        "run_name": f"Phase 47 Independent Generalization {args.split.title()}",
        "phase": "phase-47",
        "split": args.split,
        "started_at": started_at,
        "completed_at": completed_at,
        "provenance": {
            "evaluation_commit": git_commit(),
            "frozen_runtime_commit": args.frozen_runtime_commit,
            "corpus_hash": tree_sha256(CORPUS_DIR),
            "suite_hash": file_sha256(suite_file),
            "model": settings.openai_chat_model,
            "embedding_model": settings.openai_embedding_model,
            "prompt_version": DEFAULT_PROMPT_VERSION,
            "retrieval_profile": DEFAULT_RETRIEVAL_MODE,
            "top_k": DEFAULT_TOP_K,
            "rerank_candidate_limit": DEFAULT_RERANK_CANDIDATE_LIMIT,
            "temperature": 0.0,
            "platform_telemetry_enabled": settings.proofbase_telemetry_enabled,
            "project_scope": "per-case global/project/department scope",
            "preflight": preflight,
        },
        "summary": _summary(rows),
        "rows": rows,
    }
    detail_path = RESULTS_DIR / f"{run_id}.json"
    eval_run_path = EVAL_RUNS_DIR / f"{run_id}.json"
    failure_path = RESULTS_DIR / f"{run_id}-failures.json"
    report_path = PHASE_DOCS_DIR / f"{args.split}-results.md"
    write_json_atomic(detail_path, result)
    write_json_atomic(eval_run_path, _eval_run(result))
    write_json_atomic(failure_path, _failure_matrix(result))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_markdown_report(result), encoding="utf-8")
    print(json.dumps({"run_id": run_id, **result["summary"]["metrics"], "passed_count": result["summary"]["passed_count"], "failed_count": result["summary"]["failed_count"]}, indent=2))


if __name__ == "__main__":
    main()
