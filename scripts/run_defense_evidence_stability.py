from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.export_defense_readiness import STABILITY_RESULT, build_summary  # noqa: E402


def main() -> None:
    hashes: list[str] = []
    for _ in range(3):
        summary = build_summary()
        summary.pop("stability", None)
        canonical = json.dumps(summary, sort_keys=True, separators=(",", ":"))
        hashes.append(hashlib.sha256(canonical.encode()).hexdigest())
    passed = len(set(hashes)) == 1
    payload = {
        "target": "3/3 identical bounded summaries with timestamps excluded",
        "passes": 3 if passed else max(hashes.count(item) for item in set(hashes)),
        "attempts": 3,
        "passed": passed,
        "summary_sha256": hashes,
        "scope": "deterministic manifest validation and evidence export only",
    }
    STABILITY_RESULT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{'PASS' if passed else 'FAIL'} defense evidence stability: {payload['passes']}/3")
    print(f"Summary SHA-256: {hashes[0] if passed else 'mismatch'}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
