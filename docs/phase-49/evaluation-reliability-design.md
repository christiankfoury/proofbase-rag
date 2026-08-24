# Phase 49 Evaluation Reliability Design

## Durable State

Each run owns four layers under `data/evaluation/independent-generalization/runs/<run-id>/`:

1. `journal.jsonl` is append-only, fsynced after each event, sequence-numbered, and hash-chained.
2. `cases/*.json` stores one atomic, hash-verified detailed record per completed case.
3. `manifest.json` is the durable checkpoint and never reports `run_complete=true` until all rows and the final artifact validate.
4. `final.json` is built only from the contiguous persisted case records.

The journaled `case_completed` event contains the full detailed record. If atomic case-file replacement fails after an external response, recovery rebuilds the missing file from the journal and does not repeat the external call.

## Recovery Rules

- Validate the manifest's suite, case order/hashes, runtime commit, evaluator commit, configuration, and budget.
- Verify the entire journal sequence and hash chain.
- Reject duplicate completed events, corrupt hashes, unexpected record files, and later records after a missing prefix record.
- Rebuild a missing atomic record only when its exact completed payload is present and verified in the journal.
- Continue at the first case with neither a persisted nor journaled completed record.
- Re-aggregate from disk after every recovery. A saved aggregate is never treated as source data.

## Boundary

The evaluator cannot make an unjournaled provider response exactly-once across an operating-system failure between receiving the response and the first durable local write. Phase 49 closes the observed Phase 48 failure mode and the testable persistence window: once the response reaches evaluator scoring and is journaled, record-write or aggregation interruption cannot cause a duplicate call. The run manifest reports this contract honestly.
