# Efficient execution policy

Approved workflow maintenance, 2026-09-28. This policy supports AGENTS.md; it is
not a second feature roadmap. The current-position section of progress.md links
the one active implementation plan. Historical notes remain evidence, not queues.

## Work unit and completion

Before implementation, record a short goal, affected surface, acceptance criteria,
required artifacts/checks, non-goals and stopping conditions in the phase note.
Use a checklist only as detailed as the work needs. A work unit is complete when
its criteria pass (or its predeclared failed-result deliverable is published),
blocking review findings are resolved, limitations are recorded, and intended
commits are verified/pushed. Failed mandatory safety gates never mean release-ready.
Record optional discoveries in the backlog rather than expanding the current unit.

Loop: plan -> implement -> focused verification -> semantic diff review -> commit
-> commit-content check -> push. Batch related documentation and implementation
changes. Fix review findings before the commit; review only new deltas afterward.
Preserve separate freeze/seal/result commits required by evaluation custody.

## Verification matrix

Choose all applicable rows. Record exact commands/results and skips in the phase
note. Inspect scripts before invoking unfamiliar commands; live calls are never
an incidental consequence of a documentation check.

| Changed area | During development | Completion gate |
| --- | --- | --- |
| Documentation/workflow only | Inspect changed prose, local links, contradictory instructions; `git diff --check` | Complete intended diff review; no app build/API calls unless executable examples or behavior also changed |
| Evaluator/prompts/runner | Focused contract, parsing, reducer, ledger and failure-path tests; relevant Python compilation | Relevant frozen-report replay and evidence integrity; versioned development calibration/confirmation when semantics change; no automatic frontend build |
| API/service/data model | Focused unit/integration tests and compilation of changed modules | Shared API-contract, migration/rollback and authorization tests when affected; frontend checks if its contract changed |
| Retrieval/generation/memory/permissions | New development before/after cases and negative controls | Relevant permission/scope, citation, memory and shared RAG regressions; authorized-evidence invariant checks; live checks as declared by active plan |
| Frontend/shared UI contracts | Focused interaction/type checks | `npm run build` in apps/web and relevant browser smoke; inspect visible claims against evidence |
| Benchmark/evidence/reporting | Schema validation and affected report replay | `python scripts/validate_benchmark.py` when benchmark/schema affected; preserved historical hashes/replay; build/smoke if published UI data changes |
| Dependencies/Compose/infrastructure/config | Applicable lockfile/config checks; `docker compose config` for Compose changes | Affected integration/security checks and builds; no provisioning implied |
| Frozen measurement/release | Full declared preflight, custody and environment checks | Exact-runtime requirements, sealed hashes, isolation/authorization gates, complete raw evidence and honest results; never replace these with cached development checks |

Select existing focused scripts from the affected source/phase notes; do not run
every historical suite solely because it exists. Broaden when shared behavior,
security, dependencies, configuration or failures justify it. Required permission
tests, historical replay and holdout integrity are not optional optimizations.

## Reusing verification

Record the tested commit or working diff, commands, relevant environment/config,
dependencies and results. Passing evidence remains usable only while all inputs
that could affect it are unchanged. A commit, prose edit or push alone does not
require rerunning unrelated tests. Failed, stale, unknown or environment-dependent
checks cannot be silently reused. Report reuse explicitly; never label it a fresh
run. Exact-commit gates still run against their required frozen revision.

When unrelated working changes exist, establish that checks do not rely on them.
Use an isolated checkout if needed rather than testing a mixed tree and claiming
the outgoing commit passed. Avoid resetting or stashing the user's files.

## Push with unrelated local changes

The staging area must be empty after committing, but the working tree need not be.
Identify unrelated paths and preserve them. Review every outgoing commit using
the upstream range (for example `git log --oneline @{upstream}..HEAD`, appropriately
quoted in PowerShell), and verify only intended reviewed work is sent. A dirty
request log is not itself a blocker. Unknown commits, related uncommitted changes,
divergence or blocking review findings are blockers; do not force-push.

## Generated runtime files

- New local runs should set `OBSERVABILITY_LOG_PATH=data/observability/local-runs/request-logs.jsonl`.
  This ignored directory holds ephemeral development logs; do not stage it.
- The application still defaults to the legacy tracked request-log path. Existing
  services must be explicitly configured for the override; this policy does not
  migrate them. Preserve the tracked file and existing local edits for now. They
  are allowed unrelated changes, not material to include in normal commits.
- Keep reproducible test fixtures synthetic and separate from live append-only
  logs. Commit reviewed, bounded evidence artifacts only where the measurement
  protocol requires them; never blanket-ignore evaluation evidence or ledgers.
- No deletion, truncation, untracking or historical rewrite of existing logs is
  authorized merely to obtain a clean Git status. A default-path migration is
  separate runtime work with dashboard/export compatibility checks.

## Compact handoff and efficiency record

Maintain this block in the relevant phase note; progress.md links it. Update it
at work-unit boundaries or before handing off, not after every command:

```text
Goal / acceptance criteria / non-goals:
Current branch and commit; outstanding diff:
Completed work and remaining issue:
Verification: commands, results, tested revision/diff, relevant config; reused/skipped checks:
Review findings and disposition:
Next action or exact command:
Blockers / stop condition:
Elapsed work time; test/build runs and justified repeats; external call count/cost:
```

Use actual measurements when available and label estimates or unavailable values.
Do not invent token counts or percentage savings. Keep detailed output in existing
artifacts rather than copying it across Markdown files. Measure at phase/work-unit
boundaries so bookkeeping does not become another source of repeated work.

## Development and measurement boundary

The current user scope and the active plan's latest handoff take precedence over
historical standing execution authorization. The 2026-10-02 bounded redesign
superseded planning-only scope and then stopped at its application budget preflight.
Do not restart completed R1-R4 steps, paid continuations or another redesign cycle
automatically; preserve failed candidates, stop conditions and original gates.

Use cheap development cases for iteration. Full calibration/confirmation is a
declared gate; fresh holdouts are authored only after the runtime freeze and run
once. No selective reruns, exposed-case tuning or expectation changes for score.
For historical Phases 71-73 execution, the quality-completion plan's 2026-09-29 standing
authorization supersedes earlier candidate-count approval limits. Continue
cause-driven remediation without routine approval, with one bounded execution
per declared stage, preserved failed evidence and fresh post-freeze confirmation.
Do not repeat unchanged candidates, weaken scoring, tune on exposed holdouts or
continue without a defensible failure hypothesis. Escalate actual safety, custody,
unknown-cost or external-state blockers, not ordinary validation failures.
