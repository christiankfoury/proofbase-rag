from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import psycopg
from psycopg import errors
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.auth.tenant_context import set_request_principal
from apps.api.app.core.config import Settings, get_settings
from apps.api.app.db.session import apply_schema
from apps.api.app.embeddings import openai_embeddings
from apps.api.app.observability import summary as observability_summary
from apps.api.app.main import app
from apps.api.app.files.secure_files import FilePolicyError, LocalQuarantineStorage
from fastapi.testclient import TestClient


DEMO_TENANT = "00000000-0000-0000-0000-000000002801"
OTHER_TENANT = "00000000-0000-0000-0000-000000002899"
DEMO_USER = "00000000-0000-0000-0000-000000002701"
OTHER_PROJECT = "00000000-0000-0000-0000-000000002991"
OTHER_DEPARTMENT = "00000000-0000-0000-0000-000000002992"
OTHER_DOCUMENT = "00000000-0000-0000-0000-000000002993"
OTHER_VERSION = "00000000-0000-0000-0000-000000002994"
OTHER_CHUNK = "00000000-0000-0000-0000-000000002995"
OTHER_SESSION = "00000000-0000-0000-0000-000000002996"
OTHER_MESSAGE = "00000000-0000-0000-0000-000000002997"
OTHER_RUN = "00000000-0000-0000-0000-000000002998"
OTHER_USER = "00000000-0000-0000-0000-000000002990"


def _set_runtime_context(conn, tenant_id: str) -> None:
    conn.execute("set local role proofbase_runtime")
    conn.execute("select set_config('app.tenant_id', %s, true)", (tenant_id,))
    conn.execute("select set_config('app.user_id', %s, true)", (DEMO_USER,))
    conn.execute("select set_config('app.platform_admin', 'false', true)")


