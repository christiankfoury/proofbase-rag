# Rollback And Monitoring Readiness

## Local rollback

1. Mark the release decision rejected and preserve its hashes and reasons.
2. Revert the candidate through a new reviewed Git commit; do not rewrite shared history.
3. Restore the last accepted prompt/model/config versions and schema-compatible database state.
4. Close external-AI admission and risky upload/admin operations while safety is uncertain.
5. Run the full deterministic gate and relevant development suites against the rollback commit.
6. Reopen locally only after hard gates pass and the reviewer records the decision.

Database rollback must use rehearsed forward/fix migrations or the documented non-production recovery process; never use `git reset --hard` as an operational rollback.

## Production readiness

Production promotion additionally requires a connected privacy-safe monitoring destination, named primary/backup on-call, escalation and notification channels, alert-delivery proof, hosted availability/latency evidence, provider cost reconciliation, and rollback rehearsal in the target environment. None is connected here, so production remains blocked.
