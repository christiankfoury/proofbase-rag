from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.permissions.permission_filter import build_permission_trace, log_permission_trace
from apps.api.app.permissions.roles import role_variants
from apps.api.app.retrieval.types import RetrievedChunk


STOP_WORDS = {
    "about",
    "can",
    "does",
    "for",
    "from",
    "how",
    "many",
    "the",
    "what",
    "when",
    "where",
    "which",
    "who",
}


def _keyword_query(question: str) -> str:
    normalized = "".join(character if character.isalnum() else " " for character in question.lower())
    terms = [
        term
        for term in normalized.split()
        if len(term) >= 3 and term not in STOP_WORDS
    ]
    if not terms:
        return question
    return " OR ".join(dict.fromkeys(terms))


def retrieve_chunks(
    question: str,
    user_role: str,
    top_k: int | None = None,
    chunking_strategy: str = "section_based",
    project_id: str | None = None,
    department_id: str | None = None,
    excluded_document_prefixes: list[str] | tuple[str, ...] | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.default_top_k
    candidate_limit = max(limit * 4, 20)
    roles = role_variants(user_role)
    keyword_query = _keyword_query(question)
    scope_sql, scope_params = _document_filter(
        project_id=project_id,
        department_id=department_id,
        excluded_document_prefixes=excluded_document_prefixes,
    )

    candidate_sql = f"""
        with query as (
          select websearch_to_tsquery('english', %s) as tsquery
        )
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.project_id::text as project_id,
          d.department_id::text as department_id,
          d.access_roles,
          d.restricted,
          d.sensitivity
        from query
        join chunks c on c.tsv @@ query.tsquery
        join documents d on d.id = c.document_id
        join document_versions dv on dv.id = c.document_version_id
        where c.chunking_strategy = %s
          and d.status = 'active'
          and c.document_version_id = d.current_version_id
          and dv.ingestion_status = 'indexed'
          {scope_sql}
        order by ts_rank_cd(c.tsv, query.tsquery) desc, c.chunk_index asc
        limit %s
    """

    allowed_sql = f"""
        with query as (
          select websearch_to_tsquery('english', %s) as tsquery
        )
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
          ts_rank_cd(c.tsv, query.tsquery) as score
        from query
        join chunks c on c.tsv @@ query.tsquery
        join documents d on d.id = c.document_id
        join document_versions dv on dv.id = c.document_version_id
        where d.access_roles && %s
          and c.chunking_strategy = %s
          and d.status = 'active'
          and c.document_version_id = d.current_version_id
          and dv.ingestion_status = 'indexed'
          {scope_sql}
        order by score desc, c.chunk_index asc
        limit %s
    """

    with get_connection() as conn:
        candidate_rows = conn.execute(
            candidate_sql,
            (keyword_query, chunking_strategy, *scope_params, candidate_limit),
        ).fetchall()
        rows = conn.execute(allowed_sql, (keyword_query, roles, chunking_strategy, *scope_params, limit)).fetchall()

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
            keyword_score=float(row["score"]),
            retrieval_source="keyword",
        )
        for index, row in enumerate(rows)
    ]
    trace = build_permission_trace(
        user_role=user_role,
        retrieval_mode="keyword_only",
        candidate_rows=candidate_rows,
        allowed_chunks=chunks,
    )
    log_permission_trace(trace, chunking_strategy=chunking_strategy, top_k=limit)
    return chunks


def _document_filter(
    *,
    project_id: str | None = None,
    department_id: str | None = None,
    excluded_document_prefixes: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, list[str]]:
    clauses: list[str] = []
    params: list[str] = []
    if project_id:
        clauses.append("and d.project_id = %s::uuid")
        params.append(project_id)
    if department_id:
        clauses.append("and d.department_id = %s::uuid")
        params.append(department_id)
    for prefix in excluded_document_prefixes or ():
        normalized = prefix.strip()
        if not normalized:
            continue
        clauses.append("and d.external_document_id not like %s")
        params.append(f"{normalized}%")
    return "\n          ".join(clauses), params
