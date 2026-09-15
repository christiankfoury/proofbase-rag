# Saved-answer reanalysis by dimension

This reanalyzes the same Phase 65 responses. It is **not a new application run**, human review, or an improvement measurement. The original 33/60 (55.0%) protocol result is unchanged. There is deliberately no composite pass rate.

Processed: 60/60. Invalid grader outputs: 2. Unresolved means the evaluator could not establish a judgment; it is neither a pass nor a proven factual error.

| Dimension | Pass | Fail | Unresolved | Not applicable |
|---|---:|---:|---:|---:|
| Factual support in available evidence | 32 | 1 | 7 | 20 |
| Required-fact coverage | 30 | 5 | 6 | 19 |
| Relevance to the question | 41 | 13 | 6 | 0 |
| Support in cited chunks | 32 | 2 | 6 | 20 |
| Contiguous quotation formatting | 30 | 4 | 0 | 26 |
| Meaning of response behavior | 48 | 6 | 6 | 0 |

Factual-support failure means the model judged at least one assertion contradicted by the available authorized evidence. Unsupported additions without contradictory evidence remain unresolved. A factually supported answer can still answer the wrong question or omit required facts. Pure non-answers have no factual claims to assess. Citation support uses full cited chunks, while quotation formatting checks the displayed excerpt separately. These are model judgments, not human labels.

## Cases flagged by the model (not confirmed errors)

- Factual support in available evidence failures: [fresh-010](case-review.md#fresh-010).
- Required-fact coverage failures: [fresh-010](case-review.md#fresh-010), [fresh-019](case-review.md#fresh-019), [fresh-022](case-review.md#fresh-022), [fresh-036](case-review.md#fresh-036), [fresh-050](case-review.md#fresh-050).
- Relevance to the question failures: [fresh-019](case-review.md#fresh-019), [fresh-031](case-review.md#fresh-031), [fresh-033](case-review.md#fresh-033), [fresh-037](case-review.md#fresh-037), [fresh-040](case-review.md#fresh-040), [fresh-041](case-review.md#fresh-041), [fresh-043](case-review.md#fresh-043), [fresh-044](case-review.md#fresh-044), [fresh-045](case-review.md#fresh-045), [fresh-046](case-review.md#fresh-046), [fresh-047](case-review.md#fresh-047), [fresh-059](case-review.md#fresh-059), [fresh-060](case-review.md#fresh-060).
- Support in cited chunks failures: [fresh-026](case-review.md#fresh-026), [fresh-058](case-review.md#fresh-058).
- Contiguous quotation formatting failures: [fresh-001](case-review.md#fresh-001), [fresh-011](case-review.md#fresh-011), [fresh-015](case-review.md#fresh-015), [fresh-018](case-review.md#fresh-018).
- Meaning of response behavior failures: [fresh-019](case-review.md#fresh-019), [fresh-033](case-review.md#fresh-033), [fresh-045](case-review.md#fresh-045), [fresh-047](case-review.md#fresh-047), [fresh-050](case-review.md#fresh-050), [fresh-060](case-review.md#fresh-060).
- Unresolved in one or more dimensions: fresh-021, fresh-029, fresh-048, fresh-051, fresh-052, fresh-053, fresh-058.

## Semantic audit warning

**This reanalysis is not reliable enough for release gating or a factual-error headline.** Agent inspection disputes the lone model factual-failure label (fresh-010), a completeness pass (fresh-012), a citation failure on a pure refusal (fresh-026), and behavior failures for appropriate non-answers (fresh-045 and fresh-060). The wrong-topic finding in fresh-019 is confirmed by source/context inspection. These examples are not exhaustive. The raw model labels remain unchanged; do not treat their counts as confirmed errors. See [agent findings](../../data/evaluation/dimension-reanalysis-v1/agent-review.json).

## Custody and limitations

The first aggregation failed on Windows because JSON was read with the platform default encoding. UTF-8 byte comparison found four mismatched model inputs (fresh-048, 051, 052, 053). Those saved judgments remain immutable but their semantic dimensions are unresolved. No retries were made. The new offline publisher reads explicit UTF-8 and validates the exact known mismatch; any other input difference fails verification.

[Per-case questions, expected facts, actual answers and judgments](case-review.md) | [Design and calibration history](design.md) | [Original result](../phase-65/results.md) | [Machine-readable reanalysis](../../data/evaluation/dimension-reanalysis-v1/report.json)

Evaluator: `answer-dimensions.v5`. Final visible calibration passed 12/12 after four preserved failed attempts; this is development calibration, not held-out grader accuracy. The evaluator was frozen before reanalysis. It has already been informed by the original failures, so this exposed suite cannot establish evaluator generalization.

Claim verification cannot see the question or expected facts. It checks all answer assertions against authorized saved chunks and verified role-authorized reference quotes. A separate call compares answer meaning with required facts and conversation context. Gold quotes cannot establish citation support. Neither call sees the old grades. The available evidence is not an exhaustive world model; lack of support does not establish falsity.

The user accepted prior agent observations, but no individual human decisions were supplied. That agreement is not recorded as completed human adjudication. Model judgments and the original review fields remain separate.

Cumulative API token-cost estimate: $0.568773; this phase including calibration: $0.122047. The original $0.75 shared ceiling remains enforced. No new application queries or embeddings were made.

Offline checks: `python scripts/report_dimension_reanalysis.py --check` (explicit UTF-8 and input-integrity accounting). These reproduce hashes, input boundaries, grading contracts and totals, not semantic truth. Original checks remain `python scripts/report_fresh_eval.py --check` and its `--archive` variant. No selective retries or original-row edits are permitted.
