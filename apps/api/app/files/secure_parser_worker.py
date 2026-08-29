from __future__ import annotations

import json
import sys
from pathlib import Path

from apps.api.app.ingestion.pdf_extractor import extract_pdf_to_markdown


def main() -> None:
    path, title, max_pages_raw, max_chars_raw, max_ratio_raw = sys.argv[1:6]
    try:
        result = extract_pdf_to_markdown(path, title=title)
        if result.page_count < 1:
            print("parser_empty_pdf")
            raise SystemExit(2)
        if result.page_count > int(max_pages_raw):
            print("parser_page_limit")
            raise SystemExit(2)
        if len(result.markdown) > int(max_chars_raw):
            print("parser_expansion_limit")
            raise SystemExit(2)
        source_size = max(1, Path(path).stat().st_size)
        if len(result.markdown.encode("utf-8")) / source_size > int(max_ratio_raw):
            print("parser_expansion_ratio")
            raise SystemExit(2)
        print(json.dumps({
            "markdown": result.markdown,
            "page_count": result.page_count,
            "pages_with_text": result.pages_with_text,
            "confidence": result.confidence,
            "warnings": result.warnings,
        }))
    except SystemExit:
        raise
    except Exception:
        print("parser_malformed_pdf")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
