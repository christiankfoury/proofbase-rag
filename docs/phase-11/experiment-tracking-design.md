# Phase 11 Experiment Tracking Design

Prompt experiments use a small configuration object rather than a full experiment platform.

## Experiment Config

Each run records:

- `experiment_id`
- `run_name`
- `phase`
- `retrieval_mode`
- `chunking_strategy`
- `top_k`
- `prompt_name`
- `prompt_version`
- `model`
- `temperature`
- `confidence_thresholds`
- `citation_validation_mode`
- `notes`

Example:

```json
{
  "experiment_id": "phase11-answer-generation-v2",
  "run_name": "answer-generation-v2",
  "phase": "phase-11",
  "retrieval_mode": "vector_only",
  "chunking_strategy": "section_based",
  "top_k": 5,
  "prompt_name": "answer_generation",
  "prompt_version": "v2",
  "model": "gpt-4.1-mini",
  "temperature": 0,
  "citation_validation_mode": "heuristic",
  "notes": "Stricter citation requirements and multi-document citation expectations."
}
```

## Output Files

Prompt experiment runs are stored in:

```text
data/evaluation/prompt-experiments/
```

Each run includes:

- experiment metadata
- prompt metadata
- run summary metrics
- per-question results
- failed-question records

The dashboard export reads these result files and appends Phase 11 runs to the existing evaluation dashboard.

## Comparison Rules

`v1` is treated as the baseline because it is the current active answer-generation prompt.

New versions are compared to `v1` by:

- questions fixed
- questions broken
- questions still failing
- answer accuracy
- citation accuracy
- hallucination rate
- response type accuracy
- failed question count

Regressions are not hidden.
