# Evaluation evidence: start here

Proofbase has a useful regression benchmark, but it does **not** establish 100% real-world answer or citation accuracy. The benchmark was authored and checked by the project author with AI assistance, and used repeatedly during development. Its automated scores use heuristics.

The clearest evidence of that limit is the separately authored Phase 49 holdout: **22/30 automated passes (73.3%)**, with eight failures available for inspection. This is a historical result against runtime `7bbb8b4`, not a measurement of today's runtime. Later runtime work has no new executed sealed holdout supporting a current generalization claim.

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
