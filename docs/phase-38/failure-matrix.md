# Phase 38 Failure Matrix

Generated at: 2026-06-21T18:43:34.659637+00:00

- Source artifact: `data/evaluation/failed-questions/failed-questions.json`
- Source revision: `HEAD`
- Source run: `phase35-citation-alignment-v7`
- Benchmark version: `1.1`
- Failed questions: `16`

| Bucket | Count | Question IDs | Primary remediation |
| --- | ---: | --- | --- |
| ambiguity_failure | `5` | `AMB-006`, `AMB-007`, `AMB-008`, `AMB-009`, `AMB-010` | Return a clarification before generation when approval context is underspecified. |
| incomplete_answer | `2` | `MULTI-007`, `ADV-005` | Prompt for all supported required facts and exact thresholds when evidence is present. |
| multi_document_failure | `3` | `MULTI-005`, `MULTI-008`, `MULTI-013` | Keep visible for Phase 39 query decomposition and source-coverage planning. |
| retrieval_miss | `1` | `MEM-004` | Use the same memory-aware query rewrite path as the live assistant. |
| unsupported_answer | `2` | `MULTI-020`, `ADV-001` | Treat adversarial source instructions as evidence, not assistant instructions. |
| wrong_citation | `3` | `MULTI-004`, `MULTI-014`, `MULTI-017` | Prefer exact supporting chunks and backfill citations only from retrieved, permission-filtered chunks. |

## Policy

- This matrix is built from the current failed-question artifact before Phase 38 behavior changes.
- Later Phase 38 dashboard exports refresh the failed-question artifact with post-remediation failures.
- Benchmark expected answers, expected behavior, and expected sources are unchanged.
- Multi-document orchestration gaps remain visible for Phase 39 rather than being hidden by benchmark edits.
