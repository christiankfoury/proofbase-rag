# Phase 68 fresh runtime results

Status: **complete**; 60/60 cases. Runtime `89b5a38`; evaluator `answer-dimensions.v6` / `gpt-4.1-2025-04-14`.

Model judgments on 60 agent-authored synthetic cases, not human-verified accuracy. Distinct suite and evaluator; no controlled before/after claim. Invalid grades unresolved; quotation formatting separate.

Source inspection found semantic grader errors: a false factual-error finding, missed omissions, citation penalties on pure refusals, and confusion between clarification, not-found and access refusal. Counts are diagnostic model labels, not an approved release gate. See the separate agent review; raw judgments remain unchanged.

Expected behaviors: answer 38, clarify 6, not_found 9, refuse_no_access 7.

Author-assigned difficulty: hard 26, medium 34. These labels are not externally calibrated.

| Dimension | Model pass | Model fail | Unresolved | Not applicable |
|---|---:|---:|---:|---:|
| factual support | 30 | 1 | 0 | 29 |
| completeness | 30 | 8 | 0 | 22 |
| relevance | 60 | 0 | 0 | 0 |
| citation support | 29 | 2 | 0 | 29 |
| quotation fidelity | 24 | 6 | 0 | 30 |
| response behavior | 52 | 8 | 0 | 0 |

Schema/reference-invalid grades: 0. This does not count semantic disagreements described in the agent review. Cases with recorded permission/scope or HTTP safety flags: 0.

Response-type metadata differs from the expected label in: fresh-003, fresh-007, fresh-010, fresh-011, fresh-013, fresh-014, fresh-018, fresh-019, fresh-022, fresh-025, fresh-030, fresh-032, fresh-034, fresh-036, fresh-041, fresh-049, fresh-050, fresh-051, fresh-054, fresh-055, fresh-057. A metadata mismatch alone is not a factual-error judgment; inspect the actual response meaning.

Estimated cumulative API token cost: USD 1.196894; this holdout adds USD 0.543039; approved cumulative cap USD 2.00.

A pass is a model judgment under the dimension rubric. Unknown claims and invalid grades remain unresolved. No population accuracy, independent human labeling, production safety, or deterministic model-output claim is made.

Reproduce saved-evidence verification with `python scripts/report_current_eval.py --check`. The execution script refuses to rerun a started suite. A new live measurement requires a new freeze and new suite.

See [source inspection and grader disagreements](agent-review.md), [methodology and known development limitation](preflight.md), [case evidence](case-review.md), [sealed dataset](../../data/evaluation/current-runtime-v3/holdout.json), [freeze](../../data/evaluation/current-runtime-v3/freeze.json), and [raw run manifest](../../data/evaluation/current-runtime-v3/run/manifest.json).
