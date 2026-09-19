# Phase 69: failed v7 semantic calibration

The complete first attempt `calibration-v7-01` evaluated 24 independently authored
and checked development responses plus three deliberately flawed reviewer probes.
It matched all expected labels in **3/24** cases and detected all requested dispute
dimensions in **1/3** reviewer probes. The latter is minimum requested-dispute
detection, not exact review accuracy; extra unjustified disputes are not credited
as correct. **Evaluator readiness failed.** These numbers concern the evaluator,
not Proofbase application accuracy or a new holdout.

All 75 provider calls completed and their raw requests/responses are preserved.
Estimated incremental spend was **USD 0.151672**. Conservative cumulative spend,
including the handoff floor, is **USD 1.34856592** of the approved USD 5 ceiling.
There were no application calls, new embeddings or holdout executions.

The source snapshots are from reviewed/pushed implementation `4ef4221`. The live
continuation ledger and a frozen attempt ledger preserve all 1,321 prior calls.
Request hashes, response hashes, result hashes, code snapshots and both challenge
suite hashes replay offline. The original failed draft, both validation records,
the underfunded preflight and approved preflight are retained.

## Findings

- Claims assessment still enumerated pure refusals and clarification wording as
  policy assertions. A not-found statement received source support from an
  unrelated bicycle-rack passage. One clarification case even copied source-only
  deadlines into alleged answer spans; exact-span validation caught it.
- The reviewer repeatedly treated `dispute` as “the application answer is bad”
  rather than “the candidate judgment is incorrect.” For example, it explained
  that a missing-citation judgment was correct while returning a citation dispute.
- Some unsupported claims were incorrectly marked contradicted despite unrelated
  evidence. The audit probe for an omitted insurance assertion was missed.
- A reviewer probe correctly triggered its required disputes but also disputed
  relevance without justification. Detection alone does not validate reviewer
  specificity.

See [the independent agent inspection](calibration-v7-agent-review.md). This is
agent review, not human adjudication. The challenge expectations remain unchanged.
No failed judgment is silently repaired or substituted in this attempt.

## Verification and next step

```powershell
python scripts/report_quality_calibration.py
python -m unittest scripts.test_quality_calibration_replay
```

Replay reconstructs all three requests per case, provider JSON parsing, local
dimensions, disagreements and reviewer outcomes. It rejects changed raw evidence
and uses the frozen attempt ledger so later spending cannot rewrite this report.
It verifies reproducibility, not semantic correctness.

Preserve v7 evaluator/transport/runner code. The next evaluator version must make
speech-act classification explicit and present actual candidate dimension labels
to the reviewer, with unambiguous correct/incorrect judgment semantics. Validate
that repair on these development cases, retaining every attempt. Do not proceed
to application remediation or a fresh holdout while this gate is failed.
