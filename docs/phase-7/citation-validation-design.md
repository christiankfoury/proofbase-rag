# Citation Validation Design

## Goal

Citation validation checks whether the generated answer is supported by the retrieved chunks it cites.

Phase 7 uses a deterministic heuristic rather than a full LLM judge. This keeps the result explainable and avoids pretending the system has perfect claim-level validation.

## Citation Fields

Each citation includes:

- `document_id`
- `document_title`
- `section_heading`
- `chunk_id`
- `citation_text`
- `source`
- `citation_type`
- `confidence`

## Validation Method

For each citation:

1. Match the citation to a retrieved chunk by `chunk_id`.
2. Compare answer terms with cited chunk terms.
3. Combine:
   - answer/evidence term overlap
   - retrieved chunk rank
   - retrieval score
4. Produce a citation confidence score from `0.0` to `1.0`.

## Confidence Bands

| Score | Meaning |
|---:|---|
| 0.85-1.00 | Strong support |
| 0.70-0.84 | Acceptable support |
| 0.50-0.69 | Weak support |
| Below 0.50 | Not enough support |

If an answer has weak citation support, the answer generator downgrades the response to a cautious partial answer or not-found response.

## Limitations

- This is not full natural-language claim verification.
- It can miss paraphrased support.
- It can over-credit shared terminology.
- A future phase can add an LLM citation judge or reranker.
