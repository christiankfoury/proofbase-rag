from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from apps.api.app.core.config import get_settings


@dataclass(frozen=True)
class LimitResult:
    allowed: bool
    retry_after_seconds: int = 0


@dataclass(frozen=True)
class LimitContext:
    tenant_id: str
    user_id: str
    ip_risk_context: str


@dataclass(frozen=True)
class OperationPolicy:
    identity_limit: int
    tenant_limit: int
    window_seconds: int
    ip_limit: int
    concurrency_identity: int = 0
    concurrency_tenant: int = 0


class LimiterUnavailableError(RuntimeError):
    pass


class LimitBackend(Protocol):
    def consume(self, key: str, *, limit: int, window_seconds: int, cost: int = 1) -> LimitResult: ...

    def acquire(self, key: str, *, limit: int, lease_seconds: int, token: str) -> LimitResult: ...

    def release(self, key: str, *, token: str) -> None: ...


class InMemoryLimitBackend:
    """Process-local development backend; never presented as distributed protection."""

    def __init__(self, *, clock=time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[float, int]] = {}
        self._leases: dict[str, dict[str, float]] = {}

    def consume(self, key: str, *, limit: int, window_seconds: int, cost: int = 1) -> LimitResult:
        now = self._clock()
        with self._lock:
            expires_at, used = self._windows.get(key, (now + window_seconds, 0))
            if expires_at <= now:
                expires_at, used = now + window_seconds, 0
            if used + cost > limit:
                self._windows[key] = (expires_at, used)
                return LimitResult(False, max(1, int(expires_at - now + 0.999)))
            self._windows[key] = (expires_at, used + cost)
        return LimitResult(True)

    def acquire(self, key: str, *, limit: int, lease_seconds: int, token: str) -> LimitResult:
        now = self._clock()
        with self._lock:
            leases = self._leases.setdefault(key, {})
            for candidate, expires_at in list(leases.items()):
                if expires_at <= now:
                    del leases[candidate]
            if len(leases) >= limit:
                retry_after = max(1, int(min(leases.values()) - now + 0.999))
                return LimitResult(False, retry_after)
            leases[token] = now + lease_seconds
        return LimitResult(True)

    def release(self, key: str, *, token: str) -> None:
        with self._lock:
            self._leases.get(key, {}).pop(token, None)


_CONSUME_SCRIPT = """
local used = redis.call('INCRBY', KEYS[1], ARGV[1])
if used == tonumber(ARGV[1]) then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
local ttl = redis.call('TTL', KEYS[1])
if used > tonumber(ARGV[3]) then
  redis.call('DECRBY', KEYS[1], ARGV[1])
  return {0, math.max(ttl, 1)}
end
return {1, 0}
"""

_ACQUIRE_SCRIPT = """
local now = tonumber(ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[2]) then
  local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
  return {0, math.max(math.ceil(tonumber(oldest[2]) - now), 1)}
end
redis.call('ZADD', KEYS[1], now + tonumber(ARGV[3]), ARGV[4])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]) + 1)
return {1, 0}
"""


class RedisLimitBackend:
    def __init__(self, redis_url: str) -> None:
        try:
            import redis
        except ImportError as exc:
            raise LimiterUnavailableError("The Redis limiter dependency is unavailable.") from exc
        self._client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )

    def consume(self, key: str, *, limit: int, window_seconds: int, cost: int = 1) -> LimitResult:
        try:
            allowed, retry_after = self._client.eval(
                _CONSUME_SCRIPT, 1, key, cost, window_seconds, limit
            )
        except Exception as exc:
            raise LimiterUnavailableError("The shared abuse-control store is unavailable.") from exc
        return LimitResult(bool(allowed), int(retry_after))

    def acquire(self, key: str, *, limit: int, lease_seconds: int, token: str) -> LimitResult:
        try:
            now = time.time()
            allowed, retry_after = self._client.eval(
                _ACQUIRE_SCRIPT, 1, key, now, limit, lease_seconds, token
            )
        except Exception as exc:
            raise LimiterUnavailableError("The shared abuse-control store is unavailable.") from exc
        return LimitResult(bool(allowed), int(retry_after))

    def release(self, key: str, *, token: str) -> None:
        try:
            self._client.zrem(key, token)
        except Exception:
            return


