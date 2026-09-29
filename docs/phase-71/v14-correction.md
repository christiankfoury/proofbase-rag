# V14: one authorized temporal-rule correction

The user explicitly approved one bounded evaluator correction on 2026-09-29.
Goal: distinguish ordinary current-permission confirmation from explicit claims
about policy history, without relaxing evidence, citation, ambiguity or completeness
standards. This affects evaluator claim/reviewer prompts and evidence tooling only;
no App/API/database model or runtime permission changes.

Approved rule: current policy evidence supports current permission. "Still" alone
does not create a separate historical claim. Explicit past/change/dated-continuity
claims require evidence. Expired/superseded policy cannot establish current rights.
An invented topic still fails relevance and expected clarification behavior.

V14 appends that clarification to v13 claim and reviewer prompts. Coverage prompts,
schemas, reducers, exact source spans, model (gpt-5.4-2026-03-05), medium reasoning,
4096-token caps, cost rates and no-retry policy remain unchanged. Frozen v12/v13
code, failed confirmations and original reference approvals remain untouched.

Acceptance/stopping conditions: one diagnostic with 12 predeclared cases (six
prior failure-category controls and six newly composed temporal variants), then
one full unchanged 24-case calibration plus three reviewer probes. An early-stop
consumes this single correction. Require exact agreement and zero open semantic
findings before a new freeze and separate-context 16-case confirmation. Require
16/16 exact, valid contracts and clean source inspection; only then continue to
Phase 73's full runtime/corpus/config/index freeze and new 60-case measurement.
No additional repair candidate, selective retry, changed old label or adjusted pass.

Development variants test current permission, an ambiguous guessed topic, explicit
historical continuity, an invented policy-change date, a superseded permission and
an explicit approval-condition contradiction. They are primary-agent-authored,
source-reviewed development evidence, not isolated holdout or human adjudication.
The strengthened reference-label consistency check passes all six. Existing full
calibration expectations remain independently validated and unchanged.

Preflight bounds: diagnostic 36 calls, full calibration 75 calls. Per-stage token
reservations and complete ledger settlement remain mandatory; the obsolete USD 5
ceiling is not reintroduced. The conservative reservation bounds are USD 3.8817825
for diagnostics and USD 8.0568700 for full calibration, not expected charges.
Starting history: 1,983 calls, USD 4.45340577. No v14 external calls yet.

Verification before execution: `python -m unittest scripts.test_quality_v14
scripts.test_quality_confirmation_replacement` passed all eight tests; scoped
compileall and `git diff --check` passed. Dry-run plans confirm the declared call
bounds. Historical v13 calibration and replacement confirmation replay unchanged
at 24/24 plus 3/3 and 15/16 respectively. Semantic review covered all new source,
six fixtures and intended documentation changes; no open blocking findings.
Transport differs only in version/import, with the successor ledger supplied by
the runner. No application behavior changed, so Phase 72 evidence is reused and
web build/live RAG checks are unnecessary here. Work duration is not measured.

Branch: main; unrelated tracked request-log edits excluded. Next after reviewed
commit/push: `python scripts/quality_completion_eval_v14.py --stage diagnostic
--allow-external-ai`. No confirmation authoring before selected freeze.
