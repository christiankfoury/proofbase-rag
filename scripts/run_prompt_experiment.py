from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.experiments.config import default_prompt_experiment_configs, prompt_experiment_config
from apps.api.app.experiments.runner import run_prompt_experiment, write_prompt_experiment


def _configs(prompt_version: str):
    if prompt_version == "all":
        return default_prompt_experiment_configs()
    return [prompt_experiment_config(prompt_version)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run answer-generation prompt experiments.")
    parser.add_argument(
        "--prompt-version",
        default="all",
        choices=["all", "v1", "v2", "v3"],
        help="Prompt version to evaluate. Defaults to all prompt versions.",
    )
    args = parser.parse_args()

    summaries = []
    for config in _configs(args.prompt_version):
        result = run_prompt_experiment(config)
        path = write_prompt_experiment(result)
        summaries.append(result["summary"])
        print(f"Wrote {path}")

    print(json.dumps({"runs": summaries}, indent=2))


if __name__ == "__main__":
    main()