POLICIES: dict[str, OperationPolicy] = {
    "auth": OperationPolicy(20, 200, 300, 40),
    "chat_session": OperationPolicy(20, 100, 60, 60),
    "chat": OperationPolicy(20, 120, 60, 80),
    "stream": OperationPolicy(8, 40, 60, 30, 2, 10),
    "feedback": OperationPolicy(20, 100, 60, 60),
    "upload": OperationPolicy(10, 100, 3600, 30),
    "cleanup": OperationPolicy(6, 40, 3600, 20),
    "indexing": OperationPolicy(10, 100, 3600, 30, 2, 8),
    "evaluation": OperationPolicy(30, 200, 60, 80),
    "admin": OperationPolicy(30, 200, 60, 80),
}


def _opaque(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


class OperationLease:
    def __init__(self, backend: LimitBackend, keys: list[str], token: str) -> None:
        self._backend = backend
        self._keys = keys
        self._token = token
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        for key in self._keys:
            self._backend.release(key, token=self._token)
        self._released = True


class RateLimitManager:
    def __init__(self, backend: LimitBackend, *, prefix: str = "proofbase:limit:v1") -> None:
        self.backend = backend
        self.prefix = prefix

    def _key(self, scope: str, identifier: str, operation: str) -> str:
        return f"{self.prefix}:{scope}:{_opaque(identifier)}:{operation}"

    def enforce(self, operation: str, context: LimitContext) -> LimitResult:
        policy = POLICIES[operation]
        checks = (
            ("identity", context.user_id, policy.identity_limit),
            ("tenant", context.tenant_id, policy.tenant_limit),
            ("ip", context.ip_risk_context, policy.ip_limit),
        )
        for scope, identifier, limit in checks:
            result = self.backend.consume(
                self._key(scope, identifier, operation),
                limit=limit,
                window_seconds=policy.window_seconds,
            )
            if not result.allowed:
                return result
        return LimitResult(True)

    def acquire(self, operation: str, context: LimitContext, *, lease_seconds: int = 120) -> tuple[LimitResult, OperationLease | None]:
        policy = POLICIES[operation]
        limits = (
            ("identity-concurrency", context.user_id, policy.concurrency_identity),
            ("tenant-concurrency", context.tenant_id, policy.concurrency_tenant),
        )
        token = str(uuid.uuid4())
        acquired: list[str] = []
        for scope, identifier, limit in limits:
            if limit <= 0:
                continue
            key = self._key(scope, identifier, operation)
            result = self.backend.acquire(key, limit=limit, lease_seconds=lease_seconds, token=token)
            if not result.allowed:
                OperationLease(self.backend, acquired, token).release()
                return result, None
            acquired.append(key)
        return LimitResult(True), OperationLease(self.backend, acquired, token)

    def reserve_external_ai(self, context: LimitContext, *, estimated_cost_microusd: int) -> LimitResult:
        settings = get_settings()
        daily_limit = int(settings.tenant_daily_ai_budget_usd * 1_000_000)
        return self.backend.consume(
            self._key("tenant-budget", context.tenant_id, "external-ai"),
            limit=daily_limit,
            window_seconds=86_400,
            cost=max(1, estimated_cost_microusd),
        )

    def allow_denial_audit(self, operation: str, context: LimitContext) -> bool:
        result = self.backend.consume(
            self._key("denial-audit", f"{context.tenant_id}:{context.user_id}", operation),
            limit=1,
            window_seconds=60,
        )
        return result.allowed


@lru_cache
def get_rate_limit_manager() -> RateLimitManager:
    settings = get_settings()
    if settings.rate_limit_backend == "redis":
        backend: LimitBackend = RedisLimitBackend(settings.redis_url)
    else:
        backend = InMemoryLimitBackend()
    return RateLimitManager(backend)


def reset_rate_limit_manager() -> None:
    get_rate_limit_manager.cache_clear()
