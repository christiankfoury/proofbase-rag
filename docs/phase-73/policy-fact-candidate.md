# Policy-fact availability candidate

## Declared experiment

User authorization, 2026-10-02: one isolated candidate and one synchronous live
diagnostic, at most USD 0.50 from the existing USD 3.73920000 remainder. Stop after
results regardless of outcome; no retries, selective reruns or second prompt cycle.
Evidence-assessment v4 remains the default; failed conversational v5 stays disabled.
No calculator expansion, geographic work, evaluator qualification or full evaluation.

Goal: answer source-resolvable false-premise policy questions without confusing
the premise's truth with availability of the requested policy fact. Implement an
opt-in evidence-assessment v6 contract, preserving premise relations explicitly.
The complete original request binds premise quotes. Authorized source witnesses
bind policy statements; neither matching text nor IDs establish semantic support.
Only an explicit semantic entailment judgment plus valid provenance can make a
policy fact available. Conflicts, incomplete interpretation and invalid/unauthorized
bindings fail closed; absent facts remain missing. Existing answer generation and
post-generation controls remain responsible for final prose. No extra runtime calls.

Offline acceptance: reproduce the captured contradiction-as-missing decision and
legacy contradiction promotion; exercise actual assessment and synchronous/streaming
answer callers with independent correct/false premises, unknown fields, conflicting
rules, inaccessible sources, topical-but-nonentailing quotations, invalid IDs and
incomplete request coverage. Mocked decisions prove routing only, not semantics.
Review shared assessment, application, permission and scenario regressions.

Live acceptance will be frozen in `data/evaluation/policy-fact-candidate/cases.json`
before execution: six cases, including a captured false-premise request, a new
false premise, a correct premise, an unknown field, conflicting rules and an
inaccessible source. Run real synchronous application callers with frozen synthetic
retrieval/identity fixtures; request assessment, evidence assessment, generation
and validation use live responses. This isolates assessment-to-answer behavior;
it does not measure database retrieval or deployed authentication. No evaluator.

Candidate acceptance requires all three answerable cases to retain semantically
correct premise relations and produce source-supported final answers with the
requested facts, plus all three negative controls to avoid unsupported assertions
or inaccessible disclosure. Conflict must clarify; unknown information must remain
unknown; inaccessible policy must not be used. Any unmet item or incomplete run
means acceptance is not established. Inspect full final answers/citations against
saved sources, including unsupported additions; mocks earn no semantic credit.

