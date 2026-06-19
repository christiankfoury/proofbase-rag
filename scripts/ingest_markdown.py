import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import apply_schema, get_connection
from apps.api.app.embeddings.openai_embeddings import embed_texts, to_vector_literal
from apps.api.app.ingestion.chunker import chunk_markdown_document
from apps.api.app.ingestion.markdown_loader import load_markdown_documents
from apps.api.app.permissions.access_control import sensitivity_from_restricted


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _upsert_document(conn, document):
    metadata = document.metadata
    restricted = bool(metadata["restricted"])
    sensitivity = sensitivity_from_restricted(restricted)
    row = conn.execute(
        """
        insert into documents (
          project_id, department_id, external_document_id, title, department, category, source_type,
          source_path, access_roles, sensitivity, restricted, status, updated_at
        )
        values (
          '00000000-0000-0000-0000-000000000019',
          (
            select id from project_departments
            where project_id = '00000000-0000-0000-0000-000000000019'
              and seeded_data_key = %s
          ),
          %s, %s, %s, %s, 'markdown', %s, %s, %s, %s, 'active', now()
        )
        on conflict (external_document_id) do update set
          project_id = excluded.project_id,
          department_id = excluded.department_id,
          title = excluded.title,
          department = excluded.department,
          category = excluded.category,
          source_path = excluded.source_path,
          access_roles = excluded.access_roles,
          sensitivity = excluded.sensitivity,
          restricted = excluded.restricted,
          updated_at = now()
        returning id::text
        """,
        (
            metadata["category"],
            metadata["document_id"],
            metadata["title"],
            metadata["department"],
            metadata["category"],
            document.source_path,
            document.access_roles,
            sensitivity,
            restricted,
        ),
    ).fetchone()
    return row["id"]


def _upsert_version(conn, document_id: str, document):
    metadata = document.metadata
    version_label = str(metadata["version"])
    content_hash = _hash_text(document.body)
    row = conn.execute(
        """
        insert into document_versions (
          document_id, version_label, effective_date, owner, review_cycle,
          content_hash, extracted_text, metadata_json, ingestion_status, indexed_at
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, 'indexed', now())
        on conflict (document_id, version_label) do update set
          effective_date = excluded.effective_date,
          owner = excluded.owner,
          review_cycle = excluded.review_cycle,
          content_hash = excluded.content_hash,
          extracted_text = excluded.extracted_text,
          metadata_json = excluded.metadata_json,
          ingestion_status = 'indexed',
          indexed_at = now(),
          failed_at = null,
          failure_reason = null
        returning id::text
        """,
        (
            document_id,
            version_label,
            metadata["effective_date"],
            metadata["owner"],
            metadata["review_cycle"],
            content_hash,
            document.body,
            json.dumps(metadata, default=str),
        ),
    ).fetchone()
    conn.execute(
        "update documents set current_version_id = %s where id = %s",
        (row["id"], document_id),
    )
    return row["id"]


def ingest_documents(
    source_dir: str = "data/synthetic-documents",
    chunking_strategy: str = "section_based",
    chunk_size: int = 180,
    chunk_overlap: int = 40,
) -> dict:
    settings = get_settings()
    documents = load_markdown_documents(source_dir)
    counts = {"documents": 0, "chunks": 0, "embeddings": 0, "failures": 0}

    for document in documents:
        try:
            chunks = chunk_markdown_document(
                document,
                chunking_strategy=chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            embeddings = embed_texts([chunk.content for chunk in chunks])

            with get_connection() as conn:
                document_uuid = _upsert_document(conn, document)
                version_uuid = _upsert_version(conn, document_uuid, document)
                conn.execute(
                    "delete from chunks where document_version_id = %s and chunking_strategy = %s",
                    (version_uuid, chunking_strategy),
                )

                for chunk, embedding in zip(chunks, embeddings, strict=True):
                    chunk_row = conn.execute(
                        """
                        insert into chunks (
                          document_id, document_version_id, chunk_index, section_heading,
                          content, content_hash, token_count, chunking_strategy, metadata_json
                        )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        returning id::text
                        """,
                        (
                            document_uuid,
                            version_uuid,
                            chunk.chunk_index,
                            chunk.section_heading,
                            chunk.content,
                            _hash_text(chunk.content),
                            chunk.token_count,
                            chunk.chunking_strategy,
                            json.dumps(
                                {
                                    "source_path": chunk.source_path,
                                    "document_id": chunk.document_id,
                                    "document_title": chunk.document_title,
                                    "access_roles": chunk.access_roles,
                                    "sensitivity": sensitivity_from_restricted(bool(document.metadata["restricted"])),
                                }
                            ),
                        ),
                    ).fetchone()
                    conn.execute(
                        """
                        insert into chunk_embeddings (chunk_id, embedding_model, embedding)
                        values (%s, %s, %s::vector)
                        """,
                        (chunk_row["id"], settings.openai_embedding_model, to_vector_literal(embedding)),
                    )

            counts["documents"] += 1
            counts["chunks"] += len(chunks)
            counts["embeddings"] += len(embeddings)
        except Exception as exc:
            counts["failures"] += 1
            print(f"Failed to ingest {document.source_path}: {exc}")

    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-schema", action="store_true", help="Apply apps/api/app/db/schema.sql before ingestion")
    parser.add_argument("--source-dir", default="data/synthetic-documents")
    parser.add_argument("--chunking-strategy", choices=["section_based", "fixed_size"], default="section_based")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=40)
    args = parser.parse_args()

    if args.apply_schema:
        apply_schema()

    counts = ingest_documents(
        args.source_dir,
        chunking_strategy=args.chunking_strategy,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(json.dumps(counts, indent=2))
    if counts["failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
