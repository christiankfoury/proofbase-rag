# Codebase Verification Report

Generated: 2026-06-26

Scope: audit/reporting pass only. Runtime behavior, prompts, retrieval logic, benchmark expectations, metrics, and existing documentation were not changed. The only intended artifact is this report.

## Executive Summary

The Enterprise Knowledge Agent RAG pipeline is broadly consistent with its documented architecture: live requests establish scope and role, rewrite memory follow-ups, retrieve permission-filtered chunks, generate only from those chunks, validate citations against retrieved chunks, compute heuristic confidence, and log metadata without source text. There is no evidence of model training, fine-tuning, or `.fit()`-style ML training code; "training" references are corpus content, docs wording, or evaluation/prompt improvement language.

The strongest implementation property is the permission boundary. Vector and keyword retrieval apply role filtering in SQL before `RetrievedChunk` objects are built, and generation rechecks for unauthorized chunks before any OpenAI chat call. Uploaded PDFs are also correctly excluded from retrieval because they stop at `pending_review` and no chunks or embeddings are created.

The system is partially inconsistent in several important places:

- Confirmed versioning bug: retrievers do not constrain chunks to `documents.current_version_id`, so old indexed versions can remain retrievable after a document version changes.
- Confirmed security/reporting risk: `docker compose config` renders the interpolated `OPENAI_API_KEY` value from local environment or `.env`; the command passed but printed the secret in local terminal output.
- Design risk: multi-document retrieval decomposes and merges by score, but does not guarantee every required source is planned, retrieved, or cited.
- Design risk: deterministic policy guards and memory rewrite rules are narrow and partly benchmark-shaped.
- Documentation/operational mismatch: older evaluators such as `scripts/run_answer_quality_eval.py`, `scripts/run_retrieval_experiments.py`, and `scripts/run_multi_doc_eval.py` can call OpenAI-backed paths without explicit approval flags, while later phase runners are guarded.
- Metric interpretation risk: answer, citation, hallucination, faithfulness, and confidence scores are useful deterministic regression signals, not semantic proof.

Before Phase 39, fix or explicitly accept the stale-version retrieval bug, add an approval gate or clear warning to `scripts/run_multi_doc_eval.py`, and make multi-document source coverage planning the main Phase 39 target.

## System Flow Verified

Live `POST /query` and `POST /query/stream` follow the documented high-level flow:

1. Validate optional `project_id` and `department_id`; department scope requires project scope (`apps/api/app/main.py:1399`, `apps/api/app/main.py:1401`).
2. If project-scoped, require project membership and derive role from the authenticated demo user instead of trusting request role (`apps/api/app/main.py:1403`, `apps/api/app/main.py:1405`, `apps/api/app/main.py:214`).
3. Build retrieval config with mode, top-k, weights, and optional project/department scope (`apps/api/app/main.py:1407`).
4. Load session turns, rewrite follow-up questions, and build memory context only when memory is used (`apps/api/app/main.py:1426`, `apps/api/app/main.py:1437`).
5. Detect multi-document mode and call either `retrieve_multi_doc` or `retrieve_chunks` (`apps/api/app/main.py:1442`).
6. Generate from retrieved chunks and optional memory context (`apps/api/app/main.py:1454`).
7. Store session messages, including assistant answer/citations/confidence, after generation (`apps/api/app/main.py:1474`).
8. Log observability metadata including IDs, counts, costs, and latency, not chunk text (`apps/api/app/main.py:1518`, `apps/api/app/observability/logger.py:65`).
9. Return answer, citations, retrieved chunk previews, confidence, memory metadata, and permission check (`apps/api/app/main.py:1552`).

The documented sequence is accurate with one wording nuance: "retrieval -> permission filtering" is implemented as permission-filtered retrieval, not a separate post-retrieval filter for generated chunks.

## Algorithm-by-Algorithm Verification Table

