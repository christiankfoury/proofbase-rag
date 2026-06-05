# Phase 8 Permissions Implementation

## Summary

Phase 8 hardens the enterprise access-control behavior of the RAG system.

The system now keeps permission metadata on documents and retrieved chunks, applies role filters before retrieval results are passed to generation, records permission-filter audit events, and provides a dedicated permission evaluation script.

## Implemented Behavior

- Documents store `access_roles`, `restricted`, and `sensitivity`.
- Chunks inherit document permission metadata through retrieval results.
- `vector_only`, `keyword_only`, and `hybrid` retrieval apply role filters before returning chunks.
- Generation includes a safety check that refuses if unauthorized chunks ever reach the answer generator.
- Restricted-topic refusals are audited.
- Permission-sensitive retrieval events are written to `audit_logs`.
- Permission evaluation measures leakage and blocked-answer behavior on restricted benchmark cases.

## Runtime Guarantee

Unauthorized chunks must not be passed to the LLM context.

The primary enforcement happens in SQL retrieval filters. The secondary enforcement happens in `generate_answer`, which refuses and logs an audit event if an unauthorized chunk is detected.

## Current Scope

Phase 8 does not add production authentication or Clerk/Auth.js integration. The API still accepts `user_role` directly for portfolio/demo evaluation.

