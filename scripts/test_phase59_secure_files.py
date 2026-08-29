from __future__ import annotations

import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.auth.tenant_context import tenant_security_context
from apps.api.app.core.config import Settings, get_settings
from apps.api.app.db.session import apply_schema, get_connection
from apps.api.app.files.secure_files import (
    EICAR_MARKER,
    FilePolicyError,
    FixtureSignatureScanner,
    LocalQuarantineStorage,
    create_file_object,
    delete_file_object,
    issue_read_grant,
    parse_pdf_isolated,
    verify_read_grant,
)
from apps.api.app.main import app
from scripts.run_phase40_upload_e2e import _pdf_bytes


TENANT = "00000000-0000-0000-0000-000000002801"
OTHER_TENANT = "00000000-0000-0000-0000-000000002899"
USER = "00000000-0000-0000-0000-000000002706"
PROJECT = "00000000-0000-0000-0000-000000000019"
DEPARTMENT = "00000000-0000-0000-0000-000000002011"


def _expect_reason(reason: str, callback) -> None:
    try:
        callback()
    except FilePolicyError as exc:
        assert exc.reason_code == reason, (exc.reason_code, reason)
    else:
        raise AssertionError(f"Expected {reason}")


def test_envelope_scanner_parser_and_storage() -> None:
    from apps.api.app.files.secure_files import validate_pdf_envelope

    pdf = _pdf_bytes("Phase 59 safe synthetic content")
    valid = dict(filename="safe.pdf", declared_mime="application/pdf", content=pdf, data_classification="non_sensitive")
    validate_pdf_envelope(**valid)
    _expect_reason("unsupported_file_type", lambda: validate_pdf_envelope(**(valid | {"filename": "safe.txt"})))
    _expect_reason("declared_mime_mismatch", lambda: validate_pdf_envelope(**(valid | {"declared_mime": "text/plain"})))
    _expect_reason("file_signature_mismatch", lambda: validate_pdf_envelope(**(valid | {"content": b"not-pdf%%EOF"})))
    _expect_reason("malformed_pdf", lambda: validate_pdf_envelope(**(valid | {"content": b"%PDF-1.4"})))
    _expect_reason("polyglot_or_trailing_payload", lambda: validate_pdf_envelope(**(valid | {"content": pdf + b"PK\x03\x04"})))
    _expect_reason("polyglot_or_embedded_archive", lambda: validate_pdf_envelope(**(valid | {"content": pdf.replace(b"%%EOF", b"PK\x03\x04%%EOF")})))
    _expect_reason("unsupported_pdf_active_content", lambda: validate_pdf_envelope(**(valid | {"content": pdf.replace(b"%%EOF", b"/JavaScript%%EOF")})))
    _expect_reason(
        "regulated_or_personal_data_not_accepted",
        lambda: validate_pdf_envelope(**(valid | {"data_classification": "personal"})),
    )
    tiny_settings = SimpleNamespace(file_max_bytes=len(pdf) - 1)
    with patch("apps.api.app.files.secure_files.get_settings", return_value=tiny_settings):
        _expect_reason("file_too_large", lambda: validate_pdf_envelope(**valid))

    scanner = FixtureSignatureScanner()
    assert scanner.scan(pdf).verdict == "passed_fixture_checks"
    assert scanner.scan(pdf + EICAR_MARKER).reason_code == "known_test_signature"

    with tempfile.TemporaryDirectory() as directory:
        storage = LocalQuarantineStorage(Path(directory))
        key = storage.put(TENANT, pdf)
        assert key.startswith(f"{TENANT}/") and key.endswith(".blob")
        assert storage.path_for_parser(TENANT, key).read_bytes() == pdf
        _expect_reason("tenant_storage_scope_mismatch", lambda: storage.path_for_parser(OTHER_TENANT, key))
        _expect_reason("invalid_storage_key", lambda: storage.path_for_parser(TENANT, f"{TENANT}/../../escape"))
        parsed = parse_pdf_isolated(storage.path_for_parser(TENANT, key), title="Safe fixture")
        assert parsed.page_count == 1 and "Phase 59 safe synthetic content" in parsed.markdown
        parser_settings = SimpleNamespace(
            file_parser_mode="subprocess",
            file_max_pages=0,
            file_max_extracted_chars=2_000_000,
            file_max_expansion_ratio=200,
            file_parser_timeout_seconds=15,
        )
        with patch("apps.api.app.files.secure_files.get_settings", return_value=parser_settings):
            _expect_reason("parser_page_limit", lambda: parse_pdf_isolated(storage.path_for_parser(TENANT, key), title="Page limit"))
        parser_settings.file_max_pages = 100
        parser_settings.file_max_extracted_chars = 10
        with patch("apps.api.app.files.secure_files.get_settings", return_value=parser_settings):
            _expect_reason("parser_expansion_limit", lambda: parse_pdf_isolated(storage.path_for_parser(TENANT, key), title="Character limit"))
        parser_settings.file_max_extracted_chars = 2_000_000
        parser_settings.file_max_expansion_ratio = 0
        with patch("apps.api.app.files.secure_files.get_settings", return_value=parser_settings):
            _expect_reason("parser_expansion_ratio", lambda: parse_pdf_isolated(storage.path_for_parser(TENANT, key), title="Ratio limit"))
        malformed_key = storage.put(TENANT, b"%PDF-1.4\nnot a parseable PDF\n%%EOF")
        with patch("apps.api.app.files.secure_files.get_settings", return_value=parser_settings):
            _expect_reason("parser_malformed_pdf", lambda: parse_pdf_isolated(storage.path_for_parser(TENANT, malformed_key), title="Malformed"))
        with patch("apps.api.app.files.secure_files.subprocess.run", side_effect=subprocess.TimeoutExpired("parser", 1)):
            _expect_reason("parser_timeout", lambda: parse_pdf_isolated(storage.path_for_parser(TENANT, key), title="Timeout"))


