# Reproduce the published evidence

## Offline: no account, database, or API calls

From a normal repository checkout with Python 3.12, run:

```powershell
python scripts/build_evaluation_evidence.py --check
python -m unittest scripts.test_evaluation_evidence
```

The verifier uses only the Python standard library and pure scoring helpers. It does not load `.env`, import the API, contact OpenAI, execute holdout cases, or modify evidence. `--check` compares its result with the committed [public-evidence.json](../../data/evaluation/public-evidence.json). CI runs the same checks.

It checks:

- Full, unique coverage of both 130-case regression artifacts against benchmark question text and behavior.
- Recomputed answer-overlap and expected-document citation scores against saved answers and citations.
- Means, metric-specific denominators, and recorded failure counts against summaries.
- All 30 holdout case hashes, order, provenance, single-attempt records, journal chain, completion events, final rows, and final hash.
- Holdout saved-score aggregation, failure IDs, category counts, and safety fields.
- All 20 unauthorized permission cases and the corresponding 20 authorized controls.

The report records canonical-JSON hashes, portable across Windows/Linux checkout line endings. These are reproducibility fingerprints for the report, not replacements for the original raw-byte suite seals. Integrity against committed hashes does not prove external authenticity or semantic correctness. The verifier reaggregates saved holdout scores; it does not rescore facts or create a new generalization measurement.

To intentionally regenerate the report after reviewing a change to its inputs or reporting code:

```powershell
python scripts/build_evaluation_evidence.py
git diff -- data/evaluation/public-evidence.json
```

Do not change historical rows, pass flags, or sealed expectations to make this check pass. Investigate discrepancies instead.

## Evidence paths

| Artifact | Where to inspect |
| --- | --- |
| Benchmark and expected labels | [benchmark-questions.json](../../data/evaluation/benchmark-questions.json) |
| Baseline per-case answers and scores | [Phase 32 raw artifact](../../data/evaluation/expanded-baseline/phase32-expanded-answer-generation-v5.json) |
| Regression per-case answers and scores | [Phase 50 raw artifact](../../data/evaluation/expanded-baseline/phase50-manual-findings-regression.json) |
| Focused permissions | [Phase 46 unauthorized and authorized rows](../../data/evaluation/phase46-permission-evaluation.json) |
| Holdout configuration and custody | [Manifest](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/manifest.json), [authoring record](../phase-49/blind-authoring-record.md) |
| Holdout durable responses | [Case records](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/cases), [final aggregation](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/final.json), [journal](../../data/evaluation/independent-generalization/runs/phase49-independent-holdout-v3/journal.jsonl) |
| Later regression raw data | [Retention index](../../data/evaluation/raw-artifact-index.json), [historical recovery instructions](../evaluation-artifact-retention.md) |

Phase 50 is used for the public offline example because its full 130 rows remain in the current tree. Phase 54's compact regression remains available, but its raw payload was retired to Git history. Neither result measures the current runtime.

## Fresh development run: a different operation

A live run requires the normal local installation, migrated/seeded PostgreSQL database, indexed synthetic corpus, and configured OpenAI credentials. Follow the [README setup](../../README.md#docker-quickstart). Ingestion itself uses paid embeddings. Record the runtime commit, corpus/index state, model, prompt, configuration, and new run ID before running.

Preview the request inventory without calling the provider:

```powershell
python scripts/run_phase39_live_query_answer_quality.py --dry-run --run-id reviewer-development --question-filter all --prompt-version v8 --retrieval-mode vector_lexical_rerank --top-k 5 --multi-doc-mode auto --output-json data/evaluation/local-runs/reviewer-development.json --eval-run-json data/evaluation/local-runs/reviewer-development-summary.json --report-path data/evaluation/local-runs/reviewer-development.md
```

After deliberately approving the external calls, remove `--dry-run` and add `--allow-external-ai --budget-usd 2` to that command. The runner's estimate/budget is not a billing cap covering every embedding, auxiliary model call, or infrastructure charge. Use a unique run ID/output paths for subsequent runs. Local outputs in this example are ignored by Git and do not replace the official dashboard artifacts.

This tests the current runtime on **known development questions**. It cannot reproduce the frozen historical environment merely by selecting the same prompt name. Do not execute or selectively rerun the Phase 47–49 or Phase 55 holdouts. A future generalization measurement requires a new runtime freeze, separately authored and sealed suite, predeclared scoring and budgets, and one complete run.
