# Phase 69: independent challenge and live-runner preparation

The offline contract slice `8599647` was committed, inspected and self-reviewed,
fast-forwarded into main and pushed. Main aligned with origin/main; the existing
`data/observability/request-logs.jsonl` edit in the original workspace retained its
exact SHA-256 across merge and push. The temporary branch is user-authorized.

The user also explicitly authorized isolated authoring and validation agents for
evaluator challenges and, after the required freeze, a fresh application holdout.
This authorization does not increase the API ceiling or bypass readiness gates.

## Independent development expectations

A context-isolated author created 24 short fictional-policy challenges without
reading old datasets, reports, failure lists or this task's history. A separate
validator reviewed the question, answer, facts, evidence and all eight labels.
These are agent-authored development judgments, not human adjudication or fresh
application holdout evidence. The validator saw inline authored rationales;
separate context does not establish independent human assessment.

The original draft remains in `challenges-v1.json`. The first validation preserved
eight rejected cases and sixteen accepted cases in `challenge-validation-v1.json`.
Findings included weakened eligibility/ceiling conditions, broad questions with
incomplete required-fact sets, and response-form labels inferred from correctness.
The author corrected these in `challenges-v2.json`, keeping case IDs and the original
bytes. Approval of v2 is recorded separately and bound to its raw-byte SHA-256.

Three additional reviewer challenges seed demonstrably incorrect candidate grades:
reason/label contradiction, invented policy coverage from a generic refusal, and
an omitted unsupported assertion. They test whether the reviewer disputes the
specific incorrect dimensions. A generated review cannot count as correct just
because it returns valid JSON or agrees with a candidate.

See [authorship](challenge-authorship.md), [first validation](challenge-validation.md)
and [revised validation](challenge-validation-v2.md). The program checks both suite
hashes and all 24 case reviews plus three audit reviews before allowing execution.
JSON artifacts are marked `-text` to preserve exact source bytes across checkouts.

## Runner and cost controls

`quality_eval_calibration.py` defaults to an offline preflight. Explicit execution
requires an unused attempt name, approved independently checked expectations,
configured authorized credentials and conservative headroom for the whole attempt.
It has no application query or ingestion path. The three grading stages assess
claims, coverage/prose behavior, then semantic review. Expected fixture labels and
authored rationales never enter model requests. The first two stages keep the
existing evidence-versus-expected-answer separation.

`quality_eval_transport.py` records each request before execution and its raw
provider response before parsing. Malformed, refused or truncated output remains
saved and unresolved. Failed attempts and source snapshots are retained. SDK
retries are disabled; request locks, existing-path rejection and durable unknown
outcomes prevent implicit reruns. Unknown outcomes retain their reservation and
block further external work. A complete calibration manifest still records
`semantic_validation_passed: false`; agreement with visible judgments alone is
insufficient to promote the evaluator without source inspection and a readiness
decision.

The new ledger copies the entire 1,321-call Phase 68 prefix and binds its original
SHA-256. It uses the greater historical handoff spend as its starting floor.
Historical ledgers are never edited. Every request reserves input UTF-8 bytes plus
framing and capped output tokens. The whole-attempt preflight additionally reserves
the maximum allowed 12,000-byte candidate serialization for review; larger grades
cannot trigger an unbudgeted review request. These are intentionally conservative
bounds, not predicted actual charges.

The pinned grader remains `gpt-4.1-2025-04-14`. On 2026-09-19, official
[GPT-4.1 model documentation](https://developers.openai.com/api/docs/models/gpt-4.1)
confirmed USD 2 input / USD 8 output per million tokens and structured-output
support. The request schema follows the official
[structured-output guide](https://developers.openai.com/api/docs/guides/structured-outputs).
No model migration or pricing discount is assumed.

For 24 three-stage challenges plus three audit-only reviews, preflight reserves
**USD 2.713006**. Current conservative remaining funds are **USD 0.80310608** of the
approved cumulative USD 2 ceiling. Thus **live execution is blocked before any
call**. One full bounded attempt needs cumulative headroom of USD 3.90989992.
The user subsequently approved the cumulative USD 5 ceiling on 2026-09-19;
the new continuation records this separately from the preserved old authorization.
Available funds before the new attempt are USD 3.80310608. Additional development or holdout work still
requires its own conservative preflight under whichever ceiling is explicitly
authorized. There have been no new API calls or ledger writes in this slice.

## Verification and review

```powershell
python -m unittest scripts.test_quality_eval_contract scripts.test_quality_eval_preflight scripts.test_quality_eval_transport scripts.test_quality_eval_calibration
python scripts/quality_eval_calibration.py
```

The 37 new/current evaluator test methods pass, including durable invalid output,
unknown-outcome accounting, historical-prefix tampering, request and ledger
overwrite rejection, whole-attempt budget rejection before calls, independent
validation/hash rejection, source/citation identity and omission accounting.
Compilation and diff checks pass. The historical 70-test suite also passes
(107 total test methods), and current/archived historical reports, public evidence
and the 130-case benchmark replay/validate unchanged. The independently checked
but underfunded preflight is preserved as `calibration-preflight-v1.json`.

The independent validator approved all 24 revised expected judgments and all
three seeded reviewer probes, with both raw-byte hashes verified. This approves
the authored expectations only; no semantic model has run. The user was asked
to approve a cumulative USD 5 ceiling and explicitly approved it. The old blocked
preflight remains immutable; a new preflight records the approved headroom.

Self-review corrected an evaluator defect: a wrong substantive answer must produce
confirmed factual/completeness failures rather than become contract-invalid solely
because its prose is classified as an answer. Incomplete expected answers still
fail required behavior and cannot earn overall credit. Review also added pinned
response-model checks and required all independent case/audit reviews, not merely
an aggregate approved flag. No application/runtime or public metric changed.

Post-commit review of `376d2ae` found that ledger raw-file basenames alone were
ambiguous across cases. The follow-up stores relative request paths plus request
and raw-response hashes. Tests verify the three calls' distinct bindings. The
same follow-up records the explicit USD 5 approval and protects copied evaluator
source bytes from Git newline conversion. All 37 targeted tests pass again; the
approved preflight reserves USD 2.713006 against USD 3.80310608 remaining.

Next: secure the required financial approval, retain it in the new ledger's
authorization history, freeze the calibration implementation, execute the full
attempt once, inspect all disagreements and reviewer failures, and preserve every
attempt. Runtime remediation and the new 60-case freeze remain downstream gates.
