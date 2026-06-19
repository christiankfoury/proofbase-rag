from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    section_heading: str
    content: str
    access_roles: list[str]
    restricted: bool
    sensitivity: str
    rank: int
    score: float
    project_id: str | None = None
    department_id: str | None = None
    vector_score: float | None = None
    keyword_score: float | None = None
    hybrid_score: float | None = None
    retrieval_source: str = "vector"
