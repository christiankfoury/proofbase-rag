# Phase 13: Multi-Document Reasoning Design

## Problem

9 out of 10 MULTI benchmark questions failed in Phase 11 despite retrieval succeeding (all_sources_hit=1.0 for most). The failures were in generation.

## Root Causes

### 1. Aggressive response type downgrade

`_adjust_response_type()` in `answer_generator.py` used thresholds tuned for single-document answers:
- `citation_confidence < 0.5` → `not_found`
- `citation_confidence < 0.7` → `partial_answer`

Multi-document answers synthesize across two chunks from different documents. The citation validator scores term overlap between the full answer and each individual chunk. When the answer combines two partial contributions, neither chunk scores above 0.6, dragging the average below 0.7 on every clean multi-doc answer.

### 2. "Based on limited supporting evidence" prefix

`_adjust_answer_text()` prepended this phrase whenever `response_type == partial_answer`. For multi-doc questions this appeared even when the answer was accurate, making the system appear uncertain when it wasn't.

### 3. Flat context format losing document structure

`format_context()` presented all 5 chunks in a flat `---` separated list with no visual grouping by source document. The model had to inspect individual `Document ID:` fields to identify which chunks came from which required document, and often missed the secondary source.

## Solution

### Multi-doc detector (`reasoning/multi_doc_detector.py`)

Heuristic detection using cross-domain keyword pairs covering all 10 MULTI patterns. Returns `bool`. No LLM call, no I/O. Fast.

### Query decomposer + multi-source retrieval (`reasoning/query_decomposer.py`)

`decompose_question()`: one GPT-4.1-mini call that generates 2-3 subqueries, one per required document domain.

`retrieve_multi_doc()`: runs `retrieve_chunks()` per subquery with `top_k=4`, deduplicates by chunk_id, re-ranks by score, returns up to 10 chunks. Permission filtering is automatic inside each `retrieve_chunks()` call — no safety changes needed.

### Evidence grouper (`reasoning/evidence_grouper.py`)

Groups merged chunks by `document_id`, preserving rank order within each group. The grouped structure is passed to both the prompt builder and `generate_answer()`.

### Grouped context format (`generation/prompts.py`)

`format_context_grouped()` presents context as clearly separated document sections:
```
=== Document: HR-003 — Remote and Hybrid Work Policy ===

[Section: Approval Requirements]
...

=== Document: IT-002 — Device and BYOD Security Policy ===
...
```

### Multi-doc synthesis prompt (`prompts/versions/answer_generation_v4.md`)

Key additions over v3:
- Explicitly tells the model all documents are relevant
- "Use `answer` if combined context supports the answer, even if no single document is complete"
- "Cite at least one chunk per contributing document"
- "Do not downgrade to partial_answer solely because evidence is split across documents"

### Loosened confidence thresholds

For `multi_doc=True`:
- Not-found threshold: 0.3 (down from 0.5)
- Partial threshold: 0.5 (down from 0.7)
- "Based on limited supporting evidence" prefix suppressed

## Routing in POST /query

```python
multi_doc = is_multi_document_question(retrieval_question)
if multi_doc:
    chunks = retrieve_multi_doc(...)         # decomposed retrieval, top 10
    grouped_docs = group_chunks_by_document(chunks)
else:
    chunks = retrieve_chunks(...)            # existing single-doc path
    grouped_docs = None

answer = generate_answer(
    ...,
    prompt_version=request.prompt_version or ("v4" if multi_doc else None),
    multi_doc=multi_doc,
    grouped_docs=grouped_docs,
)
```

Single-doc questions take the existing fast path unchanged.

## Permission Safety

`retrieve_multi_doc()` calls the existing `retrieve_chunks()` function for each subquery. All permission SQL filtering happens inside those calls. Unauthorized chunks are never returned to the caller. No changes to the permission layer.
