from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    section_heading: str
    content: str
    rank: int
    score: float
    vector_score: float | None = None
    keyword_score: float | None = None
    hybrid_score: float | None = None
    retrieval_source: str = "vector"


def role_variants(user_role: str) -> list[str]:
    aliases = {
        "IT Admin": ["IT Admin", "IT/Admin"],
        "IT/Admin": ["IT/Admin", "IT Admin"],
    }
    return aliases.get(user_role, [user_role])
