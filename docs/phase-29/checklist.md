# Phase 29 Checklist

Goal: add benchmark schema and source-reference validation without breaking existing evaluation scripts or changing measured results.

## Implemented

- Added `scripts/validate_benchmark.py`.
- Validates top-level benchmark fields and declared `question_count`.
- Validates required per-question fields used by current evaluators.
- Checks unique `question_id` values.
- Checks valid `question_type`, `difficulty`, `user_role`, and `expected_behavior` values.
- Checks `previous_turns` shape and conversation-memory consistency.
- Checks permission-restricted, missing-information, and answerable question behavior rules.
- Checks source-document references against Markdown corpus `document_id` metadata.
- Reports category counts for the current benchmark corpus.
- Added validator to README and final cleanup evaluation command lists.

## Not Implemented

- No benchmark question content changed.
- No new benchmark fields were added.
- No retrieval, prompt, scoring, dashboard metric, or permission model behavior changed.
- No OpenAI-backed evaluation run was executed.

## Recruiter Demo Note

Phase 29 strengthens the engineering-manager proof: benchmark data can now be validated before metrics are refreshed, reducing the chance that broken source references or malformed questions corrupt future evaluation runs.
