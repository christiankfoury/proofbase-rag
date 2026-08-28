from __future__ import annotations

from contextvars import ContextVar

from apps.api.app.core.config import get_settings


_active_tenant_id: ContextVar[str | None] = ContextVar("proofbase_active_tenant_id", default=None)
_active_user_id: ContextVar[str | None] = ContextVar("proofbase_active_user_id", default=None)


def set_request_principal(*, tenant_id: str, user_id: str) -> None:
    _active_tenant_id.set(tenant_id)
    _active_user_id.set(user_id)


def current_tenant_id(*, required: bool = True) -> str | None:
    tenant_id = _active_tenant_id.get()
    if tenant_id:
        return tenant_id
    settings = get_settings()
    if settings.app_environment != "production" and settings.auth_mode == "local_demo":
        return settings.default_demo_tenant_id
    if required:
        raise RuntimeError("A validated tenant context is required for this operation.")
    return None


def current_user_id() -> str | None:
    return _active_user_id.get()
