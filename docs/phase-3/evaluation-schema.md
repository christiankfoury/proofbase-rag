# Evaluation Schema

The benchmark dataset lives at `data/evaluation/benchmark-questions.json`.

## Top-Level Shape

```json
{
  "benchmark_version": "1.0",
  "created_for_phase": "phase-3",
  "source_corpus": "data/synthetic-documents",
  "question_count": 60,
  "questions": []
}
```

## Question Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `question_id` | string | Yes | Stable ID such as `FACT-001` |
| `question_type` | string | Yes | Benchmark category |
| `difficulty` | string | Yes | `easy`, `medium`, or `hard` |
| `user_role` | string | Yes | Role used for permission filtering |
| `question` | string | Yes | User question |
| `previous_turns` | array | Yes | Prior conversation turns, empty for non-memory items |
| `expected_behavior` | string | Yes | Expected agent behavior |
| `expected_answer` | string | Yes | Supported answer, refusal, not-found response, or clarification |
| `expected_source_document` | array | Yes | Source document IDs for answerable or restricted-source tests |
| `expected_source_section_or_quote` | array | Yes | Source sections and quotes supporting expected behavior |
| `allowed_documents` | array | Yes | Documents the user role may retrieve |
| `evaluation_notes` | string | Yes | What the item tests |

## Enums

User roles:

- `Employee`
- `Sales Representative`
- `Manager`
- `HR Admin`
- `IT Admin`

Expected behaviors:

- `answer`
- `refuse_no_access`
- `say_not_found`
- `ask_clarifying_question`
- `answer_with_memory`

Question types:

- `simple_factual`
- `multi_document`
- `permission_restricted`
- `missing_information`
- `ambiguous`
- `conversation_memory`

Difficulty:

- `easy`
- `medium`
- `hard`
