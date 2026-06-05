# Query Rewriting Design

## Purpose

Follow-up questions often omit the subject from the previous turn. Query rewriting turns the follow-up into a standalone retrieval query.

Example:

```text
Previous topic: parental leave policy
Follow-up: Does that apply to adoptive parents too?
Rewritten query: Does the parental leave policy apply to adoptive parents?
```

## Implementation

Phase 9 uses deterministic heuristics instead of an LLM classifier.

The rewriter stores:

- original question
- rewritten question
- whether follow-up was detected
- whether memory was used
- rewrite strategy
- previous topic

## Supported Benchmark Rewrites

- vacation carryover
- temporary remote work location duration
- restricted data on personal devices
- standard implementation timeline
- formal performance review timing
- parental leave adoptive-parent follow-up

## Limitations

This is intentionally simple. A future phase can replace or augment it with an LLM query-rewriting prompt and evaluation judge.

