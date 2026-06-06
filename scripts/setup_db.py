from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.db.session import apply_schema, get_connection


REQUIRED_TABLES = [
    "documents",
    "document_versions",
    "chunks",
    "chunk_embeddings",
    "prompts",
    "prompt_versions",
    "evaluation_questions",
    "evaluation_runs",
    "evaluation_results",
    "audit_logs",
    "chat_sessions",
    "chat_messages",
    "feedback",
]


def verify_database() -> dict:
    with get_connection() as conn:
        vector_enabled = conn.execute(
            "select exists(select 1 from pg_extension where extname = 'vector') as enabled"
        ).fetchone()["enabled"]
        table_rows = conn.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'public'
              and table_name = any(%s)
            """,
            (REQUIRED_TABLES,),
        ).fetchall()
        existing_tables = {row["table_name"] for row in table_rows}
        missing_tables = sorted(set(REQUIRED_TABLES) - existing_tables)
        document_count = conn.execute("select count(*) as count from documents").fetchone()["count"]
        chunk_count = conn.execute("select count(*) as count from chunks").fetchone()["count"]

    return {
        "pgvector_enabled": bool(vector_enabled),
        "required_table_count": len(REQUIRED_TABLES),
        "missing_tables": missing_tables,
        "document_count": document_count,
        "chunk_count": chunk_count,
    }


def main() -> None:
    apply_schema()
    result = verify_database()
    print(json.dumps(result, indent=2))
    if not result["pgvector_enabled"] or result["missing_tables"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
