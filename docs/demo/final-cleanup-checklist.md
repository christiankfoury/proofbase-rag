# Final Cleanup Checklist

Use this before recording screenshots, publishing the project, or sending it to recruiters.

## Repository Hygiene

- [ ] Confirm no real secrets are committed.
- [ ] Confirm `.env` is ignored.
- [ ] Review `data/observability/request-logs.jsonl` before committing because it is runtime data.
- [ ] Keep only intentional generated evaluation artifacts.
- [ ] Confirm README links resolve.
- [ ] Confirm docs do not claim Azure deployment is complete.

## Local Verification

Run:

```powershell
python -m compileall apps scripts
docker compose config
docker compose build
docker compose run --rm api python scripts/setup_db.py
docker compose run --rm api python scripts/ingest_markdown.py --apply-schema --chunking-strategy section_based
docker compose run --rm api python scripts/run_smoke_test.py --api-base-url http://api:8000
```

If a check is skipped because it calls OpenAI, document that clearly.

## Dashboard Verification

- [ ] Open `/`.
- [ ] Open `/retrieval-experiments`.
- [ ] Open `/permission-safety`.
- [ ] Open `/memory-evaluation`.
- [ ] Open `/multi-doc`.
- [ ] Open `/observability`.
- [ ] Open `/audit`.

## Evaluation Commands

Run when refreshing metrics:

```powershell
docker compose run --rm api python scripts/run_retrieval_experiments.py
docker compose run --rm api python scripts/run_answer_quality_eval.py
docker compose run --rm api python scripts/run_permission_eval.py
docker compose run --rm api python scripts/run_memory_eval.py
docker compose run --rm api python scripts/run_multi_doc_eval.py
docker compose run --rm api python scripts/export_dashboard_data.py
```

## Final Portfolio Readiness

- [ ] README explains what the project is in the first screen.
- [ ] Final metrics use real numbers only.
- [ ] Demo script has exact questions and expected behavior.
- [ ] Resume bullets are copied into the resume or project page.
- [ ] Screenshots are captured and reviewed.
- [ ] Known limitations and roadmap are visible.
