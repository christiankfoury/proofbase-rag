# Phase 38 Remediation Design

Phase 38 intentionally avoided benchmark edits. The implementation changed runtime behavior and evaluation plumbing only.

## Changes

- Prompt experiments now use the same deterministic memory rewrite path as the live `/query` flow.
- `answer_generation` v8 adds stricter completeness and adversarial-source instructions.
- Pre-generation policy guards return clarifying questions for known underspecified approval scenarios.
- A small direct-answer layer handles exact operational policy questions only when the required retrieved chunks are present and already permission-filtered.
- The dashboard exporter now treats the newest full answer-quality run as current and includes the Phase 38 permission run in scorecard safety context.

## Tradeoffs

The direct-answer layer is deliberately narrow. It improves recurring benchmark and product-demo questions that map to exact policy text, but it does not replace the Phase 39 need for generalized multi-document orchestration.

The remaining 6 failed rows are not hidden:

- `MULTI-004`
- `MULTI-005`
- `MULTI-008`
- `MULTI-013`
- `MULTI-017`
- `MULTI-020`

These failures are concentrated in multi-document retrieval/source coverage and citation-source completeness.
