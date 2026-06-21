from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_permission_eval import _default_report_path, _default_run_name


def test_vector_lexical_permission_defaults() -> None:
    assert _default_run_name("vector_lexical_rerank") == "phase33-vector-lexical-rerank-permission-eval"
    assert _default_report_path("vector_lexical_rerank") == Path("docs/phase-33/permission-candidate-results.md")


def test_legacy_permission_defaults() -> None:
    assert _default_run_name("vector_only") == "phase-8-permission-eval"
    assert _default_report_path("vector_only") == Path("docs/phase-8/permission-evaluation-results.md")


def main() -> None:
    test_vector_lexical_permission_defaults()
    test_legacy_permission_defaults()
    print("Phase 33 permission eval config tests passed")


if __name__ == "__main__":
    main()
