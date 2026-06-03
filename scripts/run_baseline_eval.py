from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.evaluation.run_benchmark import run_benchmark


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip answer generation and calculate retrieval metrics only.",
    )
    args = parser.parse_args()
    summary = run_benchmark(retrieval_only=args.retrieval_only)
    for key, value in summary.items():
        print(f"{key}: {value}")
