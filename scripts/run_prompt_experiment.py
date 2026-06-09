from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.experiments.config import default_prompt_experiment_configs, prompt_experiment_config
from apps.api.app.experiments.runner import run_prompt_experiment, write_prompt_experiment

FAILED_QUESTIONS_PATH = ROOT / "data/evaluation/failed-questions/failed-questions.json"


def _configs(prompt_version: str):
    if prompt_version == "all":
        return default_prompt_experiment_configs()
    return [prompt_experiment_config(prompt_version)]


def _failed_question_ids() -> set[str]:
    failed_items = json.loads(FAILED_QUESTIONS_PATH.read_text(encoding="utf-8"))
    return {str(item["question_id"]) for item in failed_items if item.get("question_id")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run answer-generation prompt experiments.")
    parser.add_argument(
        "--prompt-version",
        default="all",
        choices=["all", "v1", "v2", "v3", "v5"],
        help="Prompt version to evaluate. Defaults to all prompt versions.",
    )
    parser.add_argument(
        "--question-filter",
        default="all",
        choices=["all", "failed"],
        help="Use 'failed' to run only dashboard-visible failed-question IDs.",
    )
    args = parser.parse_args()

    question_ids = _failed_question_ids() if args.question_filter == "failed" else None
    summaries = []
    for config in _configs(args.prompt_version):
        result = run_prompt_experiment(config, question_ids=question_ids, question_filter=args.question_filter)
        path = write_prompt_experiment(result)
        summaries.append(result["summary"])
        print(f"Wrote {path}")

    print(json.dumps({"runs": summaries}, indent=2))


if __name__ == "__main__":
    main()