| Area | Status | Evidence | Finding Type |
| --- | --- | --- | --- |
| Markdown loading | Consistent | Frontmatter required fields are enforced in `parse_markdown_file` (`apps/api/app/ingestion/markdown_loader.py:29`). | Future improvement |
| PDF extraction | Consistent, limited | `extract_pdf_to_markdown` uses deterministic `pypdf` text extraction with confidence by pages-with-text (`apps/api/app/ingestion/pdf_extractor.py:18`). | Future improvement |
| Chunking | Consistent | `section_based` splits on `##`; `fixed_size` windows section words with overlap (`apps/api/app/ingestion/chunker.py:26`, `apps/api/app/ingestion/chunker.py:66`). | Future improvement |
| Embeddings | Correct but unbatched-cacheless | `embed_texts` calls OpenAI embeddings and ingestion embeds all chunks before DB writes (`apps/api/app/embeddings/openai_embeddings.py:13`, `scripts/ingest_markdown.py:191`). | Inefficiency |
| Vector retrieval | Correct role/scope filtering; stale-version gap | SQL joins active docs and indexed versions, filters role/scope, but lacks `c.document_version_id = d.current_version_id` (`apps/api/app/retrieval/vector_retriever.py:63`). | Confirmed bug |
| Keyword retrieval | Correct role/scope filtering; stale-version gap | Same indexed-version filter and same missing current-version constraint (`apps/api/app/retrieval/keyword_retriever.py:92`). | Confirmed bug |
| Hybrid retrieval | Functionally consistent; observability imperfect | Merges permission-filtered vector and keyword results (`apps/api/app/retrieval/hybrid_retriever.py:30`), but audit traces are emitted as component retriever events. | Documentation mismatch |
| Vector lexical rerank | Name matches implementation | `retriever.py` maps mode to vector retrieval plus lexical reranker (`apps/api/app/retrieval/retriever.py:13`); reranker combines vector score, lexical score, and same-document boost (`apps/api/app/retrieval/reranker.py:74`). | Design risk |
| Project scope | Enforced when provided | API membership check plus retriever SQL scope filters (`apps/api/app/main.py:1403`, `apps/api/app/retrieval/vector_retriever.py:121`). | Future improvement |
| Department scope | Enforced when provided | API validates department belongs to project and retrievers add department SQL (`apps/api/app/main.py:1423`, `apps/api/app/retrieval/keyword_retriever.py:147`). | Future improvement |
| Role permissions | Strong | SQL uses `d.access_roles && %s`; generation rechecks unauthorized chunks (`apps/api/app/retrieval/vector_retriever.py:67`, `apps/api/app/generation/answer_generator.py:678`). | Future improvement |
| Memory rewriting | Safe boundary, narrow rules | Memory creates a retrieval question and prompt note; explicit rewrite rules exist (`apps/api/app/memory/query_rewriter.py:5`, `apps/api/app/memory/context_builder.py:18`). | Design risk |
| Multi-doc | Permission-safe, coverage not guaranteed | Decomposition retrieves each subquery with normal retriever, dedupes, sorts by score, returns top 10 (`apps/api/app/reasoning/query_decomposer.py:52`). | Design risk |
| Prompt selection | Clear | `get_prompt` selects requested version or latest active prompt (`apps/api/app/prompts/prompt_registry.py:97`). | Future improvement |
| Generation | Permission-safe; some hand-tuned guards | Unauthorized chunks short-circuit before OpenAI; `_policy_response` has missing/restricted/ambiguous/direct patterns (`apps/api/app/generation/answer_generator.py:246`, `apps/api/app/generation/answer_generator.py:678`). | Design risk |
| Citations | Correct boundary | Structured citations are matched only to retrieved chunks; validator rejects unknown chunk IDs (`apps/api/app/generation/answer_generator.py:428`, `apps/api/app/citations/citation_validator.py:88`). | Future improvement |
| Citation backfill | Correct boundary, heuristic | Backfill iterates only over retrieved chunks and adds max 3 new docs (`apps/api/app/generation/answer_generator.py:441`). | Metric interpretation risk |
| Confidence | Consistent but heuristic | Confidence combines retrieval, citation, and answer scores (`apps/api/app/confidence/confidence_scorer.py:24`). | Metric interpretation risk |
| Evaluation | Mostly consistent; legacy runner gaps | Current prompt experiment runner uses live memory rewrite; older eval scripts do not always gate external AI (`apps/api/app/experiments/runner.py:37`, `scripts/run_multi_doc_eval.py:55`). | Documentation mismatch |
| Dashboard export | Mostly honest | Adds sample size, benchmark version, failed count, and comparison notes (`scripts/export_dashboard_data.py:95`, `scripts/export_dashboard_data.py:966`). | Metric interpretation risk |

## Ingestion/Indexing Findings

### I1. Current-version filtering is missing in retrievers

Type: confirmed bug. Severity: High.

`scripts/ingest_markdown.py` upserts a document version and updates `documents.current_version_id` (`scripts/ingest_markdown.py:104`). It deletes chunks only for that specific `document_version_id` and selected chunking strategy (`scripts/ingest_markdown.py:197`). If a document later gets a new `version_label`, old chunks for older indexed versions can remain.

