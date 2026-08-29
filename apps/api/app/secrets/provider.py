from __future__ import annotations

import secrets
from pathlib import Path
from typing import Protocol


class SecretProviderError(RuntimeError):
    pass


class SecretProvider(Protocol):
    def get(self, name: str) -> str | None: ...


class MountedFileSecretProvider:
    """Reads deployment-mounted secret files; it does not claim a managed store."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def get(self, name: str) -> str | None:
        if not name.replace("_", "").isalnum():
            raise SecretProviderError("invalid_secret_name")
        path = (self.root / name).resolve()
        if self.root not in path.parents:
            raise SecretProviderError("invalid_secret_path")
        try:
            if path.stat().st_size > 16_384:
                raise SecretProviderError("secret_file_too_large")
            value = path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise SecretProviderError("secret_file_unreadable") from exc
        return value or None


class ManagedSecretProvider:
    """Fail-closed boundary for a future connected managed provider."""

    def get(self, name: str) -> str | None:
        raise SecretProviderError(f"managed_secret_provider_not_connected:{name}")


_EPHEMERAL: dict[str, str] = {}


def local_ephemeral_secret(name: str) -> str:
    if name not in _EPHEMERAL:
        _EPHEMERAL[name] = secrets.token_urlsafe(48)
    return _EPHEMERAL[name]


def is_placeholder_secret(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    exact = {"password", "postgres", "secret", "changeme", "change-me", "example", "test", "dev"}
    markers = ("change-before-production", "placeholder", "example-secret", "local-secret")
    return normalized in exact or any(marker in normalized for marker in markers)
