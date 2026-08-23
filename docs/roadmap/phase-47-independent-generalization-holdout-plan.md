# Phase 47: Independent Generalization And Holdout Evaluation

Status: planned. This document defines the implementation and evaluation contract for Phase 47. Question authoring, evaluator changes, live OpenAI-backed runs, and runtime remediation have not started.

## Purpose

Proofbase already has a 130-question benchmark (`1.1`) and a 20-probe generalization suite. Both are valuable regression assets, but both have influenced implementation decisions. Phase 47 adds independent evidence that the system works on previously unseen wording, conversations, permission combinations, scopes, and multi-document questions.

The phase should support this bounded portfolio claim:

> Proofbase was evaluated on a separately authored and frozen generalization suite, including a one-time holdout run, while preserving pre-generation permission filtering and reporting failures without tuning against the holdout.

The goal is not to manufacture another perfect score. A valid, reproducible, honestly reported result completes the evaluation work even when quality targets are missed. Missing targets limit the claim and create a future remediation backlog; they do not justify changing holdout expectations or silently rerunning the holdout.

## Current Evidence And Gap

Current measured assets:

| Asset | Size | Role |
| --- | ---: | --- |
| Benchmark `1.1` | 130 questions | Historical baseline, development, and regression comparison. |
| Phase 45/46 generalization probes | 20 probes | Memory, ambiguity, permission, document-reference, and multi-document regression after remediation. |
| Phase 46 permission evaluation | 20 restricted questions | Focused permission-safety evidence. |

Current limitations that Phase 47 addresses:

- No untouched holdout has been run against the current implementation.
- The Phase 45 probes are hardcoded in `scripts/run_generalization_eval.py` and were reused for Phase 46 remediation.
- The main benchmark is role-skewed: Employee `62`, Sales Representative `28`, Manager `23`, IT Admin `10`, and HR Admin `7`.
- Existing memory questions use only two previous-turn entries; longer conversations, corrections, topic switches, and returns to an earlier topic are not systematically covered.
- Prompt-injection and conflicting-source categories have only five questions each.
- Project/department isolation, uploaded-document lifecycle, and current-version behavior are not part of the fixed 130-question benchmark.
- Answer and citation metrics are deterministic approximations; document-level citation accuracy does not prove claim-to-passage support.
- Current perfect regression results do not prove reliability under unseen wording or repeated model runs.

## Locked Phase Decisions

These decisions are part of the Phase 47 contract and should not be casually changed after authoring starts:

1. Preserve benchmark `1.1` and the Phase 45/46 probes unchanged as historical regression assets.
2. Add exactly `100` new cases: `70` development/generalization cases and `30` frozen holdout cases.
3. Use the existing 19-document synthetic corpus for the core suite. Do not expand the corpus merely to increase question count.
4. Allow a small fixture-backed slice for uploaded-document lifecycle and cross-project isolation. Keep its metrics separate when it cannot share the same static corpus assumptions.
5. Keep development and holdout results separate from benchmark `1.1` in artifacts, dashboards, README claims, and portfolio material.
6. Author and validate expected behavior before any live run.
7. Freeze the current runtime configuration before holdout authoring is revealed to the remediation workflow. Record that commit as the frozen runtime commit.
8. Commit the holdout dataset and evaluation-only artifacts after the runtime freeze. The holdout evaluation commit may change evaluation data, validators, runner/reporting code, and documentation, but it must not change the API runtime, prompts, retrieval, generation, permissions, ingestion behavior, or seeded source corpus relative to the frozen runtime commit.
9. Run the holdout once from the clean evaluation commit after verifying the protected runtime paths are unchanged from the frozen runtime commit. Repeat only for a documented infrastructure failure that produced no usable result.
10. Do not change runtime behavior, prompts, retrieval ranking, direct-response rules, or benchmark expectations during the holdout slice.
11. Treat permission leakage and unauthorized chunks reaching generation as hard zero-tolerance gates.
12. Keep memory as query context only; previous turns are never source evidence.
13. Record failures as evidence. Any later remediation must occur in a separately numbered phase and use a new sealed holdout before making a new generalization claim.

## Suite Structure

### Split

| Split | Count | May inspect failures? | May tune against it? | Purpose |
| --- | ---: | --- | --- | --- |
| Development/generalization | 70 | Yes | Yes, in a later explicitly measured remediation slice | Diagnose behavior and exercise tooling. |
| Frozen holdout | 30 | Only after the recorded run | No during Phase 47 | Measure unseen performance against the frozen runtime. |

The holdout authoring and validation workflow must be separated from runtime remediation. Preferred independence, in order:

