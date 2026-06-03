from dataclasses import dataclass

from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection
from apps.api.app.embeddings.openai_embeddings import embed_text, to_vector_literal


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    section_heading: str
    content: str
    rank: int
    score: float


def role_variants(user_role: str) -> list[str]:
    aliases = {
        "IT Admin": ["IT Admin", "IT/Admin"],
        "IT/Admin": ["IT/Admin", "IT Admin"],
    }
    return aliases.get(user_role, [user_role])


def retrieve_chunks(question: str, user_role: str, top_k: int | None = None) -> list[RetrievedChunk]:
    settings = get_settings()
    limit = top_k or settings.default_top_k
    query_embedding = to_vector_literal(embed_text(question))
    roles = role_variants(user_role)

    sql = """
        select
          c.id::text as chunk_id,
          d.external_document_id as document_id,
          d.title as document_title,
          c.section_heading,
          c.content,
          1 - (ce.embedding <=> %s::vector) as score
        from chunk_embeddings ce
        join chunks c on c.id = ce.chunk_id
        join documents d on d.id = c.document_id
        join document_versions dv on dv.id = c.document_version_id
        where d.access_roles && %s
          and d.status = 'active'
          and dv.ingestion_status = 'indexed'
        order by ce.embedding <=> %s::vector
        limit %s
    """

    with get_connection() as conn:
        rows = conn.execute(sql, (query_embedding, roles, query_embedding, limit)).fetchall()

    return [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            document_title=row["document_title"],
            section_heading=row["section_heading"],
            content=row["content"],
            rank=index + 1,
            score=float(row["score"]),
        )
        for index, row in enumerate(rows)
    ]
