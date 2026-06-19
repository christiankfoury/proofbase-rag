from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PdfExtractionResult:
    markdown: str
    page_count: int
    pages_with_text: int
    confidence: float
    warnings: list[str]


def extract_pdf_to_markdown(path: str | Path, *, title: str) -> PdfExtractionResult:
    reader = PdfReader(str(path))
    page_markdown: list[str] = []
    warnings: list[str] = []
    pages_with_text = 0

    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages_with_text += 1
            page_markdown.append(f"## Page {index}\n\n{_normalize_text(text)}")
        else:
            warnings.append(f"Page {index} did not produce extractable text.")
            page_markdown.append(f"## Page {index}\n\n[No extractable text found on this page.]")

    page_count = len(reader.pages)
    if page_count == 0:
        warnings.append("PDF has no pages.")

    confidence = round(pages_with_text / page_count, 3) if page_count else 0.0
    if confidence < 1.0:
        warnings.append("Some pages may require OCR or manual cleanup before indexing.")

    markdown = f"# {title.strip() or 'Uploaded PDF'}\n\n" + "\n\n".join(page_markdown)
    return PdfExtractionResult(
        markdown=markdown.strip(),
        page_count=page_count,
        pages_with_text=pages_with_text,
        confidence=confidence,
        warnings=warnings,
    )


def _normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n\n".join(compact_lines)
