from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestTrace:
    """Per-request timing context. One instance per query call, never shared."""

    _checkpoints: dict[str, float] = field(default_factory=dict, repr=False)
    _started_at: float = field(default_factory=time.perf_counter, repr=False)
    retrieval_latency_ms: int | None = None
    generation_latency_ms: int | None = None
    total_latency_ms: int | None = None

    def start(self, step: str) -> None:
        self._checkpoints[f"{step}_start"] = time.perf_counter()

    def stop(self, step: str) -> None:
        start = self._checkpoints.get(f"{step}_start")
        if start is not None:
            setattr(self, f"{step}_latency_ms", int((time.perf_counter() - start) * 1000))

    def finish(self) -> None:
        self.total_latency_ms = int((time.perf_counter() - self._started_at) * 1000)

    def as_dict(self) -> dict[str, Any]:
        return {
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "generation_latency_ms": self.generation_latency_ms,
            "total_latency_ms": self.total_latency_ms,
        }
