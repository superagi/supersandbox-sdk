"""WebSocket terminal session for a running sandbox."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional
from urllib.parse import urlparse

import websockets
from websockets.exceptions import ConnectionClosed

from .exceptions import TerminalError


class TerminalSession:
    """Interactive WebSocket PTY session.

    Obtain via ``async with sandbox.terminal() as term:``.

    Usage::

        async with sandbox.terminal() as term:
            await term.send("ls /workspace\\n")

            # Single chunk (returns "" on timeout)
            output = await term.receive(timeout=2.0)

            # Stream all output until connection closes
            async for chunk in term.stream():
                print(chunk, end="", flush=True)
    """

    def __init__(self, ws_url: str, api_key: str) -> None:
        self._ws_url = ws_url
        self._api_key = api_key
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    async def __aenter__(self) -> "TerminalSession":
        try:
            self._ws = await websockets.connect(
                self._ws_url,
                additional_headers={"Open-Sandbox-Api-Key": self._api_key},
                ping_interval=20,
                ping_timeout=10,
            )
        except Exception as exc:
            raise TerminalError(f"Failed to connect to terminal: {exc}") from exc
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def send(self, text: str) -> None:
        """Send keystrokes or a command to the terminal."""
        if not self._ws:
            raise TerminalError("Terminal session is not open.")
        await self._ws.send(text)

    async def receive(self, timeout: float = 5.0) -> str:
        """Receive a single chunk of terminal output.

        Returns an empty string if no output arrives within ``timeout`` seconds.
        """
        if not self._ws:
            raise TerminalError("Terminal session is not open.")
        try:
            return await asyncio.wait_for(self._ws.recv(), timeout=timeout)  # type: ignore[return-value]
        except asyncio.TimeoutError:
            return ""

    async def stream(self) -> AsyncIterator[str]:
        """Yield terminal output chunks until the connection closes."""
        if not self._ws:
            raise TerminalError("Terminal session is not open.")
        try:
            async for message in self._ws:
                yield message  # type: ignore[misc]
        except ConnectionClosed:
            return
