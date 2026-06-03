from dataclasses import dataclass
import re

from apps.api.app.ingestion.markdown_loader import MarkdownDocument


@dataclass(frozen=True)
class DocumentChunk:
    document_id: str
    document_title: str
    source_path: str
    section_heading: str
    chunk_index: int
    access_roles: list[str]
    content: str
    chunking_strategy: str = "section_based"

    @property
    def token_count(self) -> int:
        return len(self.content.split())


SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def chunk_markdown_document(document: MarkdownDocument) -> list[DocumentChunk]:
    matches = list(SECTION_RE.finditer(document.body))
    chunks: list[DocumentChunk] = []

    if not matches:
        return [
            DocumentChunk(
                document_id=document.document_id,
                document_title=document.title,
                source_path=document.source_path,
                section_heading=document.title,
                chunk_index=0,
                access_roles=document.access_roles,
                content=document.body.strip(),
            )
        ]

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document.body)
        section_heading = match.group(1).strip()
        section_body = document.body[start:end].strip()
        content = f"{section_heading}\n\n{section_body}".strip()
        if not section_body:
            continue
        chunks.append(
            DocumentChunk(
                document_id=document.document_id,
                document_title=document.title,
                source_path=document.source_path,
                section_heading=section_heading,
                chunk_index=len(chunks),
                access_roles=document.access_roles,
                content=content,
            )
        )

    return chunks