The retrievers join `chunks` to `document_versions` and require `dv.ingestion_status = 'indexed'`, but they do not require `c.document_version_id = d.current_version_id` (`apps/api/app/retrieval/vector_retriever.py:63`, `apps/api/app/retrieval/keyword_retriever.py:92`). Schema explicitly stores `documents.current_version_id` (`apps/api/app/db/schema.sql:263`) and supports multiple `document_versions` (`apps/api/app/db/schema.sql:294`).

Impact: stale or conflicting source text can be retrieved, cited, and used for generation after version updates. Current seeded corpus likely avoids this because documents use stable versions, but Phase 40 uploaded-document indexing will make this more important.

### I2. Uploaded documents are excluded from retrieval until indexed

Type: future improvement. Severity: Low.

`create_pending_review_document` stores uploaded extraction with `ingestion_status = 'pending_review'` and status detail stating no chunks or embeddings were created (`apps/api/app/projects/document_store.py:195`, `apps/api/app/projects/document_store.py:230`). Retrieval requires `dv.ingestion_status = 'indexed'` (`apps/api/app/retrieval/vector_retriever.py:71`, `apps/api/app/retrieval/keyword_retriever.py:99`).

Impact: correct safety behavior. Phase 40 still needs approve/index/search workflow.

### I3. Re-ingestion repeats embedding work

Type: inefficiency. Severity: Medium.

Ingestion embeds every chunk before opening the DB transaction and before checking whether content hashes already exist (`scripts/ingest_markdown.py:183`, `scripts/ingest_markdown.py:191`). There is no cache keyed by content hash plus embedding model.

Impact: unnecessary OpenAI calls and cost for unchanged documents; if DB writes fail, embedding cost is already spent.

### I4. Multiple chunking strategies can coexist intentionally

Type: future improvement. Severity: Low.

Chunks are unique by `(document_version_id, chunking_strategy, chunk_index)` (`apps/api/app/db/schema.sql:386`), and retrievers filter by requested chunking strategy (`apps/api/app/retrieval/vector_retriever.py:69`). This is internally consistent. It becomes risky only when combined with missing current-version filtering.

## Retrieval Findings

### R1. Vector retrieval implementation matches its name

Type: future improvement. Severity: Low.

Vector retrieval embeds the question, queries pgvector by cosine distance, joins active indexed docs, applies role and scope filters, and returns scored chunks (`apps/api/app/retrieval/vector_retriever.py:24`, `apps/api/app/retrieval/vector_retriever.py:41`, `apps/api/app/retrieval/vector_retriever.py:67`).

### R2. Keyword retrieval implementation matches its name

Type: future improvement. Severity: Low.

Keyword retrieval normalizes terms into an OR query, uses PostgreSQL `websearch_to_tsquery`, ranks with `ts_rank_cd`, and applies the same status/scope/role filters (`apps/api/app/retrieval/keyword_retriever.py:25`, `apps/api/app/retrieval/keyword_retriever.py:52`, `apps/api/app/retrieval/keyword_retriever.py:96`).

### R3. Hybrid retrieval is fair enough for experiments, but logs are component-level

Type: documentation mismatch. Severity: Low.

Hybrid runs vector and keyword retrievers with `candidate_k = max(top_k * 4, 20)`, normalizes both result sets, merges by chunk ID, computes weighted hybrid score, and returns top-k (`apps/api/app/retrieval/hybrid_retriever.py:27`, `apps/api/app/retrieval/hybrid_retriever.py:47`, `apps/api/app/retrieval/hybrid_retriever.py:86`).

Because it calls the underlying retrievers, permission audit events are logged as `vector_only` and `keyword_only`, not as one `hybrid` trace (`apps/api/app/retrieval/vector_retriever.py:111`, `apps/api/app/retrieval/keyword_retriever.py:131`). The returned chunks are correct, but audit/log interpretation can be confusing.

### R4. `vector_lexical_rerank` is accurately named but can over-concentrate documents

Type: design risk. Severity: Medium.

The mode retrieves a larger allowed vector candidate set and reranks with vector score, lexical overlap, and a same-lead-document boost (`apps/api/app/retrieval/vector_retriever.py:22`, `apps/api/app/retrieval/reranker.py:85`, `apps/api/app/retrieval/reranker.py:93`). This matches the name and Phase 33 claims.