def test_scoped_grants_and_production_guards() -> None:
    settings = SimpleNamespace(file_access_signing_secret="phase59-test-signing-secret")
    with patch("apps.api.app.files.secure_files.get_settings", return_value=settings):
        token = issue_read_grant(file_object_id="file-1", tenant_id=TENANT, ttl_seconds=10, now=100)
        assert verify_read_grant(token, tenant_id=TENANT, now=109) == "file-1"
        _expect_reason("expired_or_wrong_tenant_file_grant", lambda: verify_read_grant(token, tenant_id=TENANT, now=111))
        _expect_reason("expired_or_wrong_tenant_file_grant", lambda: verify_read_grant(token, tenant_id=OTHER_TENANT, now=101))
        _expect_reason("invalid_file_grant", lambda: verify_read_grant(token + "tampered", tenant_id=TENANT, now=101))

    base = dict(
        app_environment="production",
        auth_mode="oidc",
        database_url="postgresql://proofbase_runtime:password@db/proofbase",
        database_enforce_rls=True,
        rate_limit_backend="redis",
    )
    try:
        Settings(**base)
    except ValueError as exc:
        assert "isolated file-parser" in str(exc)
    else:
        raise AssertionError("Production accepted the local subprocess parser")
    try:
        Settings(**(base | {"file_parser_mode": "isolated_worker"}))
    except ValueError as exc:
        assert "malware-scanner" in str(exc)
    else:
        raise AssertionError("Production accepted the fixture-only scanner")


