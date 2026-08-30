from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.abuse.limiter import (
    InMemoryLimitBackend,
    LimitContext,
    LimiterUnavailableError,
    RateLimitManager,
    RedisLimitBackend,
)
from apps.api.app.core.config import Settings
from apps.api.app.main import app


TENANT_A = "00000000-0000-0000-0000-000000002801"
TENANT_B = "00000000-0000-0000-0000-000000002899"
USER_A = "00000000-0000-0000-0000-000000002701"
USER_B = "00000000-0000-0000-0000-000000002799"
ADMIN_USER = "00000000-0000-0000-0000-000000002706"
PROJECT_ID = "00000000-0000-0000-0000-000000000019"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def _context(tenant: str = TENANT_A, user: str = USER_A) -> LimitContext:
    return LimitContext(tenant_id=tenant, user_id=user, ip_risk_context=f"direct:{user}")


def test_memory_contract() -> None:
    clock = FakeClock()
    backend = InMemoryLimitBackend(clock=clock)
    first_instance = RateLimitManager(backend, prefix="phase58-memory")
    second_instance = RateLimitManager(backend, prefix="phase58-memory")
    context = _context()

    for _ in range(20):
        assert first_instance.enforce("chat", context).allowed
    denied = second_instance.enforce("chat", context)
    assert not denied.allowed and denied.retry_after_seconds == 60
    assert first_instance.enforce("chat", _context(TENANT_B, USER_B)).allowed

    clock.now += 61
    assert second_instance.enforce("chat", context).allowed

    stream_a, lease_a = first_instance.acquire("stream", context, lease_seconds=10)
    stream_b, lease_b = second_instance.acquire("stream", context, lease_seconds=10)
    stream_c, _ = first_instance.acquire("stream", context, lease_seconds=10)
    assert stream_a.allowed and stream_b.allowed and not stream_c.allowed
    assert lease_a and lease_b
    clock.now += 11
    stream_d, lease_d = second_instance.acquire("stream", context, lease_seconds=10)
    assert stream_d.allowed and lease_d
    lease_a.release()
    lease_b.release()
    lease_d.release()

    with patch("apps.api.app.abuse.limiter.get_settings", return_value=SimpleNamespace(tenant_daily_ai_budget_usd=0.0001)):
        budget_manager = RateLimitManager(InMemoryLimitBackend(clock=clock), prefix="phase58-budget")
        assert budget_manager.reserve_external_ai(context, estimated_cost_microusd=60).allowed
        assert not budget_manager.reserve_external_ai(context, estimated_cost_microusd=50).allowed
        assert budget_manager.reserve_external_ai(_context(TENANT_B, USER_B), estimated_cost_microusd=50).allowed


