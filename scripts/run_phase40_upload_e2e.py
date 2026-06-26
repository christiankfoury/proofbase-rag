from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.api.app.main import app


PROJECT_ID = "00000000-0000-0000-0000-000000000019"
DEPARTMENT_ID = "00000000-0000-0000-0000-000000002011"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000002706"
EMPLOYEE_USER_ID = "00000000-0000-0000-0000-000000002701"
DETAIL_PATH = ROOT / "data/evaluation/phase40-upload-e2e.json"
REPORT_PATH = ROOT / "docs/phase-40/upload-e2e-results.md"
EXTERNAL_AI_APPROVAL_MESSAGE = (
    "The Phase 40 upload E2E approves an uploaded PDF for indexing and asks a scoped question, "
    "which sends uploaded text and the user question to external OpenAI embeddings and chat-completion APIs. "
    "Re-run with --allow-external-ai only after explicit approval."
)


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
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _write_report(result: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 40 Upload E2E Results",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Result",
        "",
        f"- Status: `{result['status']}`",
        f"- Uploaded document: `{result['document']['external_document_id']}`",
        f"- Ingestion status: `{result['document']['version']['ingestion_status']}`",
        f"- Chunk count: `{result['document']['chunk_count']}`",
        f"- Query response type: `{result['query']['response_type']}`",
        f"- Uploaded document retrieved: `{result['uploaded_document_retrieved']}`",
        f"- Uploaded document cited: `{result['uploaded_document_cited']}`",
        f"- Citation documents: `{', '.join(result['query']['citation_documents']) or 'None'}`",
        f"- Retrieved documents: `{', '.join(result['query']['retrieved_documents']) or 'None'}`",
        "",
        "## Notes",
        "",
        "- The test used the real upload, approve/index, and query API paths through FastAPI TestClient.",
        "- The uploaded PDF text was synthetic and generated locally for this check.",
        "- OpenAI embeddings and chat completion were called with explicit approval.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_e2e() -> dict[str, Any]:
    client = TestClient(app)
    admin_headers = {"X-Demo-User-Id": ADMIN_USER_ID}
    employee_headers = {"X-Demo-User-Id": EMPLOYEE_USER_ID}
    title = f"Phase 40 Upload Verification {datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    text = (
        "Phase 40 upload verification: vendors need Operations review before starting work. "
        "This uploaded document is scoped to the Operations department and Employee role."
    )

    upload_response = client.post(
        f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/upload",
        headers=admin_headers,
        data={
            "title": title,
            "access_roles": "Employee, Manager",
            "restricted": "false",
        },
        files={"file": ("phase40-upload-verification.pdf", _pdf_bytes(text), "application/pdf")},
    )
    upload_response.raise_for_status()
    uploaded_document = upload_response.json()["document"]
    if uploaded_document["version"]["ingestion_status"] != "pending_review":
        raise AssertionError(f"Expected pending_review after upload, got {uploaded_document['version']['ingestion_status']}")
    if uploaded_document["chunk_count"] != 0:
        raise AssertionError("Uploaded document should not have chunks before approval.")

    approve_response = client.post(
        f"/projects/{PROJECT_ID}/departments/{DEPARTMENT_ID}/documents/{uploaded_document['id']}/approve-index",
        headers=admin_headers,
    )
    approve_response.raise_for_status()
    indexed_document = approve_response.json()["document"]
    if indexed_document["version"]["ingestion_status"] != "indexed":
        raise AssertionError(f"Expected indexed after approval, got {indexed_document['version']['ingestion_status']}")
    if indexed_document["chunk_count"] < 1:
        raise AssertionError("Approved uploaded document should have at least one indexed chunk.")

    query_response = client.post(
        "/query",
        headers=employee_headers,
        json={
            "question": "What does the Phase 40 upload verification say vendors need before starting work?",
            "project_id": PROJECT_ID,
            "department_id": DEPARTMENT_ID,
            "retrieval_mode": "vector_lexical_rerank",
            "top_k": 5,
            "prompt_version": "v8",
        },
    )
    query_response.raise_for_status()
    query = query_response.json()
    external_document_id = indexed_document["external_document_id"]
    citation_documents = [citation["document_id"] for citation in query.get("citations") or []]
    retrieved_documents = [chunk["document_id"] for chunk in query.get("retrieved_chunks") or []]
    uploaded_document_retrieved = external_document_id in retrieved_documents
    uploaded_document_cited = external_document_id in citation_documents
    if not uploaded_document_retrieved:
        raise AssertionError(f"Uploaded document {external_document_id} was not retrieved: {retrieved_documents}")
    if not uploaded_document_cited:
        raise AssertionError(f"Uploaded document {external_document_id} was not cited: {citation_documents}")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed",
        "document": indexed_document,
        "uploaded_document_retrieved": uploaded_document_retrieved,
        "uploaded_document_cited": uploaded_document_cited,
        "query": {
            "question": "What does the Phase 40 upload verification say vendors need before starting work?",
            "response_type": query.get("response_type"),
            "answer": query.get("answer"),
            "citation_documents": citation_documents,
            "retrieved_documents": retrieved_documents,
            "scope": query.get("scope"),
            "permission_check": query.get("permission_check"),
            "final_confidence": (query.get("confidence") or {}).get("final_confidence"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 40 upload -> approve/index -> scoped ask E2E.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-external-ai",
        action="store_true",
        help="Confirm explicit approval to send uploaded text and query text to external AI APIs.",
    )
    args = parser.parse_args()
    if args.dry_run:
        print(
            json.dumps(
                {
                    "project_id": PROJECT_ID,
                    "department_id": DEPARTMENT_ID,
                    "would_write": [str(DETAIL_PATH), str(REPORT_PATH)],
                    "external_ai_required": True,
                },
                indent=2,
            )
        )
        return
    if not args.allow_external_ai:
        raise SystemExit(EXTERNAL_AI_APPROVAL_MESSAGE)

    result = run_e2e()
    DETAIL_PATH.parent.mkdir(parents=True, exist_ok=True)
    DETAIL_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_report(result)
    print(json.dumps(result, indent=2))
    print(f"Wrote {DETAIL_PATH}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
