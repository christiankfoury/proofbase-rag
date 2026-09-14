"""Mechanical overlap check; never prints historical questions."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.fresh_eval_protocol import ROOT, FOLDER


def questions(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in {"question", "query"} and isinstance(v, str):
                yield v
            elif isinstance(v, (dict, list)):
                yield from questions(v)
    elif isinstance(value, list):
        for v in value:
            yield from questions(v)


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def check():
    old = []
    for p in (ROOT / "data/evaluation").rglob("*.json"):
        if (p.is_relative_to(FOLDER) and "preflight-rejected-v1" not in p.parts) or "local-runs" in p.parts:
            continue
        try:
            old.extend(tokens(q) for q in questions(json.loads(p.read_text(encoding="utf-8"))))
        except (ValueError, UnicodeError):
            continue
    old = [set(t) for t in set(frozenset(t) for t in old) if t]
    suite = json.loads((FOLDER / "holdout.json").read_text())
    hits = []
    for case in suite["cases"]:
        current = tokens(case["question"])
        score = max((len(current & previous) / len(current | previous) for previous in old), default=0)
        if score >= .8:
            hits.append({"case_id": case["case_id"], "max_token_jaccard": score})
    return {"historical_unique_questions": len(old), "threshold": .8, "hits": hits,
            "limitation": "Lexical overlap only; cannot establish semantic independence"}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