def _fixture(conn) -> None:
    conn.execute(
        "insert into tenants (id, name, slug) values (%s::uuid, 'Other Tenant', 'phase57-other') on conflict (id) do nothing",
        (OTHER_TENANT,),
    )
    conn.execute(
        "insert into demo_users (id, display_name, email, business_role) values (%s::uuid, 'Other User', 'phase57-other@example.invalid', 'Employee')",
        (OTHER_USER,),
    )
    conn.execute(
        "insert into tenant_memberships (tenant_id, user_id, tenant_role) values (%s::uuid, %s::uuid, 'member')",
        (OTHER_TENANT, OTHER_USER),
    )
    conn.execute(
        "insert into external_identities (user_id, issuer, subject) values (%s::uuid, 'https://phase57.invalid', 'other-user')",
        (OTHER_USER,),
    )
    conn.execute(
        "insert into projects (id, tenant_id, name) values (%s::uuid, %s::uuid, 'Other Project')",
        (OTHER_PROJECT, OTHER_TENANT),
    )
    conn.execute(
        "insert into project_departments (id, tenant_id, project_id, name) values (%s::uuid, %s::uuid, %s::uuid, 'Other Department')",
        (OTHER_DEPARTMENT, OTHER_TENANT, OTHER_PROJECT),
    )
    conn.execute(
        "insert into project_memberships (tenant_id, project_id, user_id, membership_level) values (%s::uuid, %s::uuid, %s::uuid, 'owner')",
        (OTHER_TENANT, OTHER_PROJECT, OTHER_USER),
    )
    conn.execute(
        """
        insert into documents (
          id, tenant_id, project_id, department_id, external_document_id, title,
          department, category, source_path, access_roles
        ) values (%s::uuid, %s::uuid, %s::uuid, %s::uuid, 'PHASE57-OTHER', 'Other Document',
                  'Other Department', 'Other', 'tenant/other.md', array['Employee'])
        """,
        (OTHER_DOCUMENT, OTHER_TENANT, OTHER_PROJECT, OTHER_DEPARTMENT),
    )
    conn.execute(
        """
        insert into document_versions (id, tenant_id, document_id, version_label, content_hash, extracted_text)
        values (%s::uuid, %s::uuid, %s::uuid, 'v1', %s, 'other tenant secret')
        """,
        (OTHER_VERSION, OTHER_TENANT, OTHER_DOCUMENT, hashlib.sha256(b"other").hexdigest()),
    )
    conn.execute("update documents set current_version_id = %s::uuid where id = %s::uuid", (OTHER_VERSION, OTHER_DOCUMENT))
    conn.execute(
        """
        insert into ingestion_jobs (
          tenant_id, project_id, department_id, document_id, document_version_id, source_file_name, source_file_type
        ) values (%s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::uuid, 'other.pdf', 'pdf')
        """,
        (OTHER_TENANT, OTHER_PROJECT, OTHER_DEPARTMENT, OTHER_DOCUMENT, OTHER_VERSION),
    )
    conn.execute(
        """
        insert into chunks (id, tenant_id, document_id, document_version_id, chunk_index, section_heading, content, content_hash)
        values (%s::uuid, %s::uuid, %s::uuid, %s::uuid, 0, 'Other', 'other tenant secret', %s)
        """,
        (OTHER_CHUNK, OTHER_TENANT, OTHER_DOCUMENT, OTHER_VERSION, hashlib.sha256(b"chunk").hexdigest()),
    )
    vector = "[" + ",".join("0" for _ in range(1536)) + "]"
    conn.execute(
        "insert into chunk_embeddings (tenant_id, chunk_id, embedding_model, embedding) values (%s::uuid, %s::uuid, 'phase57', %s::vector)",
        (OTHER_TENANT, OTHER_CHUNK, vector),
    )
    conn.execute(
        "insert into chat_sessions (id, tenant_id, user_id, user_role) values (%s::uuid, %s::uuid, %s, 'Employee')",
        (OTHER_SESSION, OTHER_TENANT, OTHER_USER),
    )
    conn.execute(
        "insert into chat_messages (id, tenant_id, session_id, role, content) values (%s::uuid, %s::uuid, %s::uuid, 'user', 'other tenant chat')",
        (OTHER_MESSAGE, OTHER_TENANT, OTHER_SESSION),
    )
    conn.execute(
        "insert into feedback (tenant_id, session_id, message_id, question, answer, user_role, rating) values (%s::uuid, %s::uuid, %s::uuid, 'q', 'a', 'Employee', 'thumbs_up')",
        (OTHER_TENANT, OTHER_SESSION, OTHER_MESSAGE),
    )
    conn.execute(
        "insert into audit_logs (tenant_id, user_role, action, resource_type, outcome) values (%s::uuid, 'Employee', 'phase57_fixture', 'test', 'success')",
        (OTHER_TENANT,),
    )
    conn.execute(
        "insert into evaluation_runs (id, tenant_id, run_name, config_json, retrieval_mode, chunking_strategy, top_k, model) values (%s::uuid, %s::uuid, 'other', '{}'::jsonb, 'vector_only', 'section_based', 5, 'none')",
        (OTHER_RUN, OTHER_TENANT),
    )
    conn.execute(
        """
        insert into evaluation_results (
          tenant_id, evaluation_run_id, question_id, question_type, user_role, expected_behavior
        ) values (%s::uuid, %s::uuid, 'OTHER-1', 'simple_factual', 'Employee', 'answer')
        """,
        (OTHER_TENANT, OTHER_RUN),
    )
    conn.execute(
        """
        insert into evaluation_reviews (
          tenant_id, source_type, source_id, question, answer_correctness, citation_correctness, decision
        ) values (%s::uuid, 'failed_question', 'OTHER-1', 'other?', 0, 0, 'needs_fix')
        """,
        (OTHER_TENANT,),
    )
    conn.execute(
        """
        insert into auth_sessions (
          tenant_id, user_id, csrf_token_hash, auth_time, last_seen_at, idle_expires_at, absolute_expires_at
        ) values (%s::uuid, %s::uuid, 'hash', now(), now(), now() + interval '30 minutes', now() + interval '8 hours')
        """,
        (OTHER_TENANT, OTHER_USER),
    )


