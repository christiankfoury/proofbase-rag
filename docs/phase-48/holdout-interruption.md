# Phase 48 Fresh Holdout Interruption

## What Happened

The one-time sealed holdout started from holdout commit `d134ce3` with runtime frozen at `7bbb8b4`. Cases 1-29 executed exactly once. Before case 30 made any query, upload, embedding, or generation call, the evaluator rejected its generic same-title cross-project fixture because the legacy fixture runner required one of four Phase 47 scenario labels.

This was an evaluation-harness preflight defect, not an API or OpenAI failure. Suite validation had accepted the structurally valid `fixture_requirements` object but had not checked that the fixture runner could instantiate it.

## Preserved Observations

- Executed: `29/30` cases.
- Terminal-observed passes: `19`.
- Terminal-observed failures: `10` (`P48-H2-MD-001`, `P48-H2-MD-002`, `P48-H2-MD-004`, `P48-H2-MM-001`, `P48-H2-MM-002`, `P48-H2-MM-005`, `P48-H2-PS-001`, `P48-H2-PI-001`, `P48-H2-PI-002`, `P48-H2-PI-003`).
- Observed answer-generation cost before interruption: `$0.022619`.
- Untouched case: `P48-H2-UP-001`.

The process stopped before atomically writing its detailed rows. Request logs retain response type, retrieval documents, citation count, latency, and cost, but not complete answer text or citation payloads. Therefore aggregate behavior, recall, completeness, citation, and hallucination metrics cannot be reconstructed exactly and must remain unpublished.

Even if the untouched fixture passes, the best possible case result is `20/30`. Phase 48 therefore cannot meet either the `24/30` meaningful-improvement marker or the `27/30` portfolio target. No improvement claim will be made.

## Bounded Recovery

- Add general fixture support that consumes declared fixture documents rather than case-specific identifiers or wording.
- Commit and review that evaluator-only repair without changing the sealed suite, runtime, corpus, prompt, or scorer.
- Execute only the untouched fixture case once and preserve its detailed result separately.
- Never rerun cases 1-29 or change the Phase 47 historical evidence.
- Publish the interrupted run and incomplete-metric limitation honestly, then queue future improvement behind another newly authored holdout.
