from __future__ import annotations

from apps.api.app.retrieval.types import RetrievedChunk


def group_chunks_by_document(chunks: list[RetrievedChunk]) -> list[dict]:
    """Group retrieved chunks by document, ordered by the best rank within each group."""
    groups: dict[str, dict] = {}
    for chunk in chunks:
        if chunk.document_id not in groups:
            groups[chunk.document_id] = {
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "chunks": [],
                "_min_rank": chunk.rank,
            }
        groups[chunk.document_id]["chunks"].append(chunk)
        groups[chunk.document_id]["_min_rank"] = min(
            groups[chunk.document_id]["_min_rank"], chunk.rank
        )

    sorted_groups = sorted(groups.values(), key=lambda g: g["_min_rank"])
    return [
        {
            "document_id": g["document_id"],
            "document_title": g["document_title"],
            "chunks": sorted(g["chunks"], key=lambda c: c.rank),
        }
        for g in sorted_groups
    ]
