from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable


class ReliabilityError(RuntimeError):
    """Raised when durable evaluation state is incomplete or inconsistent."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def case_hash(case: dict[str, Any]) -> str:
    return payload_sha256(case)


def validate_fixture_declaration(case: dict[str, Any]) -> list[str]:
    requirements = case.get("fixture_requirements")
    if not requirements:
        return []
    case_id = str(case.get("case_id") or "unknown")
    if not isinstance(requirements, dict):
        return [f"{case_id}: fixture_requirements must be an object"]
    errors: list[str] = []
    documents = requirements.get("documents")
    scenario = str(requirements.get("scenario") or "")
    supported_scenarios = {
        "pending_review_not_indexed",
        "approved_document_retrievable",
        "strict_department_scope",
        "cross_project_membership",
    }
    if documents is not None:
        if not isinstance(documents, list) or not documents:
            errors.append(f"{case_id}: fixture documents must be a non-empty list")
            return errors
        query_project = str(requirements.get("query_project_id") or case.get("project_id") or "")
        query_department = str(requirements.get("query_department_id") or case.get("department_id") or "")
        if not query_project or not query_department:
            errors.append(f"{case_id}: declared-document fixture requires query project and department")
        matching = 0
        declared_ids: set[str] = set()
        for index, item in enumerate(documents):
            label = f"{case_id}: fixture document {index + 1}"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            required = ("document_id", "project_id", "department_id", "title", "content_markdown", "access_roles", "restricted")
            missing = [field for field in required if field not in item]
            if missing:
                errors.append(f"{label} missing {', '.join(missing)}")
            document_id = str(item.get("document_id") or "")
            if not document_id.startswith("UPLOAD-"):
                errors.append(f"{label} document_id must use the UPLOAD- placeholder prefix")
            if document_id in declared_ids:
                errors.append(f"{case_id}: duplicate fixture document_id {document_id}")
            declared_ids.add(document_id)
            if not str(item.get("content_markdown") or "").strip():
                errors.append(f"{label} content_markdown is empty")
            roles = item.get("access_roles")
            if not isinstance(roles, list) or not roles or not all(isinstance(role, str) and role.strip() for role in roles):
                errors.append(f"{label} access_roles must be a non-empty string list")
            if str(item.get("project_id") or "") == query_project and str(item.get("department_id") or "") == query_department:
                matching += 1
        if matching != 1:
            errors.append(f"{case_id}: fixture must declare exactly one document in the query scope; found {matching}")
        expected_uploads = {str(value) for value in case.get("expected_source_documents") or [] if str(value).startswith("UPLOAD-")}
        if not expected_uploads.issubset(declared_ids):
            errors.append(f"{case_id}: expected upload sources are not declared by the fixture")
    elif scenario not in supported_scenarios:
        errors.append(f"{case_id}: unsupported fixture scenario {scenario!r}")
    return errors


def validate_cases_for_execution(
    cases: list[dict[str, Any]],
    *,
    dependency_validator: Callable[[list[dict[str, Any]]], Iterable[str]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    ids: set[str] = set()
    hashes: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case at index {index} is not an object")
            continue
        case_id = str(case.get("case_id") or "")
        if not case_id:
            errors.append(f"case at index {index} has no case_id")
        elif case_id in ids:
            errors.append(f"duplicate case ID: {case_id}")
        ids.add(case_id)
        digest = case_hash(case)
        if digest in hashes:
            errors.append(f"duplicate case payload hash: {case_id}")
        hashes.add(digest)
        errors.extend(validate_fixture_declaration(case))
    if dependency_validator is not None:
        try:
            errors.extend(str(error) for error in dependency_validator(cases))
        except Exception as exc:  # dependency failures must remain preflight failures
            errors.append(f"dependency preflight failed: {type(exc).__name__}: {exc}")
    return {
        "valid": not errors,
        "errors": errors,
        "case_count": len(cases),
        "case_ids": [str(case.get("case_id") or "") for case in cases if isinstance(case, dict)],
        "case_hashes": [case_hash(case) for case in cases if isinstance(case, dict)],
    }


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.json"

    @property
    def journal(self) -> Path:
        return self.root / "journal.jsonl"

    @property
    def records(self) -> Path:
        return self.root / "cases"

    @property
    def final(self) -> Path:
        return self.root / "final.json"


class ReliableEvaluationRun:
    def __init__(
        self,
        *,
        run_root: Path,
        run_id: str,
        cases: list[dict[str, Any]],
        suite_hash: str,
        runtime_commit: str,
        evaluation_commit: str,
        configuration: dict[str, Any],
        budget_usd: float,
        execute_case: Callable[[dict[str, Any]], dict[str, Any]],
        aggregate: Callable[[list[dict[str, Any]]], dict[str, Any]],
        clock: Callable[[], str] = utc_now,
        fault_hook: Callable[[str, int | None], None] | None = None,
    ) -> None:
        self.paths = RunPaths(run_root)
        self.run_id = run_id
        self.cases = cases
        self.suite_hash = suite_hash
        self.runtime_commit = runtime_commit
        self.evaluation_commit = evaluation_commit
        self.configuration = configuration
        self.budget_usd = budget_usd
        self.execute_case = execute_case
        self.aggregate = aggregate
        self.clock = clock
        self.fault_hook = fault_hook or (lambda _name, _index: None)
        self.case_hashes = [case_hash(case) for case in cases]

    def _fault(self, name: str, index: int | None = None) -> None:
        self.fault_hook(name, index)

    def _initial_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "status": "running",
            "started_at": self.clock(),
            "completed_at": None,
            "suite_hash": self.suite_hash,
            "runtime_commit": self.runtime_commit,
            "evaluation_commit": self.evaluation_commit,
            "configuration": self.configuration,
            "budget_usd": self.budget_usd,
            "case_count": len(self.cases),
            "case_ids": [str(case["case_id"]) for case in self.cases],
            "case_hashes": self.case_hashes,
            "completed_case_count": 0,
            "next_case_index": 0,
            "estimated_cost_usd": 0.0,
            "run_complete": False,
            "aggregate_from_persisted_rows": False,
            "last_error": None,
        }

    def _load_manifest(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReliabilityError(f"manifest is missing or corrupted: {exc}") from exc
        expected = {
            "run_id": self.run_id,
            "suite_hash": self.suite_hash,
            "runtime_commit": self.runtime_commit,
            "evaluation_commit": self.evaluation_commit,
            "case_count": len(self.cases),
            "case_ids": [str(case["case_id"]) for case in self.cases],
            "case_hashes": self.case_hashes,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise ReliabilityError(f"manifest {key} does not match the frozen run")
        return payload

    def _journal_events(self) -> list[dict[str, Any]]:
        if not self.paths.journal.exists():
            return []
        events: list[dict[str, Any]] = []
        previous_hash = "GENESIS"
        with self.paths.journal.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                if not raw.strip():
                    raise ReliabilityError(f"journal contains a blank record at line {line_number}")
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ReliabilityError(f"journal is corrupted at line {line_number}: {exc}") from exc
                if event.get("sequence") != line_number:
                    raise ReliabilityError(f"journal is out of order at line {line_number}")
                if event.get("previous_hash") != previous_hash:
                    raise ReliabilityError(f"journal hash chain is broken at line {line_number}")
                event_hash = event.get("event_hash")
                unsigned = {key: value for key, value in event.items() if key != "event_hash"}
                if event_hash != payload_sha256(unsigned):
                    raise ReliabilityError(f"journal event hash is invalid at line {line_number}")
                previous_hash = str(event_hash)
                events.append(event)
        completed_ids = [event.get("case_id") for event in events if event.get("event") == "case_completed"]
        duplicates = sorted({case_id for case_id in completed_ids if completed_ids.count(case_id) > 1})
        if duplicates:
            raise ReliabilityError(f"duplicate completed journal records: {', '.join(duplicates)}")
        return events

    def _append_event(self, event: str, **payload: Any) -> dict[str, Any]:
        events = self._journal_events()
        unsigned = {
            "sequence": len(events) + 1,
            "previous_hash": events[-1]["event_hash"] if events else "GENESIS",
            "timestamp": self.clock(),
            "event": event,
            **payload,
        }
        record = {**unsigned, "event_hash": payload_sha256(unsigned)}
        self.paths.root.mkdir(parents=True, exist_ok=True)
        with self.paths.journal.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def _record_path(self, index: int, case_id: str) -> Path:
        safe_id = "".join(character if character.isalnum() or character in "-_" else "_" for character in case_id)
        return self.paths.records / f"{index + 1:03d}-{safe_id}.json"

    def _make_record(
        self,
        *,
        index: int,
        row: dict[str, Any],
        attempt_count: int,
        started_at: str,
        completed_at: str,
    ) -> dict[str, Any]:
        case = self.cases[index]
        case_id = str(case["case_id"])
        citations = list(row.get("citations") or [])
        retrieved_chunks = list(row.get("retrieved_chunks") or [])
        response = {
            "status_code": row.get("status_code"),
            "response_type": row.get("actual_behavior"),
            "answer": row.get("answer"),
            "rewritten_question": row.get("rewritten_question"),
            "unsupported_claims": row.get("unsupported_claims") or [],
        }
        retrieval_evidence = {
            "retrieved_documents": row.get("retrieved_documents") or [],
            "retrieved_chunks": retrieved_chunks,
            "citation_documents": row.get("citation_documents") or [],
            "permission_check": row.get("permission_check") or {},
        }
        scoring_exclusions = {
            "citations", "retrieved_chunks", "answer", "status_code", "actual_behavior", "rewritten_question",
            "unsupported_claims", "input_tokens", "output_tokens", "estimated_cost_usd",
        }
        record = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "case_index": index,
            "case_id": case_id,
            "case_hash": self.case_hashes[index],
            "suite_hash": self.suite_hash,
            "runtime_commit": self.runtime_commit,
            "evaluation_commit": self.evaluation_commit,
            "started_at": started_at,
            "completed_at": completed_at,
            "attempt_count": attempt_count,
            "status": "completed",
            "response": response,
            "citations": citations,
            "retrieval_evidence": retrieval_evidence,
            "scoring": {key: value for key, value in row.items() if key not in scoring_exclusions},
            "error_category": None,
            "tokens": {
                "input": int(row.get("input_tokens") or 0),
                "output": int(row.get("output_tokens") or 0),
            },
            "estimated_cost_usd": round(float(row.get("estimated_cost_usd") or 0.0), 9),
            "row": row,
        }
        record["record_hash"] = payload_sha256(record)
        return record

    def _validate_record(self, record: dict[str, Any], index: int) -> None:
        case_id = str(self.cases[index]["case_id"])
        if record.get("case_index") != index or record.get("case_id") != case_id:
            raise ReliabilityError(f"case record {index + 1} is out of order")
        if record.get("case_hash") != self.case_hashes[index] or record.get("suite_hash") != self.suite_hash:
            raise ReliabilityError(f"case record {case_id} has invalid provenance")
        if record.get("status") != "completed":
            raise ReliabilityError(f"case record {case_id} is not completed")
        record_hash = record.get("record_hash")
        unsigned = {key: value for key, value in record.items() if key != "record_hash"}
        if record_hash != payload_sha256(unsigned):
            raise ReliabilityError(f"case record {case_id} is corrupted")

    def _persisted_records(self) -> list[dict[str, Any]]:
        self.paths.records.mkdir(parents=True, exist_ok=True)
        expected_paths = [self._record_path(index, str(case["case_id"])) for index, case in enumerate(self.cases)]
        expected_names = {path.name for path in expected_paths}
        unexpected = sorted(path.name for path in self.paths.records.glob("*.json") if path.name not in expected_names)
        if unexpected:
            raise ReliabilityError(f"duplicate or unexpected case records: {', '.join(unexpected)}")
        records: list[dict[str, Any]] = []
        missing_seen = False
        for index, path in enumerate(expected_paths):
            if not path.exists():
                missing_seen = True
                continue
            if missing_seen:
                raise ReliabilityError(f"case records are missing or out of order before {path.name}")
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ReliabilityError(f"case record {path.name} is corrupted: {exc}") from exc
            self._validate_record(record, index)
            records.append(record)
        return records

    def _recover_journaled_records(self) -> None:
        events = self._journal_events()
        completed = {str(event["case_id"]): event for event in events if event.get("event") == "case_completed"}
        for index, case in enumerate(self.cases):
            case_id = str(case["case_id"])
            path = self._record_path(index, case_id)
            event = completed.get(case_id)
            if path.exists() or event is None:
                continue
            record = event.get("record")
            if not isinstance(record, dict) or event.get("record_hash") != record.get("record_hash"):
                raise ReliabilityError(f"journaled result for {case_id} is corrupted")
            self._validate_record(record, index)
            write_json_atomic(path, record)
            self._append_event(
                "case_record_recovered",
                case_index=index,
                case_id=case_id,
                case_hash=self.case_hashes[index],
                record_hash=record["record_hash"],
            )

    def _checkpoint(self, manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
        updated = {
            **manifest,
            "status": "running",
            "completed_case_count": len(records),
            "next_case_index": len(records),
            "estimated_cost_usd": round(sum(float(record["estimated_cost_usd"]) for record in records), 9),
            "run_complete": False,
            "aggregate_from_persisted_rows": False,
            "last_error": None,
        }
        write_json_atomic(self.paths.manifest, updated)
        return updated

    def _attempt_count(self, events: list[dict[str, Any]], case_id: str) -> int:
        return sum(1 for event in events if event.get("event") == "case_started" and event.get("case_id") == case_id) + 1

    def _finalize(self, manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
        if len(records) != len(self.cases):
            raise ReliabilityError(f"cannot aggregate incomplete run: {len(records)}/{len(self.cases)} rows")
        self._fault("before_final_aggregation", None)
        rows = [record["row"] for record in records]
        summary = self.aggregate(rows)
        completed_at = max(str(record["completed_at"]) for record in records)
        final = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "status": "complete",
            "started_at": manifest["started_at"],
            "completed_at": completed_at,
            "provenance": {
                "suite_hash": self.suite_hash,
                "runtime_commit": self.runtime_commit,
                "evaluation_commit": self.evaluation_commit,
                "configuration": self.configuration,
            },
            "run_completeness": {
                "status": "complete",
                "expected_case_count": len(self.cases),
                "persisted_case_count": len(records),
                "contiguous_case_count": len(records),
                "duplicate_case_records": 0,
                "corrupted_case_records": 0,
                "journal_verified": True,
                "aggregate_from_persisted_rows": True,
                "external_calls_duplicated": False,
            },
            "summary": summary,
            "rows": rows,
            "execution_records": records,
        }
        write_json_atomic(self.paths.final, final)
        self._fault("after_final_artifact", None)
        if not any(event.get("event") == "run_completed" for event in self._journal_events()):
            self._append_event("run_completed", case_count=len(records), final_hash=payload_sha256(final))
        completed_manifest = {
            **manifest,
            "status": "complete",
            "completed_at": completed_at,
            "completed_case_count": len(records),
            "next_case_index": len(records),
            "estimated_cost_usd": round(sum(float(record["estimated_cost_usd"]) for record in records), 9),
            "run_complete": True,
            "aggregate_from_persisted_rows": True,
            "final_artifact_hash": payload_sha256(final),
            "last_error": None,
        }
        write_json_atomic(self.paths.manifest, completed_manifest)
        return final

    def run(self) -> dict[str, Any]:
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.paths.records.mkdir(parents=True, exist_ok=True)
        if self.paths.manifest.exists():
            manifest = self._load_manifest()
        else:
            manifest = self._initial_manifest()
            write_json_atomic(self.paths.manifest, manifest)
            self._append_event("run_started", case_count=len(self.cases), suite_hash=self.suite_hash)
        try:
            self._recover_journaled_records()
            records = self._persisted_records()
            manifest = self._checkpoint(manifest, records)
            if manifest.get("status") == "complete" and self.paths.final.exists():
                return json.loads(self.paths.final.read_text(encoding="utf-8"))
            for index in range(len(records), len(self.cases)):
                case = self.cases[index]
                case_id = str(case["case_id"])
                events = self._journal_events()
                attempt_count = self._attempt_count(events, case_id)
                started_at = self.clock()
                self._append_event(
                    "case_started",
                    case_index=index,
                    case_id=case_id,
                    case_hash=self.case_hashes[index],
                    attempt_count=attempt_count,
                )
                self._fault("before_case_execution", index)
                try:
                    row = self.execute_case(case)
                except Exception as exc:
                    self._append_event(
                        "case_failed",
                        case_index=index,
                        case_id=case_id,
                        case_hash=self.case_hashes[index],
                        attempt_count=attempt_count,
                        status="error",
                        error_category=type(exc).__name__,
                        error_message=str(exc),
                    )
                    raise
                completed_at = self.clock()
                record = self._make_record(
                    index=index,
                    row=row,
                    attempt_count=attempt_count,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                self._append_event(
                    "case_completed",
                    case_index=index,
                    case_id=case_id,
                    case_hash=self.case_hashes[index],
                    attempt_count=attempt_count,
                    record_hash=record["record_hash"],
                    record=record,
                )
                self._fault("after_journaled_result", index)
                write_json_atomic(self._record_path(index, case_id), record)
                self._fault("after_case_record", index)
                records = self._persisted_records()
                manifest = self._checkpoint(manifest, records)
                if float(manifest["estimated_cost_usd"]) > self.budget_usd:
                    raise ReliabilityError(
                        f"run cost ${manifest['estimated_cost_usd']:.6f} exceeded budget ${self.budget_usd:.2f}"
                    )
                self._fault("after_case_checkpoint", index)
            records = self._persisted_records()
            return self._finalize(manifest, records)
        except Exception as exc:
            try:
                self._append_event(
                    "run_interrupted",
                    error_category=type(exc).__name__,
                    error_message=str(exc),
                )
                current = self._load_manifest()
                interrupted = {
                    **current,
                    "status": "interrupted",
                    "run_complete": False,
                    "aggregate_from_persisted_rows": False,
                    "last_error": {"category": type(exc).__name__, "message": str(exc), "timestamp": self.clock()},
                }
                write_json_atomic(self.paths.manifest, interrupted)
            except Exception:
                pass
            raise
