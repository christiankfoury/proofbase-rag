# Phase 48 Runtime-Freeze Verification

## Measured development result

- Run: `phase48-generalization-development`.
- Suite: unchanged `development-v1.json`, 70 cases.
- Result: `70/70` passed.
- Behavior accuracy: `1.000`.
- Required-source recall: `1.000`.
- Required-fact completeness: `0.937`.
- Citation document accuracy: `1.000`.
- Factual hallucination rate: `0.000`.
- Permission leakage, unauthorized generation, and memory-as-evidence hard gates: all zero.
- Estimated OpenAI cost: `$0.043606`.

## Existing regression results

- Benchmark `1.1`, run `phase48-benchmark-regression`: `130/130` passed; answer accuracy `1.000`; citation accuracy `1.000`; hallucination `0.000`; actionable submetric issues `0`; estimated cost `$0.064679`.
- Permission run `phase48-permission-evaluation`, 20 restricted plus 20 authorized retrieval checks: leakage `0.000`; blocked-answer accuracy `1.000`; unauthorized chunk exposure `0.000`; restricted citation leakage `0.000`; unauthorized chunks reaching generation `0.000`; authorized retrieval accuracy `1.000`.
- Memory run `phase48-memory-evaluation`, 20 cases: follow-up detection, rewrite quality, answer accuracy, citation accuracy, and response-type accuracy `1.000`; memory permission leakage and hallucination `0.000`; estimated cost `$0.017963`.
- The final compatibility changes affected only implementation-topic selection and the existing Legal adversarial handler. Targeted development and benchmark checks over those paths passed `4/4` after the full runs.

## Local verification

Passed:

- `python scripts/test_phase34_grounding_controls.py`
- `python scripts/test_phase35_citation_controls.py`
- `python scripts/test_phase38_answer_quality_controls.py`
- `python scripts/test_phase39_live_query_answer_quality.py`
- `python scripts/test_phase39_multi_doc_orchestration.py`
- `python scripts/test_phase46_generalization_remediation.py`
- `python scripts/test_phase47_independent_generalization.py`
- `python scripts/test_phase48_generalization_remediation.py`
- `python scripts/validate_benchmark.py`
- `python scripts/run_phase48_generalization_eval.py --split development --dry-run`
- `python -m compileall apps/api/app scripts`
- `docker compose config --quiet` (passed with the known local Docker config access warning)
- `git diff --check`

## Freeze manifest

- `apps/api/app` tree SHA-256: `e250937cb7313c8dfb487be6aa5be279fc53aa988d5fc75f0305814dc26cd387`.
- Synthetic corpus tree SHA-256: `491ca33d71b16281111eed45aaaacbdfce5e97fe2aaf5916ae90283b1343f870`.
- Development suite SHA-256: `c87696c58229f28ca40efa55de02b13d244bea51af9946b2d20c8267e916e411`.
- Original Phase 47 holdout SHA-256: `10d93cfb229813499721a973ceadabd9045c47b2e5eee29e4dca0ee01b1afb4f`, matching its recorded hash.
- Original Phase 47 holdout/result/report diff: empty.

Runtime/evaluator freeze commit `7bbb8b4af9e5f43e069347f69f2599b652d1a2c8` was reviewed with `git show --stat`, `git show --name-only`, and `git show --check`, then pushed to `origin/main` before fresh-holdout authoring began.

## Fresh holdout outcome

- Sealed holdout commit: `d134ce3`; SHA-256 `394cb6a2accd6c244c86925403ac3b9b320fc504f472254e8830bfc045e3f866`.
- The complete process executed cases 1-29 once, observed `19` passes and `10` failures, then stopped before its atomic row write because the legacy fixture runner did not support the suite's generic fixture declaration.
- Evaluator-only recovery commits `2067479` and `f4c1ef6` added general fixture support without changing runtime, corpus, prompt, scorer, or sealed suite. Only the untouched fixture case was then executed once; it machine-failed on lexical completeness despite a correct, isolated, cited answer.
- Final terminal observation: `19/30` machine passes; estimated answer cost `$0.023159`.
- Aggregate behavior, recall, completeness, citation, hallucination, permission, and memory metrics are unavailable because cases 1-29 lost their detailed in-memory rows before the atomic write.
- Human review: 1 evaluator-only, 6 product, 0 mixed, and 4 indeterminate failures; four fixed passes reviewed with the same retained-evidence limitation.
- No holdout case was rerun, no target was weakened, and no improvement claim is made.
