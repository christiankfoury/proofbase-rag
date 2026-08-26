# Review Findings

This is a documentation-first audit. It records design strengths, confusing areas, risks, and recommended verification without changing runtime behavior, prompts, retrieval logic, benchmark expectations, or metrics.

## Summary

The algorithm makes sense for a portfolio-grade enterprise RAG demo. Its strongest design choices are:

- permission filtering happens before generation
- generation defensively rechecks permissions
- citations are validated against retrieved chunks
- memory is used for query rewriting, not source evidence
- evaluation artifacts include run IDs, benchmark versions, sample sizes, failed-question counts, and diagnostic notes

The main fragile areas are:

- multi-document planning is still heuristic
- several answer-quality and Phase 50 ambiguity/injection fixes are hand-tuned policy patterns
- citation and answer metrics are deterministic approximations
- uploaded PDFs are reviewable and locally indexable after explicit approval, with optional AI cleanup drafts before indexing
- production identity and real connector permissions are not implemented

## Findings

### F1. Permission filtering is correctly before generation

Severity: strength.

Evidence:

- `apps/api/app/retrieval/vector_retriever.py` and `keyword_retriever.py` filter documents with `d.access_roles && %s`.
- `apps/api/app/retrieval/retriever.py` routes all supported retrieval modes through those retrievers.
- `apps/api/app/generation/answer_generator.py` checks for unauthorized chunks again before calling OpenAI.
- `scripts/run_permission_eval.py` measures unauthorized chunk exposure, restricted citation leakage, and unauthorized chunks reaching generation.

Why it matters:

The model should never see chunks the user cannot access. This is the right architecture for permission-sensitive RAG.

Recommended verification:

- Continue running `scripts/run_permission_eval.py` after retrieval or multi-doc changes.
- Add targeted tests for project plus department scope when Phase 39 changes orchestration.

### F2. Multi-document retrieval improves some cases but does not guarantee source coverage

Severity: medium.

Evidence:

- `apps/api/app/reasoning/multi_doc_detector.py` uses domain keyword pairs and conjunction patterns.
- `apps/api/app/reasoning/query_decomposer.py` decomposes with OpenAI, retrieves each subquery, deduplicates chunks, sorts by score, and returns the top 10.
- `data/evaluation/multi-doc-eval.json` shows multi-doc mode improved answer accuracy, citation accuracy, required-source citation rate, and hallucination rate.
- `docs/phase-39/live-query-answer-quality-results.md` shows the current live `/query` scorecard has `0` failed benchmark questions, while source-coverage diagnostics remain visible separately.

Risk:

Score-based merging can still omit a required source or cite only one part of a multi-part answer.

Recommended verification:

- Continue verifying source coverage per required answer part, not just global top score.
- Re-run `scripts/run_multi_doc_eval.py`, the live answer-quality evaluator, and permission evaluation after orchestration changes.

### F3. Ambiguity behavior improved, but the detector is pattern-based

Severity: medium.

Evidence:

- `answer_generator.py` has an `AMBIGUOUS_PATTERNS` list.
- Phase 50 adds pre-retrieval ambiguity and direct prompt-override guards for known patterns while preserving a source-discussion exemption.
- Phase 52 adds a strict-schema semantic assessor for every request not resolved by those deterministic fast paths. Its fixed 48-case development suite passed 48/48 with zero unsafe continuations, while keeping authorization outside model control.
- Prompt `answer_generation_v8.md` tells the model to clarify for underspecified approval, location, role, amount, contract, vendor, deployment, and sales-stage questions.
- Phase 46 improved generalization-probe clarification behavior from `0.000` to `1.000`.

Risk:

The semantic assessor broadens coverage to encoded, obfuscated, multilingual, mixed, and memory-poisoning requests, but a visible 48-case development suite still does not prove production robustness. Instructions embedded in retrieved sources also require a separate post-generation/source-integrity layer.

