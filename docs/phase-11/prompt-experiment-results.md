# Phase 11 Prompt Experiment Results

Generated at: 2026-06-06T00:17:42.173034+00:00

## Summary

- Best overall prompt: `v2`
- Best citation accuracy: `v2`
- Lowest hallucination rate: `v3`
- Metrics are produced by the deterministic Phase 7 answer-quality scoring pipeline.
- Estimated cost uses configured chat model pricing and excludes embedding/ingestion cost.

## Prompt Version Metrics

| Prompt | Status | Model | Temp | Answer | Citation | Hallucination | Response Type | Confidence | Failed | Input Tokens | Output Tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | active | gpt-4.1-mini | 0.200 | 0.786 | 0.843 | 0.161 | 0.900 | 0.706 | 14 | 31846 | 10449 |
| v2 | experimental | gpt-4.1-mini | 0.000 | 0.857 | 0.871 | 0.188 | 0.917 | 0.708 | 11 | 34260 | 10208 |
| v3 | experimental | gpt-4.1-mini | 0.000 | 0.843 | 0.871 | 0.156 | 0.917 | 0.706 | 11 | 34362 | 10668 |

## Experiment Notes

- `v1`: Current Phase 7/9 structured JSON answer prompt.
- `v2`: Stricter citation requirements; every key claim must map to a cited chunk.
- `v3`: Stricter unsupported-claim and not-found behavior for weak evidence.