def test_database_lifecycle_and_rls() -> None:
    apply_schema()
    pdf = _pdf_bytes("Phase 59 database lifecycle synthetic content")
    file_object_id: str | None = None
    with tempfile.TemporaryDirectory() as directory:
        storage = LocalQuarantineStorage(Path(directory))
        with tenant_security_context(tenant_id=TENANT, user_id=USER):
            key = storage.put(TENANT, pdf)
            created = create_file_object(
                project_id=PROJECT,
                department_id=DEPARTMENT,
                original_name="phase59.pdf",
                declared_mime="application/pdf",
                content=pdf,
                storage_key=key,
            )
            file_object_id = created["id"]
            _expect_reason(
                "duplicate_file",
                lambda: create_file_object(
                    project_id=PROJECT,
                    department_id=DEPARTMENT,
                    original_name="renamed.pdf",
                    declared_mime="application/pdf",
                    content=pdf,
                    storage_key=f"{TENANT}/duplicate.blob",
                ),
            )
            with get_connection() as conn:
                conn.execute("update file_objects set legal_hold = true where id = %s::uuid", (file_object_id,))
            _expect_reason("legal_hold_prevents_deletion", lambda: delete_file_object(file_object_id, storage=storage))

        with tenant_security_context(tenant_id=OTHER_TENANT, user_id=USER):
            with get_connection() as conn:
                assert conn.execute("select count(*) as count from file_objects where id = %s::uuid", (file_object_id,)).fetchone()["count"] == 0

        with tenant_security_context(tenant_id=TENANT, user_id=USER):
            with get_connection() as conn:
                conn.execute("update file_objects set legal_hold = false where id = %s::uuid", (file_object_id,))
            assert delete_file_object(file_object_id, storage=storage)
            assert not (Path(directory) / key).exists()

    if file_object_id:
        with psycopg.connect(get_settings().database_url) as conn:
            conn.execute("delete from file_objects where id = %s::uuid", (file_object_id,))


def test_api_quarantine_before_review() -> None:
    pdf = _pdf_bytes("Phase 59 API quarantine synthetic content")
    client = TestClient(app)
    document_id: str | None = None
    version_id: str | None = None
    file_object_ids: list[str] = []
    with patch("apps.api.app.main.log_audit_event", return_value=True):
        response = client.post(
            f"/projects/{PROJECT}/departments/{DEPARTMENT}/documents/upload",
            headers={"X-Demo-User-Id": USER},
            data={"title": "Phase 59 quarantine check", "data_classification": "non_sensitive"},
            files={"file": ("safe.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 201, response.text
        document = response.json()["document"]
        document_id = document["id"]
        version_id = document["version"]["id"]
        assert document["version"]["ingestion_status"] == "pending_review"
        assert document["chunk_count"] == 0
        file_object_ids.append(document["version"]["metadata"]["file_object_id"])

        fixture_pdf = pdf.replace(b"%%EOF", EICAR_MARKER + b"\n%%EOF")
        rejected = client.post(
            f"/projects/{PROJECT}/departments/{DEPARTMENT}/documents/upload",
            headers={"X-Demo-User-Id": USER},
            data={"title": "Phase 59 rejected fixture", "data_classification": "non_sensitive"},
            files={"file": ("fixture.pdf", fixture_pdf, "application/pdf")},
        )
        assert rejected.status_code == 400 and rejected.json()["detail"] == "known_test_signature"

    with tenant_security_context(tenant_id=TENANT, user_id=USER):
        with get_connection() as conn:
            rejected_row = conn.execute(
                "select id::text, lifecycle_state from file_objects where content_sha256 = %s",
                (hashlib.sha256(fixture_pdf).hexdigest(),),
            ).fetchone()
        assert rejected_row and rejected_row["lifecycle_state"] == "rejected"
        file_object_ids.append(rejected_row["id"])
        storage = LocalQuarantineStorage()
        for object_id in file_object_ids:
            assert delete_file_object(object_id, storage=storage)

    if document_id and version_id:
        with psycopg.connect(get_settings().database_url) as conn:
            conn.execute("delete from ingestion_jobs where document_id = %s::uuid", (document_id,))
            conn.execute("update documents set current_version_id = null where id = %s::uuid", (document_id,))
            conn.execute("delete from document_versions where id = %s::uuid", (version_id,))
            conn.execute("delete from documents where id = %s::uuid", (document_id,))
            conn.execute("delete from file_objects where id = any(%s::uuid[])", (file_object_ids,))


def main() -> None:
    test_envelope_scanner_parser_and_storage()
    test_scoped_grants_and_production_guards()
    test_database_lifecycle_and_rls()
    test_api_quarantine_before_review()
    print("Phase 59 secure-file checks passed.")


if __name__ == "__main__":
    main()
