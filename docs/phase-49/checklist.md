# Phase 49 Checklist

- [x] Preserve the Phase 47/48 evidence and Phase 48 six-case product backlog exactly.
- [x] Add complete preflight validation before case 1 or external calls.
- [x] Reject unsupported fixtures with a no-network test.
- [x] Add an append-only hash-chained execution journal.
- [x] Add atomic per-case records and durable manifest/checkpoint state.
- [x] Record case/suite hashes, commits, timestamps, attempts, response, citations, retrieval evidence, scores, errors, tokens, and cost.
- [x] Resume from the first unexecuted case and recover journaled results without repeating external calls.
- [x] Detect or safely recover missing records and reject duplicate, corrupted, or out-of-order state.
- [x] Aggregate only from complete persisted detailed rows.
- [x] Prove interrupted and uninterrupted execution produce the same final artifact without duplicated calls.
- [x] Expose evaluator reliability and run completeness in Dev/Admin data/UI.
- [x] Freeze the hardened evaluator commit at `3d3706e` and push it before blind authoring.
- [x] Author and independently validate blind holdout v3 with isolated clean-context agents.
- [x] Seal the approved 30-case suite at SHA-256 `22e7bfbc36469dc7b7f1aad8586ef480c607094295dc26f9451f8609307b2d8c` with a `$2.00` command budget.
- [x] Execute the complete holdout exactly once: `22/30`, cost `$0.022624`, all 30 attempt counts `1`.
- [x] Review all `8/8` automated failures and `3/22` passes (`13.6%`).
- [x] Preserve automated and adjudicated results separately without a human-adjusted aggregate.
- [x] Complete verification, commit review, code review, and push `main` (`9a28d9f`).
