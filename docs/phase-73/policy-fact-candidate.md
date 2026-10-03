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
