from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def purge_jsonl(
    path: Path,
    *,
    timestamp_field: str,
    retention_days: int,
    now: datetime | None = None,
    incident_hold: bool = False,
) -> dict[str, Any]:
    if retention_days < 1:
        raise ValueError("Retention must be at least one day.")
    if incident_hold or not path.exists():
        return {"scanned": 0, "retained": 0, "deleted": 0, "incident_hold": incident_hold}

    cutoff = (now or datetime.now(UTC)) - timedelta(days=retention_days)
    retained_lines: list[str] = []
    scanned = 0
    deleted = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        scanned += 1
        try:
            payload = json.loads(raw_line)
            timestamp = datetime.fromisoformat(str(payload[timestamp_field]).replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            retained_lines.append(raw_line)
            continue
        if timestamp < cutoff:
            deleted += 1
        else:
            retained_lines.append(raw_line)

    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text("\n".join(retained_lines) + ("\n" if retained_lines else ""), encoding="utf-8")
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "scanned": scanned,
        "retained": len(retained_lines),
        "deleted": deleted,
        "incident_hold": False,
    }
