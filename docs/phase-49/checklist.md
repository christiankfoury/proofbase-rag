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
- [ ] Freeze the hardened evaluator commit.
- [ ] Author and independently validate blind holdout v3 with isolated agents.
- [ ] Seal the suite/hash and record provenance/budget.
- [ ] Execute the complete holdout exactly once.
- [ ] Review every automated failure and at least 10% of passes.
- [ ] Preserve automated and adjudicated results separately.
- [ ] Complete verification, commit review, code review, and push `main`.
