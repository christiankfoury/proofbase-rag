from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SUITE_DIR = ROOT / "data/evaluation/independent-generalization"
DEVELOPMENT_PATH = SUITE_DIR / "development-v1.json"
HOLDOUT_PATH = SUITE_DIR / "holdout-v1.json"
HOLDOUT_HASH_PATH = SUITE_DIR / "holdout-v1.sha256"
SCHEMA_PATH = SUITE_DIR / "schema-v1.json"
CORPUS_DIR = ROOT / "data/synthetic-documents"

SUITE_VERSION = "1.0"
PROJECT_ID = "00000000-0000-0000-0000-000000000019"
USER_IDS = {
    "Employee": "00000000-0000-0000-0000-000000002701",
    "Sales Representative": "00000000-0000-0000-0000-000000002702",
    "Manager": "00000000-0000-0000-0000-000000002703",
    "HR Admin": "00000000-0000-0000-0000-000000002704",
    "IT Admin": "00000000-0000-0000-0000-000000002705",
}
DEPARTMENT_IDS = {
    "People Operations": "00000000-0000-0000-0000-000000002001",
    "HR Admin": "00000000-0000-0000-0000-000000002002",
    "IT and Security": "00000000-0000-0000-0000-000000002003",
    "IT Admin": "00000000-0000-0000-0000-000000002004",
    "Sales": "00000000-0000-0000-0000-000000002005",
    "Management": "00000000-0000-0000-0000-000000002006",
    "Finance": "00000000-0000-0000-0000-000000002007",
    "Legal": "00000000-0000-0000-0000-000000002008",
    "Engineering": "00000000-0000-0000-0000-000000002009",
    "Support": "00000000-0000-0000-0000-000000002010",
    "Operations": "00000000-0000-0000-0000-000000002011",
}

CATEGORIES = {
    "factual_robustness",
    "multi_document_claim_coverage",
    "multi_turn_memory",
    "ambiguity_boundaries",
    "permission_scope_pairs",
    "missing_information_abstention",
    "prompt_injection_adversarial",
    "conflicting_versioned_sources",
    "uploaded_document_project_isolation",
}
BEHAVIORS = {"answer", "clarify", "refuse_no_access", "not_found"}
DIFFICULTIES = {"easy", "medium", "hard"}

EXPECTED_CATEGORY_COUNTS = {
    "development": {
        "factual_robustness": 11,
        "multi_document_claim_coverage": 10,
        "multi_turn_memory": 10,
        "ambiguity_boundaries": 7,
        "permission_scope_pairs": 10,
        "missing_information_abstention": 7,
        "prompt_injection_adversarial": 7,
        "conflicting_versioned_sources": 4,
        "uploaded_document_project_isolation": 4,
    },
    "holdout": {
        "factual_robustness": 4,
        "multi_document_claim_coverage": 5,
        "multi_turn_memory": 5,
        "ambiguity_boundaries": 3,
        "permission_scope_pairs": 5,
        "missing_information_abstention": 3,
        "prompt_injection_adversarial": 3,
        "conflicting_versioned_sources": 1,
        "uploaded_document_project_isolation": 1,
    },
}

