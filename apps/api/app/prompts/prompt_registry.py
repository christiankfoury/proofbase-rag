from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


PROMPT_VERSION_DIR = Path(__file__).resolve().parent / "versions"


@dataclass(frozen=True)
class PromptVersion:
    prompt_id: str
    prompt_name: str
    prompt_type: str
    version: str
    status: str
    model: str
    temperature: float
    content: str
    created_at: str
    change_notes: str
    owner: str
    path: Path

    def metadata(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "prompt_name": self.prompt_name,
            "prompt_type": self.prompt_type,
            "prompt_version": self.version,
            "prompt_status": self.status,
            "model": self.model,
            "temperature": self.temperature,
            "change_notes": self.change_notes,
            "owner": self.owner,
        }


def _split_frontmatter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        raise ValueError(f"Prompt file is missing YAML frontmatter: {path}")
    _, raw_meta, content = text.split("---", 2)
    metadata = yaml.safe_load(raw_meta) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Prompt frontmatter must be a mapping: {path}")
    return metadata, content.strip()


def _load_prompt_file(path: Path) -> PromptVersion:
    metadata, content = _split_frontmatter(path.read_text(encoding="utf-8"), path)
    required = [
        "prompt_id",
        "prompt_name",
        "prompt_type",
        "version",
        "status",
        "model",
        "temperature",
        "created_at",
        "change_notes",
    ]
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError(f"Prompt file {path} is missing fields: {', '.join(missing)}")
    return PromptVersion(
        prompt_id=str(metadata["prompt_id"]),
        prompt_name=str(metadata["prompt_name"]),
        prompt_type=str(metadata["prompt_type"]),
        version=str(metadata["version"]),
        status=str(metadata["status"]),
        model=str(metadata["model"]),
        temperature=float(metadata["temperature"]),
        content=content,
        created_at=str(metadata["created_at"]),
        change_notes=str(metadata["change_notes"]),
        owner=str(metadata.get("owner", "Proofbase")),
        path=path,
    )


def list_prompt_versions(prompt_name: str | None = None, prompt_type: str | None = None) -> list[PromptVersion]:
    prompts = []
    for path in sorted(PROMPT_VERSION_DIR.glob("*.md")):
        prompt = _load_prompt_file(path)
        if prompt_name and prompt.prompt_name != prompt_name:
            continue
        if prompt_type and prompt.prompt_type != prompt_type:
            continue
        prompts.append(prompt)
    return prompts


def get_prompt(prompt_name: str, version: str | None = None) -> PromptVersion:
    prompts = list_prompt_versions(prompt_name=prompt_name)
    if not prompts:
        raise ValueError(f"No prompt versions found for prompt_name={prompt_name}")
    if version:
        for prompt in prompts:
            if prompt.version == version:
                return prompt
        raise ValueError(f"Prompt version not found: {prompt_name} {version}")
    active = [prompt for prompt in prompts if prompt.status == "active"]
    if active:
        return sorted(active, key=lambda item: item.created_at)[-1]
    return sorted(prompts, key=lambda item: item.created_at)[-1]


def prompt_registry_snapshot() -> dict[str, Any]:
    prompts = [prompt.metadata() | {"created_at": prompt.created_at} for prompt in list_prompt_versions()]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "prompt_count": len(prompts),
        "prompts": prompts,
    }
