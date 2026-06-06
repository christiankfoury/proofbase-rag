# Phase 10 Recruiter Demo Notes

## Demo Story

The strongest Phase 10 demo story is:

> I built an evaluation dashboard that compares RAG system versions across retrieval quality, answer accuracy, citation correctness, hallucination rate, permission leakage, and memory performance using real benchmark results.

## Suggested Flow

1. Open the overview page and show the headline metrics.
2. Open retrieval experiments and explain that hybrid did not clearly beat vector-only retrieval.
3. Open failed questions and show that failures become the next engineering backlog.
4. Open permission safety and emphasize zero leakage on the restricted benchmark.
5. Open memory evaluation and explain that memory is used only for query rewriting, not as source evidence.

## Talking Points

- This is not a simple PDF chatbot; it is benchmarked and permission-aware.
- The dashboard shows both strengths and weaknesses.
- The project uses real benchmark outputs rather than invented demo numbers.
- The next iteration can target failed multi-document and citation cases.

## Honest Caveats

- Some answer-quality metrics use deterministic and heuristic scoring.
- Estimated chat-generation cost is calculated from configured model pricing where token counts are available.
- The frontend is intentionally minimal and focused on evaluation visibility.
