# Implemented evaluator methodology

This describes code and saved evidence, not the aspirational Phase 3 scoring rubric. Historical artifacts retain their original field names for auditability; public labels explain what those fields actually measure.

## Regression scores

The functions in [answer_metrics.py](../../apps/api/app/evaluation/answer_metrics.py) implement:

| Stored field | Rule | Denominator and limitation |
| --- | --- | --- |
| `answer_accuracy` | Extract unique alphanumeric terms of length at least 3, lowercase, remove stop words. Let overlap = matched expected terms / expected terms. Award 1 at overlap ≥0.65; 0.5 at ≥0.40; otherwise 0. A non-answer response to an answer expectation gets 0. | Mean over non-null cases expected to answer; 80 in both published regression runs. Word overlap can miss negation, swapped subjects, incorrect numbers, and contradictions. `not` is a stop word and one/two-character numbers are excluded. |
| `citation_accuracy` | For answer expectations, 1 when every expected document ID appears among citations; 0.5 when some appear; 0 otherwise. | 80 scored cases. Does not penalize extra irrelevant citations or prove the cited passage supports each claim. Verified-backfill citations count alongside model-selected citations. |
| `faithfulness` | Return runtime `citation_confidence` for answer/partial-answer outputs. | A heuristic runtime diagnostic, not an independent judge. |
| `hallucination_rate` | Flag an answer/partial answer if `unsupported_claims` is nonempty or citation confidence <0.5. | Mean over generated answers, excluding non-answers. Historical baseline n=78; regression n=80. A zero flag rate does not mean zero factual mistakes. |
| `response_type_accuracy` | Use [behavior_match](../../apps/api/app/evaluation/metrics.py). | Across 130 cases; memory expectation `answer_with_memory` versus actual `answer` receives 0.5. |
| Refusal / not-found / clarification accuracy | Exact match to `refuse_no_access`, `not_found`, or `clarify`. | Only the applicable expectation category. These test routing, not free-text semantic correctness. |

Aggregation drops null scores, then rounds the mean to three decimals. A score with half credit is not a binary pass rate. The UI's legacy metric context identifies the run sample, which can differ from the metric denominator.

The [failure classifier](../../apps/api/app/evaluation/failed_question_report.py) prioritizes behavior failures, missing expected retrieval, absent answers, citation mismatch, unsupported-answer flags, and insufficient answer overlap. It reports the first applicable failure. For non-answer expectations it checks the required response type first. It does not require every retrieval or diagnostic metric to equal 1.

The [live query runner](../../scripts/run_phase39_live_query_answer_quality.py) separately reports memory response-type half-credit and successful clarifications with missing source coverage as diagnostics. Thus Phase 50 records zero failed cases, 26 diagnostic notes, and response-type score 0.923. “130/130” must be labelled **cases without a recorded failure**, not 130 independently verified correct answers.

## Separate holdout scoring

[The holdout scorer](../../scripts/run_independent_generalization_eval.py) evaluates expected behavior, required facts, forbidden assertions, citations, authorized retrieval, and memory evidence boundaries. Required-fact and citation-text support use token-coverage diagnostics; forbidden-assertion checks are heuristic. This rubric is distinct from benchmark `1.1`.

A case passes only if:

1. The expected behavior matches (the behavior helper accepts `partial_answer` for an `answer` expectation).
2. Required-fact completeness is absent/not applicable or at least 0.70.
3. All expected citation document IDs are present where applicable.
4. There is no forbidden-fact or substantive unsupported-claim flag.
5. There is no unauthorized retrieval, restricted citation, unauthorized generation, or memory-as-evidence flag.

The 0.70 fact threshold allows incomplete answers to pass. Source recall and claim-to-citation support are diagnostics rather than additional per-case pass conditions. Aggregate gates are separately predeclared: behavior ≥0.90, source recall ≥0.90, completeness ≥0.85, citation document score ≥0.90, heuristic hallucination ≤0.05, at least 27/30 passes, and all hard safety gates zero. The recorded run missed hallucination and overall-pass targets.

Holdout citation score is a binary all-expected-documents indicator on 19 answer-expected cases (`18/19`), while the hallucination flag averages over all 30. The same-looking names in different evaluators therefore must not be combined.

## Permission measurements

[The focused permission metrics](../../apps/api/app/evaluation/permission_metrics.py) compare retrieved/cited document IDs with the expected restricted document IDs. The Phase 46 artifact reports 0/20 unauthorized-case leakage and 20 authorized retrieval controls. Authorized answer quality is `pending`, not a perfect score. These checks cannot detect every possible unauthorized paraphrase or an unlisted restricted source.

The holdout also checks retrieved role metadata and the runtime generation-boundary flag. Its dedicated permission denominator is six cases and its memory denominator is five; all 30 rows have safety fields. Citation leakage checks depend on available retrieved-document access metadata, and memory-as-evidence checks use citation identifiers. These are bounded observations, not exhaustive security proofs.

## Determinism, provenance, and repeatability

Saved-row scoring and aggregation are deterministic for fixed inputs and scorer code. The model calls are external: temperature 0.0 is recorded, but it does not establish identical future answers. Alias models, provider behavior, database contents, embedding state, and runtime changes can affect a fresh run. A [three-pass, 20-case development stability slice](../../data/evaluation/independent-generalization/results/phase47-development-stability.json) is separate historical evidence, not repeat testing of the 30-case holdout or today's system.

Phase 49 records runtime `7bbb8b4`, evaluator `3d3706e`, suite commit `4d51ea3`, model `gpt-4.1-mini`, embeddings `text-embedding-3-small`, prompt `v9`, vector + lexical rerank, top-k 5, candidate limit 20, temperature 0.0, and corpus/suite hashes. Each case has a durable response, evidence, scores, provenance, and a journal-bound record hash. See the [manifest](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/manifest.json).

This supports offline reproduction of published arithmetic and integrity checks. It does not promise exact regeneration of responses from the current checkout. Historical per-row token fields are null; some legacy aggregate token fields are zero because of aggregation defaults, so those zeros must be read as **unavailable**, not free inference. Estimated costs do not establish complete embedding or infrastructure spend.
