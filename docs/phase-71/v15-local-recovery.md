# V15 local ledger-write recovery

The original diagnostic stopped after two complete cases and the next claims
response. Windows denied the atomic ledger replacement after that response and
its usage were already saved. The old transport then marked the call unknown.
No provider call is retried. This is infrastructure recovery under the standing
authorization, not a new evaluator candidate or a selective judgment retry.

Proof: reconstructing the received envelope from the saved response exactly
matches the raw SHA-256 already stored in the ledger before the failed write.
The declared request, model snapshot, input/output token counts, token bounds
and computed charge agree. The original interrupted manifest, ledger snapshot
and raw unknown envelope remain untouched. A reconciliation record binds their
hashes and a copy of the complete pre-recovery active ledger. The corrected active
ledger points to a new received-envelope copy, retaining the same charge and
all previous calls. Cumulative accounting is 2,101 calls / USD 5.57397077.

The recovered diagnostic reuses the two complete results and the already-saved
claims response. It continues only requests that were never issued, under the
original total 52-call reservation and unchanged evaluator/input plan. No result
is dropped. New recovery code/snapshots, record hash and offline replay preserve
provenance. Calibration still requires 17/17 plus the extra reviewer probe and
clean source inspection, followed by the original 24/24 plus 3/3 gate.

The new durable writer retries only a local atomic rename at most five times
with short backoff; it never retries the provider. Persistent failures remain
fail-closed with saved evidence. Frozen historical writer/transport files are
unchanged. Three filesystem-fault/reuse tests passed; a test initially used the
wrong versioned BudgetStop class, corrected before any recovery execution.
Scoped compilation passed. Source and complete intended diff reviewed. No
application changes or frontend build. Elapsed work time not measured.

Next: commit/push recovery code and its provenance, then run
`python scripts/quality_v15_local_recovery.py --stage diagnostic --allow-external-ai`.
After passing, full calibration uses the same driver with `--stage calibration`.
No confirmation authoring before development readiness and freeze. Docker is
now running, as confirmed by the user and a local engine check.
