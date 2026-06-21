from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_phase33_precision_candidate import _requires_external_embeddings_approval, _run_id


def test_phase33_precision_run_ids_are_top_k_scoped() -> None:
    assert _run_id(3) == "phase33-vector-lexical-rerank-top3"


def test_live_precision_run_requires_external_embedding_approval() -> None:
    assert _requires_external_embeddings_approval(dry_run=False)
    assert not _requires_external_embeddings_approval(dry_run=True)


def main() -> None:
    test_phase33_precision_run_ids_are_top_k_scoped()
    test_live_precision_run_requires_external_embedding_approval()
    print("Phase 33 precision candidate config tests passed")


if __name__ == "__main__":
    main()
