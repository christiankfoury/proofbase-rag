# Phase 46 Checklist

Goal: remediate measured Phase 45 memory and ambiguity generalization failures without weakening benchmark behavior or permission safety.

## Scope

- [x] Add pre-retrieval clarification reasons for project, department, role, topic, document-reference, and comparison ambiguity.
- [x] Return `clarification_reason` in `/query` and `/query/stream` responses.
- [x] Show clarification reason in App chat proof and shared query-result proof surfaces.
- [x] Add targeted follow-up detection and rewrite rules for the Phase 45 failures.
- [x] Add source planning coverage for remote/device safeguards and sales objection-handling follow-ups.
- [x] Add evidence-backed direct answers for retrieved remote/device, BYOD, sales objection, HR Admin unclear-policy, and benefits/learning-budget cases.
- [x] Keep memory as query context only; citations still come only from retrieved chunks.
- [x] Make `scripts/run_generalization_eval.py` reusable for Phase 46 output paths without overwriting the Phase 45 baseline.
- [x] Correct generalization probe department constants to match seeded Northstar departments before the final Phase 46 run.

## Out Of Scope

- Benchmark expectation changes.
- Broad prompt rewrites.
- Treating previous chat text as source evidence.
- Relaxing project, department, or role filters.

## Completion

- [x] Phase 46 live generalization remediation run captured.
- [x] Phase 39 live `/query` regression rerun returned zero failed benchmark questions.
- [x] Phase 46 permission safety run captured with zero leakage.
- [x] Dashboard exports refreshed.
