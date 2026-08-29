from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from psycopg.errors import UniqueViolation

from apps.api.app.auth.tenant_context import current_tenant_id
from apps.api.app.core.config import get_settings
from apps.api.app.db.session import get_connection

ROOT = Path(__file__).resolve().parents[4]
EICAR_MARKER = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
UNSUPPORTED_PDF_MARKERS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction", b"/AA")


class FilePolicyError(ValueError):
    def __init__(self, reason_code: str, status_code: int = 400) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.status_code = status_code


@dataclass(frozen=True)
class ScanResult:
    verdict: str
    scanner: str
    reason_code: str


@dataclass(frozen=True)
class ParsedPdf:
    markdown: str
    page_count: int
    pages_with_text: int
    confidence: float
    warnings: list[str]


class Scanner(Protocol):
    def scan(self, content: bytes) -> ScanResult: ...


class FixtureSignatureScanner:
    """Test-fixture detector, not a general malware scanner."""

    def scan(self, content: bytes) -> ScanResult:
        if EICAR_MARKER in content:
            return ScanResult("rejected", "fixture_signature_scanner", "known_test_signature")
        return ScanResult("passed_fixture_checks", "fixture_signature_scanner", "no_test_signature")


def configured_scanner() -> Scanner:
    if get_settings().file_scanner_mode == "fixture_signature":
        return FixtureSignatureScanner()
    raise FilePolicyError("hosted_scanner_not_connected", 503)


