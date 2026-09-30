"""Phase 71 authorization successor; historical ledgers and transports stay frozen."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from scripts.quality_eval_transport_v12 import Ledger as HistoricalLedger, BudgetStop
from scripts.quality_eval_preflight import HANDOFF_SPENT
from scripts.reliable_evaluation_run import write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/evaluation/quality-completion-v1"
HISTORY = ROOT / "data/evaluation/portfolio-finish/api-ledger.json"
V11 = ROOT / "data/evaluation/quality-remediation-v1/calibration-v11-01/api-ledger.json"
PHASE69 = V11.parent.parent / "api-ledger.json"
AUTHORIZATION = {
    "version": "quality-completion-authorization.v1", "date": "2026-09-29",
    "source": "User: old $5 API cap is superseded; implement Phases 71-73",
    "local_cumulative_ceiling_usd": None,
    "account_hard_budget": "user-reported; not independently verified or modified",
    "scope": "Bounded quality-completion queue only; no product-limit or infrastructure changes",
    "automatic_retries": 0,
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit():
    # The original reader validates its complete Phase 68 prefix and v11 chain.
    prior = HistoricalLedger(PHASE69)
    frozen = json.loads(V11.read_bytes())
    demo = json.loads(HISTORY.read_bytes())
    if prior.data["calls"] != frozen["calls"] or demo["calls"][:len(frozen["calls"])] != frozen["calls"]:
        raise BudgetStop("Historical ledger branches diverged")
    if demo["prior_sha256"] != digest(PHASE69) or demo.get("unknown_outcome"):
        raise BudgetStop("Portfolio provenance or settlement failed")
    if Decimal(demo["prior_spend_usd"]) != prior.spent:
        raise BudgetStop("Portfolio floor disagrees with prior conservative spend")
    extra = demo["calls"][len(frozen["calls"]):]
    for i, row in enumerate(demo["calls"]):
        charge = Decimal(str(row["charged_usd"]))
        if row["call_index"] != i or row["status"] != "completed" or not charge.is_finite() or charge < 0:
            raise BudgetStop("Unsettled or invalid historical charge")
    total = prior.spent + sum((Decimal(str(r["charged_usd"])) for r in extra), Decimal(0))
    return {"version": "quality-ledger-reconciliation.v1", "historical_calls": len(demo["calls"]),
            "phase69_calls": len(frozen["calls"]), "phase70_additional_calls": len(extra),
            "conservative_spent_usd": str(total), "authorization": AUTHORIZATION,
            "sources": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in (V11, PHASE69, HISTORY)}}


class Ledger(HistoricalLedger):
    """Reuse durable request/response settlement; replace only authorization policy."""
    def __init__(self, path):
        self.path = Path(path)
        self.reconciliation = audit()
        self.prefix = json.loads(HISTORY.read_bytes())
        self.reload()

    @classmethod
    def initialize(cls, path):
        plan = audit()
        path = Path(path)
        data = {"authorization": deepcopy(AUTHORIZATION), "reconciliation": plan,
                "calls": json.loads(HISTORY.read_bytes())["calls"], "unknown_outcome": False,
                "stage": None}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        return cls(path)

    def reload(self):
        self.data = json.loads(self.path.read_bytes())
        if self.data.get("authorization") != AUTHORIZATION or self.data.get("reconciliation") != self.reconciliation:
            raise BudgetStop("Successor authorization/provenance changed")
        if self.data["calls"][:len(self.prefix["calls"])] != self.prefix["calls"]:
            raise BudgetStop("Reconciled historical prefix changed")
        for i, row in enumerate(self.data["calls"]):
            charge = Decimal(str(row["charged_usd"]))
            if row["call_index"] != i or not charge.is_finite() or charge < 0:
                raise BudgetStop("Invalid cost history")
        if self.data.get("unknown_outcome") or any(r["status"] != "completed" for r in self.data["calls"]):
            raise BudgetStop("Unsettled external outcome; no retry")

    @property
    def spent(self):
        return Decimal(self.reconciliation["conservative_spent_usd"]) + sum(
            (Decimal(str(r["charged_usd"])) for r in self.data["calls"][len(self.prefix["calls"]):]), Decimal(0))

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

    def require_headroom(self, amount):
        stage = self.data["stage"]
        if not stage or len(self.data["calls"]) >= stage["start_calls"] + stage["maximum_calls"]:
            raise BudgetStop("Predeclared stage call allowance exhausted or missing")
        if not amount.is_finite() or amount < 0:
            raise BudgetStop("Invalid reservation")
        if self.spent - Decimal(stage["start_spent_usd"]) + amount > Decimal(stage["upper_bound_usd"]):
            raise BudgetStop("Predeclared stage cost reservation exceeded")
