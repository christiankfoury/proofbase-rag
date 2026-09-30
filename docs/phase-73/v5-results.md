# Phase 73 successor: preserved budget stop

The one-shot v5 run stopped locally before case 33's final review because its
request reservation would exceed the approved shared allowance. **32/60 evaluation
rows are complete, 33 application responses are saved and 27 cases were not
executed. No validated full-suite score or safety qualification exists.**
The completed rows retain 18 model passes, 12 failures and 2 unresolved outcomes.
These selected-prefix counts are not an overall accuracy estimate. Source
inspection also withholds approval for four recorded concerns; no adjusted score
is published. Phase 73 remains incomplete, with further paid work blocked by the
remaining budget and fresh-evidence requirements. Phases 71 and 72 remain complete.

## Custody and execution

- Runtime/evaluator qualification revision: `1cb44e30478919be93a59281907e006fa665acf2`.
  The separate runtime freeze was pushed as `f4ad2dd8` before isolated authorship.
  All 258 frozen source/corpus/protocol files, configuration and the existing local
  index passed exact preflight. The Phase 72 application behavior was unchanged.
- Evaluator: qualified v21, pinned `gpt-5.4-2026-03-05`, medium reasoning, 4,096
  output-token cap, 180-second grader timeout and zero provider retries. Its
  unchanged full development gate passed 24/24 plus 3/3 probes, followed by a
  separately authored 16/16 confirmation and source inspection. Qualification
  is bounded agent/model evidence, not infallibility or expert human validation.
- Suite `current-runtime-5`: 60 cases, 78 required facts, 36 expected answers,
  24 non-answers. Separate source-only author and validator; all five roles and
  nine category counts retained. Three pre-execution construction corrections
  preserve the original suite and both rejected validation versions. See
  [preparation and seal](v5-measurement-preparation.md),
  [authorship](v5-holdout-authoring-note.md) and
  [validation](v5-holdout-validation-note.md).
- Final suite SHA-256:
  `20365d175afe198e226e80bb1e096eb2685e8ea91e4dd7f9f1a8497a750416ad`.
  Separate seal commit: `956b481d`. Zero lexical-overlap hits across 959 historical
  questions at token Jaccard 0.8; no semantic/statistical independence claim.
- Execution: 2026-09-30 22:28:58.348532 to 23:07:40.941347 UTC, about 38 minutes
  43 seconds including grading and durable accounting. Real local `POST /query`
  requests used demo identities, Northstar project scope, vector/lexical reranking,
  top-k 5 and candidate limit 20 against `proofbase_eval_phase73`.
- No retry, resume, dropped failure, reference edit or runtime repair occurred
  after execution started. All original v4 results, source notes, receipts,
  unknown-outcome flags and cost records remain unchanged.

## Observations and coverage

Read [all 60 questions, facts and saved answers](v5-case-review.md),
[all-case primary-agent source inspection](v5-source-review.md) and the
[machine report](../../data/evaluation/current-runtime-v5/public-report.json).

The 32 completed rows contain 18 recorded passes, 12 failures and 2 unresolved
outcomes. Case 005 has a completeness/behavior disagreement; case 017 has an
invalid final review after its 4,096-token output allowance was used for reasoning
with empty response content. Its usage settled normally. Case 033 has saved
claims/coverage responses but no final review or composite. No score is inferred
for it or the 27 unexecuted cases.

Application observations include stronger-than-source modality, unsupported
consequences/benefits, unnecessary abstention after numeric validation, missed
memory context, adjacent-policy substitution and not-found responses where access
refusal was expected. Inspection findings concern question/reference scope in
005/020, contextual-role claim extraction in 013, and omitted document-title
context in 017's preliminary claim judgment. All original labels remain intact.

Quotation fidelity is separate: 20 pass, 3 fail and 9 not applicable among the
32 completed rows. Citation support checks full authorized chunks; an exact but
truncated fallback excerpt can pass quotation fidelity without being a complete
display of the claim's evidence. That metric is not a snippet-usability score.

All 33 saved requests returned HTTP 200 with zero recorded unauthorized evidence
or scope flags. Completed coverage is factual 8, multi-document 10, memory 8 and
permissions 6; one additional permission answer is saved but ungraded. The
remaining three permission cases and all dedicated ambiguity, missing-information,
injection, conflicting-policy and upload-isolation cases were unexecuted. Both
upload fixtures remain unexecuted. Every case has null department scope.
This prefix cannot establish the full zero-leakage gate or production security.

