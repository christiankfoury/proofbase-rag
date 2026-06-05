# Audit Logging

## Purpose

Phase 8 adds simple audit logging for permission-sensitive events. The goal is to make access-control behavior inspectable without introducing production auth or a full admin dashboard.

## Audit Table

Audit events are stored in `audit_logs`.

Fields:

- `id`
- `created_at`
- `user_id`
- `user_role`
- `action`
- `document_id`
- `resource_type`
- `outcome`
- `reason`
- `metadata_json`

## Events Logged

- `permission_filtered_retrieval`
- `unauthorized_candidate_blocked`
- `restricted_query_refused`
- `unauthorized_chunks_reached_generation`

## Safe Logging Rules

- Do not log chunk content.
- Do not log full prompts.
- Blocked documents are logged by document ID only.
- Audit logging failures do not break the user-facing query path.

## Example Metadata

```json
{
  "retrieval_mode": "vector_only",
  "chunking_strategy": "section_based",
  "top_k": 5,
  "candidate_chunks_before_filtering": 20,
  "allowed_chunks_after_filtering": 5,
  "blocked_chunks_count": 3,
  "blocked_document_ids": ["MGR-002"],
  "unauthorized_chunks_reached_generation": false
}
```

