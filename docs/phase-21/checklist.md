# Phase 21 Checklist

## App Surface

- [x] Add a department document library on the department detail page.
- [x] Show indexed seeded corpus documents linked to each department.
- [x] Display document ingestion status, active version label, owner, review cycle, effective date, content hash, source path, sensitivity, access roles, and chunk count.
- [x] Add an extracted Markdown preview for current indexed versions.
- [x] Add an upload entry point that is visibly disabled until real extraction starts in Phase 22.
- [x] Keep App copy honest that new upload parsing and project/department-scoped retrieval are not implemented yet.

## Backend And Data Model

- [x] Add an `ingestion_jobs` table for durable upload/extraction/indexing status tracking.
- [x] Add read-only project and department document library endpoints.
- [x] Add a document library read model that joins documents, active versions, chunk counts, and latest ingestion job metadata.
- [x] Extend seeded Markdown ingestion to upsert indexed ingestion job records for current versions.
- [x] Keep retrieval behavior unchanged.

## Verification

- [x] Run targeted Python compile checks.
- [x] Run API import smoke check.
- [x] Run web production build with `NEXT_DIST_DIR=.next-codex-build`.
- [x] Run `docker compose config`.
- [ ] Run live document library API checks against Postgres after applying the new schema and re-running ingestion.

## Remaining Work

- Real PDF/DOCX upload, extraction, Markdown normalization, and review are deferred to Phase 22.
- Project- and department-scoped retrieval is deferred to Phase 23.
- Existing databases need schema application before `/ready` includes `ingestion_jobs`.
