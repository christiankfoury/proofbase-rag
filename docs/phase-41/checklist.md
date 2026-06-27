# Phase 41 Checklist

## Goal

Make the recruiter-facing project workspace first screen feel like a real App-side product home for the seeded `Northstar Analytics` workspace.

## Completed In This Slice

- [x] Added a project-home action area with direct scoped assistant, department browsing, and document review entry points.
- [x] Added a short one-minute demo path on the first screen.
- [x] Added suggested question chips that preserve project scope and, when available, department scope.
- [x] Updated `/chat` to accept a `question=` URL parameter so project-home chips prefill the scoped ask.
- [x] Added department shortcut actions for opening a workspace or asking with a department filter.
- [x] Added representative project documents with ingestion status, role visibility, source type, chunk count, and department links.
- [x] Added upload and indexing summary counts for indexed, pending-review, failed, and uploaded documents.
- [x] Improved project API unavailable messaging for the project home.
- [x] Kept retrieval behavior, prompts, benchmark expectations, permissions, and Dev/Admin pages unchanged.

## Notes

- The new project-home counts use the existing project document API and current document version status.
- Suggested questions are demo entry points only; they do not assert new benchmark quality or change answer behavior.
- Department-scoped links continue to rely on the existing strict department filter before role filtering.
- No new quality metric was added. The quality panel still renders the existing project quality summary without turning global benchmark results into project-specific claims.
