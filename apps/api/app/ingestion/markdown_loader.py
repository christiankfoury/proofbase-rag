from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MarkdownDocument:
    metadata: dict
    body: str
    source_path: str

    @property
    def document_id(self) -> str:
        return str(self.metadata["document_id"])

    @property
    def title(self) -> str:
        return str(self.metadata["title"])

    @property
    def access_roles(self) -> list[str]:
        roles = self.metadata.get("access_roles", [])
        if not isinstance(roles, list):
            raise ValueError(f"{self.source_path} access_roles must be a list")
        return [str(role) for role in roles]


def parse_markdown_file(path: Path) -> MarkdownDocument:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"{path} is missing YAML frontmatter")

    parts = raw.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has invalid YAML frontmatter")

    metadata = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()

    required = [
        "document_id",
        "title",
        "department",
        "category",
        "access_roles",
        "restricted",
        "version",
        "effective_date",
        "owner",
        "review_cycle",
        "summary",
    ]
    missing = [field for field in required if field not in metadata]
    if missing:
        raise ValueError(f"{path} is missing metadata fields: {', '.join(missing)}")

    return MarkdownDocument(metadata=metadata, body=body, source_path=str(path))


def load_markdown_documents(root: str | Path) -> list[MarkdownDocument]:
    root_path = Path(root)
    documents: list[MarkdownDocument] = []
    for path in sorted(root_path.rglob("*.md")):
        documents.append(parse_markdown_file(path))
    return documents
