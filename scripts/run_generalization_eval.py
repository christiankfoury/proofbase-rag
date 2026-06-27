from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
from apps.api.app.core.config import get_settings
from apps.api.app.main import app
from apps.api.app.memory.session_store import add_message, create_session


PROJECT_ID = "00000000-0000-0000-0000-000000000019"
PEOPLE_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002001"
HR_ADMIN_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002002"
IT_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002003"
SALES_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002005"
OPERATIONS_DEPARTMENT_ID = "00000000-0000-0000-0000-000000002011"
EMPLOYEE_USER_ID = "00000000-0000-0000-0000-000000002701"
SALES_USER_ID = "00000000-0000-0000-0000-000000002702"
MANAGER_USER_ID = "00000000-0000-0000-0000-000000002703"
HR_ADMIN_USER_ID = "00000000-0000-0000-0000-000000002704"
IT_ADMIN_USER_ID = "00000000-0000-0000-0000-000000002705"
USER_ROLES = {
    EMPLOYEE_USER_ID: "Employee",
    SALES_USER_ID: "Sales Representative",
    MANAGER_USER_ID: "Manager",
    HR_ADMIN_USER_ID: "HR Admin",
    IT_ADMIN_USER_ID: "IT Admin",
}
DEFAULT_RUN_ID = "phase45-generalization-baseline"
DEFAULT_RUN_NAME = "Phase 45 Generalization Probe Baseline"
DEFAULT_PHASE = "phase-45"
DEFAULT_REPORT_TITLE = "Phase 45 Generalization Baseline"
DEFAULT_DETAIL_PATH = ROOT / "data/evaluation/generalization-probes/phase45-generalization-baseline.json"
DEFAULT_EVAL_RUN_PATH = ROOT / "data/evaluation/eval-runs/phase45-generalization-baseline.json"
DEFAULT_REPORT_PATH = ROOT / "docs/phase-45/generalization-baseline.md"
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The Phase 45 generalization probe baseline sends realistic user questions, prior chat turns, and "
    "permission-filtered retrieved source snippets to external OpenAI embeddings and chat-completion APIs. "
    "Re-run with --allow-external-ai only after explicit approval."
)


