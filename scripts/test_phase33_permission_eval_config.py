from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_permission_eval import _default_report_path, _default_run_name, _requires_external_embeddings_approval


def test_vector_lexical_permission_defaults() -> None:
    assert _default_run_name("vector_lexical_rerank") == "phase33-vector-lexical-rerank-permission-eval"
    assert _default_report_path("vector_lexical_rerank") == Path("docs/phase-33/permission-candidate-results.md")


def test_legacy_permission_defaults() -> None:
    assert _default_run_name("vector_only") == "phase-8-permission-eval"
    assert _default_report_path("vector_only") == Path("docs/phase-8/permission-evaluation-results.md")


def test_phase33_external_embedding_approval_scope() -> None:
    assert _requires_external_embeddings_approval("vector_lexical_rerank")
    assert not _requires_external_embeddings_approval("vector_only")
    assert not _requires_external_embeddings_approval("keyword_only")


def main() -> None:
    test_vector_lexical_permission_defaults()
    test_legacy_permission_defaults()
    test_phase33_external_embedding_approval_scope()
    print("Phase 33 permission eval config tests passed")


if __name__ == "__main__":
    main()
