# Phase 49 Verification

Status: reliability implementation verified locally and ready to freeze; fresh blind measurement pending.

Hardened evaluator freeze: `3d3706e4bbe1b42a18d3a4909464cdad63dfbedc` (reviewed and pushed before blind holdout authoring).

## Reliability Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Unsupported fixture before execution | Passed | Static fixture preflight returns an error and the fake external executor remains at zero calls. |
| Interruption before case 1 | Passed | Recovery begins at case 1; 30 unique calls total. |
| Interruption during an arbitrary case boundary | Passed | Completed prefix remains durable; recovery executes only remaining cases. |
| Interruption after case 29 | Passed | Recovery executes case 30 only. |
| Atomic record persistence interruption | Passed | Full result is recovered from the fsynced journal; the affected external call remains single. |
| Final aggregation interruption | Passed | Manifest stays incomplete; recovery rebuilds from all persisted rows without external calls. |
| Uninterrupted/recovered equivalence | Passed | Deterministic test artifacts are exactly equal and call IDs remain unique. |
| Duplicate/corrupt/missing state | Passed | Corrupt/unexpected records fail closed; a missing file with an intact journal is explicitly recovered. |

Command:

```powershell
python scripts/test_phase49_evaluation_reliability.py
```

## Broad Checks Before Evaluator Freeze

| Command | Status | Notes |
| --- | --- | --- |
| `python scripts/test_phase47_independent_generalization.py` | Passed | Historical suite validation and permission-scoring regression remain intact. |
| `python scripts/test_phase48_generalization_remediation.py` | Passed | Phase 48 scoring/runtime regression tests remain intact. |
| `python -m compileall apps/api/app scripts` | Passed | Hardened runner and supporting modules compile. |
| `python scripts/export_dashboard_data.py` | Passed | Required the established elevated Windows write path after sandboxed replacement of generated JSON was denied. |
| `cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build` | Passed | Sandboxed Node hit the known profile `EPERM`; the established elevated build passed all type and production-build checks. Build-generated `next-env.d.ts` and `tsconfig.json` edits were not retained. |
| `docker compose config --quiet` | Passed | Emitted the known inaccessible Docker config warning. |
| `git diff --check` | Passed | No whitespace errors. |

No OpenAI call, holdout execution, prompt/runtime change, or Phase 47/48 rerun occurred during the reliability implementation.

## Blind Suite Validation

- Blind author: isolated clean-context agent restricted to the synthetic corpus, schema v3, and neutral suite constants/distribution.
- Independent validator: separate isolated clean-context agent restricted to the new draft, schema v3, and synthetic corpus.
- Approved cases: `30`; unique case IDs/hashes: `30/30`.
- Locked category distribution: passed exactly.
- Coverage: all five roles, all three difficulties, all four behaviors, all three scope forms, two permission pairs, and 16 corpus documents.
- Corpus validator: passed with no errors or warnings.
- Reliable execution preflight: initially rejected both upload fixture documents for missing explicit `restricted` declarations; the isolated validator added `restricted: false` to those two declarations only, documented the correction, and the rerun passed with no errors.
- Sealed suite SHA-256: `22e7bfbc36469dc7b7f1aad8586ef480c607094295dc26f9451f8609307b2d8c`.
- Frozen RAG runtime commit: `7bbb8b4af9e5f43e069347f69f2599b652d1a2c8`.
- Hardened evaluator commit: `3d3706e4bbe1b42a18d3a4909464cdad63dfbedc`.
- Maximum live command budget: `$2.00`.

The blind author transparently recorded that its first allowed common-module read displayed the full module rather than a constants-only slice. It did not open or follow any referenced prior holdout, result, failure, runtime, remediation, or Git artifact. The independent validator had no access to that module or to any Phase 47/48 evidence.

The Phase 48 artifact, 19/30 observation, `$0.023159` cost, unavailable aggregate metrics, and adjudication counts were not changed or reconstructed.
