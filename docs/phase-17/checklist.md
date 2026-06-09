# Phase 17 Checklist

## Completed

- [x] Added failed-question cause analysis script.
- [x] Generated grouped failure summary JSON.
- [x] Generated readable cause-analysis report.
- [x] Added experimental `answer_generation:v5` prompt for unsupported-answer cleanup.
- [x] Added focused failed-question prompt experiment support.
- [x] Verified Python compile checks.

## Run When `OPENAI_API_KEY` Is Configured

```bash
python scripts/run_prompt_experiment.py --prompt-version v5 --question-filter failed
python scripts/run_prompt_experiment.py --prompt-version v5
python scripts/run_permission_eval.py
python scripts/run_memory_eval.py
python scripts/run_multi_doc_eval.py
python scripts/export_dashboard_data.py
```

## Promotion Gate

- Target bucket `answer_support_issue` should decrease from 4.
- Overall failed-question count should decrease or remain flat with a documented reason.
- Permission leakage must remain `0.000`.
- Hallucination rate must not increase without an explicit tradeoff note.
- Dashboard and README metrics should only be updated after real evaluation output exists.
