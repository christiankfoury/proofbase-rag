# Phase 48 Root-Cause Matrix

This matrix classifies all 16 failures from the one-time Phase 47 holdout. It is remediation input, not a license to modify or rerun that holdout.

| Root cause | Count | Adjudication class | General remediation | Verification |
| --- | ---: | --- | --- | --- |
| Negation-, polarity-, or number-insensitive fact scoring | 5 | Evaluator-only | Proposition-aware deterministic scoring: explicit yes/no handling, canonical terms, exact numeric agreement, and negation/supersession checks | Synthetic scorer unit cases plus unchanged development suite |
| Missing decision-variable clarification | 4 | Mixed | Intent-and-slot clarification for approval, support tier/severity, AI/data handling, and remote location/duration decisions | Paraphrased local tests and fresh holdout |
| Incomplete multi-source retrieval or evidence use | 3 | Mixed/product | Clause/domain source planning, coverage-first merge, and sentence-level citation backfill | Multi-source local tests, benchmark regression, fresh holdout |
| Correction-aware long-memory topic resolution | 1 | Product | Recency-first topic resolution with explicit correction and earlier-topic references | Multi-turn local tests, memory regression, fresh holdout |
| Restricted intent returned `not_found` instead of a generic refusal | 3 | Product | General restricted-intent classification before generation without exposing document existence or contents | Permission pairs, hard-gate regression, fresh holdout |

## Failure Accounting

- Evaluator-only failures: `5`.
- Mixed evaluator/product failures: `6`.
- Primarily product behavior failures: `5`.
- Benchmark defects: `0`.
- Human-confirmed unsupported factual claims among the ten Phase 47 heuristic hallucination flags: `0`; this does not establish a universal zero hallucination rate.

## Guardrails

- No Phase 47 holdout question, answer, case ID, or expected-source list may appear in runtime rules or tests.
- General tests use newly written paraphrases and synthetic variations.
- Memory remains query context and never source evidence.
- Permission filtering remains before generation, and refusals remain generic.
- Missing requested sources remain a completeness/citation failure even when emitted citations correctly ground the narrower answer.