1. A second human authors the holdout and a maintainer validates source truth.
2. Separate agents author and validate the holdout without performing runtime remediation.
3. If one maintainer must do everything, author the holdout only after the runtime commit is frozen, record that limitation, hash the dataset before execution, and do not inspect or tune runtime behavior between freeze and run.

### Coverage Matrix

| Category | Total | Development | Holdout | Primary risk |
| --- | ---: | ---: | ---: | --- |
| Factual robustness and paraphrases | 15 | 11 | 4 | Keyword dependence, typos, indirect wording, negation, and irrelevant detail. |
| Multi-document and claim coverage | 15 | 10 | 5 | Missing secondary sources, incomplete answers, and claim/citation alignment. |
| Multi-turn memory | 15 | 10 | 5 | Longer conversations, topic switches, corrections, and ambiguous references. |
| Ambiguity boundaries | 10 | 7 | 3 | Answer-versus-clarify-versus-not-found discrimination. |
| Permission and scope pairs | 15 | 10 | 5 | Authorized/unauthorized parity, role boundaries, and scope leakage. |
| Missing information and abstention | 10 | 7 | 3 | Unsupported answers and over-broad refusals. |
| Prompt injection and adversarial behavior | 10 | 7 | 3 | User attacks, retrieved-document instructions, and context exfiltration requests. |
| Conflicting or versioned sources | 5 | 4 | 1 | Current-version selection, conflict disclosure, and stale evidence. |
| Uploaded-document and project isolation | 5 | 4 | 1 | Review/index boundary, citations, department scope, and cross-project isolation. |
| **Total** | **100** | **70** | **30** | |

Coverage must also be checked across these dimensions:

- all five demo roles
- all 19 synthetic documents where the category permits
- easy, medium, and hard difficulty
- answer, clarify, refuse-no-access, and not-found behavior
- one-, two-, three-, and four-source answerable cases where supported by the corpus
- global Dev/Admin scope, project scope, and strict department scope
- zero-turn, two-turn, and four-to-eight-turn conversations
- authorized/unauthorized paired questions using materially equivalent intent

Do not force artificial equality when a role cannot reasonably access a domain. Instead, publish the role/category coverage matrix and explain any zero cells.

## Dataset Contract

Move new cases out of Python constants and into versioned JSON data. Use a dedicated Phase 47 schema rather than silently changing benchmark `1.1`.

Proposed artifacts:

- `data/evaluation/independent-generalization/development-v1.json`
- `data/evaluation/independent-generalization/holdout-v1.json`
- `data/evaluation/independent-generalization/holdout-v1.sha256`
- `data/evaluation/independent-generalization/schema-v1.json`

Each case should contain:

- `case_id`
- `suite_version`
- `split`
- `category`
- `difficulty`
- `user_role` and demo `user_id`
- optional `project_id` and `department_id`
- `previous_turns`
- `question`
- `expected_behavior`
- `required_facts`
- `forbidden_facts`
- `expected_source_documents`
- `expected_source_sections_or_quotes`
- `allowed_documents`
- optional `permission_pair_id`
- optional `fixture_requirements`
- `authoring_notes`
- `review_status`, `reviewed_by`, and `reviewed_at`

`required_facts` should be atomic claims rather than one long expected answer. `forbidden_facts` should capture restricted or incorrect claims whose appearance is a failure even if the rest of the answer is correct.

## Validation Requirements

Add a Phase 47 validator that fails on:

- duplicate case IDs
- incorrect split or category counts
- invalid roles, behaviors, difficulty values, project IDs, or department IDs
- missing required facts for answerable cases
- expected sources not found in the synthetic document metadata
- expected quotes that do not exist in the declared source
- multi-document cases with fewer than two expected sources unless the case explicitly tests source selection rather than synthesis
- permission cases without a permission-pair or explicit restricted-source expectation
- missing-information, clarification, or refusal cases with contradictory answer expectations
- holdout cases missing completed review metadata
- coverage-matrix gaps that violate the locked distribution

The validator should support human-readable output and `--json` for CI or dashboard export.

## Runner Requirements

Create a reusable runner instead of adding another phase-specific hardcoded list.

Required CLI behavior:

```powershell
python scripts/validate_independent_generalization_suite.py
python scripts/run_independent_generalization_eval.py --split development --dry-run
python scripts/run_independent_generalization_eval.py --split development --allow-external-ai --budget-usd 2
python scripts/run_independent_generalization_eval.py --split holdout --allow-external-ai --budget-usd 2 --frozen-runtime-commit <sha>
```

The runner must:

