from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.independent_generalization_common import validate_split


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the Phase 47 independent generalization suite.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation output.")
    parser.add_argument("--split", choices=("development", "holdout", "all"), default="all")
    args = parser.parse_args()

    splits = ("development", "holdout") if args.split == "all" else (args.split,)
    results = [validate_split(split) for split in splits]
    payload = {
        "valid": all(result["valid"] for result in results),
        "case_count": sum(int(result.get("case_count") or 0) for result in results),
        "splits": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for result in results:
            status = "PASS" if result["valid"] else "FAIL"
            print(f"{status} {result['split']}: {result['case_count']} cases")
            for warning in result.get("warnings") or []:
                print(f"  warning: {warning}")
            for error in result.get("errors") or []:
                print(f"  error: {error}")
            coverage = result.get("coverage") or {}
            if coverage:
                print(f"  categories: {coverage.get('categories')}")
                print(f"  roles: {coverage.get('roles')}")
                print(f"  behaviors: {coverage.get('behaviors')}")
                print(f"  documents: {len(coverage.get('documents') or [])}")
        print(f"Overall: {'PASS' if payload['valid'] else 'FAIL'} ({payload['case_count']} cases)")
    if not payload["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
