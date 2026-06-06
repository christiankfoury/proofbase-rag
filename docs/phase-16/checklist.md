# Phase 16 Checklist

- [x] Add configurable chat model pricing.
- [x] Add reusable cost estimator.
- [x] Add cost fields to answer generation.
- [x] Return cost fields from `/query`.
- [x] Write cost fields to observability request logs.
- [x] Aggregate total and average cost in observability summaries.
- [x] Show cost in chat answer panels.
- [x] Show cost in observability dashboard.
- [x] Show cost in evaluation runs table.
- [x] Update evaluation/dashboard export scripts to calculate cost from token counts.
- [x] Add no-LLM backfill script for saved cost artifacts.
- [x] Keep retrieval-only runs cost-null because they do not call the chat model.
- [x] Document embedding and infrastructure cost as future work.
- [ ] Run `python -m compileall apps scripts`.
- [ ] Run `cd apps/web && npm run build`.
- [ ] Run dashboard export and confirm token-backed runs have non-null estimated cost.