- refuse external calls without `--allow-external-ai`
- enforce a budget before and during execution
- refuse a holdout run when the working tree is dirty, validation fails, the suite hash differs, or protected runtime/corpus paths differ between the checked-out evaluation commit and `--frozen-runtime-commit`
- record both the checked-out evaluation commit and frozen runtime commit, plus corpus hash, suite hash, model, prompt version, retrieval profile, top-k, rerank candidate limit, temperature or determinism settings, project/department scope, start/end timestamps, sample size, and estimated cost
- support `--case-id`, `--category`, and `--limit` only for development; disallow partial holdout execution
- write raw case results, a normalized eval-run artifact, a Markdown report, and a failure matrix
- never overwrite benchmark `1.1`, Phase 45, or Phase 46 artifacts

## Scoring

Retain existing comparable metrics and add clearer claim-level diagnostics.

### Required automated metrics

- expected-source recall
- all-required-sources retrieved
- answer behavior accuracy
- required-fact completeness
- forbidden-fact violation rate
- citation document accuracy
- claim-to-citation support score
- hallucination flag/rate, clearly labeled heuristic
- clarification accuracy
- not-found accuracy
- blocked-answer accuracy
- unauthorized chunk exposure
- restricted citation leakage
- unauthorized chunks reaching generation
- memory rewrite/source recovery quality
- memory-as-evidence violation rate
- latency and estimated OpenAI cost

Report overall results and results by split, category, role, difficulty, scope, source count, and conversation depth. Always show numerators and denominators beside percentages.

### Human review

After the holdout run:

- manually review every automated failure
- manually review at least 10% of automated passes, sampled across categories
- label answer correctness, citation correctness, behavior correctness, evaluator defect, and benchmark defect separately
- preserve the original automated score
- document any adjudication without silently modifying the first-run artifact

An optional LLM judge may be added as a separate experimental metric. It must not replace deterministic metrics or human adjudication, and its prompt, model, cost, and limitations must be recorded.

## Predeclared Quality Targets

These targets control what Phase 47 may claim; they do not control whether an honest evaluation phase is considered implemented.

| Metric | Target | Gate type |
| --- | ---: | --- |
| Permission leakage | `0.000` | Hard gate |
| Unauthorized chunks reaching generation | `0.000` | Hard gate |
| Memory-as-evidence violations | `0.000` | Hard gate |
| Behavior accuracy | `>=0.900` | Portfolio claim gate |
| Required-source recall | `>=0.900` | Portfolio claim gate |
| Answer accuracy / required-fact completeness | `>=0.850` | Portfolio claim gate |
| Citation accuracy | `>=0.900` | Portfolio claim gate |
| Hallucination rate | `<=0.050` | Portfolio claim gate; heuristic limitation remains visible |

If a hard gate fails, do not promote the current retrieval or orchestration configuration. If a portfolio claim gate fails, publish the result and narrow the claim. Do not tune against or rerun the frozen holdout in Phase 47.

## Stability Slice

Before the holdout run, select 20 development cases spanning high-risk categories and execute them three times against the frozen configuration. Report:

- pass consistency per case
- response-type consistency
- source/citation consistency
- mean and range for latency and cost

This is a stability diagnostic, not a reason to cherry-pick the best run. The holdout itself remains one recorded full run.

## Product And Engineering Impact

### App side

- No behavior or feature change is required.
- Do not expose holdout questions in the App UI.
- Existing scoped chat remains the system under evaluation.

### Dev/Admin side

- Add a clearly separated Independent Evaluation section or card.
- Show development and frozen-holdout results separately.
- Show run ID, suite version, sample size, frozen commit, model, retrieval profile, cost, failed-case count, category breakdown, and limitations.
- Do not blend holdout metrics into the historical benchmark scorecard.

### Backend and data model

- No production database migration is expected for the core suite.
- Use JSON artifacts and existing API paths.
- Fixture-backed upload/project-isolation cases may create disposable test data and must verify exact cleanup targets without affecting seeded production-shaped demo data.

## Implementation Sequence

### 47A. Schema And Validation

- Add the dataset schema and validator.
- Move reusable probe execution concepts out of the Phase 45 hardcoded runner where practical.
- Add validator tests for valid and invalid fixtures.
- Publish the coverage report before authoring is considered complete.

### 47B. Development Suite

- Author and independently review 70 development cases.
- Run validation and dry-run checks.
- Capture a live baseline with explicit approval and cost budget.
- Categorize failures without changing holdout content.

### 47C. Runtime Freeze And Stability

