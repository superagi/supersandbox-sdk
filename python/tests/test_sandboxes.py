"""Tests for AsyncSuperSandbox and the Sandbox wrapper."""

from __future__ import annotations

import pytest
import respx
import httpx
from supersandbox import AsyncSuperSandbox, Sandbox
from supersandbox.exceptions import NotFoundError, UnauthorizedError, ConflictError

BASE_URL = "https://sandbox.example.com"
API_KEY = "test-api-key"


@pytest.fixture
def client():
    return AsyncSuperSandbox(api_key=API_KEY, base_url=BASE_URL)


# ── Payloads ──────────────────────────────────────────────────────────────────

SANDBOX_PAYLOAD = {
    "id": "abc-123",
    "image": {"uri": "python:3.11"},
    "status": {
        "state": "Running",
        "reason": "DependenciesReady",
        "message": "Pod is Ready",
        "lastTransitionAt": "2026-01-01T00:00:00Z",
    },
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
    "lastActivityAt": None,
}

CREATE_RESPONSE = {
    "id": "abc-123",
    "status": {
        "state": "Running",
        "reason": "DependenciesReady",
        "message": "Pod is Ready",
        "lastTransitionAt": "2026-01-01T00:00:00Z",
    },
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
}

# ── Client-level methods ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_returns_sandbox(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/sandboxes").mock(return_value=httpx.Response(202, json=CREATE_RESPONSE))
        sb = await client.create(
            image="python:3.11",
            entrypoint=["sleep", "3600"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        assert isinstance(sb, Sandbox)
        assert sb.id == "abc-123"
        assert sb.status.state == "Running"


@pytest.mark.asyncio
async def test_create_wait_false(client):
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/sandboxes").mock(return_value=httpx.Response(202, json=CREATE_RESPONSE))
        await client.create(
            image="python:3.11",
            entrypoint=["sleep", "3600"],
            resource_limits={"cpu": "500m"},
            wait=False,
        )
        assert "wait=false" in str(route.calls[0].request.url)


@pytest.mark.asyncio
async def test_get_returns_sandbox(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        sb = await client.get("abc-123")
        assert isinstance(sb, Sandbox)
        assert sb.id == "abc-123"
        assert sb.image.uri == "python:3.11"


@pytest.mark.asyncio
async def test_list_returns_sandbox_list(client):
    payload = {
        "items": [SANDBOX_PAYLOAD],
        "pagination": {
            "page": 1, "pageSize": 20, "totalItems": 1,
            "totalPages": 1, "hasNextPage": False,
        },
    }
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes").mock(return_value=httpx.Response(200, json=payload))
        sandboxes = await client.list()
        assert len(sandboxes) == 1
        assert isinstance(sandboxes[0], Sandbox)
        assert sandboxes[0].id == "abc-123"


@pytest.mark.asyncio
async def test_list_with_metadata_filter(client):
    payload = {
        "items": [],
        "pagination": {"page": 1, "pageSize": 20, "totalItems": 0, "totalPages": 0, "hasNextPage": False},
    }
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/sandboxes").mock(return_value=httpx.Response(200, json=payload))
        await client.list(metadata={"team": "ml"})
        assert "metadata=" in str(route.calls[0].request.url)


@pytest.mark.asyncio
async def test_client_delete(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.delete("/sandboxes/abc-123").mock(return_value=httpx.Response(204))
        await client.delete("abc-123")


# ── Sandbox instance methods ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sandbox_delete(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/sandboxes").mock(return_value=httpx.Response(202, json=CREATE_RESPONSE))
        mock.delete("/sandboxes/abc-123").mock(return_value=httpx.Response(204))
        sb = await client.create(image="python:3.11", entrypoint=["sleep", "3600"], resource_limits={})
        await sb.delete()


@pytest.mark.asyncio
async def test_sandbox_pause_resume(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/abc-123/pause").mock(return_value=httpx.Response(202))
        mock.post("/sandboxes/abc-123/resume").mock(return_value=httpx.Response(202))
        sb = await client.get("abc-123")
        await sb.pause()
        await sb.resume()


@pytest.mark.asyncio
async def test_sandbox_get_logs(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/abc-123/logs").mock(return_value=httpx.Response(200, text="log line 1\nlog line 2\n"))
        sb = await client.get("abc-123")
        logs = await sb.get_logs()
        assert "log line 1" in logs


@pytest.mark.asyncio
async def test_sandbox_update_env(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.put("/sandboxes/abc-123/env").mock(
            return_value=httpx.Response(200, json={"id": "abc-123", "env": {"FOO": "bar"}})
        )
        sb = await client.get("abc-123")
        result = await sb.update_env({"FOO": "bar"})
        assert result.env["FOO"] == "bar"


@pytest.mark.asyncio
async def test_sandbox_update_resource_limits(client):
    payload = {
        "id": "abc-123",
        "status": {"state": "Running", "reason": None, "message": None, "lastTransitionAt": None},
        "resourceLimits": {"cpu": "1000m", "memory": "1Gi"},
    }
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.patch("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=payload))
        sb = await client.get("abc-123")
        result = await sb.update_resource_limits(cpu="1000m", memory="1Gi")
        assert result.resource_limits["cpu"] == "1000m"


@pytest.mark.asyncio
async def test_sandbox_get_endpoint(client):
    payload = {"endpoint": "https://proxy.example.com/abc-123/3000", "headers": None}
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/abc-123/endpoints/3000").mock(return_value=httpx.Response(200, json=payload))
        sb = await client.get("abc-123")
        ep = await sb.get_endpoint(3000)
        assert "3000" in ep.endpoint


@pytest.mark.asyncio
async def test_sandbox_get_endpoint_with_proxy(client):
    payload = {"endpoint": "https://proxy.example.com/abc-123/3000", "headers": None}
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        route = mock.get("/sandboxes/abc-123/endpoints/3000").mock(return_value=httpx.Response(200, json=payload))
        sb = await client.get("abc-123")
        await sb.get_endpoint(3000, use_server_proxy=True)
        assert "use_server_proxy=true" in str(route.calls[0].request.url)


@pytest.mark.asyncio
async def test_sandbox_renew_expiration(client):
    from datetime import datetime, timezone
    exp = datetime(2026, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/abc-123/renew-expiration").mock(
            return_value=httpx.Response(200, json={"expiresAt": "2026-12-31T00:00:00+00:00"})
        )
        sb = await client.get("abc-123")
        result = await sb.renew_expiration(exp)
        assert result.expires_at.year == 2026


# ── Error handling ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_not_found_raises(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/missing").mock(
            return_value=httpx.Response(404, json={"code": "NOT_FOUND", "message": "not found"})
        )
        with pytest.raises(NotFoundError) as exc_info:
            await client.get("missing")
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_raises(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/sandboxes").mock(
            return_value=httpx.Response(401, json={"code": "MISSING_API_KEY", "message": "bad key"})
        )
        with pytest.raises(UnauthorizedError):
            await client.create(image="python:3.11", entrypoint=[], resource_limits={})


@pytest.mark.asyncio
async def test_context_manager():
    with respx.mock(base_url=BASE_URL):
        async with AsyncSuperSandbox(api_key=API_KEY, base_url=BASE_URL) as client:
            assert client is not None


@pytest.mark.asyncio
async def test_sandbox_repr(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        sb = await client.get("abc-123")
        assert "abc-123" in repr(sb)
        assert "Running" in repr(sb)
