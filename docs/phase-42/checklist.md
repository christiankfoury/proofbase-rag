# Phase 42 Checklist

## Goal

Make the short demo path obvious: project -> department -> upload/review -> ask -> inspect proof.

## Completed In This Slice

- [x] Added `/demo` as a guided route for the five-minute App walkthrough.
- [x] Added Guided Demo navigation and breadcrumbs.
- [x] Linked the App Home to the guided route.
- [x] Updated stale App Home copy so upload approval/indexing is shown as implemented and AI Markdown cleanup remains future work.
- [x] Added a visible `Why this answer?` action on chat answers.
- [x] Added an App-side answer proof summary covering citations, retrieved snippets, permission scope, confidence interpretation, and Dev/Admin proof links.
- [x] Added uploaded-document status timeline UI for upload, extraction, review, indexing, and failure state.
- [x] Fixed uploaded-document detection to use actual `UPLOAD-*` IDs and `data/uploads/` paths instead of a nonexistent `source_type=upload`.
- [x] Kept retrieval, prompts, generation, permission checks, indexing behavior, benchmark expectations, and metric artifacts unchanged.

## Notes

- The guided route is navigation and explanation only; it does not create fake activity or change demo data.
- The answer proof panel links to Dev/Admin evidence but does not reword benchmark metrics into stronger claims.
- The upload timeline uses existing document fields and marks steps as pending, current, complete, or failed. It does not imply AI cleanup or hosted storage.
