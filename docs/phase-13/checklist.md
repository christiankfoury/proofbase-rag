# Phase 13 Checklist

## Part A: Multi-Document Reasoning

- [x] apps/api/app/reasoning/ package created
- [x] multi_doc_detector.py — heuristic cross-domain detection
- [x] query_decomposer.py — LLM decomposition + retrieve_multi_doc()
- [x] evidence_grouper.py — group chunks by document
- [x] answer_generation_v4.md — multi-doc synthesis prompt
- [x] generation/prompts.py — format_context_grouped() and build_multi_doc_user_prompt()
- [x] generation/answer_generator.py — multi_doc + grouped_docs params; loosened thresholds; suppressed prefix
- [x] main.py — multi-doc routing in POST /query (v4 prompt default for multi-doc)
- [x] evaluation/multi_doc_metrics.py — source_coverage_score, all_required_sources_cited, multi_doc_summary
- [x] scripts/run_multi_doc_eval.py — baseline vs multi-doc comparison

## Part B: Live Observability

- [x] apps/api/app/observability/summary.py — compute_live_summary() reads JSONL directly
- [x] main.py GET /observability/summary — updated to use compute_live_summary()
- [x] main.py GET /observability/recent-requests — new lightweight endpoint
- [x] apps/web/components/ObservabilityRefresh.tsx — client component with 15s auto-refresh
- [x] apps/web/app/observability/page.tsx — updated with RefreshBar and live description

## Documentation

- [x] docs/phase-13/checklist.md
- [x] docs/phase-13/multi-document-reasoning-design.md
- [x] docs/phase-13/query-decomposition-design.md
- [x] docs/phase-13/live-observability-design.md
- [x] docs/phase-13/multi-document-failure-analysis.md

- [x] Run scripts/run_multi_doc_eval.py and record results
- [x] Full benchmark regression check (v1 prompt, 60 questions — no regressions confirmed)
- [x] README updated with Phase 13 commands and results