def test_api_denial_prevents_expensive_work() -> None:
    backend = InMemoryLimitBackend()
    manager = RateLimitManager(backend, prefix="phase58-api")
    context = LimitContext(tenant_id=TENANT_A, user_id=USER_A, ip_risk_context="direct:testclient")
    for _ in range(20):
        assert manager.enforce("chat", context).allowed

    client = TestClient(app)
    with patch("apps.api.app.main.get_rate_limit_manager", return_value=manager), patch(
        "apps.api.app.main.retrieve_chunks"
    ) as retrieval, patch("apps.api.app.main.generate_answer") as generation, patch(
        "apps.api.app.main.log_audit_event", return_value=True
    ) as audit:
        response = client.post("/query", json={"question": "What is the leave policy?"})
        repeated = client.post("/query", json={"question": "What is the leave policy?"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Request limit reached. Retry later."}
    assert response.headers["retry-after"].isdigit()
    assert "capacity" not in response.text.lower()
    assert repeated.status_code == 429
    assert audit.call_count == 1
    retrieval.assert_not_called()
    generation.assert_not_called()

    indexing_manager = RateLimitManager(InMemoryLimitBackend(), prefix="phase58-indexing-api")
    admin_context = LimitContext(tenant_id=TENANT_A, user_id=ADMIN_USER, ip_risk_context="direct:testclient")
    for _ in range(10):
        assert indexing_manager.enforce("indexing", admin_context).allowed
    with patch("apps.api.app.main.get_rate_limit_manager", return_value=indexing_manager), patch(
        "apps.api.app.main.approve_and_index_document"
    ) as indexing:
        indexing_response = client.post(
            f"/projects/{PROJECT_ID}/departments/{uuid.uuid4()}/documents/{uuid.uuid4()}/approve-index",
            headers={"X-Demo-User-Id": ADMIN_USER},
            json={},
        )
    assert indexing_response.status_code == 429
    indexing.assert_not_called()


def test_request_and_production_guards() -> None:
    client = TestClient(app)
    response = client.post(
        "/query",
        content=b"{}",
        headers={"Content-Type": "application/json", "Content-Length": "12000001"},
    )
    assert response.status_code == 413
    too_long = client.post("/query", json={"question": "x" * 4_001})
    assert too_long.status_code == 422

    try:
        Settings(
            _env_file=None,
            app_environment="production",
            auth_mode="oidc",
            database_url="postgresql://proofbase_app:secret@db/proofbase",
            rate_limit_backend="memory",
        )
    except ValueError as exc:
        assert "RATE_LIMIT_BACKEND" in str(exc)
    else:
        raise AssertionError("Production accepted a process-local limiter")


def test_auth_preflight_does_not_consume_auth_budget() -> None:
    manager = RateLimitManager(InMemoryLimitBackend(), prefix="phase58-auth-preflight")
    client = TestClient(app)
    with patch("apps.api.app.main.get_rate_limit_manager", return_value=manager):
        responses = [
            client.options(
                "/auth/me",
                headers={
                    "Origin": "http://localhost:3001",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "x-demo-user-id",
                },
            )
            for _ in range(25)
        ]

    assert all(response.status_code == 200 for response in responses)
    context = LimitContext(
        tenant_id="preauth:testclient",
        user_id="preauth:testclient",
        ip_risk_context="direct:testclient",
    )
    assert manager.enforce("auth", context).allowed


def test_redis_contract(redis_url: str) -> None:
    import redis

    prefix = f"phase58-redis-{uuid.uuid4()}"
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    client.ping()
    try:
        first = RateLimitManager(RedisLimitBackend(redis_url), prefix=prefix)
        second = RateLimitManager(RedisLimitBackend(redis_url), prefix=prefix)
        context = _context()
        for _ in range(20):
            assert first.enforce("chat", context).allowed
        assert not second.enforce("chat", context).allowed
        assert second.enforce("chat", _context(TENANT_B, USER_B)).allowed

        one, lease_one = first.acquire("stream", context)
        two, lease_two = second.acquire("stream", context)
        three, _ = first.acquire("stream", context)
        assert one.allowed and two.allowed and not three.allowed
        assert lease_one and lease_two
        lease_one.release()
        lease_two.release()

        keys = list(client.scan_iter(match=f"{prefix}:*"))
        assert keys
        joined = " ".join(keys)
        assert TENANT_A not in joined and USER_A not in joined
    finally:
        keys = list(client.scan_iter(match=f"{prefix}:*"))
        if keys:
            client.delete(*keys)

    try:
        RedisLimitBackend("redis://127.0.0.1:1/0").consume("unavailable", limit=1, window_seconds=1)
    except LimiterUnavailableError:
        pass
    else:
        raise AssertionError("Redis backend did not fail closed when the shared store was unavailable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-redis", action="store_true")
    parser.add_argument("--redis-url", default=os.getenv("RATE_LIMIT_TEST_REDIS_URL", "redis://localhost:6379/15"))
    args = parser.parse_args()

    test_memory_contract()
    test_api_denial_prevents_expensive_work()
    test_request_and_production_guards()
    test_auth_preflight_does_not_consume_auth_budget()
    if args.require_redis:
        test_redis_contract(args.redis_url)
    print(f"Phase 58 abuse-control tests passed (redis={'required' if args.require_redis else 'not requested'}).")


if __name__ == "__main__":
    main()
