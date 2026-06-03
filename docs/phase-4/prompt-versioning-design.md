# Prompt Versioning Design

## Purpose

Prompt versioning makes answer quality measurable. Every chat answer and evaluation run must record the exact prompt version used.

## Prompt Families

Prompt families are stored in `prompts`. Individual revisions are stored in `prompt_versions`.

Prompt types:

- `answer_generation`
- `query_rewriting`
- `citation_validation`
- `evaluation_judge`
- `refusal_policy`

## Prompt Version Fields

- prompt name
- prompt version
- prompt type
- content
- model
- temperature
- created_at
- created_by
- change notes
- active/inactive status

## Example Prompt Metadata

```json
{
  "name": "enterprise_answer",
  "version": "answer_v1",
  "prompt_type": "answer_generation",
  "model": "gpt-4.1-mini",
  "temperature": 0.2,
  "is_active": true,
  "change_notes": "Initial grounded answer prompt with citation and refusal rules."
}
```

## Connection To Evaluation

`evaluation_runs` must store the prompt version used. This allows comparisons such as:

- `answer_v1` vs `answer_v2`
- strict citation prompt vs baseline prompt
- refusal policy version A vs version B

## MVP Prompt Families

Phase 5 should start with:

- `answer_generation`: grounded answer with citations
- `refusal_policy`: no-access and not-found behavior

Later:

- `query_rewriting`
- `citation_validation`
- `evaluation_judge`

## Prompt Change Rules

- Never overwrite prompt version content.
- Create a new version for meaningful prompt changes.
- Record change notes.
- Evaluation results should always reference the prompt version used.
