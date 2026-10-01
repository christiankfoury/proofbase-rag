# Phase 73 v6: complete execution, rejected quality publication gate

All 60 sealed cases executed once on 2026-10-01. Recorded model outcomes are
**28 passes, 21 failures and 11 unresolved**. These are unadjusted diagnostic
counts, not validated accuracy: seven source-inspection findings leave
`validated_passes` null and the publication gate rejected. The 48/60 target was
not met. Four grades are invalid; nine cases have model-review disagreements
(the groups overlap). No question, expected fact, answer or grade was replaced.

[Every question, required fact, answer and citation](v6-case-review.md) and
[all 60 source inspections](v6-source-review.md) are available. The
[offline report](../../data/evaluation/current-runtime-v6/public-report.json)
and [capture inventory](../../data/evaluation/current-runtime-v6/capture-publication.json)
retain exact denominators and raw-artifact hashes. Original
[v4 timeout](results.md) and [v5 budget-stop](v5-results.md) evidence is unchanged.

## Protocol and custody

Runtime revision `c44459b86f035006e5b7cf6bd671537ab3bb0dd6`, evaluator
`answer-dimensions.v23-candidate`, pinned model `gpt-5.4-2026-03-05`, suite
`current-runtime-6`. Qualification passed 24/24 development cases, 3/3 reviewer
probes and fresh 16/16 confirmation with clean source inspection. This finite
qualification did not prevent new semantic inconsistencies during measurement.
The 287-file runtime/environment freeze was committed separately as `0e67dc47`;
independent agent authorship/validation accepted 60 cases and 102 reference facts
before the separate seal commit `a5cec125`. No-call custody/environment/budget
preflight passed before the one synchronous run. Provider retries remained zero.

The composite requires complete, relevant, supported answers and correct behavior.
Unresolved judgments receive no credit. Exact quotation fidelity is separate.
All 60 application responses and 60 evaluation rows are saved, including invalid
grades. The suite contains factual (8), multi-document (10), memory (8), permission
(10), ambiguity (6), missing-information (6), injection (6), policy-conflict (4)
and uploaded-project-isolation (2) cases. See the sealed suite for exact expected
answer/non-answer behavior; no cases are dropped from the denominator.

## Recorded dimensions

| Dimension | Model pass | Model fail | Unresolved | Not applicable |
| --- | ---: | ---: | ---: | ---: |
| Factual support | 13 | 1 | 17 | 29 |
| Completeness | 22 | 8 | 8 | 22 |
| Relevance | 56 | 0 | 4 | 0 |
| Citation support | 13 | 9 | 9 | 29 |
| Quotation fidelity | 28 | 3 | 0 | 29 |
| Response behavior | 41 | 14 | 5 | 0 |
| Composite | 28 | 21 | 11 | 0 |

The source gate records inconsistent treatment of short coverage witnesses,
evidence caveats, inability-to-find speech acts, omission versus contradiction,
contextual approval paraphrases, question-supplied conditions and policy/actor
attribution. Authorized document titles were supplied to both grading passes.
No corrected score is inferred. Three claims calls exhausted their 4,096-token
output bounds in reasoning and returned empty content; another grade used
non-exact coverage spans. These errors remain invalid without retries.

Application observations include unnecessary abstention despite retrieved support,
numeric-validation failures on scenario values and thousands-separated amounts,
incomplete mixed-request answers, overly strong obligations and unsupported
extra explanations. These require separate development controls before any repair;
failed grader labels alone do not establish application correctness.

## Safety and latency

Zero recorded safety-flag cases and zero observed unauthorized retrieval or
disclosure across this bounded suite. Both upload fixtures were approved/indexed
in separate projects, then excluded from Northstar retrieval and answers. The
10 role-permission cases executed, including allowed/denied pairs; wrong refusal
wording still fails response behavior even without disclosure. Hostile source
instructions were not followed in the inspected injection cases.

This is not production security assurance: all department scopes are null,
authorship/validation/inspection are agent work, and human adjudication and
independent security assessment remain absent. The rejected semantic gate still
prevents a validated overall result. Different suites/evaluators cannot support
a controlled before/after improvement claim.

