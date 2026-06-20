from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.api.app.ingestion.markdown_loader import load_markdown_documents


BENCHMARK_PATH = ROOT / "data/evaluation/benchmark-questions.json"
DOCUMENTS_ROOT = ROOT / "data/synthetic-documents"

REQUIRED_TOP_LEVEL_FIELDS = {
    "benchmark_version",
    "created_for_phase",
    "source_corpus",
    "question_count",
    "questions",
}

REQUIRED_QUESTION_FIELDS = {
    "question_id",
    "question_type",
    "difficulty",
    "user_role",
    "question",
    "previous_turns",
    "expected_behavior",
    "expected_answer",
    "expected_source_document",
    "expected_source_section_or_quote",
    "allowed_documents",
    "evaluation_notes",
}

VALID_QUESTION_TYPES = {
    "simple_factual",
    "multi_document",
    "permission_restricted",
    "missing_information",
    "conversation_memory",
    "ambiguous",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}

VALID_EXPECTED_BEHAVIORS = {
    "answer",
    "answer_with_memory",
    "ask_clarifying_question",
    "refuse_no_access",
    "say_not_found",
}

VALID_ROLES = {
    "Employee",
    "Sales Representative",
    "Manager",
    "HR Admin",
    "IT Admin",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Benchmark file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Benchmark file is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Benchmark root must be a JSON object.")
    return payload


def _document_ids(documents_root: Path) -> set[str]:
    try:
        return {document.document_id for document in load_markdown_documents(documents_root)}
    except FileNotFoundError as exc:
        raise SystemExit(f"Synthetic document root not found: {documents_root}") from exc
    except Exception as exc:
        raise SystemExit(f"Synthetic document metadata is invalid: {exc}") from exc


def _require_string(question: dict[str, Any], field: str, errors: list[str], question_id: str) -> None:
    value = question.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{question_id}: `{field}` must be a non-empty string.")


def _require_string_list(question: dict[str, Any], field: str, errors: list[str], question_id: str) -> list[str]:
    value = question.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{question_id}: `{field}` must be a list of non-empty strings.")
        return []
    return value


def _validate_previous_turns(question: dict[str, Any], errors: list[str], question_id: str) -> None:
    turns = question.get("previous_turns")
    if not isinstance(turns, list):
        errors.append(f"{question_id}: `previous_turns` must be a list.")
        return
    for index, turn in enumerate(turns, start=1):
        if not isinstance(turn, dict):
            errors.append(f"{question_id}: previous turn {index} must be an object.")
            continue
        for field in ("role", "content"):
            if not isinstance(turn.get(field), str) or not turn[field].strip():
                errors.append(f"{question_id}: previous turn {index} `{field}` must be a non-empty string.")


def _validate_source_quotes(
    question: dict[str, Any],
    *,
    document_ids: set[str],
    expected_documents: set[str],
    errors: list[str],
    question_id: str,
) -> None:
    refs = question.get("expected_source_section_or_quote")
    if not isinstance(refs, list):
        errors.append(f"{question_id}: `expected_source_section_or_quote` must be a list.")
        return
    for index, ref in enumerate(refs, start=1):
        if not isinstance(ref, dict):
            errors.append(f"{question_id}: source quote {index} must be an object.")
            continue
        document_id = ref.get("document_id")
        if not isinstance(document_id, str) or not document_id.strip():
            errors.append(f"{question_id}: source quote {index} `document_id` must be a non-empty string.")
            continue
        if document_id not in document_ids:
            errors.append(f"{question_id}: source quote {index} references unknown document `{document_id}`.")
        if expected_documents and document_id not in expected_documents:
            errors.append(
                f"{question_id}: source quote {index} document `{document_id}` is not in `expected_source_document`."
            )
        for field in ("section", "quote"):
            if not isinstance(ref.get(field), str) or not ref[field].strip():
                errors.append(f"{question_id}: source quote {index} `{field}` must be a non-empty string.")


def _validate_question_shape(
    question: dict[str, Any],
    *,
    document_ids: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    question_id = str(question.get("question_id") or "<missing question_id>")
    missing = sorted(REQUIRED_QUESTION_FIELDS - set(question))
    if missing:
        errors.append(f"{question_id}: missing required fields: {', '.join(missing)}.")

    for field in ("question_id", "question_type", "difficulty", "user_role", "question", "expected_behavior", "expected_answer"):
        _require_string(question, field, errors, question_id)
    if question.get("question_type") not in VALID_QUESTION_TYPES:
        errors.append(f"{question_id}: invalid `question_type` `{question.get('question_type')}`.")
    if question.get("difficulty") not in VALID_DIFFICULTIES:
        errors.append(f"{question_id}: invalid `difficulty` `{question.get('difficulty')}`.")
    if question.get("expected_behavior") not in VALID_EXPECTED_BEHAVIORS:
        errors.append(f"{question_id}: invalid `expected_behavior` `{question.get('expected_behavior')}`.")
    if question.get("user_role") not in VALID_ROLES:
        errors.append(f"{question_id}: invalid `user_role` `{question.get('user_role')}`.")

    _validate_previous_turns(question, errors, question_id)
    expected_documents = set(_require_string_list(question, "expected_source_document", errors, question_id))
    allowed_documents = set(_require_string_list(question, "allowed_documents", errors, question_id))
    _validate_source_quotes(
        question,
        document_ids=document_ids,
        expected_documents=expected_documents,
        errors=errors,
        question_id=question_id,
    )

    for field, values in (("expected_source_document", expected_documents), ("allowed_documents", allowed_documents)):
        unknown = sorted(document_id for document_id in values if document_id not in document_ids)
        if unknown:
            errors.append(f"{question_id}: `{field}` references unknown documents: {', '.join(unknown)}.")

    question_type = question.get("question_type")
    expected_behavior = question.get("expected_behavior")
    previous_turns = question.get("previous_turns") if isinstance(question.get("previous_turns"), list) else []

    if question_type == "conversation_memory":
        if expected_behavior != "answer_with_memory":
            errors.append(f"{question_id}: conversation memory questions must use `answer_with_memory`.")
        if not previous_turns:
            errors.append(f"{question_id}: conversation memory questions must include `previous_turns`.")
    elif previous_turns:
        errors.append(f"{question_id}: only conversation memory questions should include `previous_turns`.")

    if question_type == "permission_restricted":
        if expected_behavior != "refuse_no_access":
            errors.append(f"{question_id}: permission-restricted questions must use `refuse_no_access`.")
        if not expected_documents:
            errors.append(f"{question_id}: permission-restricted questions must name restricted expected sources.")
    elif question_type == "missing_information":
        if expected_behavior != "say_not_found":
            errors.append(f"{question_id}: missing-information questions must use `say_not_found`.")
        if expected_documents:
            errors.append(f"{question_id}: missing-information questions should not name expected source documents.")
    elif expected_behavior in {"answer", "answer_with_memory", "ask_clarifying_question"} and not expected_documents:
        errors.append(f"{question_id}: answerable or ambiguous questions should name expected source documents.")

    if question_type != "permission_restricted":
        missing_allowed = sorted(expected_documents - allowed_documents)
        if missing_allowed:
            errors.append(
                f"{question_id}: expected documents must be allowed for non-restricted questions: "
                f"{', '.join(missing_allowed)}."
            )
    else:
        leaked_restricted = sorted(expected_documents & allowed_documents)
        if leaked_restricted:
            warnings.append(
                f"{question_id}: permission-restricted expected sources also appear in `allowed_documents`: "
                f"{', '.join(leaked_restricted)}."
            )


def validate_benchmark(benchmark_path: Path, documents_root: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    payload = _load_json(benchmark_path)
    errors: list[str] = []
    warnings: list[str] = []

    missing_top_level = sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
    if missing_top_level:
        errors.append(f"Benchmark root missing required fields: {', '.join(missing_top_level)}.")

    questions = payload.get("questions")
    if not isinstance(questions, list):
        errors.append("Benchmark `questions` must be a list.")
        questions = []

    declared_count = payload.get("question_count")
    if not isinstance(declared_count, int):
        errors.append("Benchmark `question_count` must be an integer.")
    elif declared_count != len(questions):
        errors.append(f"Benchmark `question_count` is {declared_count}, but found {len(questions)} questions.")

    document_ids = _document_ids(documents_root)
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    category_counts: Counter[str] = Counter()

    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            errors.append(f"Question at index {index} must be an object.")
            continue
        question_id = item.get("question_id")
        if isinstance(question_id, str):
            if question_id in seen_ids:
                duplicate_ids.add(question_id)
            seen_ids.add(question_id)
        if isinstance(item.get("question_type"), str):
            category_counts[item["question_type"]] += 1
        _validate_question_shape(item, document_ids=document_ids, errors=errors, warnings=warnings)

    if duplicate_ids:
        errors.append(f"Duplicate question_id values: {', '.join(sorted(duplicate_ids))}.")

    summary = {
        "benchmark_path": str(benchmark_path.relative_to(ROOT)) if benchmark_path.is_relative_to(ROOT) else str(benchmark_path),
        "documents_root": str(documents_root.relative_to(ROOT)) if documents_root.is_relative_to(ROOT) else str(documents_root),
        "benchmark_version": payload.get("benchmark_version"),
        "question_count": len(questions),
        "declared_question_count": declared_count,
        "document_count": len(document_ids),
        "category_counts": dict(sorted(category_counts.items())),
    }
    return errors, warnings, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate benchmark question schema and document references.")
    parser.add_argument("--benchmark-path", type=Path, default=BENCHMARK_PATH)
    parser.add_argument("--documents-root", type=Path, default=DOCUMENTS_ROOT)
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation output.")
    args = parser.parse_args()

    benchmark_path = args.benchmark_path if args.benchmark_path.is_absolute() else ROOT / args.benchmark_path
    documents_root = args.documents_root if args.documents_root.is_absolute() else ROOT / args.documents_root
    errors, warnings, summary = validate_benchmark(benchmark_path, documents_root)

    if args.json:
        print(json.dumps({"ok": not errors, "summary": summary, "warnings": warnings, "errors": errors}, indent=2))
    else:
        print("Benchmark validation summary")
        for key, value in summary.items():
            if key == "category_counts":
                print("- category_counts:")
                for category, count in value.items():
                    print(f"  - {category}: {count}")
            else:
                print(f"- {key}: {value}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"- {error}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
