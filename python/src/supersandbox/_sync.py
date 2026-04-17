"""Synchronous wrappers — SyncSandbox, SyncTasks, SyncTerminalSession."""

from __future__ import annotations

import asyncio
import contextlib
import threading
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from .models import (
    Endpoint,
    RenewExpirationResponse,
    Task,
    TaskLogsResponse,
    UpdateEnvResponse,
    UpdateResourceLimitsResponse,
)
from .terminal import TerminalSession


class _EventLoopThread:
    """Persistent background thread that owns a single asyncio event loop."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()


class SyncTerminalSession:
    """Synchronous terminal session, obtained via ``SyncSandbox.terminal()``."""

    def __init__(self, session: TerminalSession, runner: _EventLoopThread) -> None:
        self._s = session
        self._r = runner

    def send(self, text: str) -> None:
        """Send keystrokes or a command to the terminal."""
        self._r.run(self._s.send(text))

    def receive(self, timeout: float = 5.0) -> str:
        """Receive one chunk of terminal output (empty string on timeout)."""
        return self._r.run(self._s.receive(timeout))


class SyncTasks:
    """Synchronous task execution, obtained via ``SyncSandbox.tasks``."""

    def __init__(self, async_tasks: Any, runner: _EventLoopThread) -> None:
        self._a = async_tasks
        self._r = runner

    def submit(self, command: str, **kwargs: Any) -> Task:
        return self._r.run(self._a.submit(command, **kwargs))

    def get(self, task_id: str) -> Task:
        return self._r.run(self._a.get(task_id))

    def logs(self, task_id: str, **kwargs: Any) -> TaskLogsResponse:
        return self._r.run(self._a.logs(task_id, **kwargs))

    def kill(self, task_id: str) -> None:
        self._r.run(self._a.kill(task_id))


class SyncSandbox:
    """Synchronous sandbox wrapper, returned by :class:`SuperSandbox` methods."""

    def __init__(self, async_sandbox: Any, runner: _EventLoopThread) -> None:
        self._s = async_sandbox
        self._r = runner
        # Mirror data fields from the async sandbox
        self.id: str = async_sandbox.id
        self.image = async_sandbox.image
        self.status = async_sandbox.status
        self.metadata = async_sandbox.metadata
        self.entrypoint = async_sandbox.entrypoint
        self.expires_at = async_sandbox.expires_at
        self.created_at = async_sandbox.created_at
        self.last_activity_at = async_sandbox.last_activity_at

    # ── Sub-resources ─────────────────────────────────────────────────────────

    @property
    def tasks(self) -> SyncTasks:
        return SyncTasks(self._s.tasks, self._r)

    @contextlib.contextmanager
    def terminal(self) -> Iterator[SyncTerminalSession]:
        """Open a synchronous terminal session.

        Raises SandboxNotRunningError if the sandbox is not Running.
        """
        from .exceptions import SandboxNotRunningError

        if self.status.state != "Running":
            raise SandboxNotRunningError(
                f"Sandbox {self.id!r} is not running (state={self.status.state!r})"
            )
        token_data = self._r.run(
            self._s._http.post(f"/sandboxes/{self.id}/terminal/token")
        )
        ws_url = token_data.get("url") or (
            self._s._base_url.replace("https://", "wss://").replace("http://", "ws://")
            + f"/sandboxes/{self.id}/terminal?token={token_data['token']}"
        )
        session = TerminalSession(ws_url, self._s._api_key)
        self._r.run(session.__aenter__())
        try:
            yield SyncTerminalSession(session, self._r)
        finally:
            self._r.run(session.__aexit__(None, None, None))

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def delete(self) -> None:
        self._r.run(self._s.delete())

    def pause(self) -> None:
        self._r.run(self._s.pause())

    def resume(self) -> None:
        self._r.run(self._s.resume())

    def renew_expiration(self, expires_at: datetime) -> RenewExpirationResponse:
        return self._r.run(self._s.renew_expiration(expires_at))

    def update_resource_limits(self, **kwargs: Any) -> UpdateResourceLimitsResponse:
        return self._r.run(self._s.update_resource_limits(**kwargs))

    def update_env(self, env: Dict[str, Optional[str]]) -> UpdateEnvResponse:
        return self._r.run(self._s.update_env(env))

    def get_endpoint(self, port: int, **kwargs: Any) -> Endpoint:
        return self._r.run(self._s.get_endpoint(port, **kwargs))

    def get_logs(self, **kwargs: Any) -> str:
        return self._r.run(self._s.get_logs(**kwargs))

    def __repr__(self) -> str:
        return f"SyncSandbox(id={self.id!r}, state={self.status.state!r})"
