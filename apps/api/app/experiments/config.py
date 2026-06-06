from __future__ import annotations

from dataclasses import asdict, dataclass, field

from apps.api.app.prompts.prompt_registry import get_prompt


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    run_name: str
    phase: str = "phase-11"
    retrieval_mode: str = "vector_only"
    chunking_strategy: str = "section_based"
    top_k: int = 5
    prompt_name: str = "answer_generation"
    prompt_version: str = "v1"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    confidence_thresholds: dict[str, float] = field(
        default_factory=lambda: {"not_found": 0.5, "partial_answer": 0.7}
    )
    citation_validation_mode: str = "heuristic"
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def prompt_experiment_config(prompt_version: str) -> ExperimentConfig:
    prompt = get_prompt("answer_generation", prompt_version)
    notes = {
        "v1": "Current Phase 7/9 structured JSON prompt.",
        "v2": "Stricter citation requirements and multi-document citation expectations.",
        "v3": "Stricter not-found and unsupported-claim behavior.",
    }.get(prompt_version, prompt.change_notes)
    return ExperimentConfig(
        experiment_id=f"phase11-answer-generation-{prompt_version}",
        run_name=f"answer-generation-{prompt_version}",
        prompt_version=prompt_version,
        model=prompt.model,
        temperature=prompt.temperature,
        notes=notes,
    )


def default_prompt_experiment_configs() -> list[ExperimentConfig]:
    return [prompt_experiment_config(version) for version in ["v1", "v2", "v3"]]
