# Confidence Scoring

## Goal

Phase 7 adds explainable confidence scores for answers and citations.

The scores are not treated as perfect correctness probabilities. They are operational signals that help identify weak evidence and risky answers.

## Scores

| Score | Meaning |
|---|---|
| `retrieval_confidence` | How strong the top retrieved evidence appears based on score, rank, and source diversity. |
| `citation_confidence` | How well cited chunks appear to support the generated answer. |
| `answer_confidence` | Whether the answer type and citation support look safe enough to return. |
| `final_confidence` | Combined score returned to the API and evaluation report. |

## Calculation

Retrieval confidence combines:

- top retrieval score
- rank position
- source diversity across top chunks

Citation confidence combines:

- overlap between answer terms and cited evidence
- cited chunk rank
- retrieval score

Final confidence combines retrieval, citation, and answer confidence. For normal answers, citation support receives the most weight. For refusal, not-found, and clarification responses, answer behavior receives more weight.

## Behavior Thresholds

- `0.85-1.00`: strong support
- `0.70-0.84`: acceptable support
- `0.50-0.69`: weak support; answer cautiously
- below `0.50`: not enough support

The system can downgrade weak answers to `partial_answer` or `not_found`.

## Limitations

- Scores are heuristic.
- They are useful for ranking risk and comparing experiments.
- They should not be presented as legal, compliance, or factual certainty.