Risk: same-document boost can help precision but may work against multi-document coverage when a question needs several sources.

### R5. Top-k and candidate limits are mostly consistent

Type: future improvement. Severity: Low.

Vector uses final `top_k` as output and larger candidate sets only when reranking (`apps/api/app/retrieval/vector_retriever.py:21`). Hybrid uses larger candidate sets in both retrievers and returns final top-k (`apps/api/app/retrieval/hybrid_retriever.py:27`). Phase 33/38 runners record rerank candidate limits in dashboard run metadata (`scripts/run_phase38_answer_quality_candidate.py:204`).

## Permission/Scope Findings

### P1. Role filtering happens before generation

Type: future improvement. Severity: Low.

Vector and keyword allowed queries require `d.access_roles && %s` before creating `RetrievedChunk` objects (`apps/api/app/retrieval/vector_retriever.py:67`, `apps/api/app/retrieval/keyword_retriever.py:96`). `generate_answer` and `generate_answer_stream` recheck with `unauthorized_chunks` before OpenAI calls (`apps/api/app/generation/answer_generator.py:678`, `apps/api/app/generation/answer_generator.py:789`).

### P2. Project and department scope are enforced when supplied

Type: future improvement. Severity: Low.

API rejects department scope without project scope (`apps/api/app/main.py:1401`). Project-scoped requests require membership (`apps/api/app/main.py:1403`). Retrievers add project and department SQL filters (`apps/api/app/retrieval/vector_retriever.py:121`, `apps/api/app/retrieval/keyword_retriever.py:141`).

Design note: unscoped `/query` intentionally remains global for Dev/Admin and legacy chat. This is not a bug, but App-side callers must pass project scope to avoid cross-project retrieval.

### P3. Unauthorized chunks should not reach prompts, citations, returned context, or memory evidence

Type: future improvement. Severity: Low.

Citations are matched to chunks from the current retrieved list (`apps/api/app/generation/answer_generator.py:144`, `apps/api/app/citations/citation_validator.py:95`). Backfill also iterates only over the retrieved chunk list (`apps/api/app/generation/answer_generator.py:453`). Returned `retrieved_chunks` comes from the same allowed chunk list (`apps/api/app/main.py:1598`).

Memory stores prior user/assistant text and citation metadata, but retrieval still re-runs through role filters (`apps/api/app/memory/session_store.py:57`, `apps/api/app/main.py:1437`).

### P4. Audit logs do not leak text, but may disclose blocked document IDs

Type: design risk. Severity: Medium.

Audit logs store metadata JSON and document IDs, not source text (`apps/api/app/audit/audit_logger.py:25`). Permission traces log `blocked_document_ids` for unauthorized candidates (`apps/api/app/permissions/permission_filter.py:63`) and emit one audit event per blocked document ID (`apps/api/app/permissions/permission_filter.py:68`).

Impact: admin-only audit visibility is useful, but document IDs like `HR-ADMIN-001` or `IT-ADMIN-001` can reveal existence/topic of restricted documents. The `/audit/events` route is admin-gated (`apps/api/app/main.py:692`), so this is an admin-observability tradeoff, not user-facing leakage.

### P5. Multi-doc preserves permission filtering per subquery

Type: future improvement. Severity: Low.

`retrieve_multi_doc` calls `retrieve_chunks` for each subquery with the same `user_role` and config (`apps/api/app/reasoning/query_decomposer.py:56`). Since `retrieve_chunks` dispatches to role-filtered retrievers, subquery results preserve permissions.

## Generation/Prompt Findings

### G1. Prompt selection is clear

Type: future improvement. Severity: Low.

`get_prompt` returns a requested version if supplied; otherwise it selects the latest active prompt or latest prompt by `created_at` (`apps/api/app/prompts/prompt_registry.py:97`). Live multi-doc defaults to `v4` when no explicit version is supplied (`apps/api/app/main.py:1462`). Phase 38 runner explicitly uses `v8` (`scripts/run_phase38_answer_quality_candidate.py:216`).

### G2. Deterministic policy responses are permission-safe but benchmark-shaped

Type: design risk. Severity: Medium.

`_policy_response` can return missing-information, no-access, adversarial-source, ambiguity, or direct supported answers before OpenAI (`apps/api/app/generation/answer_generator.py:246`). Direct answers require matching retrieved chunks (`apps/api/app/generation/answer_generator.py:339`). This does not bypass permission checks because generation already rechecks unauthorized chunks and the direct layer uses the retrieved chunks.

