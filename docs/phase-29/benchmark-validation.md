# Phase 29 Benchmark Validation

## Purpose

Phase 29 adds a validation gate for `data/evaluation/benchmark-questions.json`. The validator is intentionally conservative: it protects the existing benchmark schema and evaluator compatibility before later phases expand documents and questions.

## Validator

Command:

```powershell
python scripts/validate_benchmark.py
```

Optional machine-readable output:

```powershell
python scripts/validate_benchmark.py --json
```

The validator checks:

- required top-level benchmark fields
- declared question count versus actual question count
- required per-question fields
- unique `question_id`
- valid `question_type`, `difficulty`, `user_role`, and `expected_behavior`
- `previous_turns` shape
- conversation-memory questions use `answer_with_memory`
- permission-restricted questions use `refuse_no_access`
- missing-information questions use `say_not_found` and do not name expected sources
- source document IDs referenced by expected sources, allowed documents, and source quotes exist in `data/synthetic-documents`
- category counts for the current corpus

## Current Result

The current benchmark passes validation:

| Category | Count |
|---|---:|
| simple_factual | 20 |
| multi_document | 10 |
| permission_restricted | 10 |
| missing_information | 10 |
| conversation_memory | 10 |
| ambiguous | 5 |
| Total | 65 |

The validator found 14 synthetic source documents.

## Compatibility Notes

- The existing benchmark JSON field names were preserved.
- Existing evaluation scripts continue to read the same fields.
- Permission-restricted questions are allowed to name expected restricted documents that are not in `allowed_documents`, because that is how the current permission suite represents unauthorized access.
- `scripts/validate_benchmark.py` is a local deterministic check and does not call OpenAI.

## Limitations

- The validator checks references and schema shape; it does not judge whether expected answers are semantically correct.
- It does not verify that quoted text exactly appears in the Markdown source yet.
- It does not add the future fields listed in the improvement roadmap, such as `requires_citation`, `should_abstain`, `restricted_documents`, or `document_version`.