- Finish any development-only fixes that are explicitly approved for this phase.
- Rerun benchmark `1.1`, Phase 46 permission safety, and the development suite.
- Freeze and record the runtime Git commit, protected runtime paths, corpus hash, prompt version, model, and retrieval configuration.
- Run the three-pass 20-case stability slice.

### 47D. Holdout Authoring And Freeze

- Author and validate 30 holdout cases using an independent workflow.
- Record review metadata.
- Generate and commit the dataset hash in an evaluation-only commit whose protected runtime and corpus paths still match the frozen runtime commit.
- Do not change runtime behavior after the frozen configuration is declared.

### 47E. One-Time Holdout Run

- Verify a clean evaluation commit, unchanged protected runtime paths relative to the frozen runtime commit, corpus hash, suite hash, credentials, and budget.
- Execute the full 30-case holdout once.
- Preserve raw and normalized artifacts.
- Perform human adjudication without altering the original run.

### 47F. Reporting And Portfolio Handoff

- Export separate Dev/Admin evidence.
- Update README, algorithm evaluation docs, demo material, and limitations.
- State exactly what the result proves and does not prove.
- Create a future remediation backlog from development and holdout findings without implementing holdout-specific fixes in Phase 47.

## Verification

Required local checks:

```powershell
python scripts/validate_benchmark.py
python scripts/validate_independent_generalization_suite.py
python scripts/validate_independent_generalization_suite.py --json
python scripts/run_independent_generalization_eval.py --split development --dry-run
python scripts/run_independent_generalization_eval.py --split holdout --dry-run
python -m compileall apps/api/app scripts
docker compose config --quiet
git diff --check
cd apps/web; $env:NEXT_DIST_DIR='.next-codex-build'; $env:NEXT_TELEMETRY_DISABLED='1'; npm run build
```

Required live checks after explicit approval:

```powershell
python scripts/run_independent_generalization_eval.py --split development --allow-external-ai --budget-usd 2
python scripts/run_permission_eval.py --phase phase-47 --run-id phase47-permission-evaluation --allow-external-embeddings
python scripts/run_phase39_live_query_answer_quality.py --allow-external-ai --budget-usd 2
python scripts/run_independent_generalization_eval.py --split holdout --allow-external-ai --budget-usd 2 --frozen-runtime-commit <sha>
python scripts/export_dashboard_data.py
```

Record actual cost, skipped checks, infrastructure failures, model availability, and any rerun reason. An infrastructure failure may be rerun only when it produced no complete usable holdout result.

## Required Phase Artifacts

- `docs/phase-47/checklist.md`
- `docs/phase-47/design.md`
- `docs/phase-47/coverage-matrix.md`
- `docs/phase-47/development-results.md`
- `docs/phase-47/stability-results.md`
- `docs/phase-47/holdout-results.md`
- `docs/phase-47/human-adjudication.md`
- `docs/phase-47/verification.md`
- raw result JSON under `data/evaluation/independent-generalization/results/`
- eval-run summaries under `data/evaluation/eval-runs/`
- updated `docs/algorithm/evaluation-metrics.md`
- updated `docs/algorithm/review-findings.md`
- updated `docs/roadmap/progress.md`
- README and demo claim updates after measured results exist

## Completion Criteria

Phase 47 is complete when:

- all 100 new cases exist and validate against the locked distribution
- development and holdout splits are reported separately
- the frozen runtime commit, evaluation commit, corpus hash, and holdout hash are recorded
- the one-time holdout run is preserved with provenance and cost
- all permission and memory evidence hard gates are evaluated
- every automated holdout failure and at least 10% of passes receive human review
- existing benchmark and permission regressions are rerun against the frozen runtime
- Dev/Admin and documentation show measured results without blending them into benchmark `1.1`
- limitations and any missed quality targets remain visible
- no holdout-specific runtime remediation is included in the Phase 47 completion commit

## Out Of Scope

- Expanding the synthetic corpus solely to increase sample size.
- Production SSO, hosted storage, or enterprise connectors.
- Replacing deterministic evaluation with an opaque LLM judge.
- Claiming universal hallucination prevention from a synthetic suite.
- Tuning against the frozen holdout.
- Changing benchmark `1.1` expected answers, expected sources, or historical artifacts.
- Hiding or deleting failed holdout cases.

## Stop And Ask Conditions

Pause implementation if:

- a proposed case requires changing permission semantics or project data ownership
- source documents do not provide an unambiguous ground truth
- a new evaluator would change the meaning of existing published metrics
- expected OpenAI cost would exceed the approved per-command budget
- holdout independence cannot be maintained under the documented workflow
- a hard permission gate fails and the cause is not a test-fixture defect
