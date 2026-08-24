# Phase 49: Holdout Evaluation Reliability And Fresh Measurement

## Goal

Make one-time holdout measurement durable and recoverable before collecting new generalization evidence. Phase 49 changes the evaluator and Dev/Admin reporting only. It does not tune prompts, retrieval, generation, permissions, memory, direct-response behavior, or any other RAG runtime path.

## Immutable Inputs

- Phase 47 development remains `64/70`; its original holdout remains `14/30` and is never rerun.
- Phase 48 development remains `70/70`; benchmark regression remains `130/130`; memory remains `20/20`; permission hard gates remain zero.
- Phase 48 holdout remains the interrupted `19/30` machine observation at `$0.023159`.
- Phase 48 aggregate behavior, recall, completeness, citation, hallucination, permission, and memory metrics remain unavailable.
- Phase 48 adjudication remains 1 evaluator-only, 6 product, and 4 indeterminate failures. The six product failures remain a later remediation backlog.

## Reliability Work

1. Validate every case, role, user, scope, source, fixture declaration, suite/hash, frozen commit, database dependency, indexed chunk dependency, API key presence, and budget before case 1.
2. Reject unsupported fixtures during no-egress preflight.
3. Persist a hash-chained append-only journal, atomic manifest/checkpoint, and atomic detailed record after every completed case.
4. Store complete case/evaluator provenance, response, citations, retrieval evidence, scores, errors, tokens, and cost.
5. Recover journaled results before executing the first unexecuted case; never repeat a completed case.
6. Reject corrupted, duplicate, or out-of-order records and aggregate only a validated contiguous set of persisted detailed rows.
7. Mark a run complete only after the validated final artifact exists and contains every expected row.
8. Simulate failures before case 1, during arbitrary cases, after case 29, after journal-before-record persistence, before/during finalization, and on unsupported fixtures.

## Fresh Measurement Contract

After the hardened evaluator is tested, commit and freeze it. Keep the Phase 48 runtime commit unchanged. Use two isolated agents with no Phase 47/48 holdout or failure-remediation context: one authors a new 30-case suite from the corpus and locked schema/distribution; another independently validates every question, expected fact, quote, role, scope, and fixture.

Seal the reviewed suite and hash before execution. Record the frozen runtime commit, evaluator commit, execution commit, corpus hash, suite hash, configuration, and `$2.00` maximum command budget. Dry-run and complete preflight first. Execute each case exactly once, do not tune after disclosure, review every automated failure and at least 10% of automated passes, and preserve automated and adjudicated results separately.

## Claim Gates

| Gate | Threshold |
| --- | ---: |
| Permission leakage | `0` |
| Unauthorized chunks reaching generation | `0` |
| Restricted citation leakage | `0` |
| Memory-as-evidence violations | `0` |
| Behavior accuracy | `>= 0.90` |
| Required-source recall | `>= 0.90` |
| Required-fact completeness | `>= 0.85` |
| Citation accuracy | `>= 0.90` |
| Heuristic hallucination rate | `<= 0.05` |
| Overall automated target | `>= 27/30` |

A valid missed target completes Phase 49 but prohibits an improvement claim and creates evidence for a later product-remediation phase.

## Verification

```powershell
python scripts/test_phase49_evaluation_reliability.py
python -m compileall apps/api/app scripts
python scripts/export_dashboard_data.py
cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; npm run build
docker compose config --quiet
```

The live command is separately approval-gated and refuses budgets above `$2.00`.