Call ceiling: six cases, at most one request assessment, one evidence assessment,
one generation and one post-generation validation per case: 24 chat calls, zero
embeddings. No generation repairs or provider retries in this experiment; an
attempted additional stage stops the run. GPT-4.1-mini standard synchronous rates
verified from its [official model page](https://developers.openai.com/api/docs/models/gpt-4.1-mini):
USD 0.40 input, 0.10 cached input, 1.60 output per million tokens. At 16,384 input
and 2,048 output tokens per call, the uncached absolute maximum is USD 0.23592960.
Prepare actual stage payloads offline and guard every submitted dynamic payload;
retain original receipts, unknown reservations and historical journal entries.

Freeze reviewed runtime, suite and preflight in a commit before the live run.
Then inspect sources, publish actual costs/limitations, review, commit/push and stop.

## Offline verification and freeze

Six new candidate methods pass, including twelve synchronous/streaming case paths;
five new transport methods verify duplicate-stage/repair blocking, unknown-outcome
reservation, model/payload rejection and call/dollar bounds. Shared checks pass:
25 v2 remediation methods, 17 v3 remediation methods, 30 application compatibility
methods (evidence/validator v2 fixtures), four frozen-custody methods, 13 bounded
scenario methods and 11 conversational plumbing methods. These do not establish
semantic improvement. The first combined discovery command incorrectly used v4
with historical v2 mocks and loaded the imported, unfrozen custody base test;
the documented standalone commands/configurations resolve those invocation failures.

`python scripts/policy_fact_candidate_diagnostic.py --preflight` exercised 18 mocked
stage payloads through the real synchronous caller. Largest complete input bounds:
request 3,598; evidence 3,582; generation 3,000; validation 4,398 tokens, including
2,048 framing reserve. Another 4,096 input tokens fit for dynamic candidate text;
each real payload is independently checked before submission. Preflight binds the
runtime, source/case fixtures, payloads and original spending journal. Existing
source security instructions and all post-generation validation remain unchanged.

Review caught a harness issue before live execution: the evidence-assessment body
contains dynamic request-routing metadata. Its frozen comparison now permits only
that context-only field to vary, while binding the full original question, sources,
prompt, schema and settings. A negative regression rejects changed source payloads.
The initial offline preflight is retained separately; final preflight binds the fix.

Review covers the full intended diff, default isolation, complete-request binding,
explicit contradiction retention, negative routes, fixture authorization, receipt
preservation and cost guards. Frozen v4/v5 artifacts and the unrelated request log
are preserved. The live result is pending; no activation or success claim follows
from this offline gate.

## Single live result: acceptance not established

Frozen commit **`17840a18`**, executed 2026-10-02 local time (2026-10-03 UTC).
**The candidate does not meet the declared acceptance criteria.** Three of six
cases were attempted, then the predeclared no-repair guard stopped the run. All
three final responses are `partial_answer`, versus their declared `answer` route;
the three negative controls were never executed. They are unmeasured, not passes
or failures. Keep v6 isolated and unpromoted, v4 default and v5 disabled. No second
run or prompt cycle follows this result.

### Source inspection, not evaluator scores

Each case file contains the original request, authorized source text, internal
policy-fact relations, normalized assessment and final application response.
Provider originals are `run/raw/call-NNN.json` in the same evidence folder.

| Case / saved calls | Assessment and final response against authorized sources |
| --- | --- |
| [fact-01](../../data/evaluation/policy-fact-candidate/run/fact-01.json), captured two-premise question; assessment001, generation002, validation003 | Both policy facts are available and both proposed rules remain explicitly contradicted. FIN-001 establishes USD 300 for office supplies and USD 1,500/event with approval before purchase for conference registration. The final answer correctly corrects both false premises, rather than abstaining. The model also lists the rejected premises in `unsupported_claims`; existing response-type adjustment therefore marks the complete correction partial. Its joined citation is replaced with a contiguous source excerpt containing both rows. |
| [fact-02](../../data/evaluation/policy-fact-candidate/run/fact-02.json), independently worded false book limit; assessment005, generation006, validation007 | Available policy statement correctly says EUR 460/order; EUR 90 remains a contradicted premise. Final prose correctly denies EUR 90 and supplies EUR 460 with an exact authorized quotation. Again, the generator lists the denied premise as an unsupported claim and the application unnecessarily labels the answer partial. `requested_fact` repeats the user's biased question instead of a neutral field description, but the separate policy statement and premise relation remain correct. |
| [fact-03](../../data/evaluation/policy-fact-candidate/run/fact-03.json), correct book limit; assessment009, generation010, validation011 | Assessment correctly confirms EUR 460/order. Generation says “Yes, you are correct” followed by the supported limit. Validation labels the confirmation unsupported while accepting the limit, then requests repair. The harness blocks that additional generation before submission and stops. Final fallback retains EUR 460 with a citation but adds a misleading inability-to-validate-the-rest caveat. The source-backed answer did not need a factual correction. |
| fact-04 / fact-05 / fact-06 in the [frozen suite](../../data/evaluation/policy-fact-candidate/cases.json) | Unknown fee, conflicting limits and inaccessible relocation rule: **not executed** after the stop. Their offline routing tests cannot establish live semantic safety. |

Confirmed bounded observations: **three completed assessments correctly retain
availability and premise truth separately** (three contradicted premises and one
confirmed premise across those cases); **two final corrections are source-supported**.
The historical [live-v2 case 02](../../data/evaluation/application-reliability-live-v2/run/check-02.json)
abstained on the same first question despite retrieving the critical FIN-001 row.
This controlled run supplies only that relevant chunk and uses the current
downstream runtime, so it is not an isolated estimate of the candidate's causal
effect or an overall improvement rate. No baseline exists for the new book case.

Remaining confirmed defects are downstream of the new availability decision:

- Generation's `unsupported_claims` mixes rejected user premises with unsupported
  assertions made by the answer. `_adjust_response_type` in
  [answer_generator.py](../../apps/api/app/generation/answer_generator.py) consequently
  downgrades both complete corrections even though semantic validation accepts them.
- Validation calls 003/007 label USD 217, USD 375 and EUR 90 as `user_scenario`,
  contrary to the unchanged v4 validator contract: these are proposed policy
  amounts being denied, not hypothetical purchases applying a rule. Correct final
  prose does not make that provenance judgment correct or prove the guard reliable.
- Validation of the correct-premise confirmation ignores its question context.
  The [caller](../../apps/api/app/main.py) requests repair, then catches the harness
  rejection and reports `repair_count=1`, `validator_service_error` and `repair_failed`.
  Those fields describe an attempted application repair: **no repair provider call
  occurred**, and there was no provider outage or uncertain charge. This is a
  validation defect followed by a planned diagnostic stop, not a completed live
  test of the remaining negative cases.

Retain this evidence as a promising assessment-stage observation only. Semantic
entailment, full request coverage and premise interpretation still depend on the
model; quote/ID checks prove provenance, not those meanings. Internal `policy_facts`
preserves contradictions and is captured by the diagnostic; the existing public
assessment schema is unchanged. No permission control, validator, calculator or
generation prompt was relaxed. Default activation is not justified by this run.

### Accounting, verification and stop

The [receipt summary](../../data/evaluation/policy-fact-candidate/receipt-summary.json)
verifies **12 settled synchronous chat calls**: three each for request assessment,
evidence assessment, generation and validation. There were zero provider retries,
repair submissions, embeddings, evaluator calls or unknown outcomes. Reported usage:
13,764 input tokens, including 2,048 cached, and 2,027 output tokens. **Actual
receipt-derived cost USD 0.00813440; remaining shared budget USD 3.73106560.**
The USD 0.50 allocation was part of the existing budget; no unused amount is added
again. Run wall time was 33.546 seconds including local persistence, not a latency
benchmark. The original unknown historical reservation remains unchanged.

`python scripts/report_policy_fact_candidate.py` passes: frozen bindings, raw and
case hashes, no repeated stages, canonical payload/call/cost bounds, citation
identity and contiguous quotes, and unchanged prior journal entries. Source
inspection covers all three original/final answer pairs and the exact stopping
cause. Historical custody checks remain passing; unrelated request-log hash stays
`f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e`.
No runtime or prompt changed after freeze. Reviewed result evidence, accounting
and tracker are committed/pushed, then work stops at this failed acceptance result.
