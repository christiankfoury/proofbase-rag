"""Local portfolio verification server with a durable USD 0.50 incremental cap.

Existing USD 5 cumulative authorization only. Not an evaluation or production server.
"""
from contextlib import contextmanager
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.reliable_evaluation_run import write_json_atomic

PRIOR = ROOT / "data/evaluation/quality-remediation-v1/api-ledger.json"
OUT = ROOT / "data/evaluation/portfolio-finish"
RATES = {"gpt-4.1-mini": (Decimal("0.4"), Decimal("1.6")),
         "text-embedding-3-small": (Decimal("0.02"), Decimal("0"))}
FLOOR = Decimal("2.13692667")


class DemoBudget:
    def __init__(self, path=OUT / "api-ledger.json"):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.prior = json.loads(PRIOR.read_bytes())
        self.prefix = self.prior["calls"]
        self.binding = hashlib.sha256(PRIOR.read_bytes()).hexdigest()
        if not self.path.exists():
            write_json_atomic(self.path, {"prior_sha256": self.binding, "prior_spend_usd": str(FLOOR),
                "cumulative_limit_usd": "5", "demo_incremental_limit_usd": "0.50",
                "calls": self.prefix.copy(), "unknown_outcome": False})
        self.data = json.loads(self.path.read_bytes())
        if (self.data["calls"][:len(self.prefix)] != self.prefix or self.data["prior_sha256"] != self.binding
            or self.data["prior_spend_usd"] != str(FLOOR) or self.data["cumulative_limit_usd"] != "5"
            or self.data["demo_incremental_limit_usd"] != "0.50"):
            raise RuntimeError("Demo cost provenance changed")
        self.check()

    def check(self):
        if self.data["unknown_outcome"] or any(r["status"] != "completed" for r in self.data["calls"]):
            raise RuntimeError("Unknown API outcome; no further calls")

    @property
    def spent(self):
        return FLOOR + sum((Decimal(str(r["charged_usd"])) for r in self.data["calls"][len(self.prefix):]), Decimal(0))

    def save(self):
        write_json_atomic(self.path, self.data)

    def invoke(self, original, resource, args, kwargs):
        if args or kwargs.get("tools") or kwargs.get("model") not in RATES:
            raise RuntimeError("Unpriced demo request")
        body = dict(kwargs)
        embedding = body["model"] == "text-embedding-3-small"
        cap = 0 if embedding else min(int(body.pop("max_tokens", body.get("max_completion_tokens", 2048))), 2048)
        if not embedding:
            body["max_completion_tokens"] = cap
        if body.get("stream"):
            body["stream_options"] = {"include_usage": True}
        rate_in, rate_out = RATES[body["model"]]
        input_bound = len(json.dumps(body, ensure_ascii=False).encode()) + 2048
        reserve = (input_bound * rate_in + cap * rate_out) / 1_000_000
        with self.lock:
            self.check()
            if self.spent + reserve > min(Decimal("5"), FLOOR + Decimal("0.50")):
                raise RuntimeError("Demo budget exhausted before call")
            row = {"call_index": len(self.data["calls"]), "status": "started", "model": body["model"],
                   "operation": "embedding" if embedding else "chat", "stream": bool(body.get("stream")),
                   "reserved_usd": str(reserve), "charged_usd": str(reserve)}
            self.data["calls"].append(row)
            self.save()

        def unknown():
            with self.lock:
                row["status"] = "unknown"
                self.data["unknown_outcome"] = True
                self.save()

        def settle(usage):
            inputs, outputs = usage.prompt_tokens, getattr(usage, "completion_tokens", 0)
            if not 0 <= inputs <= input_bound or not 0 <= outputs <= cap:
                raise RuntimeError("Usage exceeds demo reservation")
            with self.lock:
                row.update(status="completed", input_tokens=inputs, output_tokens=outputs,
                           charged_usd=str((inputs * rate_in + outputs * rate_out) / 1_000_000))
                self.save()

        try:
            response = original(resource, **body)
            if not body.get("stream"):
                settle(response.usage)
                return response
        except BaseException:
            unknown()
            raise

        def consume():
            usage = None
            settled = False
            try:
                for chunk in response:
                    if getattr(chunk, "usage", None) is not None:
                        usage = chunk.usage
                    yield chunk
                if usage is None:
                    raise RuntimeError("Stream ended without usage")
                settle(usage)
                settled = True
            finally:
                response.close()
                if not settled:
                    unknown()
        return consume()

    @contextmanager
    def intercept(self):
        from openai import OpenAI
        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings
        chat, embed, init = Completions.create, Embeddings.create, OpenAI.__init__
        def initialize(client, *args, **kwargs):
            kwargs["max_retries"] = 0
            return init(client, *args, **kwargs)
        with patch.object(OpenAI, "__init__", initialize), \
             patch.object(Completions, "create", lambda r,*a,**kw:self.invoke(chat,r,a,kw)), \
             patch.object(Embeddings, "create", lambda r,*a,**kw:self.invoke(embed,r,a,kw)):
            yield


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-external-ai", action="store_true")
    args = parser.parse_args()
    if not args.allow_external_ai:
        raise SystemExit("Explicit --allow-external-ai required; configure existing credentials in environment")
    logs = ROOT / "data/evaluation/local-runs/portfolio-finish"
    for name, file in {"OBSERVABILITY_LOG_PATH":"requests.jsonl", "AUDIT_LOG_PATH":"audit.jsonl",
                       "SECURITY_EVENT_LOG_PATH":"security.jsonl", "SECURITY_NOTIFICATION_LOG_PATH":"notifications.jsonl"}.items():
        os.environ[name] = str(logs / file)
    os.environ["PROOFBASE_TELEMETRY_ENABLED"] = "false"
    os.environ["EXTERNAL_AI_MAX_RETRIES"] = "0"
    import uvicorn
    with DemoBudget().intercept():
        uvicorn.run("apps.api.app.main:app", host="127.0.0.1", port=8001, access_log=False)


if __name__ == "__main__":
    main()
