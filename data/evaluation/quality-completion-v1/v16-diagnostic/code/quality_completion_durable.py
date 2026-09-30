"""Local write resilience only; the provider is always called at most once."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import time
from scripts.quality_completion_ledger import Ledger as PreviousLedger
from scripts.quality_eval_transport_v15 import reserve, exclusive_lock, MODEL, INPUT_RATE, OUTPUT_RATE
from scripts.quality_eval_transport_v12 import BudgetStop


def write_json_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    # Antivirus/indexer sharing violations may briefly block replacement on Windows.
    # Retry only the same local rename, never an API request or a grade.
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (2 ** attempt))


class Ledger(PreviousLedger):
    def call(self, create, body, raw_path):
        with exclusive_lock(self.path.parent):
            self.reload()
            bound = reserve(body)
            self.require_headroom(bound["reserved_usd"])
            raw_path = Path(raw_path)
            relative_raw = raw_path.resolve().relative_to(self.path.parent.resolve()).as_posix()
            if raw_path.exists():
                raise BudgetStop("Request already attempted; preserve prior evidence")
            entry = {"request": deepcopy(body), "status": "started", "response": None}
            write_json_atomic(raw_path, entry)
            row = {"call_index": len(self.data["calls"]), "operation": "chat", "model": MODEL,
                   "status": "started", **{k: str(v) if isinstance(v, Decimal) else v for k, v in bound.items()},
                   "charged_usd": str(bound["reserved_usd"]), "raw_path": relative_raw,
                   "request_sha256": hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()}
            self.data["calls"].append(row)
            write_json_atomic(self.path, self.data)
            try:
                response = create(**body)
                entry.update(status="received", response=response.model_dump(mode="json"))
                # Preserve raw malformed/refused/truncated responses before parsing.
                write_json_atomic(raw_path, entry)
                if response.model != MODEL:
                    raise BudgetStop("Provider returned an unpriced model snapshot")
                usage = response.usage
                prompt_tokens, completion_tokens = usage.prompt_tokens, usage.completion_tokens
                if type(prompt_tokens) is not int or type(completion_tokens) is not int or not 0 <= prompt_tokens <= bound["input_bound"] or not 0 <= completion_tokens <= bound["output_cap"]:
                    raise BudgetStop("Provider usage outside reservation")
                cost = (prompt_tokens * INPUT_RATE + completion_tokens * OUTPUT_RATE) / 1_000_000
                row.update(status="completed", input_tokens=prompt_tokens, output_tokens=completion_tokens,
                           charged_usd=str(cost), response_model=response.model,
                           system_fingerprint=getattr(response, "system_fingerprint", None),
                           raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest())
                write_json_atomic(self.path, self.data)
                return response
            except BaseException as exc:
                row["status"] = "unknown"
                self.data["unknown_outcome"] = True
                entry.update(status="unknown", exception_type=type(exc).__name__)
                write_json_atomic(self.path, self.data)
                write_json_atomic(raw_path, entry)
                raise


    def begin_stage(self, name, maximum_calls, upper_bound):
        self.reload()
        if self.data["stage"] is not None:
            raise BudgetStop("A stage is already reserved; investigate before continuing")
        if type(maximum_calls) is not int or not 0 < maximum_calls <= 75:
            raise BudgetStop("Invalid bounded stage call count")
        if not upper_bound.is_finite() or upper_bound <= 0:
            raise BudgetStop("Invalid stage estimate")
        self.data["stage"] = {"name": name, "start_calls": len(self.data["calls"]),
                              "maximum_calls": maximum_calls, "upper_bound_usd": str(upper_bound),
                              "start_spent_usd": str(self.spent)}
        write_json_atomic(self.path, self.data)

    def finish_stage(self):
        self.reload()
        self.data["stage"] = None
        write_json_atomic(self.path, self.data)

