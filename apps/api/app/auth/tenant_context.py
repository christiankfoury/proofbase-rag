from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from collections.abc import Iterator

from apps.api.app.core.config import get_settings


_active_tenant_id: ContextVar[str | None] = ContextVar("proofbase_active_tenant_id", default=None)
_active_user_id: ContextVar[str | None] = ContextVar("proofbase_active_user_id", default=None)
_platform_admin: ContextVar[bool] = ContextVar("proofbase_platform_admin", default=False)


def set_request_principal(*, tenant_id: str, user_id: str, platform_admin: bool = False) -> None:
    _active_tenant_id.set(tenant_id)
    _active_user_id.set(user_id)
    _platform_admin.set(platform_admin)


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


def database_security_context() -> tuple[str, str, bool]:
    tenant_id = _active_tenant_id.get()
    user_id = _active_user_id.get()
    if tenant_id and user_id:
        return tenant_id, user_id, _platform_admin.get()
    settings = get_settings()
    if settings.app_environment == "production":
        raise RuntimeError("Production database access requires an explicit validated request or worker context.")
    return settings.default_demo_tenant_id, settings.default_demo_user_id, True


@contextmanager
def tenant_security_context(*, tenant_id: str, user_id: str, platform_admin: bool = False) -> Iterator[None]:
    tenant_token = _active_tenant_id.set(tenant_id)
    user_token = _active_user_id.set(user_id)
    admin_token = _platform_admin.set(platform_admin)
    try:
        yield
    finally:
        _platform_admin.reset(admin_token)
        _active_user_id.reset(user_token)
        _active_tenant_id.reset(tenant_token)
