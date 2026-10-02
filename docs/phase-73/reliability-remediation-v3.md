# Offline remediation of the six live-v2 findings

Authorized 2026-10-02, offline only. Goal: remediate omitted scenario provenance,
false-premise classification, compound qualifier scope, malformed generation JSON,
paid-failure telemetry and serialization-order cost estimation. Affects App query
generation/validation and diagnostic payload preparation; no permissions, database
schema, benchmarks, evaluator standards or historical receipt changes.

Acceptance: replay each saved failure through its owning application/diagnostic
path before editing behavior; add independently worded positive/negative tests;
verify caller routing, bounded repair and authorized evidence; retain before/after
evidence and distinguish deterministic results from unmeasured semantic behavior.
Review the complete intended diff, commit/push main, then stop with proposed live
checks. No provider calls, qualification, full evaluation or budget consumption.

Baseline: main e69b5bae; unrelated tracked request log remains excluded. Saved
live-v2 run, old prompts and runners remain historical evidence. USD 3.74777920
remaining is unchanged, not authority for another paid stage.

## Before and after

Saved inputs and provider responses were replayed with provider HTTP transports
and outbound connections blocked. `before.json` was recorded on e69b5bae before
runtime edits. `after.json` uses the new v4 contracts; `after-legacy-contract.json`
repeats the same responses under v3 on the changed runtime to separate schema
rejection from better semantic judgment. These are development replays, not new
model answers, evaluator results or an overall success-rate measurement.

| Root cause / captured evidence | Reproduced before | Offline result after | Remaining live question |
| --- | --- | --- | --- |
| Scenario provenance omitted: live-v2 call 004, case 01 | Correct-looking USD 217 application was downgraded because `numeric_context` was empty | v4 computes each claim/literal obligation, requests exact array cardinality, and checks identity, request quote, provenance and authorized citation locally. Independently worded EUR 93 and EUR 1,230 scenarios pass with valid supplied judgments; missing provenance, policy-origin values and currency changes remain blocked | Will the model consistently supply correct provenance and apply the rule? The saved response still fails; no recovered live answer is claimed |
| False premise treated as missing evidence: call 007, case 02 (also case 04) | Assessor describes the actual limits but labels both facts unsupported; application chooses not_found | v4 moves correction/denial answerability to the opening instruction, uses neutral fact questions and explicit input guidance. Source-backed contradictions route to answer; topical or unauthorized references still cannot prove support | Entirely unmeasured semantic improvement. Replaying the original unsupported judgment still abstains |
| Compound scope accepted: call 014, case 03 | Complete copied sentence expands an international-only ambiguity condition to longer domestic work; v3 accepts it | Every exact unit now needs an independent scope check. A negative check overrides a supported label and takes the existing single repair/downgrade path. Fresh shift/suspension contrasts and numeric/scope interactions verify this behavior | The model can still falsely mark scope preserved. Old v3 output fails the new schema because the new checks are absent; that is not evidence that v4 detects the meaning error |
| Malformed generation JSON displayed: call 023, case 05 | Overescaped citation delimiters cause raw JSON to become a partial answer, then 23 validation units | Generation, repair and stream requests now include strict structured output. Invalid JSON/types/enums produce a safe not_found with no citations; captured output is never displayed as JSON and retains its 999 input tokens. Oversized validation candidates stop before a provider request | Provider acceptance of the new schema, valid authorized answer completion and output-cap sufficiency need live checks. The saved malformed answer is rejected, not repaired into a correct answer |
| Paid failure reported as zero usage: call 004 (also 024) | Captured 1,950 input / 298 output tokens become 0 / 0 and USD 0 in application validation metadata | Same captured failure now retains 1,950 / 298 and an application estimate of USD 0.001257. Evidence-assessment schema errors also retain usage. Missing usage stays unknown, including combined attempts | Application estimates use existing uncached pricing/rounding; the independent receipt ledger remains the authority for actual diagnostic cost |
| Payload ordering changes reservations | Historical persisted requests differ by 1–3 tokens from original reservations. A controlled recursive key permutation of captured call 000 reproduces 3,603 before persistence versus 3,592 afterward through the ledger | New preparation adapter canonicalizes the object before estimation, ledger reservation, submission and persistence: 3,592 at both ends. Unicode content and existing model/call/token guards are preserved | Future executor must adopt `submit_prepared` with a fresh ledger identity and pricing/payload preflight. Frozen v2 runner/estimator and historical bounds remain unchanged |

Artifacts: [baseline replay](../../data/evaluation/reliability-remediation-v3/before.json),
[v4 replay](../../data/evaluation/reliability-remediation-v3/after.json),
[legacy-contract control](../../data/evaluation/reliability-remediation-v3/after-legacy-contract.json),
and [verification metadata](../../data/evaluation/reliability-remediation-v3/verification.json).

