# Phase 33 No-Egress Retrieval Candidates

Generated at: 2026-06-21T01:36:46.248056+00:00

## Scope

- Method: local Postgres full-text retrieval using `keyword_only` mode.
- Network/API use: none.
- Answer generation: skipped.
- This is safe negative/triage evidence; it does not replace the OpenAI-backed vector rerank live gate.

## Candidate Results

| Top K | Precision@k | Source Recall | MRR | Failed Source Questions | Unauthorized Chunk Exposure | Unauthorized Chunks Reached Generation | Precision Gate | Recall Gate | MRR Gate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | 0.878 | 0.765 | 0.878 | 31 | 0.000 | 0.000 | pass | fail | fail |
| 2 | 0.678 | 0.846 | 0.906 | 22 | 0.000 | 0.000 | fail | fail | fail |
| 3 | 0.607 | 0.911 | 0.920 | 14 | 0.000 | 0.000 | fail | fail | fail |
| 4 | 0.561 | 0.961 | 0.921 | 6 | 0.000 | 0.000 | fail | pass | fail |
| 5 | 0.513 | 0.978 | 0.923 | 4 | 0.000 | 0.000 | fail | pass | fail |

## Findings

- No keyword-only no-egress candidate satisfies all Phase 33 retrieval gates.
- Top-1 passes the precision target but fails recall and MRR.
- Top-4 and top-5 preserve recall but miss the precision target and MRR gate.
- Permission-boundary retrieval checks show zero unauthorized chunks reaching the retrieved context for these keyword-only runs.
- The vector lexical rerank live run remains the next required gate, but it requires explicit approval for external embedding API data egress.
