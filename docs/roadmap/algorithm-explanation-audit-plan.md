# Algorithm Explanation And Audit Plan

Status: the documentation-first audit was completed, and later phases remediated several findings. Use `docs/algorithm/README.md`, `docs/algorithm/review-findings.md`, `docs/roadmap/progress.md`, and `README.md` for current state before treating this plan's Phase 39 handoff notes as active.

## Purpose

This is a documentation-first pass for a new chat where the AI should inspect the Proofbase algorithm and explain whether it makes sense.

The output should help a reader understand the system without already knowing RAG, vector search, benchmark evaluation, prompt versions, or permission-filtered retrieval.

This is not a metric-improvement phase by itself. It should not change retrieval, prompts, benchmark expectations, permission behavior, or dashboard numbers unless the user explicitly turns a finding into implementation work.

## Goal

Create clear Markdown documents under `docs/algorithm/` that explain:

- how a question enters the system
- how project, department, and role scope are applied
- how retrieval candidates are found and ranked
- how permission filtering happens before generation
- how answer generation uses retrieved evidence
- how citations, confidence, and validation are calculated
- how memory is used for query rewriting only
- how multi-document and ambiguity behavior works today
- how the benchmark and dashboard metrics prove or fail to prove quality
- where the algorithm is strong, fragile, confusing, or incomplete

## Required Code Review

Start by reading these areas:

- `apps/api/app/main.py`
- `apps/api/app/retrieval`
- `apps/api/app/services`
- `apps/api/app/prompts`
- `apps/api/app/evaluation`
- `scripts/run_retrieval_experiments.py`
- `scripts/run_answer_quality_eval.py`
- `scripts/run_permission_eval.py`
- `scripts/run_memory_eval.py`
- `scripts/run_multi_doc_eval.py`
- `scripts/export_dashboard_data.py`
- `data/evaluation`
- latest completed `docs/phase-*` notes, especially Phases 32-38

Use `rg` to find the active functions instead of assuming file names are complete.

## Suggested Document Set

Create these files unless the code review shows a better split:

| Document | Purpose |
| --- | --- |
| `docs/algorithm/README.md` | Reading order, high-level mental model, and glossary. |
| `docs/algorithm/end-to-end-flow.md` | Step-by-step request lifecycle from user question to returned answer. |
| `docs/algorithm/retrieval-and-ranking.md` | Vector search, keyword search, hybrid retrieval, reranking, top-k, source coverage, and known tradeoffs. |
| `docs/algorithm/permissions-and-scope.md` | Project/department scope, role filtering, pre-generation permissions, and why restricted chunks must never reach generation. |
| `docs/algorithm/generation-citations-confidence.md` | Prompt versions, response types, citation selection, citation validation, supported claims, confidence, and hallucination controls. |
| `docs/algorithm/memory-and-multi-doc.md` | Session memory, query rewriting, multi-document behavior, ambiguity behavior, and current limitations. |
| `docs/algorithm/evaluation-metrics.md` | Benchmark shape, evaluation runners, dashboard exports, metrics, run IDs, sample sizes, and what each metric proves. |
| `docs/algorithm/review-findings.md` | Findings, design risks, confusing areas, recommended next work, and verification suggestions. |

## Writing Style

- Write for a portfolio reviewer or developer learning the codebase.
- Prefer short sections, numbered flows, tables, and diagrams where useful.
- Define terms the first time they appear.
- Link to code files and phase docs.
- Explain why design choices exist, not only what the code does.
- Mark uncertain interpretations as questions or findings.
- Keep claims honest: say "implemented", "measured", "planned", or "not verified".

## Audit Questions

Answer these in the documents:

- Does permission filtering happen before generation?
- Can unauthorized chunks appear in prompts, citations, memory, logs, or feedback?
- What exactly does memory influence?
- Which retrieval profile is the current best measured reference?
- Why does reranking improve precision, and what does it not solve?
- How are unsupported answers and not-found answers controlled?
- What do citation accuracy and hallucination metrics actually mean?
- What historical failures remained after Phase 38, and what does the current live `/query` scorecard report now?
- Which parts are product-ready, demo-only, or planned?

## Verification

This pass should usually run documentation checks rather than expensive AI evaluations:

```powershell
rg -n "TODO|FIXME|not sure|unknown" docs/algorithm
git diff --check docs/algorithm AGENTS.md docs/roadmap
```

If code examples or imports are changed, broaden verification to:

```powershell
python -m compileall apps scripts
cd apps/web; npm run build
```

OpenAI-backed evaluation runs are not required for this explanation pass unless the user explicitly asks to validate a behavior with live metrics.

## Handoff To Phase 39

After the documentation pass, Phase 39 remains the next implementation phase unless the review findings reveal a more urgent correctness or permission issue.

If findings change the Phase 39 plan, update:

- `docs/roadmap/progress.md`
- `docs/roadmap/post-phase-37-remediation-plan.md`
- the relevant `docs/algorithm/review-findings.md` section
