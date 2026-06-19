# Phase 25 Result Verification And Human Review Design

## Goal

Phase 25 adds a human review workflow so answer quality, citation quality, and feedback-derived evaluation candidates are reviewed before they affect benchmark work.

## Review Sources

The first review queues come from existing Dev/Admin proof surfaces:

- failed benchmark questions
- recent negative feedback

This keeps the workflow tied to real failure and feedback data instead of adding synthetic review tasks.

## Labels

The workflow uses the existing project scoring shape:

- `1.0 correct`
- `0.5 partial`
- `0.0 incorrect`

Evaluators label answer correctness and citation correctness independently.

## Decisions

Review decisions are:

- `needs_fix`
- `evaluation_candidate`
- `approved_reference`
- `rejected`

`evaluation_candidate` means the item can be considered for benchmark authoring later. It does not mutate benchmark JSON or automatically rerun evaluation.

## Persistence

Reviews are stored in the new `evaluation_reviews` table with:

- source type and source ID
- question and answer
- expected answer and expected sources
- actual citations and retrieved chunks
- answer and citation labels
- decision
- reviewer metadata
- notes

Saving a review also logs an `evaluation_review_saved` audit event.

## Limitations

- There is no assignment workflow.
- There is no benchmark-JSON promotion button.
- Approved candidates still require a later authoring/export step.
- Live save verification against Postgres was not run during implementation.
