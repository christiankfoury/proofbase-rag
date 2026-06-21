# Phase 35 Checklist

- [x] Start from Phase 34 answer-grounding results and citation failures.
- [x] Classify citation failures into wrong document, wrong chunk, missing citation, unsupported claim, and restricted-source categories.
- [x] Add Dev/Admin failed-question evidence for citation failure categories and document gaps.
- [x] Add verifier-backed citation backfill that only uses retrieved, permission-filtered chunks.
- [x] Add `answer_generation` v7 citation-alignment prompt candidate.
- [x] Narrow over-broad missing-information guards that blocked answerable password-sharing and roadmap-promising policy questions.
- [x] Run local citation-control tests, benchmark validation, compile checks, and dashboard export.
- [x] Run live Phase 35 answer-quality evaluation on benchmark v1.1 after explicit external OpenAI approval.
- [x] Verify citation accuracy >= 0.92 and stretch target >= 0.95.
- [x] Verify hallucination does not increase from Phase 34.
- [x] Verify permission leakage remains 0.000 with the matching top-k 5 retrieval configuration.