def _expect_rls_write_denial(conn) -> None:
    conn.execute("savepoint denied_write")
    try:
        conn.execute(
            "insert into projects (tenant_id, name) values (%s::uuid, 'Forbidden Cross Tenant Write')",
            (OTHER_TENANT,),
        )
    except errors.InsufficientPrivilege:
        conn.execute("rollback to savepoint denied_write")
    else:
        raise AssertionError("RLS permitted a cross-tenant insert")


def _expect_cross_tenant_fk_denial(conn) -> None:
    conn.execute("reset role")
    conn.execute("savepoint denied_fk")
    try:
        conn.execute(
            """
            insert into documents (
              tenant_id, project_id, department_id, external_document_id, title,
              department, category, source_path, access_roles
            ) values (%s::uuid, %s::uuid, %s::uuid, 'PHASE57-BAD-FK', 'Bad', 'Bad', 'Bad', 'bad', array['Employee'])
            """,
            (DEMO_TENANT, OTHER_PROJECT, OTHER_DEPARTMENT),
        )
    except errors.ForeignKeyViolation:
        conn.execute("rollback to savepoint denied_fk")
    else:
        raise AssertionError("Composite tenant foreign keys permitted a cross-tenant relationship")


def test_database_role_and_rls() -> None:
    apply_schema()
    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        _fixture(conn)
        role = conn.execute(
            "select rolsuper, rolbypassrls, rolcreaterole, rolcreatedb from pg_roles where rolname = 'proofbase_runtime'"
        ).fetchone()
        assert role == {"rolsuper": False, "rolbypassrls": False, "rolcreaterole": False, "rolcreatedb": False}

        _set_runtime_context(conn, DEMO_TENANT)
        assert conn.execute("select current_user as name").fetchone()["name"] == "proofbase_runtime"
        protected = {
            "tenants": ("id", OTHER_TENANT),
            "demo_users": ("id", OTHER_USER),
            "external_identities": ("user_id", OTHER_USER),
            "tenant_memberships": ("user_id", OTHER_USER),
            "auth_sessions": ("user_id", OTHER_USER),
            "projects": ("id", OTHER_PROJECT),
            "project_memberships": ("user_id", OTHER_USER),
            "project_departments": ("id", OTHER_DEPARTMENT),
            "documents": ("id", OTHER_DOCUMENT),
            "document_versions": ("id", OTHER_VERSION),
            "ingestion_jobs": ("document_id", OTHER_DOCUMENT),
            "chunks": ("id", OTHER_CHUNK),
            "chunk_embeddings": ("chunk_id", OTHER_CHUNK),
            "chat_sessions": ("id", OTHER_SESSION),
            "chat_messages": ("id", OTHER_MESSAGE),
            "feedback": ("session_id", OTHER_SESSION),
            "audit_logs": ("action", "phase57_fixture"),
            "evaluation_runs": ("id", OTHER_RUN),
            "evaluation_results": ("evaluation_run_id", OTHER_RUN),
            "evaluation_reviews": ("source_id", "OTHER-1"),
        }
        for table, (column, value) in protected.items():
            cast = "" if column in {"action", "source_id"} else "::uuid"
            count = conn.execute(f"select count(*) as n from {table} where {column} = %s{cast}", (value,)).fetchone()["n"]
            assert count == 0, (table, count)
        assert conn.execute("update projects set name = 'leak' where id = %s::uuid", (OTHER_PROJECT,)).rowcount == 0
        assert conn.execute("delete from projects where id = %s::uuid", (OTHER_PROJECT,)).rowcount == 0
        assert conn.execute(
            "select count(*) as n from chunk_embeddings ce join chunks c on c.id = ce.chunk_id join documents d on d.id = c.document_id where d.external_document_id = 'PHASE57-OTHER'"
        ).fetchone()["n"] == 0
        _expect_rls_write_denial(conn)

        conn.execute("select set_config('app.tenant_id', %s, true)", (OTHER_TENANT,))
        assert conn.execute("select count(*) as n from projects where id = %s::uuid", (OTHER_PROJECT,)).fetchone()["n"] == 1
        assert conn.execute("select count(*) as n from chunks where id = %s::uuid", (OTHER_CHUNK,)).fetchone()["n"] == 1
        _expect_cross_tenant_fk_denial(conn)
        conn.rollback()
    finally:
        conn.close()


