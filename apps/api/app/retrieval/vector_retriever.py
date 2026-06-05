from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.embeddings.openai_embeddings import embed_text, to_vector_literal
from apps.api.app.permissions.permission_filter import build_permission_trace, log_permission_trace
from apps.api.app.permissions.roles import role_variants
from apps.api.app.retrieval.types import RetrievedChunk


def retrieve_chunks(
    question: str,
    user_role: str,
    top_k: int | None = None,
    chunking_strategy: str = "section_based",
) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.default_top_k
    candidate_limit = max(limit * 4, 20)
    query_embedding = to_vector_literal(embed_text(question))
    roles = role_variants(user_role)

    candidate_sql = """
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.access_roles,
          d.restricted,
          d.sensitivity
        from chunk_embeddings ce
        join chunks c on c.id = ce.chunk_id
        join documents d on d.id = c.document_id
        join document_versions dv on dv.id = c.document_version_id
        where ce.embedding_model = %s
          and c.chunking_strategy = %s
          and d.status = 'active'
          and dv.ingestion_status = 'indexed'
        order by ce.embedding <=> %s::vector
        limit %s
    """

    allowed_sql = """
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.title as document_title,
          c.section_heading,
          c.content,
          d.access_roles,
          d.restricted,
          d.sensitivity,
          1 - (ce.embedding <=> %s::vector) as score
        from chunk_embeddings ce
        join chunks c on c.id = ce.chunk_id
        join documents d on d.id = c.document_id
        join document_versions dv on dv.id = c.document_version_id
        where d.access_roles && %s
          and ce.embedding_model = %s
          and c.chunking_strategy = %s
          and d.status = 'active'
          and dv.ingestion_status = 'indexed'
        order by ce.embedding <=> %s::vector
        limit %s
    """

    with get_connection() as conn:
        candidate_rows = conn.execute(
            candidate_sql,
            (settings.openai_embedding_model, chunking_strategy, query_embedding, candidate_limit),
        ).fetchall()
        rows = conn.execute(
            allowed_sql,
            (query_embedding, roles, settings.openai_embedding_model, chunking_strategy, query_embedding, limit),
        ).fetchall()

    chunks = [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            document_title=row["document_title"],
            section_heading=row["section_heading"],
            content=row["content"],
            access_roles=list(row["access_roles"]),
            restricted=bool(row["restricted"]),
            sensitivity=row["sensitivity"],
            rank=index + 1,
            score=float(row["score"]),
            vector_score=float(row["score"]),
            retrieval_source="vector",
        )
        for index, row in enumerate(rows)
    ]
    trace = build_permission_trace(
        user_role=user_role,
        retrieval_mode="vector_only",
        candidate_rows=candidate_rows,
        allowed_chunks=chunks,
    )
    log_permission_trace(trace, chunking_strategy=chunking_strategy, top_k=limit)
    return chunks
