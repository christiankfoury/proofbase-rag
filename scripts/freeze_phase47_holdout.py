from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.independent_generalization_common import (  # noqa: E402
    HOLDOUT_HASH_PATH,
    HOLDOUT_PATH,
    file_sha256,
    validate_split,
)


def main() -> None:
    validation = validate_split("holdout")
    if not validation["valid"]:
        for error in validation.get("errors") or []:
            print(f"error: {error}")
        raise SystemExit("Refusing to freeze an invalid holdout suite.")

    digest = file_sha256(HOLDOUT_PATH)
    HOLDOUT_HASH_PATH.write_text(f"{digest}  {HOLDOUT_PATH.name}\n", encoding="utf-8")
    print(f"Frozen {HOLDOUT_PATH.relative_to(ROOT)}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
