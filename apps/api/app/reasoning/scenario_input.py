"""Model proposals are interpretation, never authorization or policy evidence."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ScenarioExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

    scope: Literal['row_comparison', 'policy_assertion', 'overall_permission', 'conditional', 'unsupported']
    complete_request: bool
    unhandled_parts: list[str] = Field(max_length=8)
    amount_quote: str | None
    category_quote: str | None
    source_chunk_id: str | None