PROTECTED_RUNTIME_PATHS = (
    "apps/api/app",
    "data/synthetic-documents",
)
IGNORED_DIRTY_PATHS = {"data/observability/request-logs.jsonl"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    _, block, *_ = text.split("---", 2)
    values: dict[str, Any] = {}
    for raw_line in block.splitlines():
        if ":" not in raw_line or raw_line.startswith((" ", "\t")):
            continue
        key, raw_value = raw_line.split(":", 1)
        value = raw_value.strip().strip('"\'')
        if value.startswith("[") and value.endswith("]"):
            values[key.strip()] = [item.strip().strip('"\'') for item in value[1:-1].split(",") if item.strip()]
        else:
            values[key.strip()] = value
    return values


def corpus_documents() -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for path in sorted(CORPUS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata = _frontmatter(text)
        document_id = str(metadata.get("document_id") or "")
        if document_id:
            documents[document_id] = {"path": path, "text": text, "metadata": metadata}
    return documents


def suite_path(split: str) -> Path:
    if split == "development":
        return DEVELOPMENT_PATH
    if split == "holdout":
        return HOLDOUT_PATH
    raise ValueError(f"Unsupported split: {split}")


def load_suite(split: str) -> dict[str, Any]:
    return load_json(suite_path(split))


def _quote_entries(case: dict[str, Any]) -> Iterable[tuple[str, str, str]]:
    for item in case.get("expected_source_sections_or_quotes") or []:
        if isinstance(item, str):
            for document_id in case.get("expected_source_documents") or []:
                yield str(document_id), "", item
        elif isinstance(item, dict):
            yield str(item.get("document_id") or ""), str(item.get("section") or ""), str(item.get("quote") or "")


def validate_suite_payload(
    payload: dict[str, Any],
    *,
    expected_split: str,
    expected_suite_version: str = SUITE_VERSION,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    cases = payload.get("cases")
    if not isinstance(cases, list):
        cases = []
        errors.append("cases must be a list")
    if payload.get("suite_version") != expected_suite_version:
        errors.append(f"suite_version must be {expected_suite_version}")
    if payload.get("split") != expected_split:
        errors.append(f"split must be {expected_split}")

    expected_counts = EXPECTED_CATEGORY_COUNTS[expected_split]
    expected_total = sum(expected_counts.values())
    if len(cases) != expected_total:
        errors.append(f"{expected_split} must contain exactly {expected_total} cases; found {len(cases)}")
    if payload.get("case_count") != len(cases):
        errors.append("case_count does not match cases length")

    ids = [str(case.get("case_id") or "") for case in cases if isinstance(case, dict)]
    duplicates = sorted(case_id for case_id, count in Counter(ids).items() if case_id and count > 1)
    if duplicates:
        errors.append(f"duplicate case IDs: {', '.join(duplicates)}")

    category_counts = Counter(str(case.get("category")) for case in cases if isinstance(case, dict))
    if dict(sorted(category_counts.items())) != dict(sorted(expected_counts.items())):
        errors.append(f"category counts do not match locked distribution: {dict(sorted(category_counts.items()))}")

    documents = corpus_documents()
    valid_department_ids = set(DEPARTMENT_IDS.values())
    role_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    behavior_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    source_count_counts: Counter[str] = Counter()
    conversation_depth_counts: Counter[str] = Counter()
    permission_pairs: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    covered_documents: set[str] = set()

    required_fields = {
        "case_id",
        "suite_version",
        "split",
        "category",
        "difficulty",
        "user_role",
        "user_id",
        "previous_turns",
        "question",
        "expected_behavior",
        "required_facts",
        "forbidden_facts",
        "expected_source_documents",
        "expected_source_sections_or_quotes",
        "allowed_documents",
        "authoring_notes",
        "review_status",
        "reviewed_by",
        "reviewed_at",
    }
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case at index {index} is not an object")
            continue
        case_id = str(case.get("case_id") or f"index-{index}")
        missing = sorted(field for field in required_fields if field not in case)
        if missing:
            errors.append(f"{case_id}: missing fields {', '.join(missing)}")
        if case.get("suite_version") != expected_suite_version:
            errors.append(f"{case_id}: suite_version must be {expected_suite_version}")
        if case.get("split") != expected_split:
            errors.append(f"{case_id}: split must be {expected_split}")
        if case.get("category") not in CATEGORIES:
            errors.append(f"{case_id}: invalid category {case.get('category')}")
        if case.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{case_id}: invalid difficulty {case.get('difficulty')}")
        if case.get("user_role") not in USER_IDS:
            errors.append(f"{case_id}: invalid role {case.get('user_role')}")
        elif case.get("user_id") != USER_IDS[case["user_role"]]:
            errors.append(f"{case_id}: user_id does not match user_role")
        if case.get("expected_behavior") not in BEHAVIORS:
            errors.append(f"{case_id}: invalid expected_behavior {case.get('expected_behavior')}")
        if case.get("project_id") not in {None, PROJECT_ID}:
            errors.append(f"{case_id}: invalid project_id")
        if case.get("department_id") not in {None, *valid_department_ids}:
            errors.append(f"{case_id}: invalid department_id")
        if not str(case.get("question") or "").strip():
            errors.append(f"{case_id}: question is empty")
        if not isinstance(case.get("previous_turns"), list):
            errors.append(f"{case_id}: previous_turns must be a list")
        else:
            for turn in case["previous_turns"]:
                if not isinstance(turn, dict) or turn.get("role") not in {"user", "assistant"} or not str(turn.get("content") or "").strip():
                    errors.append(f"{case_id}: invalid previous_turns entry")
                    break

        behavior = case.get("expected_behavior")
        required_facts = case.get("required_facts") or []
        expected_sources = [str(value) for value in case.get("expected_source_documents") or []]
        if behavior == "answer" and not required_facts:
            errors.append(f"{case_id}: answerable case requires required_facts")
        if behavior in {"clarify", "refuse_no_access", "not_found"} and required_facts:
            errors.append(f"{case_id}: non-answer behavior cannot require answer facts")
        if behavior in {"refuse_no_access", "not_found"} and case.get("allowed_documents") and behavior == "refuse_no_access":
            restricted_expected = set(expected_sources) - set(case.get("allowed_documents") or [])
            if not restricted_expected:
                errors.append(f"{case_id}: refusal must declare an expected source outside allowed_documents")

        for document_id in expected_sources:
            if document_id.startswith("UPLOAD-"):
                continue
            if document_id not in documents:
                errors.append(f"{case_id}: expected source {document_id} is not in the corpus")
            else:
                covered_documents.add(document_id)
        for document_id, section, quote in _quote_entries(case):
            if document_id.startswith("UPLOAD-"):
                continue
            document = documents.get(document_id)
            if not document:
                errors.append(f"{case_id}: quote document {document_id} is not in the corpus")
                continue
            if section and f"## {section}" not in document["text"]:
                errors.append(f"{case_id}: section {section!r} not found in {document_id}")
            if quote and quote not in document["text"]:
                errors.append(f"{case_id}: expected quote not found in {document_id}: {quote[:80]!r}")

        if case.get("category") == "multi_document_claim_coverage" and len(set(expected_sources)) < 2 and not case.get("source_selection_only"):
            errors.append(f"{case_id}: multi-document case requires at least two expected sources")
        if case.get("category") == "permission_scope_pairs":
            pair_id = str(case.get("permission_pair_id") or "")
            restricted_expectation = case.get("restricted_source_expectation") is True
            if not pair_id and not restricted_expectation:
                errors.append(
                    f"{case_id}: permission case requires permission_pair_id or "
                    "restricted_source_expectation=true"
                )
            if pair_id:
                permission_pairs[pair_id].append(case)
        if case.get("category") == "uploaded_document_project_isolation" and not case.get("fixture_requirements"):
            errors.append(f"{case_id}: uploaded/project-isolation case requires fixture_requirements")
        if expected_split == "holdout" and (
            case.get("review_status") != "approved" or not case.get("reviewed_by") or not case.get("reviewed_at")
        ):
            errors.append(f"{case_id}: holdout review metadata is incomplete")

        role_counts[str(case.get("user_role"))] += 1
        difficulty_counts[str(case.get("difficulty"))] += 1
        behavior_counts[str(case.get("expected_behavior"))] += 1
        scope = "global" if not case.get("project_id") else ("department" if case.get("department_id") else "project")
        scope_counts[scope] += 1
        source_count_counts[str(len(expected_sources))] += 1
        conversation_depth_counts[str(len(case.get("previous_turns") or []))] += 1

    for pair_id, pair_cases in sorted(permission_pairs.items()):
        behaviors = {case.get("expected_behavior") for case in pair_cases}
        questions = {re.sub(r"\s+", " ", str(case.get("question") or "").strip().lower()) for case in pair_cases}
        if len(pair_cases) != 2 or not {"answer", "refuse_no_access"}.issubset(behaviors):
            errors.append(f"permission pair {pair_id} must contain one answer and one refusal")
        if len(questions) != 1:
            errors.append(f"permission pair {pair_id} must use materially equivalent intent text")

    if cases:
        missing_roles = sorted(set(USER_IDS) - set(role_counts))
        missing_difficulties = sorted(DIFFICULTIES - set(difficulty_counts))
        missing_behaviors = sorted(BEHAVIORS - set(behavior_counts))
        if missing_roles:
            errors.append(f"coverage missing roles: {', '.join(missing_roles)}")
        if missing_difficulties:
            errors.append(f"coverage missing difficulties: {', '.join(missing_difficulties)}")
        if missing_behaviors:
            errors.append(f"coverage missing behaviors: {', '.join(missing_behaviors)}")
        if expected_split == "development" and len(covered_documents) < 19:
            errors.append(f"development split must cover all 19 corpus documents; covered {len(covered_documents)}")
        if expected_split == "holdout" and len(covered_documents) < 12:
            warnings.append(f"holdout covers {len(covered_documents)} corpus documents; publish this coverage limitation")

    return {
        "valid": not errors,
        "split": expected_split,
        "suite_version": payload.get("suite_version"),
        "case_count": len(cases),
        "errors": errors,
        "warnings": warnings,
        "coverage": {
            "categories": dict(sorted(category_counts.items())),
            "roles": dict(sorted(role_counts.items())),
            "difficulties": dict(sorted(difficulty_counts.items())),
            "behaviors": dict(sorted(behavior_counts.items())),
            "scopes": dict(sorted(scope_counts.items())),
            "source_counts": dict(sorted(source_count_counts.items())),
            "conversation_depths": dict(sorted(conversation_depth_counts.items())),
            "documents": sorted(covered_documents),
            "permission_pair_count": len(permission_pairs),
        },
    }


def validate_split(split: str) -> dict[str, Any]:
    path = suite_path(split)
    if not path.exists():
        return {"valid": False, "split": split, "case_count": 0, "errors": [f"missing suite file: {path}"], "warnings": [], "coverage": {}}
    return validate_suite_payload(load_json(path), expected_split=split)


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # Porcelain status uses leading columns for index/worktree state. Preserve
    # the first line's leading space so dirty_paths() does not truncate a path.
    return completed.stdout.rstrip()


def git_commit() -> str:
    return git_output("rev-parse", "HEAD")


def dirty_paths() -> list[str]:
    output = git_output("status", "--porcelain", "--untracked-files=all")
    paths: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path not in IGNORED_DIRTY_PATHS:
            paths.append(path)
    return sorted(paths)


def protected_path_changes(frozen_runtime_commit: str) -> list[str]:
    return [
        line.strip().replace("\\", "/")
        for line in git_output("diff", "--name-only", f"{frozen_runtime_commit}..HEAD", "--", *PROTECTED_RUNTIME_PATHS).splitlines()
        if line.strip()
    ]


def verify_holdout_preflight(frozen_runtime_commit: str) -> dict[str, Any]:
    dirty = dirty_paths()
    protected = protected_path_changes(frozen_runtime_commit)
    actual_hash = file_sha256(HOLDOUT_PATH) if HOLDOUT_PATH.exists() else None
    recorded_hash = None
    if HOLDOUT_HASH_PATH.exists():
        recorded_hash = HOLDOUT_HASH_PATH.read_text(encoding="utf-8").strip().split()[0]
    validation = validate_split("holdout")
    errors: list[str] = []
    if dirty:
        errors.append(f"working tree has non-ignored changes: {', '.join(dirty)}")
    if protected:
        errors.append(f"protected runtime/corpus paths changed since freeze: {', '.join(protected)}")
    if not validation["valid"]:
        errors.extend(validation["errors"])
    if not actual_hash or actual_hash != recorded_hash:
        errors.append("holdout suite hash does not match holdout-v1.sha256")
    return {
        "valid": not errors,
        "errors": errors,
        "dirty_paths": dirty,
        "protected_path_changes": protected,
        "suite_hash": actual_hash,
        "recorded_suite_hash": recorded_hash,
        "corpus_hash": tree_sha256(CORPUS_DIR),
        "evaluation_commit": git_commit(),
        "frozen_runtime_commit": frozen_runtime_commit,
    }
