# Phase 16 Cost Tracking

## Summary

Phase 16 adds configurable chat-completion cost estimation for live API requests and evaluation summaries.

The estimator uses token counts already returned by the OpenAI chat API and model pricing from `apps/api/app/costing/model_pricing.json`.

Configured default:

| Model | Input | Output | Source |
|---|---:|---:|---|
| `gpt-4.1-mini` | `$0.40 / 1M tokens` | `$1.60 / 1M tokens` | https://openai.com/api/pricing/ |

## What Is Included

- Chat-generation input token cost.
- Chat-generation output token cost.
- Total estimated chat cost per `/query` response.
- Total and average estimated cost in observability summaries.
- Estimated cost in evaluation run exports when token counts are available.
- Backfilled dashboard cost from saved token counts.

Backfill command:

```powershell
python scripts/backfill_cost_estimates.py
python scripts/export_dashboard_data.py
```

## What Is Not Included

- Embedding generation cost during ingestion.
- Database, Docker, hosting, or Azure infrastructure cost.
- Cached-input discounts.
- Batch API discounts.

Those are future production cost-modeling improvements.

## Public Fields

`/query` responses now include:

- `input_cost_usd`
- `output_cost_usd`
- `estimated_cost_usd`
- `pricing_status`

Observability summaries include:

- `total_estimated_cost_usd`
- `avg_estimated_cost_usd`

Recent request logs include:

- `input_cost_usd`
- `output_cost_usd`
- `estimated_cost_usd`
- `pricing_status`

## Pricing Status

- `estimated`: model price and token usage were available.
- `missing_model_price`: token usage exists but no model price is configured.
- `missing_token_usage`: token usage was unavailable.
