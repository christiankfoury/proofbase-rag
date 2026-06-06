# Phase 12: Audit Log Design

## Existing Audit Events (Phases 8-11)

| Action | Where logged |
|--------|-------------|
| restricted_query_refused | answer_generator.py policy check |
| unauthorized_chunks_reached_generation | answer_generator.py permission check |
| permission_filtered_retrieval | vector_retriever.py |
| unauthorized_candidate_blocked | vector_retriever.py |

## New Audit Events (Phase 12)

| Action | Where logged | Outcome |
|--------|-------------|---------|
| feedback_submitted | main.py POST /feedback | success |
| evaluation_run_started | run_benchmark.py _create_run() | started |
| evaluation_run_completed | run_benchmark.py run_benchmark() | completed |
| prompt_version_changed | main.py POST /query | success |

### prompt_version_changed

Logged when `request.prompt_version` is set and is not the default `"v1"`. Metadata includes `{"prompt_version": "<version>"}`.

## New Read Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | /audit/events | Recent events (filters: action, outcome, limit=20) |
| GET | /audit/summary | Count of events grouped by action |

## Fail-Silent Requirement

All audit logging (reads and writes) must never raise exceptions that reach the user-facing path. `log_audit_event()` wraps the DB write in a bare `except Exception: return`. The new `list_audit_events()` and `audit_summary()` return empty fallback values on failure.

## What Is NOT Logged

- Full retrieved chunk text
- Full restricted document content
- API keys or credentials
- Personally identifiable information beyond user_role
