# Phase 7 Answer Generation Design

## Goal

Phase 7 improves answer quality after retrieval. The default retrieval configuration remains the best Phase 6 setup:

```json
{
  "retrieval_mode": "vector_only",
  "chunking_strategy": "section_based",
  "top_k": 5
}
```

Hybrid retrieval remains available as an experimental option, but it is not the default because Phase 6 did not show it clearly outperforming vector-only retrieval.

## Response Types

The answer generator now returns structured response types:

- `answer`
- `partial_answer`
- `not_found`
- `refuse_no_access`
- `clarify`

These map to the benchmark behaviors used in Phase 3:

- `not_found` maps to `say_not_found`
- `clarify` maps to `ask_clarifying_question`
- `partial_answer` maps to `answer`
- `refuse_no_access` maps to `refuse_no_access`

## Prompt Behavior

The prompt tells the model to:

- answer only from retrieved context
- cite every factual claim
- use document IDs, titles, section headings, and chunk IDs
- return `not_found` when evidence is missing
- return `refuse_no_access` when access is insufficient
- return `clarify` when the question is ambiguous
- return `partial_answer` when evidence is weak or incomplete
- avoid unsupported assumptions
- return valid JSON

## Runtime Behavior

The generator:

1. Formats retrieved chunks with document metadata and source text.
2. Requests a structured JSON answer.
3. Parses model citations.
4. Matches citations back to retrieved chunks.
5. Validates citations.
6. Computes confidence scores.
7. Downgrades weakly supported answers to `partial_answer` or `not_found`.

This keeps the system practical while avoiding fake semantic-judge scores.