Median application latency is **33.383485 seconds**; P95 is **51.95137 seconds**,
across all 60 responses. Grading, fixture indexing and orchestration overhead are
excluded. Run start/end timestamps are retained in the manifest.

## Accounting

| Item | Recorded value |
| --- | ---: |
| Measurement API calls, all settled | 453 |
| Application chat / embedding / grader calls | 204 / 75 / 174 |
| Measurement estimated cost, including auxiliary calls | USD 3.50002860 |
| New allowance qualification/development cost | USD 1.70517650 |
| Total spent from the new USD 9 allowance | USD 5.20520510 |
| Remaining new allowance | USD 3.79479490 |
| Combined additional journal / ceiling | USD 15.08344195 / 18.87823685 |
| Complete historical attempts / accounting | 4,086 / USD 25.93914272 |
| New unknown outcomes / retries | 0 / 0 |

The CAD 14.32 instruction was conservatively bounded to USD 9; CAD 1.59/USD is
only the recorded budget buffer, not a billing conversion. The old USD 0.12176315
was not added again. All 3,633 prior call records remain an immutable prefix.
The historical unknown call retains its full USD 0.146775 reservation under the
specific carry-forward authorization; its provider outcome is still unknown.
These amounts are usage estimates/reservations, not account balances or invoices.
No local budget stop occurred in v6 and no ceiling was increased.

## Verification and continuation

```powershell
python scripts/report_phase73_v6.py --check
python scripts/report_phase73_v6_capture.py --check
python scripts/report_phase73_v5.py --check
python scripts/report_phase73_interruption.py --check
```

All four offline replay commands above passed on this publication diff. The
capture supplement binds 516 run artifacts and nine supporting records. Local
Markdown links, all 60 case/answer/dimension entries, all 60 inspection rows and
a credential-pattern scan passed. `npm run build` passed once, including lint,
types and static generation. Browser smoke confirmed exact counts, costs and
rejected-gate wording for Admin, and denied access for Employee. The original
demo identity was restored and both temporary servers stopped. That check used
an empty API key and isolated logs, with no additional paid calls.

Semantic review covered the complete intended diff, all new publication files,
60 source-inspection rows, raw artifacts through receipt/reducer replay, budget
prefixes, README/methodology and UI claims. It caught and corrected one prose
encoding regression. No blocking publication-code finding remains; the seven
evaluation findings are explicitly unresolved. The unrelated tracked request log
retains SHA256 f37906539da34d369b0259b014fc061bb2d15b42e31605800d55b724335c176e
and is excluded. No tests depend on those unstaged log edits.
The unchanged 21 measurement/title/history controls and four capture controls
already passed before sealing and are reused; no runtime, evaluator or benchmark
schema changed in this publication work unit.

The run is complete, but Phase 73's validated-quality gate remains unsatisfied.
The remaining USD 3.79479490 is below the existing USD 4.50 minimum launch
headroom even before successor qualification costs. Further paid qualification
cannot lead to another full measurement within the present allowance. Preserve
that remainder; do not launch another paid cycle, silently increase the cap,
resume this suite or relax evaluation. The next defensible cycle needs separately
composed development controls, source-supported repairs, full qualification,
a new freeze and newly isolated/sealed cases with adequate authorized funding.

No production roadmap phase is auto-started. This work unit publishes the complete
failed-gate evidence and records the actual funding/qualification boundary.


## Compact handoff

Goal: publish the one-shot measurement honestly, with full cost/custody evidence,
all-case inspection, coherent Dev/Admin reporting and preserved history.
Branch: main; prior seal a5cec125; execution/publication files form one coherent
commit. Runtime, evaluator, corpus, scoring meaning and sealed cases are unchanged.
Measured run elapsed: 95 minutes 43.8 seconds (19:45:41.648518 to
21:21:25.414046 UTC). Publication wall time is not separately instrumented.
One frontend build; four report replay commands; prior 21+4 focused controls reused.
No new broad runtime tests, benchmark validation, Docker image build, cloud
provisioning or further live evaluation: corresponding inputs did not change.
Next: preserve USD 3.79479490 and resolve the adequate-funding boundary before
another paid qualification/fresh-measurement cycle. This run cannot be resumed.
