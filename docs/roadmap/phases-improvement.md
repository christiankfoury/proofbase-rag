# Post-Phase 27 Improvement Roadmap

This roadmap begins after Phase 27. Its goal is to make Proofbase more credible, safer, and more measurable without overstating what has been implemented.

The improvement story should focus on five areas:

1. Dashboard credibility.
2. Benchmark depth.
3. Enterprise document realism.
4. Retrieval quality.
5. Answer grounding and hallucination reduction.

## Current Evaluation Truth

- Full benchmark source file: `data/evaluation/benchmark-questions.json`.
- Current benchmark corpus size: 130 questions.
- Current primary retrieval and answer-quality dashboard runs: legacy 60-question pre-expansion suites.
- Current permission safety run: 10 restricted-access questions.
- Current memory evaluation run: 5 follow-up questions.
- Current headline metrics must be treated as measured outputs, not promises.

When dashboard copy, README copy, or phase notes mention metrics, they must include the run, sample size, benchmark version, and any skipped or filtered subset.

## Recommended Phase Order

Use this order instead of tuning prompts blindly:

| Phase | Improvement Slice | Why It Comes Here |
| --- | --- | --- |
| 28 | Dashboard Transparency | Make current metrics defensible before changing them. |
| 29 | Benchmark Schema Cleanup And Validation | Prevent bad benchmark data from corrupting future runs. |
| 30 | Enterprise Document Expansion | Add realistic source material before adding many more questions. |
| 31 | Benchmark Expansion | Grow to roughly 120-150 questions against richer documents. |
| 32 | Expanded Baseline Run | Establish the before picture on the expanded corpus. |
| 33 | Precision@k Improvement | Tune retrieval after the benchmark is stable. |
| 34 | Hallucination And Abstention Reduction | Tighten answer grounding where the current system is weakest. |
| 35 | Citation Accuracy Improvement | Make citation evidence more reliable and easier to audit. |
| 36 | Permission And Memory Evaluation Expansion | Strengthen safety and memory claims with larger suites. |
| 37 | Regression Scorecard | Produce the final baseline-vs-current portfolio story. |

## Phase 28: Dashboard Transparency

Goal: make the Dev & Admin dashboard honest, explicit, and recruiter-readable.

Key changes:

- Show the sample size behind each headline metric.
- Show benchmark version, run ID, and run timestamp near the metric context.
- Show corpus/run context:
  - full benchmark corpus: 130 questions
  - main evaluation run: legacy 60-question pre-expansion suite
  - permission safety suite: 10 questions
  - memory suite: 5 questions
- Add category breakdown for the current benchmark corpus and latest applicable run.
- Do not improve scores in this phase; make existing scores defensible.

Acceptance criteria:

- Dashboard exposes `sample_size`, `passed_count`, `failed_count`, `benchmark_version`, `run_timestamp`, and `category_breakdown` where the data exists.
- Missing counts are rendered as `pending`, `not available`, or `not measured`, not invented.
- README and demo copy no longer imply every metric comes from the same 60-question run.
- Verification includes `npm run build` in `apps/web`; backend compile only if API/data-export code changes.

## Phase 29: Benchmark Schema Cleanup And Validation

Goal: make `data/evaluation/benchmark-questions.json` easier to validate and scale.

Keep the current schema names where possible:

- `question_id`
- `question_type`
- `difficulty`
- `user_role`
- `question`
- `previous_turns`
- `expected_behavior`
- `expected_answer`
- `expected_source_document`
- `expected_source_section_or_quote`
- `allowed_documents`
- `evaluation_notes`

Add new fields only when they remove ambiguity:

- `requires_citation`
- `requires_memory`
- `requires_permission`
- `should_abstain`
- `restricted_documents`
- `allowed_roles`
- `effective_date` or `document_version` for future conflicting-source tests

Acceptance criteria:

- Add `scripts/validate_benchmark.py` or equivalent validation integrated with existing Python tooling.
- Validator checks required fields, unique `question_id`, valid `question_type`, source-document references, and category counts.
- Existing evaluation scripts still work.
- Verification includes:
  - `python scripts/validate_benchmark.py`
  - `python -m compileall apps scripts`

## Phase 30: Enterprise Document Expansion

Goal: make the corpus feel like a realistic enterprise knowledge system, not a narrow demo set.

Add synthetic Markdown documents before expanding the benchmark heavily. Candidate departments and documents:

| Department | Example Documents |
| --- | --- |
| Finance | Expense policy, reimbursement rules, procurement thresholds |
| Legal | NDA policy, contract approval process, data retention policy |
| Engineering | Deployment handbook, on-call policy, API standards |
| Support | Escalation policy, SLA guide, customer refund rules |
| Operations | Vendor onboarding, travel policy, equipment request process |

Add harder document patterns:

- Old policy vs new policy.
- Public docs vs restricted docs.
- Similar terminology across departments.
- Tables and exceptions.
- Documents with explicit "do not reveal" sections.
- Documents containing prompt-injection text.
- Overlapping policies with different effective dates.

Acceptance criteria:

- New documents are honest synthetic enterprise docs under `data/synthetic-documents`.
- Ingestion maps them into projects/departments without breaking existing seeded Northstar data.
- New sensitive documents have role metadata and are covered by permission tests before claims are made.
- Verification includes schema/ingestion checks where practical and clearly states whether OpenAI-backed embedding regeneration was run or skipped.

## Phase 31: Benchmark Expansion

Goal: increase benchmark credibility against the expanded corpus.

Target distribution:

| Category | Current | Target |
| --- | ---: | ---: |
| Simple factual | 20 | 30 |
| Multi-document | 10 | 20 |
| Permission-restricted | 10 | 20 |
| Missing-information | 10 | 20 |
| Conversation-memory | 10 in corpus / 5 in current memory run | 20 |
| Ambiguous | 5 | 15 |
| Prompt injection / adversarial | 0 | 15 |
| Conflicting-source / versioned docs | 0 | 10 |
| Total | 65 | 120-150 |

Acceptance criteria:

- Benchmark file contains roughly 120-150 validated questions.
- Dashboard displays exact sample sizes for every run.
- Expanded questions include expected sources and expected behavior.
- No generated question is promoted without human review.

## Phase 32: Expanded Baseline Run

Goal: capture the baseline on the expanded benchmark before tuning retrieval or prompts.

Acceptance criteria:

- Run the relevant evaluation suite against the expanded benchmark.
- Export dashboard data with `python scripts/export_dashboard_data.py`.
- Record baseline run IDs, sample sizes, known failures, and skipped OpenAI-backed checks.
- Do not claim improvement yet.

## Phase 33: Precision@k Improvement

Goal: reduce noisy retrieved chunks while preserving strong recall.

Current reference metrics:

- Source recall: 0.975.
- MRR / first source rank: 0.980.
- Precision@k: 0.650.

Targets:

- Source recall >= 0.95.
- MRR >= 0.95.
- Precision@k >= 0.75.
- Permission leakage rate = 0.000.

Likely approaches:

- Metadata filters.
- Department and document-type filters.
- Chunk-size and overlap tuning.
- Top-k tuning.
- Query rewriting improvements.
- Reranking only if simpler retrieval tuning is insufficient.

Acceptance criteria:

- Before/after run comparison proves improvement.
- Recall and permission safety do not regress.
- Cost and latency tradeoffs are documented.

## Phase 34: Hallucination And Abstention Reduction

Goal: reduce unsupported claims and improve missing-information behavior.

Current reference metric:

- Hallucination rate: 0.156.

Targets:

- Phase target: hallucination rate <= 0.08.
- Stretch target: hallucination rate <= 0.05.
- Answer accuracy should not regress.

Grounding controls:

- Every factual claim must be supported by retrieved context.
- If the answer is not in accessible sources, say so.
- Do not infer policy details from general knowledge.
- Do not answer from restricted documents.
- Prefer short, source-grounded answers over broad summaries.

Acceptance criteria:

- Hallucination rate improves on a real run.
- Missing-information accuracy improves or remains clearly explained.
- Permission leakage remains zero.
- Any evaluator/validator step is documented with cost and latency impact.

## Phase 35: Citation Accuracy Improvement

Goal: make citations reliable and recruiter-worthy.

Current reference metric:

- Citation accuracy: 0.857.

Targets:

- Citation accuracy >= 0.92.
- Stretch target >= 0.95.
- Hallucination rate does not increase.
- Permission leakage rate remains 0.000.

Track citation failure categories:

- Wrong document cited.
- Right document but wrong chunk.
- Citation missing.
- Citation attached to unsupported claim.
- Citation from restricted source.

Acceptance criteria:

- Citation verifier maps citation IDs to retrieved chunks.
- Citation failure categories appear in Dev & Admin evidence.
- Before/after metrics prove the improvement.

## Phase 36: Permission And Memory Evaluation Expansion

Goal: make safety and memory claims credible with larger suites.

Targets:

- Permission tests: 20-30 questions.
- Memory tests: 20-30 questions.
- Permission leakage rate = 0.000.
- Memory answer accuracy >= 0.90 across the larger suite.

Permission scenarios:

- Direct restricted document request.
- Indirect restricted summary request.
- Cross-department access request.
- Cross-project access request.
- Follow-up asking about restricted info.
- Prompt injection trying to reveal restricted info.
- Allowed and restricted docs overlapping in terminology.

Memory scenarios:

- Pronoun follow-ups.
- Topic switching.
- Multi-turn clarification.
- Memory plus document retrieval.
- Memory plus permission boundary.
- Stale or conflicting conversation context.
- User asks about something never mentioned.

Acceptance criteria:

- Memory never bypasses permissions.
- Expanded suites run separately and appear with exact sample size.
- Any failure is visible in Dev & Admin rather than hidden.

## Phase 37: Regression Scorecard

Goal: produce the final before/after portfolio story.

Dashboard should show:

- Baseline run.
- Latest run.
- Metric deltas.
- Benchmark version.
- Sample sizes.
- Category breakdown.
- Failed questions.
- Failure reasons.

Target story, only after measured:

| Metric | Target |
| --- | --- |
| Source Recall | Keep above 0.950 |
| Precision@k | 0.750-0.850 |
| MRR / First Source Rank | Keep above 0.950 |
| Answer Accuracy | 0.900+ |
| Citation Accuracy | 0.920+ |
| Hallucination Rate | Below 0.080, ideally below 0.050 |
| Permission Leakage Rate | Keep at 0.000 with harder tests |
| Memory Answer Accuracy | 0.900+ across a larger benchmark |

Portfolio claim template, only after verified:

```text
Built an evaluation-driven enterprise RAG platform with permission-aware retrieval, citation verification, conversation-memory evaluation, adversarial safety tests, and a benchmark dashboard tracking answer accuracy, citation accuracy, retrieval quality, hallucination rate, and permission leakage.

Expanded the benchmark from 65 to 120-150 questions across factual, multi-document, restricted-access, missing-information, memory, ambiguous, adversarial, and conflicting-source scenarios.
```

If the measured results support it, add:

```text
Reduced hallucination rate from 15.6% to below 8%, improved citation accuracy above 92%, and maintained 0% permission leakage across adversarial access-control tests.
```

Do not publish the result claim until the dashboard and phase notes point to the supporting run IDs.
