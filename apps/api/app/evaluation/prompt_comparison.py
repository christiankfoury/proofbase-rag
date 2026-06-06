from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class PromptComparison:
    baseline_version: str
    candidate_version: str
    fixed_questions: list[str]
    broken_questions: list[str]
    still_failing: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "fixed_questions": self.fixed_questions,
            "broken_questions": self.broken_questions,
            "still_failing": self.still_failing,
        }


PROMPT_EXPERIMENT_GLOB = "*-answer-generation-*.json"


def load_prompt_experiment_results(directory: Path) -> list[dict]:
    results = []
    for path in sorted(directory.glob(PROMPT_EXPERIMENT_GLOB)):
        results.append(json.loads(path.read_text(encoding="utf-8")))
    return results


def failed_ids(result: dict) -> set[str]:
    return {item["question_id"] for item in result.get("failed_questions", [])}


def compare_to_baseline(baseline: dict, candidate: dict) -> PromptComparison:
    baseline_failed = failed_ids(baseline)
    candidate_failed = failed_ids(candidate)
    return PromptComparison(
        baseline_version=baseline["summary"]["prompt_version"],
        candidate_version=candidate["summary"]["prompt_version"],
        fixed_questions=sorted(baseline_failed - candidate_failed),
        broken_questions=sorted(candidate_failed - baseline_failed),
        still_failing=sorted(baseline_failed & candidate_failed),
    )


def best_prompt_summary(results: list[dict]) -> dict:
    if not results:
        return {}

    def score(result: dict) -> tuple[float, float, float, float]:
        summary = result["summary"]
        answer = summary.get("answer_accuracy") or 0.0
        citation = summary.get("citation_accuracy") or 0.0
        hallucination = summary.get("hallucination_rate") or 1.0
        failed = summary.get("failed_question_count") or 999
        return (answer, citation, -hallucination, -failed)

    best = max(results, key=score)
    lowest_hallucination = min(results, key=lambda item: item["summary"].get("hallucination_rate") or 1.0)
    best_citations = max(results, key=lambda item: item["summary"].get("citation_accuracy") or 0.0)
    return {
        "best_overall": best["summary"]["prompt_version"],
        "lowest_hallucination": lowest_hallucination["summary"]["prompt_version"],
        "best_citations": best_citations["summary"]["prompt_version"],
    }
