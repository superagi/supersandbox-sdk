"""Tests for Tasks sub-resource."""

from __future__ import annotations

import json
import pytest
import respx
import httpx
from supersandbox import AsyncSuperSandbox

BASE_URL = "https://sandbox.example.com"
API_KEY = "test-api-key"

SANDBOX_PAYLOAD = {
    "id": "abc-123",
    "image": {"uri": "python:3.11"},
    "status": {"state": "Running", "reason": None, "message": None, "lastTransitionAt": None},
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
    "lastActivityAt": None,
}

TASK_PAYLOAD = {
    "id": "task-xyz",
    "status": "running",
    "exitCode": None,
    "startedAt": "2026-01-01T00:00:00Z",
    "finishedAt": None,
}


@pytest.fixture
def client():
    return AsyncSuperSandbox(api_key=API_KEY, base_url=BASE_URL)


@pytest.mark.asyncio
async def test_submit_returns_task(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/abc-123/tasks").mock(return_value=httpx.Response(201, json=TASK_PAYLOAD))
        sb = await client.get("abc-123")
        task = await sb.tasks.submit("ls /workspace")
        assert task.id == "task-xyz"
        assert task.status == "running"


@pytest.mark.asyncio
async def test_submit_with_options(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        route = mock.post("/sandboxes/abc-123/tasks").mock(return_value=httpx.Response(201, json=TASK_PAYLOAD))
        sb = await client.get("abc-123")
        await sb.tasks.submit("python script.py", cwd="/app", timeout_ms=30000, envs={"DEBUG": "1"})
        payload = json.loads(route.calls[0].request.content)
        assert payload["cwd"] == "/app"
        assert payload["timeout"] == 30000
        assert payload["envs"] == {"DEBUG": "1"}


@pytest.mark.asyncio
async def test_get_task(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/abc-123/tasks/task-xyz").mock(return_value=httpx.Response(200, json=TASK_PAYLOAD))
        sb = await client.get("abc-123")
        task = await sb.tasks.get("task-xyz")
        assert task.id == "task-xyz"
        assert task.status == "running"


@pytest.mark.asyncio
async def test_kill_task(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.delete("/sandboxes/abc-123/tasks/task-xyz").mock(return_value=httpx.Response(204))
        sb = await client.get("abc-123")
        await sb.tasks.kill("task-xyz")


@pytest.mark.asyncio
async def test_task_logs_with_cursor(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/abc-123/tasks/task-xyz/logs").mock(
            return_value=httpx.Response(
                200, text="stdout line 1\n", headers={"X-Task-Log-Cursor": "42"}
            )
        )
        sb = await client.get("abc-123")
        result = await sb.tasks.logs("task-xyz")
        assert "stdout line 1" in result.logs
        assert result.next_cursor == 42


@pytest.mark.asyncio
async def test_task_logs_no_cursor(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/abc-123").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/abc-123/tasks/task-xyz/logs").mock(
            return_value=httpx.Response(200, text="done\n")
        )
        sb = await client.get("abc-123")
        result = await sb.tasks.logs("task-xyz")
        assert result.next_cursor is None
