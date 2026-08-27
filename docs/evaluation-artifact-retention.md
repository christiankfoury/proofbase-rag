# Evaluation Artifact Retention

Proofbase commits compact run summaries, promotion evidence, failure IDs, metric provenance, and the detailed rows required by active defense manifests. Large per-question runtime payloads are local build artifacts by default.

## Policy

- `data/evaluation/eval-runs/` contains compact dashboard and regression summaries.
- `data/evaluation/defense/` may contain bounded detailed development-suite evidence when a manifest validates its hash and case count.
- `data/evaluation/local-runs/` contains raw per-question runtime payloads and is ignored by Git.
- Raw runtime artifacts promoted during Phases 52-54 are indexed in `data/evaluation/raw-artifact-index.json`. Their byte counts and SHA-256 values remain recorded, and their original bytes remain recoverable from historical commit `9a22a02`.
- A normal retention change must not rewrite shared Git history. Historical-object removal is a separate destructive maintenance operation requiring explicit approval and coordinated recloning.

Run `python scripts/manage_evaluation_artifacts.py` to validate that retired raw files are absent, compact summaries remain available, detailed defense results have valid hashes, and the Phase 54 memory evidence is preserved.

The live query evaluator writes its detailed JSON to `data/evaluation/local-runs/` unless an operator supplies an explicit `--output-json` path. It continues to write the compact dashboard summary and Markdown report to their declared locations.

## Recovering historical raw evidence

Use Git object inspection without restoring the file into the current tree:

```powershell
git show 9a22a02:data/evaluation/expanded-baseline/phase54-live-query-regression-v5.json
```

The artifact index contains the equivalent path, original byte count, row count, SHA-256, and retained compact-summary path for every retired file.