Application latency across all 33 saved responses: median **23.10 seconds**,
p95 **37.89 seconds**. The frozen main report uses only its 32 completed rows
(median 23.62 seconds); the separate capture supplement exposes both the broader
saved-response denominator and all unfinished evidence. Grading and fixture
indexing are excluded from these latency measurements.

## Costs and stopping boundary

| Accounting item | Value |
| --- | ---: |
| New calls | 279, all settled |
| Operations | 128 application chat, 53 embeddings, 98 grader |
| Attempt's estimated usage | USD 1.75748926 |
| Shared additional conservative accounting | USD 9.87823685 of 10.00 |
| Remaining headroom | USD 0.12176315 |
| Blocked review's required reservation | USD 0.14052250 |
| Full cumulative history | 3,474 attempted calls; USD 20.73393762 |
| New unknown outcomes | 0 |

The final review reservation exceeded remaining headroom by USD 0.01875935.
It was rejected before writing a started call or contacting the provider and
is not counted as a call or charge. The
[offline reconstruction](../../data/evaluation/current-runtime-v5/budget-stop.json)
binds its request hash to the saved initial responses and frozen transport; it is
explicitly not a provider receipt. The execution ledger remains budget-exhausted.

All 3,195 prior call records are retained verbatim; all 279 new records append
once. Additional accounting still includes earlier conservative reservations and
the original v4 timeout's full USD 0.146775. That historical provider outcome
remains unknown under the user's narrow carry-forward authorization. These are
usage estimates and reservations, not invoices. No ceiling, model, output cap,
retry rule or evaluation gate was relaxed, and no new spending is authorized.

## Reproduction and verification

```powershell
python scripts/report_phase73_v5.py --check
python scripts/report_phase73_v5_capture.py --check
python scripts/report_phase73_interruption.py --check
python -m unittest scripts.test_phase73_v5_capture_report
```

These are offline checks; no API calls or database access are needed. The frozen
main reporter replays qualification/custody, all complete judgments and reducers,
every new receipt and charge, the historical prefix and shared-spend snapshot.
The new capture supplement binds all 315 run artifacts, supporting records,
unfinished captures, request scopes, category counts and all-response latencies.
Four focused controls pass for partial denominators, unfinished-response tampering,
wrong scope and refusal to snapshot a running attempt. The suite and original
interruption replay remain intact; unchanged frozen runner tests are reused.

Source inspection covers all 33 saved answers and leaves the publication gate
rejected. The public page retains original v4 evidence separately. No human
adjudication, independent security assessment, cloud deployment or numerical
before/after improvement is claimed. Unrelated tracked request-log edits remain
excluded and their pre-existing content hash is unchanged.

Publication verification passed for this working diff: all three offline report
checks above, four capture controls, compilation of the two new Python modules,
local Markdown links, and `npm run build` in `apps/web`. Browser smoke confirmed
that the Admin page displays the correct partial counts, costs, rejected source
gate and separate original evidence; Employee access remains denied. The original
demo identity was restored and both temporary servers were stopped. The browser
check used an empty API key and isolated logs, with no additional paid calls.
The 258-file frozen inventory and ledger snapshots match; generated case inventory
checks cover all 60 questions, 33 answers and 32 dimension tables.

Semantic review covered the complete intended publication diff, including the
new capture helper, all source-inspection rows, raw evidence through offline
receipt/reducer replay, documentation and UI claims. No blocking publication-code
finding remains; the four evaluation concerns remain explicitly unresolved.
The unchanged 17 frozen runner controls are reused. No benchmark/schema change,
Docker image build, cloud deployment or further live evaluation was performed.

## Continuation boundary

This exposed suite cannot be resumed, selectively regraded or relabeled. The
remaining USD 0.12176315 cannot fund even its blocked review reservation, and no
additional allowance is inferred. A future full measurement requires addressing
the documented evaluation/reference concerns under applicable qualification
gates, a new freeze and freshly isolated/sealed cases with an adequate authorized
budget. No production roadmap or additional paid cycle is started automatically.
