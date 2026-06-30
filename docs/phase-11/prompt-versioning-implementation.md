# Phase 11 Prompt Versioning Implementation

Phase 11 adds a simple prompt registry and prompt experiment workflow for the Proofbase.

## What Was Implemented

- Answer-generation prompts are stored as Markdown files with YAML frontmatter.
- Each prompt version records `prompt_id`, `prompt_name`, `prompt_type`, `version`, `status`, `model`, `temperature`, `created_at`, `change_notes`, and owner metadata.
- The answer generator loads prompts by `prompt_name` and `prompt_version` instead of using only hardcoded prompt text.
- API responses and evaluation results include prompt version, model, and temperature metadata.
- Prompt experiments can run the same 60-question benchmark with different answer-generation prompts.

## Prompt Registry Location

```text
apps/api/app/prompts/
  prompt_registry.py
  prompt_loader.py
  versions/
    answer_generation_v1.md
    answer_generation_v2.md
    answer_generation_v3.md
```

## Prompt Versions

| Version | Status | Purpose |
|---|---|---|
| `v1` | active | Current Phase 7/9 structured JSON prompt. |
| `v2` | experimental | Stricter citation requirements and multi-document citation expectations. |
| `v3` | experimental | Stricter not-found and unsupported-claim behavior. |

## Runtime Behavior

The default answer-generation prompt is the active `answer_generation` prompt. Evaluation scripts can pass a specific prompt version, such as `v2`, to compare behavior without editing generation code.

Normal chat requests continue to use the active default unless `prompt_version` is provided.

## Boundaries

- No production A/B testing was added.
- No LangSmith integration was added.
- Prompt versions are repo files, not database rows.
- Evaluation metrics remain deterministic or heuristic unless explicitly marked pending.