Risk: exact patterns such as `lost or stolen device`, `proposal stage`, `cross-border remote work`, and specific ambiguity strings can look hand-tuned to benchmark/demo cases (`apps/api/app/generation/answer_generator.py:339`, `apps/api/app/generation/answer_generator.py:105`).

### G3. Response type behavior is consistent but adjusted after validation

Type: metric interpretation risk. Severity: Medium.

The model returns a structured `response_type`, then `_finalize_generated_answer` validates citations and may adjust response type or answer text (`apps/api/app/generation/answer_generator.py:603`, `apps/api/app/generation/answer_generator.py:622`). This is consistent with hallucination control, but reviewers should understand that final `response_type` is not purely the model's original label.

### G4. Legacy answer-quality evaluator is not the current live-equivalent path

Type: documentation mismatch. Severity: Medium.

`scripts/run_answer_quality_eval.py` builds memory queries by concatenating previous turns into the query (`scripts/run_answer_quality_eval.py:35`). The current prompt-experiment runner uses `rewrite_followup_question` and `memory_context_text`, matching live flow more closely (`apps/api/app/experiments/runner.py:37`). Current Phase 38 results are based on the newer runner.

## Citation/Confidence Findings

### C1. Citations can only survive if they match retrieved chunks

Type: future improvement. Severity: Low.

Structured citations are normalized by `_match_citation_to_chunk`; unmatched citations are dropped before validation (`apps/api/app/generation/answer_generator.py:144`, `apps/api/app/generation/answer_generator.py:428`). `validate_citations` also rejects unknown chunk IDs (`apps/api/app/citations/citation_validator.py:95`).

### C2. Citation backfill only uses permission-filtered chunks

Type: future improvement. Severity: Low.

Backfill iterates over `chunks` passed into generation, which have already passed retrieval permissions, and avoids duplicate chunk IDs/document IDs (`apps/api/app/generation/answer_generator.py:450`, `apps/api/app/generation/answer_generator.py:453`). It adds at most three citations (`apps/api/app/generation/answer_generator.py:495`).

### C3. Citation confidence is heuristic

Type: metric interpretation risk. Severity: Medium.

Citation support uses term overlap plus rank and retrieval score (`apps/api/app/citations/citation_validator.py:76`). This can over-credit lexical overlap and under-credit correct paraphrase. It is suitable for regression tracking, not proof of factual correctness.

### C4. Final confidence can overstate non-answer certainty

Type: metric interpretation risk. Severity: Medium.

For `not_found`, `refuse_no_access`, and `clarify`, `answer_confidence` floors at `0.65` (`apps/api/app/confidence/confidence_scorer.py:19`) and final confidence combines that with retrieval confidence (`apps/api/app/confidence/confidence_scorer.py:34`). This can be meaningful as "confidence in the system behavior," but misleading if read as "confidence in factual answer content."

Follow-up status: mitigated in the Phase 40 polish slice by returning `confidence_interpretation` from `/query` and labeling non-answer final confidence as behavior confidence in the App/Dev result panel. The score remains heuristic.

## Memory Findings

### M1. Memory is not source evidence in the live path

Type: future improvement. Severity: Low.

Memory rewrite uses previous turns to produce a standalone retrieval question (`apps/api/app/memory/query_rewriter.py:5`). Prompt context says it is for clarification only (`apps/api/app/generation/prompts.py:79`). Retrieved chunks and citations still come from the current role-filtered retrieval pass.

### M2. Previous assistant answers are stored but not directly cited as evidence

Type: future improvement. Severity: Low.

Assistant messages are stored with content, citations, confidence, and metadata (`apps/api/app/memory/session_store.py:57`). `memory_context_text` provides topic/source labels, not source text, to the prompt; current retrieval provides evidence.

### M3. Memory rewrite is benchmark-shaped

Type: design risk. Severity: Medium.

`extract_previous_topic` and `rewrite_followup_question` contain many explicit topic and rewrite rules for known scenarios (`apps/api/app/memory/context_builder.py:18`, `apps/api/app/memory/query_rewriter.py:53`). This is safe but not broadly general. Phase 36's `1.000` memory score should be read as benchmark-suite performance, not universal conversational memory.

### M4. Memory leakage metric is narrow

Type: metric interpretation risk. Severity: Low.

