# Phase 12: Observability Design

## Approach

Structured JSONL file logging, not OpenTelemetry. Each POST /query call appends one JSON line to `data/observability/request-logs.jsonl`. A summary script reads the file and produces `data/observability/summary.json` for the dashboard.

This keeps the observability layer simple, dependency-free, and portable.

## Request Log Fields

| Field | Source |
|-------|--------|
| request_id | uuid generated at start of query() |
| timestamp | datetime.now(UTC) at start of query() |
| user_role | QueryRequest.user_role |
| session_id | session_id after session lookup/create |
| question | request.question truncated to 120 chars |
| rewritten_question | rewrite["rewritten_question"] |
| retrieval_mode | config.retrieval_mode |
| chunking_strategy | config.chunking_strategy |
| top_k | config.top_k |
| retrieved_chunk_ids | [c.chunk_id for c in chunks] |
| retrieved_document_ids | deduplicated document IDs from chunks |
| response_type | answer["response_type"] |
| citation_count | len(answer["citations"]) |
| final_confidence | answer["final_confidence"] |
| retrieval_latency_ms | RequestTrace.retrieval_latency_ms |
| generation_latency_ms | RequestTrace.generation_latency_ms |
| total_latency_ms | RequestTrace.total_latency_ms |
| prompt_version | answer["prompt_version"] |
| model | answer["model"] |
| input_tokens | answer["input_tokens"] |
| output_tokens | answer["output_tokens"] |
| estimated_cost | always null — pricing not hardcoded |
| error | exception message if query fails, else null |

## Tracing

`RequestTrace` is a mutable dataclass instantiated once per query call. It uses `time.perf_counter()` for sub-millisecond accuracy. `trace.start("retrieval")` / `trace.stop("retrieval")` bracket the `retrieve_chunks()` call, and similarly for `generate_answer()`. `trace.finish()` records total_latency_ms after message persistence.

## Summary Generation

`scripts/generate_observability_summary.py` reads the JSONL file, computes averages, and writes `data/observability/summary.json` with the last 20 requests embedded as `recent_requests`.

Run after a session of queries:
```bash
python scripts/generate_observability_summary.py
```

## Why JSONL, Not Database

- No schema migration needed
- Easy to inspect and parse
- Safe to delete/rotate without affecting query path
- The query path only writes; reads happen offline via the summary script
