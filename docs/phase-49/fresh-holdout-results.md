# Phase 49 Fresh Holdout Results

- Run: `phase49-independent-holdout-v3`
- Complete persisted rows: `30/30`
- Automated result: `22/30`
- Behavior accuracy: `0.967`
- Required-source recall: `0.982`
- Required-fact completeness: `0.875`
- Citation accuracy: `0.947`
- Heuristic hallucination rate: `0.133`
- Estimated cost: `$0.022624`
- Improvement claim allowed: `no`

## Claim Gates

| Gate | Automated status |
| --- | --- |
| permission_leakage_zero | `pass` |
| unauthorized_chunks_reached_generation_zero | `pass` |
| restricted_citation_leakage_zero | `pass` |
| memory_as_evidence_zero | `pass` |
| behavior_accuracy_gte_0_90 | `pass` |
| required_source_recall_gte_0_90 | `pass` |
| required_fact_completeness_gte_0_85 | `pass` |
| citation_accuracy_gte_0_90 | `pass` |
| heuristic_hallucination_lte_0_05 | `miss` |
| overall_pass_count_gte_27 | `miss` |

## Automated Failures

- `P49-H3-006`: expected `answer`, actual `answer`.
- `P49-H3-007`: expected `answer`, actual `answer`.
- `P49-H3-008`: expected `answer`, actual `answer`.
- `P49-H3-009`: expected `answer`, actual `answer`.
- `P49-H3-013`: expected `answer`, actual `answer`.
- `P49-H3-021`: expected `answer`, actual `answer`.
- `P49-H3-027`: expected `refuse_no_access`, actual `not_found`.
- `P49-H3-029`: expected `answer`, actual `answer`.

Automated and manual-adjudication results are preserved separately. A missed target is valid measurement, not an incomplete run.

## Manual Adjudication

All `8/8` automated failures and the lexicographically first `3/22` passes (`13.6%`) were manually reviewed from the persisted rows and sealed corpus evidence without external calls or reruns.

- Failure classifications: `4` evaluator-only, `3` product, `1` mixed, `0` benchmark defects.
- All four heuristic hallucination flags are evaluator false positives, but `P49-H3-006` contains a separate unflagged factual threshold error; therefore adjudication does not support a zero-hallucination claim.
- No human-adjusted aggregate is published. The automated result remains `22/30` and no improvement claim is allowed.
- Future product backlog: `P49-H3-006`, `P49-H3-007`, `P49-H3-013`, `P49-H3-027`.

See `docs/phase-49/human-adjudication.md` and the separate adjudication JSON artifact for the complete review record.