`memory_permission_leakage` first checks unauthorized chunks, then only flags restricted citations if unauthorized chunks also reached generation (`apps/api/app/evaluation/memory_metrics.py:20`). Because citation validation should prevent citations outside retrieved chunks, this is probably fine in current code, but as a metric it may miss a hypothetical citation-only leak.

Follow-up status: clarified in evaluation docs and Phase 39 live reporting. Raw answer-quality response-type half-credit for `answer_with_memory` remains comparable, while memory-specific response behavior is treated as a diagnostic note when answer/citation/permission behavior is correct.

## Multi-Document/Ambiguity Findings

### D1. Multi-doc detection works as documented but is heuristic

Type: design risk. Severity: Medium.

`is_multi_document_question` uses hard-coded domain pairs and conjunction patterns (`apps/api/app/reasoning/multi_doc_detector.py:6`, `apps/api/app/reasoning/multi_doc_detector.py:62`). This matches docs and current behavior, but new phrasing can miss auto-detection unless the user forces multi-doc mode.

### D2. Query decomposition is permission-safe but does not guarantee required sources

Type: design risk. Severity: High.

`decompose_question` asks OpenAI for 2-3 search queries and falls back to the original question on any exception (`apps/api/app/reasoning/query_decomposer.py:28`). `retrieve_multi_doc` retrieves each subquery, deduplicates chunks, sorts all chunks by score, and returns the top 10 (`apps/api/app/reasoning/query_decomposer.py:52`, `apps/api/app/reasoning/query_decomposer.py:61`).

There is no source plan, expected-source guarantee, per-subquery quota, or source-coverage repair step. Phase 38 still reports 6 failed questions, all `MULTI-*`, with 3 multi-document failures and 2 wrong citations (`docs/phase-38/answer-quality-remediation-results.md:37`, `docs/phase-38/answer-quality-remediation-results.md:46`).

### D3. Ambiguity behavior improved but remains pattern-driven

Type: design risk. Severity: Medium.

Phase 38 improved clarification accuracy from `0.500` to `1.000` (`docs/phase-38/answer-quality-remediation-results.md:29`) using pre-generation patterns (`apps/api/app/generation/answer_generator.py:105`). This is effective on benchmark v1.1 but not a general ambiguity classifier.

### D4. Why Phase 39 is still needed

Type: future improvement. Severity: High.

Phase 39 should add explicit multi-document source planning and strict ambiguity decisioning. Current code can retrieve/cite multiple documents, but it cannot prove every required source has a retrieval path before synthesis, and it cannot robustly identify underspecified intent outside known patterns.

## Evaluation/Dashboard Findings

### E1. Benchmark schema is consistent

Type: future improvement. Severity: Low.

`python scripts/validate_benchmark.py` passed. It confirmed benchmark version `1.1`, `130` declared questions, `19` documents, and expected category counts.

### E2. Current answer-quality runs use the live memory rewrite path

Type: future improvement. Severity: Low.

`run_prompt_experiment` uses `_query_plan`, `rewrite_followup_question`, and `memory_context_text` (`apps/api/app/experiments/runner.py:37`), aligning current Phase 38 answer-quality evaluation with live memory behavior.

### E3. Some older evaluators lack explicit external-AI approval flags

Type: documentation mismatch. Severity: Medium.

Later phase runners require `--allow-external-ai` or `--allow-external-embeddings` (`scripts/run_phase38_answer_quality_candidate.py:222`, `scripts/run_memory_eval.py:269`, `scripts/run_permission_eval.py:252`). Older/general scripts call OpenAI-backed retrieval or generation without a required flag:

- `scripts/run_answer_quality_eval.py` calls `retrieve_chunks` and `generate_answer` (`scripts/run_answer_quality_eval.py:175`, `scripts/run_answer_quality_eval.py:177`).
- `scripts/run_retrieval_experiments.py` calls `run_benchmark`, which calls retrieval embedding (`scripts/run_retrieval_experiments.py:139`, `apps/api/app/evaluation/run_benchmark.py:234`).
- `scripts/run_multi_doc_eval.py` calls `retrieve_multi_doc` and `generate_answer` (`scripts/run_multi_doc_eval.py:49`, `scripts/run_multi_doc_eval.py:55`).

This conflicts with the spirit of the current guarded-run policy.

### E4. Dashboard comparisons are mostly fair and well-labeled

Type: future improvement. Severity: Low.

`export_dashboard_data.py` annotates sample size, pass/fail counts, benchmark version, and run timestamp (`scripts/export_dashboard_data.py:95`). It also warns about subset runs not being directly comparable (`scripts/export_dashboard_data.py:454`) and includes scorecard limitations (`scripts/export_dashboard_data.py:1016`).

