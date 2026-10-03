# Evaluation evidence: start here

The current [planning handoff](../roadmap/application-reliability-plan.md) records
post-measurement fixes and small component/application diagnostics through
`65e6650f`. None replaces the full-suite evidence below. Policy-fact v6 has three
untested live negative controls and is not accepted; conversational v5 is closed.
The user wants to discuss a 75% milestone; the existing 48/60 release gate remains
unchanged. No validated current-runtime overall accuracy is available.

The latest [Phase 73 v6 run](../phase-73/v6-results.md) completed all 60 cases
once: 28 recorded model passes, 21 failures and 11 unresolved. Seven
[source-inspection findings](../phase-73/v6-source-review.md) reject the publication
gate, so there is no validated full-suite score and the 48/60 target was not met.
Zero unauthorized retrieval/disclosure was observed across the executed role and
project cases; this is bounded synthetic evidence, not production assurance.
[Inspect all cases](../phase-73/v6-case-review.md). Offline checks:
`python scripts/report_phase73_v6.py --check` and
`python scripts/report_phase73_v6_capture.py --check`.

The previous [Phase 73 successor](../phase-73/v5-results.md) stopped at the spending
guard: 32/60 evaluation rows complete, 33 responses saved, 27 unexecuted. The
18 passes, 12 failures and 2 unresolved outcomes are partial-prefix model counts,
not a full-suite score. Four inspection concerns and incomplete safety coverage
remain. [Every case](../phase-73/v5-case-review.md) and
[source inspection](../phase-73/v5-source-review.md) preserve all observations.
Offline checks: `python scripts/report_phase73_v5.py --check` and
`python scripts/report_phase73_v5_capture.py --check`. Shared additional
accounting is USD 9.87823685 of 10; no extra budget was inferred.

The [original Phase 73 timeout](../phase-73/results.md), its 10 completed rows,
11 saved responses and retained unknown reservation remain unchanged.
Verify that evidence with `python scripts/report_phase73_interruption.py --check`.

Proofbase has a useful regression benchmark, but it does **not** establish 100% real-world answer or citation accuracy. The benchmark was authored and checked by the project author with AI assistance, and used repeatedly during development. Its automated scores use heuristics.

The separately authored Phase 49 holdout recorded **22/30 automated passes (73.3%)**, with eight failures available for inspection. This is a historical result against runtime `7bbb8b4`, not a measurement of today's runtime. The [fresh frozen-runtime experiment](../phase-65/results.md) reports its execution status separately with a stronger rubric and pending named-human review. Its percentage must not be presented as a before/after improvement over Phase 49.

| Reviewer question | Evidence |
| --- | --- |
| What was tested, and who labelled it? | [Dataset card](dataset-card.md), [130 questions and expected answers](../../data/evaluation/benchmark-questions.json), [synthetic documents](../../data/synthetic-documents) |
| What exactly counts as accuracy? | [Implemented methodology](methodology.md), including formulas, exclusions, and pass rules |
| What failed? | [Failure taxonomy and concrete examples](failure-taxonomy.md), [all eight holdout failures](../../data/evaluation/independent-generalization/results/phase49-independent-holdout-v3-failures.json) |
| Can I check the numbers without buying API calls? | [Reproduction instructions](reproducing-results.md), [offline verifier](../../scripts/build_evaluation_evidence.py), [generated report](../../data/evaluation/public-evidence.json) |
| Was the reviewer independent? | Project-author review and isolated holdout-authoring/validation roles are disclosed separately below. No external expert assessment or inter-rater agreement is established. |

## Results and denominators

These values come from committed rows and are checked by `python scripts/build_evaluation_evidence.py --check`.

| Measure | Historical baseline | Historical regression | Meaning |
| --- | ---: | ---: | --- |
| Expected-answer overlap score | `0.850` (68 score points / 80 scored cases) | `1.000` (80 / 80) | Mean heuristic score, with possible half credit; excludes 50 non-answer cases |
| Expected-document citation score | `0.844` (67.5 / 80) | `1.000` (80 / 80) | Expected document presence, not claim-level correctness |
| Heuristic unsupported-answer flag rate | `16/78` (`0.205`) | `0/80` | Only generated answers/partial answers are scored; denominator changes with behavior |
| Recorded failure cases | `43/130` | `0/130` | Historical runner's failure rules; not all submetrics must be perfect |
| Raw response-type score | See generated report | `0.923` across 130 | Memory `answer_with_memory` expectations get half credit for API behavior `answer` |

Baseline: `phase32-expanded-answer-generation-v5`; regression: `phase50-manual-findings-regression`; both use benchmark `1.1`. The baseline uses direct generation; the later run exercises `POST /query`, including orchestration and memory. This is a development history with changing prompts, retrieval, and request paths, not a controlled single-variable experiment. The later run also retains **26 diagnostic notes** despite zero failure cases. Neither run is the latest runtime.

| Separate evidence | Result | Scope |
| --- | ---: | --- |
| Phase 49 v3 automated holdout | `22/30` (`73.3%`) | Missed the predeclared `27/30` target |
| Holdout expected-document citation score | `18/19` (`0.947`) | 19 answer-expected cases; not all 30 |
| Holdout heuristic hallucination flags | `4/30` (`0.133`) | Different scoring and denominator from the regression flag rate |
| Phase 46 focused unauthorized tests | `0/20` observed leakage cases | 20 separate authorized retrieval controls; authorized answer quality was not measured |
| Holdout safety | Zero recorded flags across 30 rows | Dedicated permission aggregate uses 6 cases; memory-as-evidence aggregate uses 5 |

Zero observed violations in a small, designed synthetic suite is a test outcome, not a probability bound or security guarantee. The cases are not a random sample of enterprise traffic. We do not attach population confidence intervals or imply statistical significance.

## Review and independence

The project author confirmed benchmark authoring and checking with AI assistance on 2026-09-14. Benchmark `1.1` does not preserve per-label human identities, timestamps, second-reviewer decisions, or agreement statistics. Those details cannot be reconstructed from scores.

The Phase 49 holdout has an [isolated authoring record](../phase-49/blind-authoring-record.md), a sealed suite, frozen runtime/evaluator commits, and case-level validator role metadata. Here, **separate** means separate from the in-phase runtime-tuning context; it does not mean an external institution or independent human assessor certified the results.

The artifact titled [Human Adjudication](../phase-49/human-adjudication.md) records review findings for all eight failures and three lexicographically selected passes. Its artifact does not establish an independently identifiable human reviewer or inter-rater agreement. Treat it as recorded project review, not independent validation. Four failures were classified evaluator-only, three product, and one mixed. Keep the official automated `22/30`; do not turn partial review into a human-adjusted aggregate.

## Portfolio wording supported by the evidence

> Built a permission-aware RAG application with a public 130-case synthetic regression benchmark and reproducible per-case evaluation evidence. A separate frozen 30-case holdout passed 22 cases (73.3%) under the automated rubric, exposing both product failures and evaluator limitations. Published scoring rules, denominators, failure analysis, provenance, and bounded permission-test results.

An improved headline score requires a newly authored, sealed suite after the candidate runtime is frozen. Preserve Phase 47–49 and Phase 55 seals; do not rerun or tune against them. Independent human assessment remains future work.
