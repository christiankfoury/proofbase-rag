"""Evaluation-only accounting around SDK calls; no application changes.

Reserve an upper bound before every call, including embeddings and grading.
Unknown outcomes keep the reservation and block subsequent external work.
"""
from __future__ import annotations
from contextlib import contextmanager
import json
from pathlib import Path
import threading
from unittest.mock import patch
from scripts.reliable_evaluation_run import write_json_atomic

MAX_BUDGET = 0.75
PRICES = {"gpt-4.1-mini": (0.4, 1.6), "gpt-4.1-mini-2025-04-14": (0.4, 1.6),
          "text-embedding-3-small": (0.02, 0.0)}


class BudgetStop(RuntimeError):
    pass


class Ledger:
    def __init__(self, path: Path, limit: float = MAX_BUDGET):
        if not 0 < limit <= MAX_BUDGET:
            raise ValueError("Budget must be in (0, 0.75]")
        self.path, self.limit = path, limit
        self.lock = threading.Lock()
        self.data = json.loads(path.read_text()) if path.exists() else {"limit_usd": limit, "calls": [], "unknown_outcome": False}
        if self.data["limit_usd"] != limit:
            raise ValueError("Ledger budget cannot change")

    @property
    def spent(self) -> float:
        return sum(row["charged_usd"] for row in self.data["calls"])

    def save(self):
        write_json_atomic(self.path, self.data)

    def invoke(self, operation, original, resource, args, kwargs):
        if args or kwargs.get("stream"):
            raise BudgetStop("Only bounded non-stream SDK calls are supported")
        model = kwargs.get("model")
        if model not in PRICES:
            raise BudgetStop("Unpriced model")
        if operation == "chat":
            requested = kwargs.get("max_completion_tokens", kwargs.get("max_tokens", 2048))
            cap = min(int(requested), 2048)
            kwargs = dict(kwargs)
            if "max_tokens" in kwargs:
                kwargs["max_tokens"] = cap
            else:
                kwargs["max_completion_tokens"] = cap
        else:
            cap = 0
        # UTF-8 bytes bound text token counts conservatively; extra allowance
        # covers role/schema framing. No tools, images, audio, or token arrays.
        if kwargs.get("tools") or kwargs.get("functions"):
            raise BudgetStop("Tools are outside the pricing contract")
        body = json.dumps(kwargs, ensure_ascii=False, default=str).encode("utf-8")
        input_bound = len(body) + 2048
        rate_in, rate_out = PRICES[model]
        reserve = (input_bound * rate_in + cap * rate_out) / 1_000_000
        with self.lock:
            if self.data["unknown_outcome"] or any(c["status"] == "started" for c in self.data["calls"]):
                raise BudgetStop("Unsettled external call; no retry permitted")
            if self.spent + reserve > self.limit:
                self.data["budget_exhausted"] = True
                self.save()
                raise BudgetStop("Pre-call budget reservation exceeds remaining budget")
            row = {"call_index": len(self.data["calls"]), "operation": operation, "model": model,
                   "status": "started", "reserved_usd": reserve, "charged_usd": reserve,
                   "input_bound": input_bound, "output_cap": cap, "input_tokens": None, "output_tokens": None}
            self.data["calls"].append(row)
            self.save()
        try:
            response = original(resource, **kwargs)
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = getattr(usage, "completion_tokens", 0)
            actual = (input_tokens * rate_in + output_tokens * rate_out) / 1_000_000
            if input_tokens > input_bound or output_tokens > cap or actual > reserve:
                raise BudgetStop("Provider usage exceeded declared bounds")
            row.update(status="completed", charged_usd=actual, input_tokens=input_tokens, output_tokens=output_tokens,
                       response_model=getattr(response, "model", model),
                       system_fingerprint=getattr(response, "system_fingerprint", None))
            self.save()
            return response
        except Exception:
            row["status"] = "unknown"
            self.data["unknown_outcome"] = True
            self.save()
            raise

    @contextmanager
    def intercept(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        chat, embed, init = Completions.create, Embeddings.create, OpenAI.__init__
        ledger = self
        def initialize(client, *args, **kwargs):
            kwargs["max_retries"] = 0
            return init(client, *args, **kwargs)
        def chat_call(resource, *args, **kwargs):
            return ledger.invoke("chat", chat, resource, args, kwargs)
        def embedding_call(resource, *args, **kwargs):
            return ledger.invoke("embedding", embed, resource, args, kwargs)
        with patch.object(OpenAI, "__init__", initialize), patch.object(Completions, "create", chat_call), patch.object(Embeddings, "create", embedding_call):
            yield self
