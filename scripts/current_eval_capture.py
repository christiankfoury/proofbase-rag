"""Capture one application response with custody before optional separate grading."""
from scripts.run_fresh_eval import now, setup_upload, authoritative_evidence
from scripts.current_eval_budget import BudgetStop
from scripts.reliable_evaluation_run import write_json_atomic
import time

def measure_case(client, settings, case, path, ledger):
    from apps.api.app.auth.demo_auth import DEMO_USER_HEADER
    from apps.api.app.memory.session_store import create_session, add_message
    from apps.api.app.auth.tenant_context import tenant_security_context
    from openai import OpenAI
    record = {"case_id": case["case_id"], "category": case["category"], "started_at": now(),
              "status": "started", "call_start": len(ledger.data["calls"])}
    write_json_atomic(path, record)
    if case.get("upload_fixture"):
        def save_fixture(state):
            record["fixture"] = state
            write_json_atomic(path, record)
        record["fixture"] = setup_upload(client, case, progress=save_fixture)
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
    record.update(status="complete", completed_at=now(), call_end=len(ledger.data["calls"]))
    write_json_atomic(path, record)
    return record
