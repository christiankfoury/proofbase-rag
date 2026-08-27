# Phase 55 Post-Review Remediation

## Scope

This correction addresses four issues found during the post-run review. It does not begin Phase 56 or change the production identity and tenancy decision gate.

## Corrections

1. Post-generation source-instruction normalization now preserves a semantic finding backed by authorized evidence even when the source uses wording outside the deterministic fast-path phrases. A missing or unauthorized semantic evidence ID fails safe. Focused tests cover novel wording and an unauthorized semantic evidence reference.
2. The three formerly literal-zero readiness gates now come from `defense-hard-gate-evidence.v1`. The offline check injects a tenant field into an otherwise valid semantic request decision, injects malformed outputs into request assessment, evidence assessment, and post-generation validation, and reads the memory-as-evidence rate derived from the 20 Phase 54 memory rows. The exporter verifies exact source-file hashes and refuses stale or incomplete evidence.
3. A permission-filter invariant violation now gives the trace stage `failed_safe` status and an explicit invariant reason code instead of reporting success.
4. Seven Phase 52-54 raw runtime artifacts containing 682 per-question rows and 7,684,360 bytes were removed from the current tree. Their compact summaries, paths, byte counts, row counts, and SHA-256 values remain committed. Eight duplicated Phase 52-53 `eval-runs` artifacts now omit their detailed `results` arrays and point to the hash-bound detailed copies under `data/evaluation/defense/`.

The seven retired raw files accounted for 168,493 formatted lines. Together with compacting duplicated development results, the correction removes more than 177,000 generated lines from the current tree. Git history was not rewritten; historical bytes remain recoverable from commit `9a22a02`.

## Evidence behavior

- Assessment scope-expansion gate: derived from a malicious extra-field contract check, the absence of authority fields in the semantic output model, and the absence of request-assessment authority reads in the API orchestrator.
- Memory-as-source gate: derived from citation sources on 20 conversation-memory cases in `phase54-live-query-regression-v5`.
- Invalid-schema continuation gate: derived from three injected malformed semantic results; request and evidence assessment must return `temporary_unavailable`, while post-generation validation must downgrade.
- Readiness export: rejects a missing gate, a mismatched pass calculation, a changed source hash, or an incomplete source binding.

## Verification

- The novel-instruction regression injects a valid semantic finding for wording outside `SOURCE_INSTRUCTION_PATTERNS`. The former normalization would suppress that finding; the corrected path returns `downgrade`. A semantic reference to an unauthorized chunk returns `failed_safe`.
- Phase 52, 53, 54, and 55 focused tests pass, including the stale hard-gate source-hash rejection test.
- Phase 39 multi-document orchestration, live-query evaluator, and pre-Phase 39 guardrail tests pass.
- Benchmark 1.1 validates at 130 questions; the 102-case defense manifest and sealed, unexecuted 30-case Phase 55 holdout validate without opening or scoring the holdout.
- Artifact retention validation, dashboard export, Python compilation, Docker Compose configuration, `git diff --check`, and the isolated Next.js production build pass.
- The refreshed dashboard contains 39 runs and keeps `phase54-live-query-regression-v5` as the current answer-quality run.

No external AI evaluation was rerun. The corrected defect was in trusted normalization after a semantic response, so the regression test injects the exact structured model decision needed to isolate the behavior without adding cost or semantic-model variability.

## Limitations

The focused checks and existing development suites are local engineering evidence, not an independent security assessment. The citation-source memory metric validates the implemented evidence boundary on the measured cases; it is not a proof over every future input. Removing files from the current tree does not shrink existing Git object history.
