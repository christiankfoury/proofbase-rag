from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.embeddings.openai_embeddings import embed_text, to_vector_literal
from apps.api.app.permissions.permission_filter import build_permission_trace, log_permission_trace
from apps.api.app.permissions.roles import role_variants
from apps.api.app.retrieval.reranker import rerank_chunks
from apps.api.app.retrieval.types import RetrievedChunk


def retrieve_chunks(
    question: str,
    user_role: str,
    top_k: int | None = None,
    chunking_strategy: str = "section_based",
    project_id: str | None = None,
    department_id: str | None = None,
    reranker: str | None = None,
    rerank_candidate_limit: int | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.default_top_k
    candidate_limit = max(limit * 4, 20)
    allowed_limit = rerank_candidate_limit or (candidate_limit if reranker else limit)
    query_embedding = to_vector_literal(embed_text(question))
    roles = role_variants(user_role)
    scope_sql, scope_params = _scope_filter(project_id=project_id, department_id=department_id)

    candidate_sql = f"""
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.project_id::text as project_id,
          d.department_id::text as department_id,
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
          and c.document_version_id = d.current_version_id
          and dv.ingestion_status = 'indexed'
          {scope_sql}
        order by ce.embedding <=> %s::vector
        limit %s
    """

    allowed_sql = f"""
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.title as document_title,
          d.project_id::text as project_id,
          d.department_id::text as department_id,
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
          and c.document_version_id = d.current_version_id
          and dv.ingestion_status = 'indexed'
          {scope_sql}
        order by ce.embedding <=> %s::vector
        limit %s
    """

    with get_connection() as conn:
        candidate_rows = conn.execute(
            candidate_sql,
            (settings.openai_embedding_model, chunking_strategy, *scope_params, query_embedding, candidate_limit),
        ).fetchall()
        rows = conn.execute(
            allowed_sql,
            (query_embedding, roles, settings.openai_embedding_model, chunking_strategy, *scope_params, query_embedding, allowed_limit),
        ).fetchall()

    chunks = [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            document_title=row["document_title"],
            project_id=row["project_id"],
            department_id=row["department_id"],
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
    if reranker == "lexical":
        chunks = rerank_chunks(question, chunks)[:limit]
    elif reranker:
        raise ValueError(f"Unsupported reranker: {reranker}")

    trace = build_permission_trace(
        user_role=user_role,
        retrieval_mode="vector_lexical_rerank" if reranker == "lexical" else "vector_only",
        candidate_rows=candidate_rows,
        allowed_chunks=chunks,
    )
    log_permission_trace(trace, chunking_strategy=chunking_strategy, top_k=limit)
    return chunks


def _scope_filter(*, project_id: str | None = None, department_id: str | None = None) -> tuple[str, list[str]]:
    clauses: list[str] = []
    params: list[str] = []
    if project_id:
        clauses.append("and d.project_id = %s::uuid")
        params.append(project_id)
    if department_id:
        clauses.append("and d.department_id = %s::uuid")
        params.append(department_id)
    return "\n          ".join(clauses), params
