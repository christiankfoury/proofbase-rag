# Reproduce the published evidence

## Latest Phase 73 v6 evidence

```powershell
python scripts/report_phase73_v6.py --check
python scripts/report_phase73_v6_capture.py --check
python -m unittest scripts.test_phase73_v6_capture_report
```

These saved-file checks need no API calls or database. They verify freeze/seal,
qualification, raw receipts, complete historical accounting, all 60 reduced rows,
request scope and artifact hashes. They do not turn model judgments into validated
accuracy: the [source gate](../phase-73/v6-source-review.md) remains rejected.
[Results](../phase-73/v6-results.md) and [all cases](../phase-73/v6-case-review.md)
retain 28 model passes, 21 failures and 11 unresolved, without corrected labels.
Do not rerun/resume the exposed suite or selectively retry grades. A successor
requires applicable qualification, another freeze, newly isolated cases and
adequate authorized headroom; USD 3.79479490 remains below the USD 4.50 launch floor.
Original attempts remain independently reproducible below.

## Previous Phase 73 successor evidence

```powershell
python scripts/report_phase73_v5.py --check
python scripts/report_phase73_v5_capture.py --check
python -m unittest scripts.test_phase73_v5_capture_report
```

These checks use saved files only, without API calls or database access. The frozen
main reporter replays custody, qualification, all completed judgments, every new
usage receipt and the complete cost prefix/shared-spend snapshot. The capture
supplement binds all 315 run artifacts, supporting records and unfinished answers,
checks saved question/project scope and reports all 33 response latencies and
27 unexecuted cases. Its four focused controls cover incomplete denominators,
tampering, wrong scope and refusal to publish a running snapshot.

Read [results](../phase-73/v5-results.md), [cases](../phase-73/v5-case-review.md) and
[inspection](../phase-73/v5-source-review.md). The source gate remains rejected;
replay does not establish semantic infallibility or a full-suite score. The local
budget guard prevented the final review request for case 33 before it was sent.
No new unknown outcome exists. Do not rerun or resume `phase73_v5_run.py`, edit
sealed expectations, clear the budget flag or reduce bounds to fit the balance.
Any successor needs applicable qualification, a new freeze and freshly isolated
cases within a separately adequate authorized allowance. Original evidence follows.

## Original Phase 73 saved evidence

With the repository Python dependencies installed, run:

```powershell
python scripts/report_phase73_interruption.py --check
```

This performs no API or database calls. It checks the committed frozen source,
suite seal, authorized source references, exact grader request/response replay,
dimension reduction, complete historical ledger prefix, every new usage charge,
the retained unknown-call reservation, shared additional-spending snapshot and
published interrupted report. It verifies
preservation and computation, not semantic infallibility. Read the
[results](../phase-73/results.md) and [source inspection](../phase-73/source-review.md)
alongside the machine report. Human adjudication remains false.

The frozen `report_phase73_eval.py` full-run path still rejects the unsettled
ledger. The separate interruption reporter does not bypass that execution gate,
release the reservation, retry a call or qualify the partial result. Focused
controls are `python -m unittest scripts.test_phase73_interruption`.

The one-shot execution command is `python scripts/phase73_eval_run.py --allow-external-ai`.
It refuses an existing run. Do not delete artifacts, edit sealed expectations or
resume this exposed suite. A future measurement requires a separately authorized
work unit, a new freeze, newly isolated cases and preflight. This attempt did not
reach either upload fixture. Historical sections below describe earlier stages;
their then-pending Phase 73 status is not the current tracker.

## Offline: no account, database, or API calls

From a normal repository checkout with Python 3.12, run:

```powershell
python scripts/build_evaluation_evidence.py --check
python -m unittest scripts.test_evaluation_evidence
```

The verifier uses only the Python standard library and pure scoring helpers. It does not load `.env`, import the API, contact OpenAI, execute holdout cases, or modify evidence. `--check` compares its result with the committed [public-evidence.json](../../data/evaluation/public-evidence.json). CI runs the same checks.

It checks:

- Full, unique coverage of both 130-case regression artifacts against benchmark question text and behavior.
- Recomputed answer-overlap and expected-document citation scores against saved answers and citations.
- Means, metric-specific denominators, and recorded failure counts against summaries.
- All 30 holdout case hashes, order, provenance, single-attempt records, journal chain, completion events, final rows, and final hash.
- Holdout saved-score aggregation, failure IDs, category counts, and safety fields.
- All 20 unauthorized permission cases and the corresponding 20 authorized controls.

The report records canonical-JSON hashes, portable across Windows/Linux checkout line endings. These are reproducibility fingerprints for the report, not replacements for the original raw-byte suite seals. Integrity against committed hashes does not prove external authenticity or semantic correctness. The verifier reaggregates saved holdout scores; it does not rescore facts or create a new generalization measurement.

To intentionally regenerate the report after reviewing a change to its inputs or reporting code:

```powershell
python scripts/build_evaluation_evidence.py
git diff -- data/evaluation/public-evidence.json
```

Do not change historical rows, pass flags, or sealed expectations to make this check pass. Investigate discrepancies instead.

## Evidence paths

