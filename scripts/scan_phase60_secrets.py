from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "credential_url": re.compile(r"(?i)\b(?:postgres(?:ql)?|redis(?:s)?)://[^\s/@:'\"]+:[^\s/@'\"]+@[^\s'\"]+"),
}
TEXT_SUFFIXES = {
    ".cfg", ".css", ".env", ".example", ".html", ".ini", ".js", ".json", ".jsx",
    ".md", ".mjs", ".py", ".sql", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml",
}
SKIP_PARTS = {".git", ".next", ".next-codex-build", ".venv", "node_modules", "__pycache__"}
FORBIDDEN_IMAGE_ARTIFACTS = (
    "data/audit",
    "data/observability",
    "data/quarantine",
    "data/security",
    "data/uploads",
    ".env",
)


def _allowed_local_fixture(match: str) -> bool:
    lowered = match.lower()
    return (
        lowered.startswith("postgresql://postgres:postgres@localhost")
        or lowered.startswith("postgresql://postgres:postgres@postgres")
        or lowered.startswith("postgresql://proofbase_runtime:password@db")
        or lowered.startswith("postgresql://postgres:secret@db")
        or lowered.startswith("postgresql://proofbase_runtime:secret@db")
        or lowered.startswith("postgresql://proofbase_app:secret@db")
        or lowered.startswith("redis://localhost")
        or lowered.startswith("redis://redis")
    )


def scan_path(path: Path, *, include_build_output: bool = False) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    candidates = [path] if path.is_file() else path.rglob("*")
    for candidate in candidates:
        if not candidate.is_file() or candidate.stat().st_size > 5_000_000:
            continue
        relative_parts = set(candidate.relative_to(path if path.is_dir() else candidate.parent).parts)
        if not include_build_output and relative_parts & SKIP_PARTS:
            continue
        if candidate.suffix.lower() not in TEXT_SUFFIXES and candidate.name not in {"Dockerfile", ".env.example", ".dockerignore"}:
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    matched = match.group(0)
                    if kind == "credential_url" and _allowed_local_fixture(matched):
                        continue
                    findings.append({
                        "path": str(candidate),
                        "line": line_number,
                        "kind": kind,
                        "fingerprint": hashlib.sha256(matched.encode()).hexdigest()[:12],
                    })
    return findings


def _scan_container(image: str) -> list[dict[str, object]]:
    command = [
        "docker", "run", "--rm", "--network", "none", image,
        "python", "scripts/scan_phase60_secrets.py", "--filesystem", "--root", "/app",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        try:
            payload = json.loads(result.stdout)
            return list(payload.get("findings") or [])
        except json.JSONDecodeError:
            pass
    return _scan_container_archive(image)


def _scan_container_archive(image: str) -> list[dict[str, object]]:
    """Fallback for minimal images that do not contain Python or this scanner."""
    created = subprocess.run(
        ["docker", "create", "--network", "none", image],
        capture_output=True,
        text=True,
        check=False,
    )
    container_id = created.stdout.strip()
    if created.returncode != 0 or not container_id:
        return [{"path": image, "line": 0, "kind": "container_scan_failed", "fingerprint": "not_available"}]
    findings: list[dict[str, object]] = []
    try:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "filesystem.tar"
            exported = subprocess.run(
                ["docker", "export", "--output", str(archive_path), container_id],
                capture_output=True,
                text=True,
                check=False,
            )
            if exported.returncode != 0:
                return [{"path": image, "line": 0, "kind": "container_scan_failed", "fingerprint": "not_available"}]
            with tarfile.open(archive_path, "r") as archive:
                for member in archive.getmembers():
                    relative = member.name.lstrip("./")
                    if any(relative == f"app/{path}" or relative.startswith(f"app/{path}/") for path in FORBIDDEN_IMAGE_ARTIFACTS):
                        findings.append({"path": f"{image}:{relative}", "line": 0, "kind": "forbidden_runtime_artifact", "fingerprint": "present"})
                    candidate = Path(relative)
                    if not member.isfile() or not relative.startswith("app/") or member.size > 5_000_000:
                        continue
                    if candidate.suffix.lower() not in TEXT_SUFFIXES and candidate.name not in {"Dockerfile", ".env.example", ".dockerignore"}:
                        continue
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        continue
                    try:
                        text = extracted.read().decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    for line_number, line in enumerate(text.splitlines(), start=1):
                        for kind, pattern in PATTERNS.items():
                            for match in pattern.finditer(line):
                                matched = match.group(0)
                                if kind == "credential_url" and _allowed_local_fixture(matched):
                                    continue
                                findings.append({
                                    "path": f"{image}:{relative}",
                                    "line": line_number,
                                    "kind": kind,
                                    "fingerprint": hashlib.sha256(matched.encode()).hexdigest()[:12],
                                })
        return findings
    finally:
        subprocess.run(["docker", "rm", "--force", container_id], capture_output=True, text=True, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan source, build output, or a local image for high-confidence secret patterns.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--scan-path", action="append", default=[])
    parser.add_argument("--include-build-output", action="store_true")
    parser.add_argument("--container-image")
    parser.add_argument("--filesystem", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    roots = [Path(value).resolve() for value in args.scan_path] or [Path(args.root).resolve()]
    findings: list[dict[str, object]] = []
    for root in roots:
        findings.extend(scan_path(root, include_build_output=args.include_build_output or args.filesystem))
        if args.filesystem:
            for relative in FORBIDDEN_IMAGE_ARTIFACTS:
                if (root / relative).exists():
                    findings.append({"path": str(root / relative), "line": 0, "kind": "forbidden_runtime_artifact", "fingerprint": "present"})
    if args.container_image:
        findings.extend(_scan_container(args.container_image))
    payload = {"status": "passed" if not findings else "failed", "finding_count": len(findings), "findings": findings}
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if not findings else 1)


if __name__ == "__main__":
    main()
