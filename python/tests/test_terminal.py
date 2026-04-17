"""Tests for TerminalSession and Sandbox.terminal()."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
import httpx

from supersandbox import AsyncSuperSandbox
from supersandbox.exceptions import SandboxNotRunningError, TerminalError
from supersandbox.terminal import TerminalSession

BASE_URL = "https://sandbox.example.com"
API_KEY = "test-api-key"

RUNNING_SANDBOX = {
    "id": "sb-1",
    "image": {"uri": "python:3.11"},
    "status": {"state": "Running", "reason": None, "message": None, "lastTransitionAt": None},
    "metadata": None,
    "entrypoint": ["sleep", "3600"],
    "expiresAt": None,
    "createdAt": "2026-01-01T00:00:00Z",
    "lastActivityAt": None,
}

PAUSED_SANDBOX = {**RUNNING_SANDBOX, "status": {**RUNNING_SANDBOX["status"], "state": "Paused"}}
TOKEN_RESPONSE = {"token": "jwt-abc123"}


@pytest.fixture
def client():
    return AsyncSuperSandbox(api_key=API_KEY, base_url=BASE_URL)


@pytest.mark.asyncio
async def test_terminal_raises_when_not_running(client):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-1").mock(return_value=httpx.Response(200, json=PAUSED_SANDBOX))
        sb = await client.get("sb-1")
        with pytest.raises(SandboxNotRunningError, match="Paused"):
            async with sb.terminal():
                pass


@pytest.mark.asyncio
async def test_terminal_connects_with_jwt(client):
    mock_ws = MagicMock()
    mock_ws.close = AsyncMock()
    mock_connect = AsyncMock(return_value=mock_ws)

    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/sandboxes/sb-1").mock(return_value=httpx.Response(200, json=RUNNING_SANDBOX))
        mock.post("/sandboxes/sb-1/terminal/token").mock(
            return_value=httpx.Response(200, json=TOKEN_RESPONSE)
        )
        with patch("supersandbox.terminal.websockets.connect", mock_connect):
            async with (await client.get("sb-1")).terminal() as term:
                assert term._ws is mock_ws

    mock_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_terminal_send_and_receive():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value="hello from sandbox\r\n")

    session = TerminalSession("wss://example.com/terminal", API_KEY)
    session._ws = mock_ws

    await session.send("echo hello\n")
    mock_ws.send.assert_awaited_once_with("echo hello\n")

    output = await session.receive(timeout=1.0)
    assert output == "hello from sandbox\r\n"


@pytest.mark.asyncio
async def test_terminal_receive_timeout():
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(side_effect=asyncio.TimeoutError)

    session = TerminalSession("wss://example.com/terminal", API_KEY)
    session._ws = mock_ws

    result = await session.receive(timeout=0.001)
    assert result == ""


@pytest.mark.asyncio
async def test_terminal_send_raises_when_not_open():
    session = TerminalSession("wss://example.com/terminal", API_KEY)
    with pytest.raises(TerminalError, match="not open"):
        await session.send("hello")


@pytest.mark.asyncio
async def test_terminal_stream():
    messages = ["line1\n", "line2\n"]

    async def async_iter(items):
        for item in items:
            yield item

    mock_ws = MagicMock()
    mock_ws.__aiter__ = lambda self: async_iter(messages).__aiter__()

    session = TerminalSession("wss://example.com/terminal", API_KEY)
    session._ws = mock_ws

    received = []
    async for chunk in session.stream():
        received.append(chunk)

    assert received == messages


@pytest.mark.asyncio
async def test_terminal_connection_failure():
    session = TerminalSession("wss://bad-host/terminal", API_KEY)
    with patch(
        "supersandbox.terminal.websockets.connect",
        side_effect=OSError("connection refused"),
    ):
        with pytest.raises(TerminalError, match="Failed to connect"):
            async with session:
                pass