## Verification and review

- `python scripts/test_reliability_remediation_v3.py --record-replay after.json`:
  **17 methods passed**, covering all six causes with new positive, negative and
  interaction fixtures. Real generation, repair, streaming, evidence assessment,
  validator and main answer-validation callers run against injected responses.
  File creation is exclusive: reruns cannot overwrite recorded evidence.
- `python scripts/test_reliability_remediation_v3.py --legacy-replay Contracts.test_saved_failures_through_callers --record-replay after-legacy-contract.json`:
  one control replay passed. The scope defect remains accepted under v3.
- `python scripts/test_reliability_remediation_v2.py`: **25 methods passed**;
  citation excerpt selection, substring planning and prior permission/provenance
  controls remain intact.
- `python scripts/test_application_reliability.py`, with both evidence and
  post-generation prompt-version environment variables explicitly set to `v2`:
  **30 methods passed**, including nested Phase 52/53/54, permission/ambiguity,
  memory, multi-document/citation checks and frozen v6 report/capture replay.
  This preserves compatibility with those historical fake-response schemas;
  it is not a v4 semantic assessment. New v4 fixtures use v4 explicitly.
- `python scripts/test_phase53_evidence_assessment.py`: passed independently;
  the registry assertion now expects v4, with no changed scoring expectation.
- `python scripts/test_reliability_v3_custody.py`: **4 methods passed**. The
  unchanged live-v2 report runs against Git-archived d4c50ebe sources restored
  only when their bytes match the recorded hash (including LF/CRLF custody).
  Receipt totals match the published summary; charge/source tampering fails.
  No current runtime is falsely labeled as the frozen live runtime.
- Changed Python sources compile; intended diff passes whitespace review.

Review found and fixed normalized repetition producing duplicate numeric
obligations, and known-plus-unknown validation usage producing a partial total.
Security filtering, source-instruction checks, strict citations, bounded repair,
memory-as-context and scoring standards are retained. Historical raw receipts,
prompts, holdouts, runners and cost accounting are unchanged. The unrelated
tracked request log remains excluded and byte-identical to the turn's start.

Skipped: live calls, database-backed end-to-end execution, provider schema
acceptance, evaluator qualification and full evaluation. No frontend/API response
shape or migration changed, so no web build was needed. Offline fixture execution
does not establish retrieval performance, live latency or model reliability.

## Proposed next diagnostic — not authorized or executed

Use six separately recorded synchronous development questions after freezing the
new runtime, inspecting every answer against authorized sources:

1. Apply the office-supply limit to a newly worded below-limit personal scenario;
   check numeric provenance and the relevant approval condition.
2. Ask whether an incorrect office-supply limit and an incorrect conference
   approval exemption are policy; require source-backed correction, not agreement
   or unnecessary abstention.
3. Contrast extended domestic work, work outside Canada/US, and personal-device
   restrictions; inspect each condition and the referent of every compound claim.
4. Challenge automatic payroll deductions and mandatory return shipping; preserve
   the review prerequisite, optional shipping wording and relevant excerpt.
5. Ask an IT/Admin user for privileged-access review intervals and exception
   fields; verify valid structured output and completeness.
6. Ask the same protected question as Employee; verify refusal and no protected
   content reaching generation or citations.

Expected cost is roughly **USD 0.03–0.08**, allowing for the larger validation
contract; this is an estimate from prior diagnostics, not a fresh price quote.
Propose a **USD 0.50 ceiling from the unchanged USD 3.74777920 remainder**.
At the last verified rates (mini input/output USD 0.40/1.60 per million, embeddings
USD 0.02), 42 chat calls bounded at 16,384 input and 2,048 output tokens plus 18
embeddings bounded at 8,192 tokens reserve at most **USD 0.41582592**. Reverify
pricing, complete serialized v4 bodies, output headroom, permissions and fresh
ledger identity before any execution; stop if preflight exceeds those bounds.
Use no automatic retries, no evaluator, no full benchmark and no selective reruns.
Authorization is still required because the current request expressly forbids
paid calls. No overall success-rate claim is justified by this proposed sample.

## Handoff

Goal: six-root-cause offline work unit complete after reviewed commit/push to main.
Baseline e69b5bae; tested working diff recorded in verification metadata. Remaining
issues are semantic provenance/correction/scope reliability, live structured
generation completeness and adoption/preflight of the future diagnostic adapter.
Actual external AI calls/cost this work unit: **0 / USD 0**. API remainder unchanged.
Wall-clock work duration was not instrumented; no latency improvement claimed.
Initial fixture errors (wrong helper key, source-role metadata and newline custody)
were corrected before passing captures; no provider attempts occurred. Tests were
repeated only after those errors or affected contract/accounting changes.
Stop here; next action is review of the proposed bounded live stage, not execution.
