# Failure taxonomy and review examples

Keep automated failure labels, product findings, and evaluator defects separate. The original automated outcome remains official even when review identifies a scoring error. The report reproduces historical labels; it does not silently reclassify old results with a new evaluator.

For the [fresh run](../phase-65/results.md), `required_fact_incorrect_or_missing` covers omissions/contradictions; `unsupported_claim` and `irrelevant_citation` assess exact passage support; `citation_quote_not_in_chunk` rejects text that is not one contiguous normalized excerpt of the cited chunk (including stitched genuine sentences, not only invented quotes); `citation_not_in_authorized_retrieval` rejects unmatched evidence; `behavior_mismatch`/`behavior_semantics` cover incorrect response behavior; `forbidden_assertion` flags prohibited disclosure; schema/coverage/uncertainty failures mean the evaluator cannot establish a pass. Raw records preserve the fact- and claim-level reasons. Infrastructure interruption is a separate incomplete-run status, never a silently excluded failure or a full-suite score.

| Failure family | Evidence to inspect | Recorded example |
| --- | --- | --- |
| Retrieval/source coverage | Expected IDs versus retrieved IDs and exact source passages | `P49-H3-007`: missing `SALES-002`, omitting key prohibited sales commitments |
| Incomplete answer | Required facts versus generated answer, even when sources were retrieved | `P49-H3-006`: omitted vendor-intake details |
| Factual contradiction | Numbers, comparisons, subjects, and policy qualifiers in answer versus evidence | `P49-H3-006`: treats USD 8,000 as above USD 10,000; not caught by heuristic hallucination flag |
| Unsupported addition | Assertion lacking supporting authorized evidence | `P49-H3-013`: speculative cross-border review for a within-Canada move |
| Citation precision/support | Per-claim supporting passage, missing citations, and irrelevant extra citations | `P49-H3-001`: automated pass with an irrelevant extra vacation citation in the review sample |
| Safe but incorrect routing | Expected refusal, not-found, or clarification versus returned behavior | `P49-H3-027`: `not_found` instead of `refuse_no_access`; no leakage observed |
| Permission/memory boundary violation | Unauthorized retrieved chunks, restricted citations, generation boundary, memory treated as evidence | Zero recorded violations in this holdout; still a hard failure condition |
| Evaluator false positive | Token matches lose negation, subject association, or policy scope | `P49-H3-008`, `009`, `021`, `029`: all four heuristic hallucination flags classified as evaluator errors |
| Evaluator false negative | Semantic error passes a heuristic | The unflagged threshold error in `P49-H3-006`; case failed on completeness |
| Dataset defect | Expected facts contradict the corpus or expectations are unresolvable | None identified in the recorded Phase 49 review; requires separate versioned correction |
| Execution/integrity failure | Missing rows, interrupted calls, corrupt journals, or unverifiable aggregates | Phase 48 interrupted run; exact complete aggregate unavailable |

The benchmark failure classifier uses `retrieval_miss`, `multi_document_failure`, `answer_not_generated`, `wrong_citation`, `unsupported_answer`, `incomplete_answer`, `missed_refusal`, `not_found_failure`, and `ambiguity_failure`. The first applicable label wins, so counts are not exhaustive multi-label root-cause counts. [Citation diagnostics](../../apps/api/app/evaluation/citation_failures.py) provide more granular support checks.

Inspect the [eight complete failure records](../../data/evaluation/independent-generalization/results/phase49-independent-holdout-v3-failures.json), [30 individual case records](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/cases), and [separate review artifact](../../data/evaluation/independent-generalization/results/phase49-independent-holdout-v3-adjudication.json).

Recorded review covered 8/8 failures and 3/22 passes, with pass selection by lexicographic ID rather than random sampling. Findings were four evaluator-only, three product, and one mixed. This sample cannot establish the correctness of the other 19 passes. No independently identified human reviewer, second-reviewer agreement, or human-adjusted aggregate is established by that artifact.