Recommended verification:

- Keep pre-retrieval clarification reasons visible in API and App proof surfaces.
- Keep expanding predeclared development regressions without reopening the Phase 47-49 sealed holdouts.
- Follow `docs/roadmap/post-phase-50-defense-and-production-readiness-plan.md`: Phase 52 request assessment is implemented; next add the permission-aware evidence-sufficiency gate and post-generation claim/source-instruction validation. Keep permission enforcement independent of every classifier output.

### F4. Some answer improvements are direct policy responses, not general reasoning

Severity: medium.

Evidence:

- `_direct_supported_response` in `answer_generator.py` returns exact supported answers for selected known cases.
- `_policy_response` returns deterministic not-found, no-access, clarify, and adversarial-source responses for pattern matches.

Why it may be acceptable:

Deterministic controls are useful for safety and high-confidence policy cases. They reduced measured failures without weakening benchmark expectations.

Risk:

If too many benchmark-specific rules accumulate, the system can look tuned to the test set rather than generally robust.

Recommended verification:

- Keep direct responses documented and small.
- Prefer orchestration and generalization improvements over adding broad benchmark-specific direct answers.
- When adding deterministic responses, add a note explaining why a general retrieval/generation path is not enough.

### F5. Citation validation is useful but heuristic

Severity: medium.

Evidence:

- `citation_validator.py` scores citation support using term overlap, rank score, and retrieval score.
- `answer_metrics.py` treats low citation confidence or unsupported claims as hallucination indicators.

Risk:

Term overlap can over-credit shallow lexical matches or under-credit correct paraphrases. It is a regression signal, not a complete semantic judge.

Recommended verification:

- Keep human review workflows visible for failed questions.
- For future high-stakes claims, add human or stronger judge-based evaluation as a separate metric rather than replacing deterministic metrics silently.

### F6. Memory boundaries are conceptually sound but benchmark-tuned

Severity: low to medium.

Evidence:

- `query_rewriter.py` contains explicit rewrite rules for many known memory benchmark cases.
- `memory_context_text` passes previous topic and cited source labels, not source text.
- Phase 36 memory evaluation reports `1.000` across its suite and `0.000` leakage.

Risk:

The system may perform less well on natural follow-ups outside the covered patterns.

Recommended verification:

- Add broader memory follow-up variations before making stronger memory claims.
- Keep the claim phrased as measured on the benchmark suite.

### F7. Uploaded-document workflow is locally searchable after approval, but hosted storage is still future work

Severity: remaining product gap, not algorithm bug.

Evidence:

- `create_pending_review_document` stores uploaded PDF extraction with `ingestion_status = 'pending_review'`.
- Retrieval filters require `dv.ingestion_status = 'indexed'`.
- Phase 40 added explicit approve/index behavior for local/Postgres storage, and Phases 43-44 added editor-triggered AI cleanup metadata and review diffs.

Risk:

The App side can ask scoped questions over approved/indexed uploaded PDFs, but raw file storage is still local/repository-backed rather than hosted Blob storage.

Recommended verification:

- Keep testing pending-review not searchable, approve/index searchable, project/department scoped citations, and permission filtering.
- Add hosted storage verification before claiming production document durability.

### F8. Evaluation metrics are honest but should be explained as approximations

Severity: low.

Evidence:

- `answer_metrics.py` uses expected-answer term overlap.
- `citation_accuracy` checks expected document IDs.
- `hallucination_flag` is based on unsupported claims or low citation confidence.
- `export_dashboard_data.py` includes notes that metrics are deterministic and heuristic.

Risk:

A reviewer might read `0.000` hallucination as a universal safety guarantee.

Recommended verification:

- Keep dashboard and README copy tied to run IDs, sample sizes, and benchmark version.
- Keep "synthetic benchmark" and "heuristic evaluator" limitations visible.