### E5. Old and current permission/memory baselines are not same-sample comparisons

Type: metric interpretation risk. Severity: Low.

The dashboard explicitly notes legacy permission/memory baselines used smaller suites and should be read as coverage expansion plus safety preservation, not same-sample accuracy deltas (`scripts/export_dashboard_data.py:1016`). This is honest but should remain visible in the UI.

### E6. Dashboard config rendering can leak secrets

Type: confirmed bug. Severity: High.

`docker-compose.yml` interpolates `OPENAI_API_KEY` into the API service environment (`docker-compose.yml:30`). The requested `docker compose config` command passed, but rendered the local secret value in terminal output. The key value is intentionally not reproduced here.

Impact: local logs, CI logs, or shared terminal transcripts can leak secrets. This is outside RAG correctness but important for portfolio/demo safety.

## Inefficiency List

1. Re-ingestion embeds every chunk without content-hash/model cache (`scripts/ingest_markdown.py:191`).
2. Vector retrieval embeds the query on every retrieval call; hybrid calls vector retrieval once and keyword retrieval once, and multi-doc calls retrieval once per subquery (`apps/api/app/retrieval/vector_retriever.py:24`, `apps/api/app/reasoning/query_decomposer.py:56`). Phase 40 polish added a per-process embedding cache for duplicate text/model pairs; it does not persist content and does not eliminate distinct subquery embedding calls.
3. Multi-doc uses an OpenAI chat call for decomposition plus embedding calls per subquery plus generation (`apps/api/app/reasoning/query_decomposer.py:30`, `scripts/run_multi_doc_eval.py:55`).
4. Hybrid retrieval logs and queries both component retrievers separately, resulting in repeated audit rows (`apps/api/app/retrieval/hybrid_retriever.py:30`). Phase 40 polish labels those component audit rows with `parent_retrieval_mode=hybrid` and `hybrid_component`.
5. `python -m compileall apps scripts` traverses `apps/web/node_modules` and `.next*` directories, making verification noisy and slower.
6. Prompt context includes full chunk content for every retrieved chunk (`apps/api/app/generation/prompts.py:8`), which can increase token cost when top-k or chunk sizes grow.
7. No DB connection pooling is visible; each DB helper opens a new psycopg connection (`apps/api/app/db/session.py:10`).

## Inconsistency List

| Inconsistency | Type | Evidence |
| --- | --- | --- |
| Retrievers ignore `documents.current_version_id` | Confirmed bug | `scripts/ingest_markdown.py:104`, `apps/api/app/retrieval/vector_retriever.py:63` |
| `docker compose config` prints local OpenAI key | Confirmed bug | `docker-compose.yml:30` |
| Documentation says later OpenAI evaluators are guarded, but older/general scripts are not | Documentation mismatch | `docs/algorithm/evaluation-metrics.md:197`, `scripts/run_multi_doc_eval.py:55` |
| Hybrid audit trail is component-level, not hybrid-level | Mitigated documentation mismatch | `apps/api/app/retrieval/hybrid_retriever.py:30`, `apps/api/app/permissions/permission_filter.py:57` |
| Phase 38 permission doc shows `vector_only`, while answer-quality run used `vector_lexical_rerank` | Metric interpretation risk | `docs/phase-38/permission-safety-results.md:9`, `docs/phase-38/answer-quality-remediation-results.md:10` |
| Memory claims can sound general but implementation is rule-heavy | Design risk | `apps/api/app/memory/query_rewriter.py:53` |
| Ambiguity claims can sound general but implementation is pattern-heavy | Design risk | `apps/api/app/generation/answer_generator.py:105` |

## Risk Ranking

### Critical

No critical runtime permission leak was confirmed in this audit.

### High

- Confirmed bug: stale indexed document versions can be retrieved because retrievers do not filter to `documents.current_version_id`.
- Confirmed bug: `docker compose config` renders the local `OPENAI_API_KEY`, creating a realistic secret-exposure path.
- Design risk: multi-document retrieval does not guarantee required source coverage before synthesis.

### Medium

- Design risk: deterministic answer and ambiguity guards are narrow and partly benchmark-shaped.
- Design risk: audit logs reveal blocked document IDs to admins.
- Documentation mismatch: older/general eval scripts can call OpenAI without explicit approval gates.
- Metric interpretation risk: confidence and hallucination scores can be overread as semantic proof.
- Inefficiency: repeated embeddings and decomposition calls increase cost and latency.

