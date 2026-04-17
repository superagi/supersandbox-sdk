"""Tests for the synchronous SuperSandbox client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from supersandbox import SuperSandbox
from supersandbox._sync import SyncSandbox
from supersandbox.exceptions import NotFoundError, SandboxNotRunningError

BASE_URL = "https://sandbox.example.com"
API_KEY = "test-api-key"

SANDBOX_PAYLOAD = {
    "id": "sb-sync-1",
    "image": {"uri": "python:3.11"},
    "status": {"state": "Running", "reason": None, "message": None, "lastTransitionAt": None},
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
    "lastActivityAt": None,
}

CREATE_RESPONSE = {
    "id": "sb-sync-1",
    "status": {"state": "Running", "reason": None, "message": None, "lastTransitionAt": None},
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
}

TASK_PAYLOAD = {
    "id": "task-sync-1",
    "status": "running",
    "exitCode": None,
    "startedAt": "2026-01-01T00:00:00Z",
    "finishedAt": None,
}


@pytest.fixture
def client():
    c = SuperSandbox(api_key=API_KEY, base_url=BASE_URL)
    yield c
    c.close()


def test_context_manager():
    with SuperSandbox(api_key=API_KEY, base_url=BASE_URL) as client:
        assert client is not None


def test_create_returns_sync_sandbox(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/sandboxes").mock(return_value=httpx.Response(202, json=CREATE_RESPONSE))
        sb = client.create(
            image="python:3.11",
            entrypoint=["sleep", "3600"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        assert isinstance(sb, SyncSandbox)
        assert sb.id == "sb-sync-1"
        assert sb.status.state == "Running"


def test_get_returns_sync_sandbox(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        sb = client.get("sb-sync-1")
        assert isinstance(sb, SyncSandbox)
        assert sb.image.uri == "python:3.11"


def test_list_returns_sync_sandboxes(client):
    payload = {
        "items": [SANDBOX_PAYLOAD],
        "pagination": {"page": 1, "pageSize": 20, "totalItems": 1, "totalPages": 1, "hasNextPage": False},
    }
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes").mock(return_value=httpx.Response(200, json=payload))
        sandboxes = client.list()
        assert len(sandboxes) == 1
        assert isinstance(sandboxes[0], SyncSandbox)


def test_sandbox_delete(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.delete("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(204))
        sb = client.get("sb-sync-1")
        sb.delete()


def test_sandbox_pause_resume(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/sb-sync-1/pause").mock(return_value=httpx.Response(202))
        mock.post("/sandboxes/sb-sync-1/resume").mock(return_value=httpx.Response(202))
        sb = client.get("sb-sync-1")
        sb.pause()
        sb.resume()


def test_sandbox_update_env(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.put("/sandboxes/sb-sync-1/env").mock(
            return_value=httpx.Response(200, json={"id": "sb-sync-1", "env": {"FOO": "bar"}})
        )
        sb = client.get("sb-sync-1")
        result = sb.update_env({"FOO": "bar"})
        assert result.env["FOO"] == "bar"


def test_sandbox_get_logs(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/sb-sync-1/logs").mock(
            return_value=httpx.Response(200, text="log line 1\nlog line 2\n")
        )
        sb = client.get("sb-sync-1")
        logs = sb.get_logs()
        assert "log line 1" in logs


def test_not_found_raises(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/missing").mock(
            return_value=httpx.Response(404, json={"code": "NOT_FOUND", "message": "not found"})
        )
        with pytest.raises(NotFoundError):
            client.get("missing")


def test_tasks_submit_and_get(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/sb-sync-1/tasks").mock(return_value=httpx.Response(201, json=TASK_PAYLOAD))
        mock.get("/sandboxes/sb-sync-1/tasks/task-sync-1").mock(return_value=httpx.Response(200, json=TASK_PAYLOAD))
        sb = client.get("sb-sync-1")
        task = sb.tasks.submit("ls /workspace")
        assert task.id == "task-sync-1"
        task2 = sb.tasks.get("task-sync-1")
        assert task2.status == "running"


def test_tasks_logs_cursor(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.get("/sandboxes/sb-sync-1/tasks/task-sync-1/logs").mock(
            return_value=httpx.Response(200, text="output\n", headers={"X-Task-Log-Cursor": "7"})
        )
        sb = client.get("sb-sync-1")
        result = sb.tasks.logs("task-sync-1")
        assert "output" in result.logs
        assert result.next_cursor == 7


def test_tasks_kill(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.delete("/sandboxes/sb-sync-1/tasks/task-sync-1").mock(return_value=httpx.Response(204))
        sb = client.get("sb-sync-1")
        sb.tasks.kill("task-sync-1")


def test_terminal_raises_when_not_running(client):
    paused = {**SANDBOX_PAYLOAD, "status": {**SANDBOX_PAYLOAD["status"], "state": "Paused"}}
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=paused))
        sb = client.get("sb-sync-1")
        with pytest.raises(SandboxNotRunningError, match="Paused"):
            with sb.terminal():
                pass


def test_terminal_send_receive(client):
    mock_ws = MagicMock()
    mock_ws.close = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(return_value="$ ")
    mock_connect = AsyncMock(return_value=mock_ws)

    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        mock.post("/sandboxes/sb-sync-1/terminal/token").mock(
            return_value=httpx.Response(200, json={"token": "tok-xyz"})
        )
        with patch("supersandbox.terminal.websockets.connect", mock_connect):
            with client.get("sb-sync-1").terminal() as term:
                term.send("echo hi\n")
                output = term.receive(timeout=1.0)

    assert output == "$ "
    mock_ws.send.assert_awaited_once_with("echo hi\n")


def test_sandbox_repr(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-sync-1").mock(return_value=httpx.Response(200, json=SANDBOX_PAYLOAD))
        sb = client.get("sb-sync-1")
        assert "sb-sync-1" in repr(sb)
        assert "Running" in repr(sb)