| Artifact | Where to inspect |
| --- | --- |
| Benchmark and expected labels | [benchmark-questions.json](../../data/evaluation/benchmark-questions.json) |
| Baseline per-case answers and scores | [Phase 32 raw artifact](../../data/evaluation/expanded-baseline/phase32-expanded-answer-generation-v5.json) |
| Regression per-case answers and scores | [Phase 50 raw artifact](../../data/evaluation/expanded-baseline/phase50-manual-findings-regression.json) |
| Focused permissions | [Phase 46 unauthorized and authorized rows](../../data/evaluation/phase46-permission-evaluation.json) |
| Holdout configuration and custody | [Manifest](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/manifest.json), [authoring record](../phase-49/blind-authoring-record.md) |
| Holdout durable responses | [Case records](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/cases), [final aggregation](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/final.json), [journal](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/journal.jsonl) |
| Later regression raw data | [Retention index](../../data/evaluation/raw-artifact-index.json), [historical recovery instructions](../evaluation-artifact-retention.md) |

Phase 50 is used for the public offline example because its full 130 rows remain in the current tree. Phase 54's compact regression remains available, but its raw payload was retired to Git history. Neither result measures the current runtime.

## Fresh development run: a different operation

A live run requires the normal local installation, migrated/seeded PostgreSQL database, indexed synthetic corpus, and configured OpenAI credentials. Follow the [README setup](../../README.md#docker-quickstart). Ingestion itself uses paid embeddings. Record the runtime commit, corpus/index state, model, prompt, configuration, and new run ID before running.

Preview the request inventory without calling the provider:

```powershell
python scripts/run_phase39_live_query_answer_quality.py --dry-run --run-id reviewer-development --question-filter all --prompt-version v8 --retrieval-mode vector_lexical_rerank --top-k 5 --multi-doc-mode auto --output-json data/evaluation/local-runs/reviewer-development.json --eval-run-json data/evaluation/local-runs/reviewer-development-summary.json --report-path data/evaluation/local-runs/reviewer-development.md
```

After deliberately approving the external calls, remove `--dry-run` and add `--allow-external-ai --budget-usd 2` to that command. The runner's estimate/budget is not a billing cap covering every embedding, auxiliary model call, or infrastructure charge. Use a unique run ID/output paths for subsequent runs. Local outputs in this example are ignored by Git and do not replace the official dashboard artifacts.

This tests the current runtime on **known development questions**. It cannot reproduce the frozen historical environment merely by selecting the same prompt name. Do not execute or selectively rerun the Phase 47–49 or Phase 55 holdouts. A future generalization measurement requires a new runtime freeze, separately authored and sealed suite, predeclared scoring and budgets, and one complete run.


## Phase 68 saved-evidence replay

Run `python scripts/report_current_eval.py --check` to check the recorded runtime
revision, suite seal, per-case hashes, authorized evidence, exact UTF-8 grader
inputs, raw grader-call replay, separated counts and publication artifacts.
No API key or application service is used by this command. Tests are
`python -m unittest scripts.test_current_dimension_grader scripts.test_current_eval_integrity`.

`python scripts/current_eval_run.py --allow-external-ai` is the one-shot execution
entry point. It refuses an existing run folder; do not delete the folder or
change the seal to repeat the experiment. A new live measurement needs newly
frozen code/configuration/index and a newly authored suite. Current DB state is
not expected to equal the pre-run fingerprint after upload fixtures execute.


## Phase 71 bounded evaluator evidence

The historical v14 correction is replayed offline with
`python scripts/report_quality_completion_v14.py --stage diagnostic` and
`python scripts/report_quality_completion_v14.py --stage calibration`.
Its diagnostic matched 12/12 and full calibration matched 24/24 dimensions plus
3/3 reviewer probes, but [source inspection](../phase-71/v14-source-review.md)
found an incorrect underlying coverage status that reduced to the expected failed
dimension. Reproduction of dimensional agreement does not establish semantic
readiness. The source-inspection gate failed; no v14 confirmation or new runtime
holdout was authored. Historical v13 evidence below remains unchanged.

These commands replay saved evaluator requests/responses, source spans, dimension
reducers and costs without API calls or application services:

```powershell
python scripts/report_quality_completion.py --candidate v12 --stage calibration
python scripts/report_quality_completion.py --candidate v13 --stage calibration
python scripts/report_quality_confirmation_v13.py
```

V12 finished 22/24 exact development cases; the sole repair, v13, finished 24/24
and 3/3 reviewer probes. Fresh isolated confirmation finished 15/16 exact cases.
[Source inspection](../phase-71/confirmation-source-review.md) identifies a
reference-validation defect; the sealed expectations are not corrected after
execution. Reproduction verifies recorded outcomes, not semantic infallibility.
The confirmation gate failed, so no Phase 73 runtime holdout or new overall score
exists. Do not rerun live execution or tune against these exposed cases.


The subsequently authorized single replacement uses the same frozen evaluator and
new reference-consistency checks. Replay it with
`python scripts/report_quality_confirmation_replacement.py`. It also finished
15/16, with a different [semantic interpretation disagreement](../phase-71/confirmation-replacement-source-review.md).
Both confirmation suites and reference approvals remain unchanged. Phase 73 is
still blocked; neither report establishes a new application quality score.


## Standing-autonomy v15 evidence

Replay v15 development with `python scripts/report_quality_v15_recovery.py --stage diagnostic`
and `--stage calibration`: 17/17 + 1/1 and 24/24 + 3/3, with separate passing
source inspection. The recovery retains and reconciles the original local-write
interruption without replaying a provider call. Replay its fresh confirmation
with `python scripts/report_quality_confirmation_v15.py`: 15/16, failed readiness.
[Source review](../phase-71/confirmation-v15-source-review.md) explains the actor
assignment defect. Frozen references and judgments are not changed. The new
standing workflow permits cause-driven v16 remediation; it does not convert this
failure into a pass or authorize reuse of the exposed suite for a fresh claim.
