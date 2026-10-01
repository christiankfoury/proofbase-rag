"""Isolated local database and reproducible, non-secret runtime fingerprint."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
from importlib.metadata import distributions
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DBNAME = "proofbase_eval_phase73"


def configure():
    from apps.api.app.core.config import get_settings
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    original = get_settings()
    parts = conninfo_to_dict(original.database_url)
    if parts.get("host") not in {"localhost", "127.0.0.1"}:
        raise ValueError("Only local evaluation databases are permitted")
    parts["dbname"] = DBNAME
    isolated = make_conninfo(**parts)
    os.environ["DATABASE_URL"] = isolated
    os.environ["PROOFBASE_TELEMETRY_ENABLED"] = "false"
    os.environ["EXTERNAL_AI_MAX_RETRIES"] = "0"
    # Test-process admission capacity for 60 queries plus upload indexing.
    # Application defaults stay unchanged; the evaluation ledger enforces declared call/token bounds.
    os.environ["TENANT_DAILY_AI_BUDGET_USD"] = "10"
    for key, filename in {"OBSERVABILITY_LOG_PATH": "requests.jsonl", "AUDIT_LOG_PATH": "audit.jsonl",
                          "SECURITY_EVENT_LOG_PATH": "security.jsonl", "SECURITY_NOTIFICATION_LOG_PATH": "notifications.jsonl",
                          "UPLOAD_STORAGE_DIR": "uploads", "FILE_QUARANTINE_DIR": "quarantine"}.items():
        os.environ[key] = str(ROOT / "data/evaluation/local-runs/current-phase73-v6" / filename)
    # Dedicated Redis namespace prevents evaluation admission from consuming demo quotas.
    if original.rate_limit_backend == "redis":
        from urllib.parse import urlsplit, urlunsplit
        redis = urlsplit(original.redis_url)
        os.environ["REDIS_URL"] = urlunsplit(redis._replace(path="/15"))
    get_settings.cache_clear()
    return get_settings()


def fingerprint(settings):
    import psycopg
    safe = {k: v for k, v in settings.model_dump(mode="json").items()
            if k.startswith(("retrieval_", "request_assessment_", "evidence_assessment_", "post_generation_"))
            or isinstance(v, (bool, int, float))
            or k in {"default_demo_tenant_id", "default_demo_user_id", "database_runtime_role", "openai_chat_model", "openai_embedding_model", "auth_mode", "app_environment", "rate_limit_backend",
                     "file_parser_mode", "file_scanner_mode"}}
    tables = {}
    security = {}
    runtime = {"python_version": platform.python_version(),
               "packages": dict(sorted((d.metadata["Name"].lower().replace("_", "-"), d.version)
                                       for d in distributions() if d.metadata.get("Name")))}
    with psycopg.connect(settings.database_url) as conn:
        scope = [{'source_path': row[0].replace('\\', '/'), 'tenant_id': row[1],
                  'project_id': row[2], 'department_id': row[3], 'access_roles': row[4]}
                 for row in conn.execute("select source_path,tenant_id::text,project_id::text,department_id::text,access_roles from documents where archived_at is null and source_type='markdown' order by source_path,id").fetchall()]
        runtime["postgres_version"] = conn.info.server_version
        runtime["postgres_extensions"] = dict(conn.execute("select extname, extversion from pg_extension order by extname").fetchall())
        for table in ("documents", "document_versions", "chunks", "chunk_embeddings", "demo_users", "tenants", "tenant_memberships", "projects", "project_departments", "project_memberships", "prompt_versions"):
            # Preserve row content, including embeddings/ACLs, without publishing credentials or user data.
            rows = conn.execute(f"select row_to_json(t)::text from {table} t order by row_to_json(t)::text").fetchall()
            tables[table] = {"count": len(rows), "sha256": hashlib.sha256("\n".join(r[0] for r in rows).encode()).hexdigest()}
        # Bind mutable database authorization metadata without publishing identities or secrets.
        checks = [
            ("policies", "select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where schemaname='public' order by tablename,policyname", ()),
            ("rls_tables", "select c.relname,c.relrowsecurity,c.relforcerowsecurity,pg_get_userbyid(c.relowner) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind in ('r','p') order by c.relname", ()),
            ("runtime_role", "select rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,rolreplication,rolbypassrls from pg_roles where rolname=%s", (settings.database_runtime_role,)),
            ("table_grants", "select grantee,table_name,privilege_type,is_grantable from information_schema.role_table_grants where table_schema='public' order by grantee,table_name,privilege_type,is_grantable", ()),
            ("functions", "select p.proname,pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.prokind='f' order by p.proname,pg_get_functiondef(p.oid)", ()),
        ]
        for name, query, parameters in checks:
            rows = conn.execute(query, parameters).fetchall()
            security[name] = {"count": len(rows), "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()}
    return {"settings": safe, "tables": tables, "database": DBNAME, "runtime": runtime,
            "gold_source_scope": scope,
            "database_security": security,
            "call_output_cap": 2048, "sdk_retries": 0, "temperature_note": "runtime configuration; grader GPT-5.4 medium reasoning; provider output is not deterministic"}


def prepare():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    from apps.api.app.core.config import get_settings
    parts = conninfo_to_dict(get_settings().database_url)
    if parts.get("host") not in {"localhost", "127.0.0.1"} or parts.get("dbname") == DBNAME:
        raise ValueError("Expected original local database, not evaluation target")
    source = parts["dbname"]
    parts["dbname"] = "postgres"
    with psycopg.connect(make_conninfo(**parts), autocommit=True) as conn:
        if conn.execute("select 1 from pg_database where datname=%s", (DBNAME,)).fetchone():
            raise ValueError("Isolated database already exists; refuse replacement")
        conn.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(DBNAME), sql.Identifier(source)))
    print("Created isolated local evaluation database; original retained")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        print(json.dumps(fingerprint(configure()), indent=2))
