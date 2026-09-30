# Phase 73 interrupted measurement

The one-shot measurement stopped on a transport read timeout during case 11's
final grader review. **10/60 cases have complete model grading; 11 application
responses are saved; 49 cases were not executed. There is no full-suite score.**
The predeclared 48/60 quality target and dedicated safety gates are not established.
Phases 71 and 72 are complete; Phase 73's full measurement remains blocked. This
document completes the interruption evidence/publication work, not the missing run.

## What was executed

- Runtime/source freeze: `8bd72ba1a840307e69e63f80610dbeb67b401540`, recorded in
  separate freeze commit `9dc1e867` before authorship.
- Qualified evaluator: `answer-dimensions.v20-candidate`, pinned
  `gpt-5.4-2026-03-05`, medium reasoning, 4,096 maximum output tokens, zero retries.
  Qualification passed 24/24 development cases, 3/3 reviewer probes and 16/16
  fresh confirmation cases with source inspection. This is bounded agent/model
  qualification, not expert human validation.
- Suite: `current-runtime-4`, 60 cases, authored and independently agent-validated
  after freeze. All 136 required facts were checked against exact corpus quotes.
  Raw suite SHA-256: `231129164098d2582c08652b24e9cfae50eb9c3a3cd2c963bbcf0c65aedda841`.
- Separate suite-seal commit: `b964f70a`. No runtime output informed pre-execution
  authorship/validation. Zero lexical overlap hits among 877 historical questions
  at token Jaccard 0.8; this is not proof of semantic independence.
- Fresh preflight verified all 244 frozen files, corpus/index/configuration,
  qualified evaluator, scope, complete historical cost prefix and unused run.
- Local PostgreSQL clone: `proofbase_eval_phase73`, 32 documents and 247 chunks/
  embeddings before execution. Real `POST /query` calls used demo identities,
  Northstar project scope, vector/lexical reranking, top-k 5 and candidate limit 20.
- Measurement window: 2026-09-30 20:02:11.786909 to 20:17:12.737033 UTC, about
  15 minutes 1 second including application calls, grading and durable accounting.

## Observed partial results

The ten complete rows contain **3 recorded model passes and 7 recorded model
failures**. Passes are fresh-002, fresh-004 and fresh-005. This selected prefix is
not an overall accuracy estimate or a substitute denominator for the 60-case gate.
No adjusted score is published. No completed grade is schema-invalid and the
model reviewer disputed none, but primary-agent source inspection found two
unresolved semantic concerns among completed cases and a related concern in the
unfinished case. Therefore source-inspection approval is also withheld.

See [every question, reference and captured answer](case-review.md), the
[primary source inspection](source-review.md), and the
[machine report](../../data/evaluation/current-runtime-v4/public-report.json).
The four pure abstentions on answerable questions are 001, 003, 009 and 010.
Cases 001 and 003 expose exact-literal validation rejecting a user-supplied date,
amount and document identifier despite relevant evidence. Case 008 lacks a
required recipient condition. These are preserved observations, not repairs
performed against this exposed suite. Case 006's purpose-phrase judgment and
case 007's question-specific answer versus broader gold fact remain unresolved.
Case 011 has only initial claims/coverage grading; no final decision is invented.

All 11 captured requests returned HTTP 200, with zero recorded unauthorized
evidence/scope flags. **The dedicated permission, memory, ambiguity, missing-
information, injection, conflicting-policy and uploaded-isolation groups were
not reached.** Both upload fixtures remain unexecuted. This is not a safety pass.
All suite cases have null department scope; narrower department isolation was
not covered even by the planned suite. Application latency across the 11 saved
responses was median **23.41 seconds**, p95 **36.86 seconds**; grading is excluded.

## Cost and timeout custody

| Accounting item | USD / calls |
| --- | ---: |
| This attempt's settled usage estimate | 0.61799184 |
| Unknown final-call reservation retained in full | 0.14677500 |
| This attempt's conservative accounted cost | 0.76476684 |
| New attempts | 94: 93 settled, 1 unknown |
| Operation counts | 46 application chat, 15 embeddings, 33 grader |
| Additional accounted spend across the authorized continuation | 6.69192009 of 10.00 |
| Remaining additional headroom, with reservations retained | 3.30807991 |
| Complete cumulative history | 3,039 rows; 17.54762086 conservative USD |

These are usage estimates and reservations, not provider invoices. The additional
total still includes USD 2.80849875 retained from earlier rejected/cancelled Batch
work. Successful cancelled usage is not added twice. The original 2,595 attempts,
32 cancelled receipts and 318 standard evaluator calls remain an immutable
2,945-row prefix. All 94 new attempts append to that prefix.

The final request has `APITimeoutError`, a transport `ReadTimeout`, no response
body and no usage receipt. This is not a billing-limit rejection. Provider
completion and charge are unknown; the USD 0.146775 bound is retained, not assumed
spent or free. Zero retries were configured and no subsequent call was made.
The unknown-outcome flag remains set. The suite cannot be resumed or selectively
regraded. No extra money or changed evaluation standard has been inferred.

## Reproduction and verification

```powershell
python scripts/report_phase73_interruption.py --check
python -m unittest scripts.test_phase73_interruption
```

The interruption reporter is a new offline publication supplement. The frozen
full-run reporter and runner remain unchanged and reject the unsettled ledger.
The supplement verifies custody, all 108 saved run artifacts, unchanged complete
prefix, 93 settled receipts and costs, the final request/reservation, both saved
initial grades for case 11, all ten complete raw grader/reducer replays, contiguous
call intervals, the exact shared-spend snapshot and the rejected publication gate.
It cannot qualify a partial score or release a reservation. Five focused tests
cover full replay, changed requests, invented usage/receipts and cost release.

Unchanged Phase 72 application regressions and 19 frozen evaluator/accounting
tests are reused as documented in [preflight](preflight.md); no application,
dependency, corpus or evaluator edit followed the freeze. The
benchmark/schema was not changed, so no benchmark rerun is required. No additional
API call is used for publication. Unrelated request-log edits remain excluded.

Publication verification passed: five focused interruption tests, Python
compilation, final offline report comparison, source inventory and shared-journal
integrity, local Markdown links, and `npm run build`. The first browser check
found a missing inter-sentence space; it was fixed and the affected build repeated
once. The final built page was checked in the local browser: Employee denied,
existing Kai Admin allowed, 10/60 completed, 11 saved, 49 unexecuted, no validated
score, 3/10 prefix passes, correct costs/latencies and historical evidence retained.
The original demo selection was restored. Temporary API/web processes used only
local read requests and are stopped after the check. No Docker image rebuild or
deployment was performed; its added JSON copy matches the verified import path.

The complete intended diff was reviewed, including raw-evidence/cost replay and
new files. Review also removed duplicated README prose and corrected a statement
that could imply the upload fixtures ran. No unresolved publication-code finding
remains. The measurement/source-inspection limitations above remain unresolved and
visible, with the full-run qualification gate still rejected.

## Continuation boundary

The approved plan requires a stop on an unknown provider outcome. Remaining budget
does not authorize clearing that flag or repeating this exposed suite. A successor
measurement needs a documented outcome/accounting resolution, source-driven
development controls for the review/reference concerns, revalidation if semantics
change, a new freeze and freshly isolated cases. No guarantee is made that the
remaining USD 3.30807991 can fund that work. External human adjudication and
independent security assessment remain unperformed.