PROBES: list[dict[str, Any]] = [
    {
        "id": "GEN-MEM-001",
        "category": "that_policy",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": PEOPLE_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "How many vacation days do employees get?"}],
        "question": "What does that policy say about carrying unused days?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-002"],
        "expected_rewrite_terms": ["vacation", "unused", "carry"],
    },
    {
        "id": "GEN-MEM-002",
        "category": "same_department",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "What are remote work approval expectations?"}],
        "question": "In the same department, what security expectations apply?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-003", "IT-002"],
        "expected_rewrite_terms": ["remote", "security"],
    },
    {
        "id": "GEN-MEM-003",
        "category": "contractors",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": OPERATIONS_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "Tell me about vendor onboarding."}],
        "question": "What about contractors?",
        "expected_behavior": "answer",
        "expected_documents": ["OPS-001"],
        "expected_rewrite_terms": ["vendor", "contractor"],
    },
    {
        "id": "GEN-MEM-004",
        "category": "compare_two",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "I am comparing remote work and device security."}],
        "question": "Compare those two for an employee.",
        "expected_behavior": "answer",
        "expected_documents": ["HR-003", "IT-002"],
        "expected_rewrite_terms": ["remote", "device", "security"],
    },
    {
        "id": "GEN-MEM-005",
        "category": "which_applies",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "I have a laptop replacement and a travel request."}],
        "question": "Which one applies to me if my laptop was lost?",
        "expected_behavior": "answer",
        "expected_documents": ["OPS-001"],
        "expected_rewrite_terms": ["laptop", "lost", "equipment"],
    },
    {
        "id": "GEN-AMB-001",
        "category": "project_ambiguity",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": None,
        "department_id": None,
        "prior_turns": [],
        "question": "What does the project policy say about approvals?",
        "expected_behavior": "clarify",
        "expected_documents": [],
        "expected_rewrite_terms": [],
    },
    {
        "id": "GEN-AMB-002",
        "category": "department_ambiguity",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [],
        "question": "What does the department handbook say about approvals?",
        "expected_behavior": "clarify",
        "expected_documents": [],
        "expected_rewrite_terms": [],
    },
    {
        "id": "GEN-AMB-003",
        "category": "role_ambiguity",
        "user_id": MANAGER_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [],
        "question": "Which approval limit applies to my role?",
        "expected_behavior": "clarify",
        "expected_documents": [],
        "expected_rewrite_terms": [],
    },
    {
        "id": "GEN-AMB-004",
        "category": "topic_ambiguity",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [],
        "question": "What is the policy for that?",
        "expected_behavior": "clarify",
        "expected_documents": [],
        "expected_rewrite_terms": [],
    },
    {
        "id": "GEN-AMB-005",
        "category": "document_reference",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [],
        "question": "What does the second document say about exceptions?",
        "expected_behavior": "clarify",
        "expected_documents": [],
        "expected_rewrite_terms": [],
    },
    {
        "id": "GEN-PERM-001",
        "category": "permission_memory",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "assistant", "content": "Promotion calibration is covered in manager guidance."}],
        "question": "What does it say about calibration?",
        "expected_behavior": "refuse",
        "expected_documents": [],
        "expected_rewrite_terms": ["promotion", "calibration"],
    },
    {
        "id": "GEN-PERM-002",
        "category": "permission_role",
        "user_id": SALES_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "I am reviewing refund guidance."}],
        "question": "Can I approve a refund above 1,000 dollars?",
        "expected_behavior": "answer",
        "expected_documents": ["SUPPORT-001"],
        "expected_rewrite_terms": ["refund", "1000"],
    },
    {
        "id": "GEN-PERM-003",
        "category": "permission_it_admin",
        "user_id": MANAGER_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "Tell me about privileged access incidents."}],
        "question": "What containment steps should I take?",
        "expected_behavior": "refuse",
        "expected_documents": [],
        "expected_rewrite_terms": ["privileged", "containment"],
    },
    {
        "id": "GEN-DOC-001",
        "category": "doc_reference",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": PEOPLE_DEPARTMENT_ID,
        "prior_turns": [{"role": "assistant", "content": "The PTO policy covers vacation and sick leave."}],
        "question": "What does the PTO document say about sick time?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-002"],
        "expected_rewrite_terms": ["pto", "sick"],
    },
    {
        "id": "GEN-DOC-002",
        "category": "doc_reference",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "I saw the benefits overview."}],
        "question": "What does that document say about learning budget?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-004"],
        "expected_rewrite_terms": ["benefits", "learning", "budget"],
    },
    {
        "id": "GEN-COMP-001",
        "category": "compare_two",
        "user_id": SALES_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": SALES_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "Compare discovery questions and objection handling."}],
        "question": "Which one should I use for price objections?",
        "expected_behavior": "answer",
        "expected_documents": ["SALES-003"],
        "expected_rewrite_terms": ["price", "objection"],
    },
    {
        "id": "GEN-HR-001",
        "category": "role_applicability",
        "user_id": HR_ADMIN_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": HR_ADMIN_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "I am checking employee-facing HR guidance."}],
        "question": "Which answer should I give if the policy is unclear?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-ADMIN-001"],
        "expected_rewrite_terms": ["policy", "unclear"],
    },
    {
        "id": "GEN-IT-001",
        "category": "same_department",
        "user_id": IT_ADMIN_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": IT_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "We discussed acceptable use."}],
        "question": "What about BYOD devices?",
        "expected_behavior": "answer",
        "expected_documents": ["IT-002"],
        "expected_rewrite_terms": ["byod", "device"],
    },
    {
        "id": "GEN-MISS-001",
        "category": "missing_info_followup",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": PEOPLE_DEPARTMENT_ID,
        "prior_turns": [{"role": "user", "content": "Tell me about leave benefits."}],
        "question": "What about sabbaticals?",
        "expected_behavior": "not_found",
        "expected_documents": [],
        "expected_rewrite_terms": ["sabbatical"],
    },
    {
        "id": "GEN-MULTI-001",
        "category": "multi_doc_reference",
        "user_id": EMPLOYEE_USER_ID,
        "project_id": PROJECT_ID,
        "department_id": None,
        "prior_turns": [{"role": "user", "content": "I work remotely and use a personal device."}],
        "question": "What approvals and safeguards apply?",
        "expected_behavior": "answer",
        "expected_documents": ["HR-003", "IT-002"],
        "expected_rewrite_terms": ["remote", "device"],
    },
]


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def _average(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    return round(mean(real_values), 3) if real_values else None


def _sum_cost(values: list[float | None]) -> float | None:
    real_values = [value for value in values if value is not None]
    return round(sum(real_values), 6) if real_values else None


def _citation_documents(response: dict[str, Any]) -> list[str]:
    return [str(citation.get("document_id")) for citation in response.get("citations") or [] if citation.get("document_id")]


def _retrieved_documents(response: dict[str, Any]) -> list[str]:
    return [str(chunk.get("document_id")) for chunk in response.get("retrieved_chunks") or [] if chunk.get("document_id")]


def _expected_docs_hit(expected: list[str], actual_docs: list[str]) -> float | None:
    if not expected:
        return None
    actual_text = " ".join(actual_docs)
    return 1.0 if all(expected_doc in actual_text for expected_doc in expected) else 0.0


def _rewrite_quality(probe: dict[str, Any], response: dict[str, Any]) -> float | None:
    terms = [str(term).lower() for term in probe.get("expected_rewrite_terms") or []]
    if not terms:
        return None
    rewritten = str((response.get("memory") or {}).get("rewritten_question") or response.get("question") or "").lower()
    return 1.0 if all(term in rewritten for term in terms) else 0.0


def _behavior_score(expected_behavior: str, response_type: str | None) -> float:
    if expected_behavior == "answer":
        return 1.0 if response_type in {"answer", "partial_answer"} else 0.0
    if expected_behavior == "clarify":
        return 1.0 if response_type == "clarify" else 0.0
    if expected_behavior == "refuse":
        return 1.0 if response_type == "refuse_no_access" else 0.0
    if expected_behavior == "not_found":
        return 1.0 if response_type == "not_found" else 0.0
    return 0.0


def _memory_as_evidence_violation(response: dict[str, Any]) -> float:
    citation_text = " ".join(_citation_documents(response)).lower()
    return 1.0 if "memory" in citation_text or "conversation" in citation_text else 0.0


def _permission_safety(response: dict[str, Any]) -> float:
    permission_check = response.get("permission_check") or {}
    return 0.0 if permission_check.get("unauthorized_chunks_reached_generation") else 1.0


def _create_session_with_history(probe: dict[str, Any]) -> str | None:
    prior_turns = probe.get("prior_turns") or []
    if not prior_turns:
        return None
    session_id = create_session(USER_ROLES.get(probe["user_id"], "Employee"), user_id=probe["user_id"])
    for turn in prior_turns:
        add_message(session_id=session_id, role=turn["role"], content=turn["content"])
    return session_id


def _run_probe(client: TestClient, probe: dict[str, Any]) -> dict[str, Any]:
    session_id = _create_session_with_history(probe)
    started = time.perf_counter()
    response = client.post(
        "/query",
        headers={DEMO_USER_HEADER: probe["user_id"]},
        json={
            "question": probe["question"],
            "session_id": session_id,
            "project_id": probe.get("project_id"),
            "department_id": probe.get("department_id"),
            "retrieval_mode": "vector_lexical_rerank",
            "top_k": 5,
            "rerank_candidate_limit": 20,
            "prompt_version": "v8",
        },
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    response.raise_for_status()
    payload = response.json()
    citation_docs = _citation_documents(payload)
    retrieved_docs = _retrieved_documents(payload)
    response_type = payload.get("response_type")
    expected_behavior = probe["expected_behavior"]
    behavior_score = _behavior_score(expected_behavior, response_type)
    citation_score = _expected_docs_hit(probe.get("expected_documents") or [], citation_docs)
    retrieval_score = _expected_docs_hit(probe.get("expected_documents") or [], retrieved_docs)
    row = {
        "probe_id": probe["id"],
        "category": probe["category"],
        "question": probe["question"],
        "expected_behavior": expected_behavior,
        "response_type": response_type,
        "behavior_score": behavior_score,
        "memory_rewrite_quality": _rewrite_quality(probe, payload),
        "clarification_behavior": behavior_score if expected_behavior == "clarify" else None,
        "answer_citation_quality": citation_score if expected_behavior == "answer" else None,
        "retrieval_expected_source_hit": retrieval_score,
        "permission_safety": _permission_safety(payload),
        "memory_as_evidence_violation": _memory_as_evidence_violation(payload),
        "rewritten_question": (payload.get("memory") or {}).get("rewritten_question"),
        "memory_used": (payload.get("memory") or {}).get("memory_used"),
        "citation_documents": citation_docs,
        "retrieved_documents": retrieved_docs,
        "unauthorized_chunks_reached_generation": (payload.get("permission_check") or {}).get("unauthorized_chunks_reached_generation"),
        "input_tokens": payload.get("input_tokens"),
        "output_tokens": payload.get("output_tokens"),
        "estimated_cost_usd": payload.get("estimated_cost_usd"),
        "latency_ms": latency_ms,
    }
    row["passed"] = (
        row["behavior_score"] == 1.0
        and (row["answer_citation_quality"] in {None, 1.0})
        and row["permission_safety"] == 1.0
        and row["memory_as_evidence_violation"] == 0.0
    )
    return row


def _summary(rows: list[dict[str, Any]], *, run_id: str, run_name: str, phase: str, baseline: bool) -> dict[str, Any]:
    failed = [row for row in rows if not row["passed"]]
    final_note = (
        "This is a baseline run; no prompt or retrieval remediation is included."
        if baseline
        else "This is a remediation run against the same probe suite; compare with phase45-generalization-baseline."
    )
    return {
        "run_id": run_id,
        "run_name": run_name,
        "phase": phase,
        "probe_count": len(rows),
        "failed_probe_count": len(failed),
        "category_counts": dict(sorted(Counter(row["category"] for row in rows).items())),
        "behavior_accuracy": _average([row["behavior_score"] for row in rows]),
        "memory_rewrite_quality": _average([row["memory_rewrite_quality"] for row in rows]),
        "clarification_behavior": _average([row["clarification_behavior"] for row in rows]),
        "answer_citation_quality": _average([row["answer_citation_quality"] for row in rows]),
        "permission_safety": _average([row["permission_safety"] for row in rows]),
        "memory_as_evidence_violation_rate": _average([row["memory_as_evidence_violation"] for row in rows]),
        "input_tokens": sum(row.get("input_tokens") or 0 for row in rows),
        "output_tokens": sum(row.get("output_tokens") or 0 for row in rows),
        "estimated_cost": _sum_cost([row.get("estimated_cost_usd") for row in rows]),
        "notes": [
            "This suite is separate from benchmark v1.1 and should not be folded into benchmark metrics.",
            "Memory is evaluated as query context only; citations must still come from retrieved documents.",
            final_note,
        ],
    }


def _eval_run(result: dict[str, Any]) -> dict[str, Any]:
    summary = result["summary"]
    return {
        "run_id": summary["run_id"],
        "run_name": summary["run_name"],
        "phase": summary["phase"],
        "run_type": "generalization_eval",
        "timestamp": result["generated_at"],
        "benchmark_version": "generalization-probes-v0",
        "total_questions": summary["probe_count"],
        "metrics": {
            "failed_probe_count": summary["failed_probe_count"],
            "behavior_accuracy": summary["behavior_accuracy"],
            "memory_rewrite_quality": summary["memory_rewrite_quality"],
            "clarification_behavior": summary["clarification_behavior"],
            "answer_citation_quality": summary["answer_citation_quality"],
            "permission_safety": summary["permission_safety"],
            "memory_as_evidence_violation_rate": summary["memory_as_evidence_violation_rate"],
            "input_tokens": summary["input_tokens"],
            "output_tokens": summary["output_tokens"],
            "estimated_cost": summary["estimated_cost"],
        },
        "notes": summary["notes"],
    }


def _report(result: dict[str, Any], *, title: str) -> str:
    summary = result["summary"]
    lines = [
        f"# {title}",
        "",
        f"Generated at: {result['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Probe count: `{summary['probe_count']}`",
        f"- Failed probes: `{summary['failed_probe_count']}`",
        f"- Behavior accuracy: `{summary['behavior_accuracy']}`",
        f"- Memory rewrite quality: `{summary['memory_rewrite_quality']}`",
        f"- Clarification behavior: `{summary['clarification_behavior']}`",
        f"- Answer/citation quality: `{summary['answer_citation_quality']}`",
        f"- Permission safety: `{summary['permission_safety']}`",
        f"- Memory-as-evidence violation rate: `{summary['memory_as_evidence_violation_rate']}`",
        f"- Estimated chat cost: `{summary['estimated_cost']}`",
        "",
        "## Probe Results",
        "",
        "| Probe | Category | Expected | Actual | Rewrite | Citation Docs | Passed |",
        "|---|---|---|---|---|---|---:|",
    ]
    for row in result["rows"]:
        lines.append(
            "| {probe_id} | {category} | {expected_behavior} | {response_type} | {rewritten_question} | {citation_documents} | {passed} |".format(
                **{
                    **row,
                    "rewritten_question": row.get("rewritten_question") or "",
                    "citation_documents": ", ".join(row.get("citation_documents") or []),
                }
            )
        )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in summary["notes"])
    return "\n".join(lines) + "\n"


def run_live(*, run_id: str, run_name: str, phase: str, baseline: bool) -> dict[str, Any]:
    client = TestClient(app)
    rows = [_run_probe(client, probe) for probe in PROBES]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": _summary(rows, run_id=run_id, run_name=run_name, phase=phase, baseline=baseline),
        "rows": rows,
        "failed_probes": [row for row in rows if not row["passed"]],
        "probes": PROBES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 45 generalization probe baseline.")
    parser.add_argument("--dry-run", action="store_true", help="Print probe metadata without external AI calls.")
    parser.add_argument("--allow-external-ai", action="store_true", help="Confirm approval for external OpenAI calls.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--phase", default=DEFAULT_PHASE)
    parser.add_argument("--detail-path", type=Path, default=DEFAULT_DETAIL_PATH)
    parser.add_argument("--eval-run-path", type=Path, default=DEFAULT_EVAL_RUN_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--report-title", default=DEFAULT_REPORT_TITLE)
    parser.add_argument("--remediation-run", action="store_true", help="Use remediation-run notes instead of baseline notes.")
    args = parser.parse_args()
    detail_path = args.detail_path if args.detail_path.is_absolute() else ROOT / args.detail_path
    eval_run_path = args.eval_run_path if args.eval_run_path.is_absolute() else ROOT / args.eval_run_path
    report_path = args.report_path if args.report_path.is_absolute() else ROOT / args.report_path

    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_id": args.run_id,
                    "run_name": args.run_name,
                    "phase": args.phase,
                    "probe_count": len(PROBES),
                    "categories": dict(sorted(Counter(probe["category"] for probe in PROBES).items())),
                    "would_write": [str(detail_path), str(eval_run_path), str(report_path)],
                    "external_ai_required": True,
                },
                indent=2,
            )
        )
        return

    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)
    if not get_settings().openai_api_key:
        raise SystemExit("OPENAI_API_KEY or OPENAI_API_KEY_FILE is required for the live generalization run.")

    result = run_live(run_id=args.run_id, run_name=args.run_name, phase=args.phase, baseline=not args.remediation_run)
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    eval_run_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    detail_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    eval_run_path.write_text(json.dumps(_eval_run(result), indent=2), encoding="utf-8")
    _write_text_atomic(report_path, _report(result, title=args.report_title))
    print(json.dumps(result["summary"], indent=2))
    print(f"Wrote {detail_path}")
    print(f"Wrote {eval_run_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