class LocalQuarantineStorage:
    def __init__(self, root: Path | None = None) -> None:
        configured = Path(get_settings().file_quarantine_dir)
        self.root = (root or (configured if configured.is_absolute() else ROOT / configured)).resolve()

    def _path(self, tenant_id: str, storage_key: str) -> Path:
        expected_prefix = f"{tenant_id}/"
        if not storage_key.startswith(expected_prefix):
            raise FilePolicyError("tenant_storage_scope_mismatch", 404)
        target = (self.root / storage_key).resolve()
        if self.root not in target.parents:
            raise FilePolicyError("invalid_storage_key")
        return target

    def put(self, tenant_id: str, content: bytes) -> str:
        storage_key = f"{tenant_id}/{uuid.uuid4()}.blob"
        target = self._path(tenant_id, storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        descriptor = os.open(target, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return storage_key

    def path_for_parser(self, tenant_id: str, storage_key: str) -> Path:
        target = self._path(tenant_id, storage_key)
        if not target.is_file():
            raise FilePolicyError("file_object_not_found", 404)
        return target

    def delete(self, tenant_id: str, storage_key: str) -> None:
        self._path(tenant_id, storage_key).unlink(missing_ok=True)


def validate_pdf_envelope(*, filename: str, declared_mime: str | None, content: bytes, data_classification: str) -> None:
    settings = get_settings()
    if data_classification != "non_sensitive":
        raise FilePolicyError("regulated_or_personal_data_not_accepted", 400)
    if Path(filename).suffix.lower() != ".pdf":
        raise FilePolicyError("unsupported_file_type")
    if declared_mime != "application/pdf":
        raise FilePolicyError("declared_mime_mismatch")
    if not content.startswith(b"%PDF-"):
        raise FilePolicyError("file_signature_mismatch")
    if len(content) > settings.file_max_bytes:
        raise FilePolicyError("file_too_large", 413)
    eof_index = content.rfind(b"%%EOF")
    if eof_index < 0:
        raise FilePolicyError("malformed_pdf")
    if content[eof_index + len(b"%%EOF") :].strip():
        raise FilePolicyError("polyglot_or_trailing_payload")
    if b"PK\x03\x04" in content:
        raise FilePolicyError("polyglot_or_embedded_archive")
    if any(marker in content for marker in UNSUPPORTED_PDF_MARKERS):
        raise FilePolicyError("unsupported_pdf_active_content")


def parse_pdf_isolated(path: Path, *, title: str) -> ParsedPdf:
    settings = get_settings()
    if settings.file_parser_mode != "subprocess":
        raise FilePolicyError("isolated_parser_not_connected", 503)
    command = [
        sys.executable,
        "-m",
        "apps.api.app.files.secure_parser_worker",
        str(path),
        title,
        str(settings.file_max_pages),
        str(settings.file_max_extracted_chars),
        str(settings.file_max_expansion_ratio),
    ]
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "PYTHONPATH": str(ROOT),
        "PYTHONNOUSERSITE": "1",
    }
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=settings.file_parser_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise FilePolicyError("parser_timeout") from exc
    if result.returncode != 0:
        reason = result.stdout.strip() if result.stdout.strip().startswith("parser_") else "parser_failed"
        raise FilePolicyError(reason)
    try:
        payload = json.loads(result.stdout)
        return ParsedPdf(**payload)
    except (json.JSONDecodeError, TypeError) as exc:
        raise FilePolicyError("parser_invalid_output") from exc


def create_file_object(*, project_id: str, department_id: str, original_name: str, declared_mime: str, content: bytes, storage_key: str) -> dict:
    tenant_id = str(current_tenant_id())
    digest = hashlib.sha256(content).hexdigest()
    settings = get_settings()
    with get_connection() as conn:
        duplicate = conn.execute(
            """
            select id::text from file_objects
            where tenant_id = %s::uuid and project_id = %s::uuid and department_id = %s::uuid
              and content_sha256 = %s and lifecycle_state not in ('rejected', 'deleted')
            limit 1
            """,
            (tenant_id, project_id, department_id, digest),
        ).fetchone()
        if duplicate:
            raise FilePolicyError("duplicate_file", 409)
        try:
            row = conn.execute(
                """
                insert into file_objects (
                  tenant_id, project_id, department_id, storage_key, original_name_hash,
                  declared_mime, detected_mime, size_bytes, content_sha256, lifecycle_state,
                  retention_expires_at, data_classification
                ) values (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, 'application/pdf', %s, %s,
                          'quarantined', now() + (%s || ' days')::interval, 'non_sensitive')
                returning id::text, storage_key, lifecycle_state, retention_expires_at
                """,
                (
                    tenant_id,
                    project_id,
                    department_id,
                    storage_key,
                    hashlib.sha256(original_name.encode("utf-8")).hexdigest(),
                    declared_mime,
                    len(content),
                    digest,
                    settings.file_quarantine_retention_days,
                ),
            ).fetchone()
        except UniqueViolation as exc:
            raise FilePolicyError("duplicate_file", 409) from exc
    return dict(row)


def transition_file_object(file_object_id: str, *, state: str, scanner: ScanResult | None = None, page_count: int | None = None, reason_code: str | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            update file_objects set lifecycle_state = %s, scanner_name = coalesce(%s, scanner_name),
              scanner_verdict = coalesce(%s, scanner_verdict), page_count = coalesce(%s, page_count),
              rejection_reason = %s, updated_at = now()
            where id = %s::uuid
            """,
            (state, scanner.scanner if scanner else None, scanner.verdict if scanner else None, page_count, reason_code, file_object_id),
        )


def mark_file_object_approved(file_object_id: str) -> None:
    settings = get_settings()
    with get_connection() as conn:
        conn.execute(
            """
            update file_objects set retention_expires_at = now() + (%s || ' days')::interval,
              updated_at = now()
            where id = %s::uuid and lifecycle_state = 'clean'
            """,
            (settings.file_approved_original_retention_days, file_object_id),
        )


def issue_read_grant(*, file_object_id: str, tenant_id: str, ttl_seconds: int = 60, now: int | None = None) -> str:
    if not 1 <= ttl_seconds <= 300:
        raise ValueError("File grant TTL must be between 1 and 300 seconds.")
    issued = int(time.time() if now is None else now)
    payload = {"file_object_id": file_object_id, "tenant_id": tenant_id, "exp": issued + ttl_seconds}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(get_settings().file_access_signing_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_read_grant(token: str, *, tenant_id: str, now: int | None = None) -> str:
    try:
        encoded, supplied = token.split(".", 1)
        expected = hmac.new(get_settings().file_access_signing_secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied, expected):
            raise FilePolicyError("invalid_file_grant", 403)
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    except (ValueError, json.JSONDecodeError) as exc:
        raise FilePolicyError("invalid_file_grant", 403) from exc
    try:
        expires = int(payload.get("exp", 0))
        file_object_id = payload["file_object_id"]
    except (KeyError, TypeError, ValueError) as exc:
        raise FilePolicyError("invalid_file_grant", 403) from exc
    current = int(time.time() if now is None else now)
    if payload.get("tenant_id") != tenant_id or expires <= current or not isinstance(file_object_id, str):
        raise FilePolicyError("expired_or_wrong_tenant_file_grant", 403)
    return file_object_id


def delete_file_object(file_object_id: str, *, storage: LocalQuarantineStorage) -> bool:
    tenant_id = str(current_tenant_id())
    with get_connection() as conn:
        row = conn.execute(
            "select storage_key, legal_hold from file_objects where id = %s::uuid",
            (file_object_id,),
        ).fetchone()
        if not row:
            return False
        if row["legal_hold"]:
            raise FilePolicyError("legal_hold_prevents_deletion", 409)
        conn.execute(
            "update file_objects set lifecycle_state = 'deleted', deleted_at = now(), updated_at = now() where id = %s::uuid",
            (file_object_id,),
        )
    storage.delete(tenant_id, row["storage_key"])
    return True
