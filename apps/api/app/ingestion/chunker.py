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


def _section_chunks(document: MarkdownDocument) -> list[DocumentChunk]:
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


def _fixed_size_chunks(document: MarkdownDocument, chunk_size: int, chunk_overlap: int) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be greater than or equal to 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    for section in _section_chunks(document):
        words = section.content.split()
        if not words:
            continue
        step = chunk_size - chunk_overlap
        for start in range(0, len(words), step):
            window = words[start : start + chunk_size]
            if not window:
                continue
            chunks.append(
                DocumentChunk(
                    document_id=document.document_id,
                    document_title=document.title,
                    source_path=document.source_path,
                    section_heading=section.section_heading,
                    chunk_index=len(chunks),
                    access_roles=document.access_roles,
                    content=" ".join(window),
                    chunking_strategy="fixed_size",
                )
            )
            if start + chunk_size >= len(words):
                break
    return chunks


def chunk_markdown_document(
    document: MarkdownDocument,
    chunking_strategy: str = "section_based",
    chunk_size: int = 180,
    chunk_overlap: int = 40,
) -> list[DocumentChunk]:
    if chunking_strategy == "section_based":
        return _section_chunks(document)
    if chunking_strategy == "fixed_size":
        return _fixed_size_chunks(document, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    raise ValueError(f"Unsupported chunking strategy: {chunking_strategy}")
