from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.audit.audit_logger import log_audit_event
from apps.api.app.permissions.access_control import role_can_access
from apps.api.app.retrieval.types import RetrievedChunk


@dataclass(frozen=True)
class PermissionTrace:
    user_role: str
    retrieval_mode: str
    candidate_chunks_before_filtering: int
    allowed_chunks_after_filtering: int
    blocked_chunks_count: int
    blocked_document_ids: list[str]
    unauthorized_chunks_reached_generation: bool = False
    metadata: dict | None = None


def build_permission_trace(
    *,
    user_role: str,
    retrieval_mode: str,
    candidate_rows: list[dict],
    allowed_chunks: list[RetrievedChunk],
    metadata: dict | None = None,
) -> PermissionTrace:
    blocked_document_ids = []
    blocked_chunks_count = 0
    for row in candidate_rows:
        access_roles = list(row.get("access_roles") or [])
        if not role_can_access(access_roles, user_role):
            blocked_chunks_count += 1
            document_id = str(row.get("document_id") or "")
            if document_id and document_id not in blocked_document_ids:
                blocked_document_ids.append(document_id)

    return PermissionTrace(
        user_role=user_role,
        retrieval_mode=retrieval_mode,
        candidate_chunks_before_filtering=len(candidate_rows),
        allowed_chunks_after_filtering=len(allowed_chunks),
        blocked_chunks_count=blocked_chunks_count,
        blocked_document_ids=blocked_document_ids,
        metadata=metadata or {},
    )


def log_permission_trace(trace: PermissionTrace, *, chunking_strategy: str, top_k: int) -> None:
    outcome = "blocked_candidates" if trace.blocked_chunks_count else "allowed_only"
    log_audit_event(
        action="permission_filtered_retrieval",
        user_role=trace.user_role,
        resource_type="retrieval",
        outcome=outcome,
        reason="query_time_role_filter",
        metadata={
            "retrieval_mode": trace.retrieval_mode,
            "chunking_strategy": chunking_strategy,
            "top_k": top_k,
            "candidate_chunks_before_filtering": trace.candidate_chunks_before_filtering,
            "allowed_chunks_after_filtering": trace.allowed_chunks_after_filtering,
            "blocked_chunks_count": trace.blocked_chunks_count,
            "blocked_document_ids": trace.blocked_document_ids,
            "unauthorized_chunks_reached_generation": trace.unauthorized_chunks_reached_generation,
            **(trace.metadata or {}),
        },
    )

    for document_id in trace.blocked_document_ids:
        log_audit_event(
            action="unauthorized_candidate_blocked",
            user_role=trace.user_role,
            resource_type="document",
            document_id=document_id,
            outcome="blocked",
            reason="role_not_in_document_access_roles",
            metadata={"retrieval_mode": trace.retrieval_mode, **(trace.metadata or {})},
        )
