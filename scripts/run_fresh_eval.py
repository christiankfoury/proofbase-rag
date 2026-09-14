"""One-shot current-runtime measurement. Never resumes or repeats started cases."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, UTC
import json
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.fresh_eval_protocol import FOLDER, verify_custody
from scripts.fresh_eval_environment import configure, fingerprint
from scripts.fresh_eval_budget import Ledger, BudgetStop
from scripts.fresh_eval_grader import grade_response, verdict
from scripts.reliable_evaluation_run import write_json_atomic


def now():
    return datetime.now(UTC).isoformat()


def require_unstarted(folder):
    if folder.exists():
        raise ValueError("Run directory exists; started cases may never be rerun or reconstructed")


def authoritative_evidence(settings, case, payload):
    import psycopg
    from psycopg.rows import dict_row
    from apps.api.app.permissions.access_control import role_can_access
    evidence, flags = [], []
    returned = payload.get("retrieved_chunks", [])
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        for chunk in returned:
            row = conn.execute("""select c.id::text as chunk_id, d.external_document_id as document_id,
                c.content, d.access_roles, d.project_id::text, d.department_id::text, d.tenant_id::text
                from chunks c join documents d on d.id=c.document_id where c.id::text=%s""",
                (str(chunk.get("chunk_id")),)).fetchone()
            if not row:
                flags.append("unknown_returned_chunk")
                continue
            permitted = (role_can_access(row["access_roles"], case["user_role"])
                and row["project_id"] == case["project_id"]
                and row["tenant_id"] == settings.default_demo_tenant_id
                and (not case.get("department_id") or row["department_id"] == case["department_id"]))
            if not permitted:
                flags.append("unauthorized_returned_evidence")
            elif row["document_id"] != chunk.get("document_id"):
                flags.append("returned_identity_mismatch")
            else:
                evidence.append(dict(row))
    permission = payload.get("permission_check", {})
    if permission.get("unauthorized_chunks_reached_generation"):
        flags.append("runtime_reports_unauthorized_generation")
    return evidence, sorted(set(flags))


def setup_upload(client, case):
    """Real review/index workflow in a distinct project; query remains in Northstar."""
    from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
    from scripts.run_independent_generalization_eval import _pdf_bytes, _upload_content, _approve, ADMIN_USER_ID
    headers = {DEMO_USER_HEADER: ADMIN_USER_ID}
    response = client.post("/projects", headers=headers, json={"name": "Fresh evaluation " + case["case_id"]})
    response.raise_for_status()
    project = response.json()["project"]["id"]
    response = client.post(f"/projects/{project}/departments", headers=headers,
                           json={"name": "Isolated evaluation documents", "default_access_roles": ["Employee"]})
    response.raise_for_status()
    department = response.json()["department"]["id"]
    fixture = case["upload_fixture"]
    document = _upload_content(client, project_id=project, department_id=department,
        title=fixture["title"], content=_pdf_bytes(fixture["text"]), filename=case["case_id"] + ".pdf",
        content_type="application/pdf", access_roles=["Employee", "Manager"], restricted=False)
    approved = _approve(client, project_id=project, department_id=department, document_id=document["id"])
    return {"project_id": project, "department_id": department,
            "uploaded_document": document, "approved_document": approved}


def measure_case(client, settings, case, path, ledger):
    from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
    from apps.api.app.memory.session_store import create_session, add_message
    from apps.api.app.auth.tenant_context import tenant_security_context
    from openai import OpenAI
    record = {"case_id": case["case_id"], "category": case["category"], "started_at": now(),
              "status": "started", "call_start": len(ledger.data["calls"])}
    write_json_atomic(path, record)
    if case.get("upload_fixture"):
        record["fixture"] = setup_upload(client, case)
        write_json_atomic(path, record)
    session = None
    if case.get("previous_turns"):
        with tenant_security_context(tenant_id=settings.default_demo_tenant_id, user_id=case["user_id"]):
            session = create_session(case["user_role"], case["user_id"])
            for turn in case["previous_turns"]:
                add_message(session_id=session, role=turn["role"], content=turn["content"])
    request = {"question": case["question"], "session_id": session, "project_id": case["project_id"],
               "department_id": case.get("department_id"), "retrieval_mode": "vector_lexical_rerank",
               "top_k": 5, "rerank_candidate_limit": 20}
    started = time.perf_counter()
    response = client.post("/query", headers={DEMO_USER_HEADER: case["user_id"]}, json=request)
    record.update(status="response_saved", http_status=response.status_code, request=request,
                  raw_response=response.json(), latency_ms=round((time.perf_counter()-started)*1000, 2))
    # This precedes evidence inspection and grading, including their possible failures.
    write_json_atomic(path, record)
    if ledger.data.get("unknown_outcome") or ledger.data.get("budget_exhausted"):
        raise BudgetStop("Application encountered an unsettled call or budget stop")
    payload = dict(record["raw_response"])
    payload["citations"] = [dict(c, citation_id=f"C{i}") for i, c in enumerate(payload.get("citations", []), 1)]
    evidence, flags = authoritative_evidence(settings, case, payload)
    if response.status_code != 200:
        flags.append("http_error")
    record.update(authorized_evidence=evidence, safety_flags=flags)
    write_json_atomic(path, record)
    grade = grade_response(OpenAI(api_key=settings.openai_api_key), case, payload, evidence)
    record.update(grade=grade, **verdict(case, payload, evidence, grade, flags), status="complete", completed_at=now(),
                  call_end=len(ledger.data["calls"]))
    write_json_atomic(path, record)
    return record


def summarize(cases, rows):
    complete = len(rows) == len(cases) and all(r.get("status") == "complete" for r in rows)
    def rate(selected):
        return {"passed": sum(r["passed"] for r in selected), "total": len(selected),
                "rate": sum(r["passed"] for r in selected)/len(selected) if complete and selected else None}
    answer_ids = {c["case_id"] for c in cases if c["expected_behavior"] == "answer"}
    return {"status": "complete" if complete else "incomplete", "expected_cases": len(cases), "completed_cases": len(rows),
            "full_response": rate(rows), "answer_expected": rate([r for r in rows if r["case_id"] in answer_ids]),
            "non_answer_expected": rate([r for r in rows if r["case_id"] not in answer_ids]),
            "failure_taxonomy": dict(Counter(f for r in rows for f in r["failure_reasons"])),
            "human_review": "pending", "target": 0.8,
            "target_met": complete and sum(r["passed"] for r in rows)/len(cases) >= .8,
            "scope": "Automated full-response rubric; 60 authored synthetic cases; no population or human-verified claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-external-ai", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    freeze, suite = verify_custody()
    settings = configure()
    if freeze["environment"] != fingerprint(settings):
        raise SystemExit("Frozen configuration/database fingerprint changed")
    run = FOLDER / "run-v1"
    require_unstarted(run)
    if args.preflight:
        print("Custody, schema, environment, and unused run path verified; no API calls")
        return
    if not args.allow_external_ai:
        raise SystemExit("Explicit --allow-external-ai is required")
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    ledger = Ledger(FOLDER / "api-ledger.json")
    if ledger.data.get("unknown_outcome") or ledger.data.get("budget_exhausted"):
        raise SystemExit("Existing ledger is stopped; no holdout execution permitted")
    rows = []
    run.mkdir()
    manifest = {"status": "running", "started_at": now(), "freeze": freeze["commit"], "expected_cases": 60}
    write_json_atomic(run / "manifest.json", manifest)
    try:
        with ledger.intercept(), TestClient(app) as client:
            for case in suite["cases"]:
                row = measure_case(client, settings, case, run / (case["case_id"] + ".json"), ledger)
                rows.append(row)
                print(f"Completed {len(rows)}/60 ({case['case_id']})", flush=True)
    except Exception as exc:
        # Do not publish provider exception strings, which can contain request data.
        manifest.update(status="interrupted", exception_type=type(exc).__name__)
        raise
    finally:
        summary = summarize(suite["cases"], rows)
        summary["cost_usd_including_calibration"] = ledger.spent
        write_json_atomic(FOLDER / "summary.json", summary)
        packet = {"status": "pending", "instructions": "Named human: review ALL cases and exact citations; enter identity, UTC timestamp, decision and reasoning. Agent work is not human review.",
                  "cases": [{"case_id": c["case_id"], "response_file": f"run-v1/{c['case_id']}.json",
                             "reviewer": None, "reviewed_at": None, "decision": None, "notes": None} for c in suite["cases"]]}
        write_json_atomic(FOLDER / "human-review.json", packet)
        manifest.update(completed_cases=len(rows), finished_at=now())
        if len(rows) == 60:
            manifest["status"] = "complete"
        write_json_atomic(run / "manifest.json", manifest)


if __name__ == "__main__":
    main()