### Low

- Hybrid audit events are component-level.
- Memory leakage metric is narrow but protected by current citation validation.
- Uploaded documents are intentionally not searchable yet.
- Compile verification command is noisy because it scans web build and dependency folders.

## Recommended Verification Commands

Already run in this audit:

```powershell
rg -n "train|training|fine.?tune|finetune|fit\(|embedding|chunk|retrieve|rerank|permission|citation|confidence|memory|multi_doc|evaluate" apps scripts docs data
python scripts/validate_benchmark.py
python -m compileall apps scripts
git diff --check docs/algorithm apps scripts
docker compose config
```

Result notes:

- `scripts/validate_benchmark.py` passed for benchmark version `1.1`, 130 questions, and 19 source documents.
- `python -m compileall apps scripts` passed, but it also traversed web build/dependency directories, making output noisy.
- `git diff --check docs/algorithm apps scripts` passed; because the report was untracked at the time, a staged diff check should also be run before commit.
- `docker compose config` passed but rendered the local `OPENAI_API_KEY` value, which is recorded above as a High severity secret-exposure finding.

Before committing this report:

```powershell
git diff --check --cached
```

Skipped live checks:

- OpenAI-backed answer, retrieval, memory, permission, and multi-doc evaluations were not run because the user explicitly said not to rerun OpenAI-backed evaluations.
- Live API/Postgres query tests were not run because they require local services and potentially OpenAI calls depending on path.
- No network checks were run.

Recommended before Phase 39 implementation:

```powershell
python scripts/validate_benchmark.py
python -m compileall apps/api/app scripts
python scripts/run_phase38_answer_quality_candidate.py --dry-run
python scripts/run_memory_eval.py --phase phase-36 --dry-run
python scripts/run_permission_eval.py --help
```

Recommended after Phase 39 implementation, with explicit approval for external AI:

```powershell
python scripts/run_multi_doc_eval.py
python scripts/run_phase38_answer_quality_candidate.py --allow-external-ai --budget-usd 2
python scripts/run_permission_eval.py --retrieval-mode vector_lexical_rerank --top-k 5 --rerank-candidate-limit 20 --allow-external-embeddings
python scripts/export_dashboard_data.py
```

## Recommended Next Fixes, Ordered By Value

1. Fix current-version retrieval: require chunks to belong to `documents.current_version_id` in vector and keyword retrievers, then add a regression test with two indexed versions of one document.
2. Stop `docker compose config` secret exposure: move OpenAI key injection to a non-rendered secret pattern or document a safe config command that redacts secrets; rotate the exposed local key if it was real and still active.
3. Add an explicit external-AI approval gate to `scripts/run_multi_doc_eval.py` and either gate or clearly mark older `run_answer_quality_eval.py` and `run_retrieval_experiments.py`.
4. Phase 39: add source-coverage planning for multi-document questions before generation, with per-source retrieval quotas or repair retrieval.
5. Phase 39: add a generalized ambiguity decision step before generation instead of relying mainly on string patterns.
6. Keep deterministic policy responses small and documented; prefer orchestration improvements over more benchmark-specific direct answers.
7. Improve metric labels so final confidence for `not_found`, `refuse_no_access`, and `clarify` is described as confidence in response behavior, not answer factuality.
8. Add embedding/content-hash caching to ingestion before Phase 40 uploaded-document indexing.
9. Add project/department scoped permission regression tests around multi-doc orchestration.

## Training Terminology Check

The requested `rg` scan found no evidence of model fine-tuning, ML training, or `.fit()`-style training code. Relevant code paths use OpenAI embeddings and chat completions, not model training (`apps/api/app/embeddings/openai_embeddings.py:13`, `apps/api/app/generation/answer_generator.py:756`). The word "training" appears in synthetic HR/operations content and documentation, mostly as employee training or evaluation/prompt improvement language.

For this project, "training process" should be described as ingestion, indexing, retrieval, generation, and evaluation, not machine-learning training.

## Final Assessment

The RAG algorithm is broadly consistent, with localized but important inconsistencies. Permission safety is the strongest and most internally consistent part. The biggest correctness gap is stale version retrieval; the biggest product-quality gap is multi-document source coverage; the biggest reporting/security gap is rendered secret exposure from Docker Compose config. Phase 39 should proceed only after the stale-version decision is made, because source planning over stale chunks would make multi-document behavior harder to trust.