def test_tenant_scoped_cache_and_storage_contract() -> None:
    class FakeEmbeddings:
        def __init__(self):
            self.calls = 0

        def create(self, **_kwargs):
            self.calls += 1
            return SimpleNamespace(data=[SimpleNamespace(embedding=[float(self.calls)])], usage=None)

    fake = FakeEmbeddings()
    openai_embeddings.clear_embedding_cache()
    with patch.object(openai_embeddings, "_client", return_value=SimpleNamespace(embeddings=fake)), patch.object(
        openai_embeddings, "submit_auxiliary_telemetry", return_value=None
    ):
        set_request_principal(tenant_id=DEMO_TENANT, user_id=DEMO_USER)
        first = openai_embeddings.embed_text("same text")
        assert openai_embeddings.embed_text("same text") == first
        set_request_principal(tenant_id=OTHER_TENANT, user_id=DEMO_USER)
        second = openai_embeddings.embed_text("same text")
    assert fake.calls == 2
    assert first != second
    with tempfile.TemporaryDirectory() as directory:
        storage = LocalQuarantineStorage(Path(directory))
        storage_key = storage.put(DEMO_TENANT, b"tenant scoped")
        assert storage.path_for_parser(DEMO_TENANT, storage_key).read_bytes() == b"tenant scoped"
        try:
            storage.path_for_parser(OTHER_TENANT, storage_key)
        except FilePolicyError as exc:
            assert exc.reason_code == "tenant_storage_scope_mismatch"
        else:
            raise AssertionError("Cross-tenant storage access was not denied")


def test_tenant_scoped_observability() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "requests.jsonl"
        path.write_text(
            "\n".join(
                json.dumps({"tenant_id": tenant, "request_id": tenant, "total_latency_ms": 1})
                for tenant in (DEMO_TENANT, OTHER_TENANT)
            )
            + "\n",
            encoding="utf-8",
        )
        set_request_principal(tenant_id=DEMO_TENANT, user_id=DEMO_USER)
        with patch.object(observability_summary, "get_observability_log_path", return_value=path):
            result = observability_summary.compute_live_summary()
    assert result["total_requests"] == 1
    assert result["recent_requests"][0]["tenant_id"] == DEMO_TENANT


def test_production_database_guards() -> None:
    for values, expected in (
        (
            {"database_url": "postgresql://postgres:secret@db/proofbase", "database_enforce_rls": True},
            "superuser",
        ),
        (
            {"database_url": "postgresql://postgres@db/proofbase", "database_enforce_rls": True},
            "superuser",
        ),
        (
            {"database_url": "postgresql://proofbase_runtime:secret@db/proofbase", "database_enforce_rls": False},
            "DATABASE_ENFORCE_RLS",
        ),
    ):
        try:
            Settings(_env_file=None, app_environment="production", auth_mode="oidc", **values)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"Expected production database guard: {expected}")


def test_malformed_identity_headers_fail_before_database_context() -> None:
    client = TestClient(app)
    response = client.get("/auth/me", headers={"X-Tenant-Id": "not-a-uuid"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Identity selections must be valid UUIDs."


def main() -> None:
    test_database_role_and_rls()
    test_tenant_scoped_cache_and_storage_contract()
    test_tenant_scoped_observability()
    test_production_database_guards()
    test_malformed_identity_headers_fail_before_database_context()
    print("Phase 57 tenant isolation tests passed.")


if __name__ == "__main__":
    main()
