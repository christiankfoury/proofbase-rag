# Phase 13: Live Observability Design

## Problem

Phase 12 observability required running `python scripts/generate_observability_summary.py` before the dashboard showed any data. The summary was a stale pre-computed file.

## Solution

Replace static file reading with an in-process computation that reads the JSONL log directly on every API call.

## New Module: `apps/api/app/observability/summary.py`

```python
def compute_live_summary(limit: int = 20) -> dict
```

Reads `data/observability/request-logs.jsonl` on every call, parses entries, computes averages, returns the last `limit` requests as `recent_requests`. No file caching, no script dependency.

Returns a stub `{"status": "not_generated", ...}` if the JSONL file doesn't exist yet (e.g., no queries have been sent).

## Updated Endpoints

`GET /observability/summary` — now calls `compute_live_summary(limit=20)` directly. Returns fresh data on every request.

`GET /observability/recent-requests` — alias with configurable `limit` parameter.

## Frontend Auto-Refresh

`ObservabilityRefresh` is a client component (`"use client"`) that:
- Calls `router.refresh()` every 15 seconds via `setInterval`
- Shows "Last updated: {time}" so the user can see when data was last fetched
- Has a manual Refresh button

`router.refresh()` re-runs the server component, which re-fetches from `GET /observability/summary`, which calls `compute_live_summary()`. No client-side fetch duplication.

## Performance

For Phase 13 scale (hundreds of requests), reading the JSONL file on every dashboard load takes < 5ms. If the file grows to tens of thousands of entries in a future phase, add tail-reading with a bounded deque.

## `generate_observability_summary.py` Script

The script remains available for generating a static `summary.json` file for offline analysis or exporting. It is no longer required for the dashboard to work.

## Fields Returned

Same shape as Phase 12 `ObservabilitySummary` TypeScript type:
- `generated_at`, `total_requests`
- `avg_total_latency_ms`, `avg_retrieval_latency_ms`, `avg_generation_latency_ms`
- `avg_final_confidence`, `avg_input_tokens`, `avg_output_tokens`
- `estimated_cost: null`
- `recent_requests: [...]` (last N entries from JSONL)