### F9. The frozen holdout exposes behavior and coverage gaps hidden by the regression benchmark

Severity: medium to high for broader portfolio claims; hard safety gates remained intact.

Evidence:

- Phase 47 froze runtime commit `50e149c` before isolated holdout authoring and ran the hashed 30-case suite once from `58ed3fc`.
- The holdout produced behavior accuracy `0.767`, expected-source recall `0.947`, required-fact completeness `0.788`, citation document accuracy `0.842`, and heuristic hallucination rate `0.333`.
- Unauthorized exposure, restricted citation leakage, unauthorized chunks reaching generation, and memory-as-evidence violations remained `0.000`.
- Failures cluster around strict ambiguity behavior, four-source synthesis, longer memory/topic returns, and `refuse_no_access` versus safe `not_found` classification.

Risk:

The perfect 130-question regression score reflects a known, implementation-influencing benchmark and cannot support a general unseen-query claim. The raw Phase 47 hallucination signal also overstates factual hallucination in some negation and token-overlap cases, so it must remain labeled heuristic and paired with human review.

Recommended verification:

- Treat the one-time holdout as immutable evidence and do not remediate against it in Phase 47.
- In a later phase, address the confirmed behavior/retrieval gaps and evaluate with a newly authored sealed holdout.
- Improve negation-aware and semantic adjudication as a separate metric while preserving the original deterministic score for comparability.

## Answers To The Audit Questions

| Question | Answer |
| --- | --- |
| Does permission filtering happen before generation? | Yes. SQL retrieval filters by role and scope before chunks are built, and generation rechecks. |
| Can unauthorized chunks appear in prompts? | They should not under current retrieval paths; generation refuses if they do. |
| Can unauthorized chunks appear in citations? | They should not because citations must match retrieved chunks. Permission eval checks this. |
| Can unauthorized chunks appear in memory? | Memory stores prior turns and citation labels; it does not provide source text as evidence, and current retrieval still filters by role. |
| Can unauthorized chunks appear in logs or feedback? | Audit logs record blocked document IDs, not source text. Feedback can contain user-visible prior answers and citations, so review workflows should remain gated. |
| What exactly does memory influence? | Follow-up detection, retrieval query rewrite, and a prompt note for clarification only. |
| Which retrieval profile is current best measured reference? | `phase33-vector-lexical-rerank-top3`, with Precision@k `0.778`, expected-source recall `0.950`, and MRR `0.965` over 130 questions. |
| Why does reranking improve precision? | It boosts chunks whose document ID, title, heading, or content lexically match the query while retaining vector similarity. |
| What does reranking not solve? | It does not guarantee each required source for a multi-document question is retrieved or cited. |
| How are unsupported and not-found answers controlled? | Prompt rules, missing-information patterns, citation validation, response downgrades, and hallucination scoring. |
| What do citation accuracy and hallucination metrics mean? | Citation accuracy checks expected document IDs in citations. Hallucination flags unsupported claims or low citation confidence. Both are heuristic. |
| What known failures remain after Phase 39? | The current live `/query` scorecard has `0` failed benchmark questions. Diagnostic submetric notes and historical stress cases remain visible for review. |
| Which parts are product-ready, demo-only, or planned? | Permission-filtered seeded-corpus RAG and local uploaded-document indexing are demo-ready. Local demo auth is demo-only. Production SSO, real connectors, hosted storage, and Azure deployment are planned. |

## Recommended Next Work

1. Use the Phase 47 findings to define later ambiguity, long-memory, and multi-document remediation, then measure against a new sealed holdout rather than rerunning this one.
2. Add project-specific evaluation authoring for uploaded and customer-specific knowledge bases.
3. Add hosted storage/Azure Blob and production authentication before production claims.
4. Keep permission evaluation as a hard gate for any orchestration or retrieval-default change.
5. Preserve honest dashboard language: run ID, sample size, benchmark version, skipped checks, and limitations.
