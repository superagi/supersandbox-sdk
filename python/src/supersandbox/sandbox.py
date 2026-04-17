"""Sandbox — high-level wrapper around a running sandbox instance."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union

from ._http import AsyncHTTPClient
from ._utils.errors import intercept_errors
from .exceptions import SandboxNotRunningError
from .models import (
    CreateSandboxResponse,
    Endpoint,
    ImageSpec,
    RenewExpirationResponse,
    Sandbox as _SandboxData,
    SandboxStatus,
    UpdateEnvResponse,
    UpdateResourceLimitsResponse,
)
from .tasks import Tasks
from .terminal import TerminalSession

# Union of the two shapes returned by the API (create vs. get/list)
_AnyData = Union[_SandboxData, CreateSandboxResponse]


class Sandbox:
    """A running sandbox instance.

    Returned by :meth:`AsyncSuperSandbox.create`, :meth:`AsyncSuperSandbox.get`,
    and :meth:`AsyncSuperSandbox.list`.

    Sub-resources are accessed as properties::

        task = await sandbox.tasks.submit("echo hello")
        async with sandbox.terminal() as term:
            await term.send("ls /\\n")
    """

    def __init__(
        self,
        data: _AnyData,
        http: AsyncHTTPClient,
        base_url: str,
        api_key: str,
    ) -> None:
        self.id: str = data.id
        self.image: Optional[ImageSpec] = getattr(data, "image", None)
        self.status: SandboxStatus = data.status
        self.metadata: Optional[Dict[str, str]] = data.metadata
        self.entrypoint: List[str] = data.entrypoint
        self.expires_at: Optional[datetime] = data.expires_at
        self.created_at: datetime = data.created_at
        self.last_activity_at: Optional[datetime] = getattr(data, "last_activity_at", None)

        self._http = http
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    # ── Sub-resources ─────────────────────────────────────────────────────────

    @property
    def tasks(self) -> Tasks:
        """Background task execution on this sandbox."""
        return Tasks(self._http, self.id)

    @asynccontextmanager
    @intercept_errors
    async def terminal(self) -> AsyncIterator[TerminalSession]:
        """Open an interactive WebSocket terminal session.

        Raises:
            SandboxNotRunningError: If the sandbox is not in ``Running`` state.

        Usage::

            async with sandbox.terminal() as term:
                await term.send("echo hello\\n")
                print(await term.receive())
        """
        if self.status.state != "Running":
            raise SandboxNotRunningError(
                f"Sandbox {self.id!r} is not running (state={self.status.state!r})"
            )
        token_data = await self._http.post(f"/sandboxes/{self.id}/terminal/token")
        ws_url = token_data.get("url") or (
            self._base_url.replace("https://", "wss://").replace("http://", "ws://")
            + f"/sandboxes/{self.id}/terminal?token={token_data['token']}"
        )
        session = TerminalSession(ws_url, self._api_key)
        async with session as term:
            yield term

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @intercept_errors
    async def delete(self) -> None:
        """Terminate and delete this sandbox."""
        await self._http.delete(f"/sandboxes/{self.id}")

    @intercept_errors
    async def pause(self) -> None:
        """Pause the sandbox (scales to zero, /workspace is preserved)."""
        await self._http.post(f"/sandboxes/{self.id}/pause")

    @intercept_errors
    async def resume(self) -> None:
        """Resume a paused sandbox."""
        await self._http.post(f"/sandboxes/{self.id}/resume")

    @intercept_errors
    async def renew_expiration(self, expires_at: datetime) -> RenewExpirationResponse:
        """Extend the sandbox TTL to ``expires_at``."""
        data = await self._http.post(
            f"/sandboxes/{self.id}/renew-expiration",
            json={"expiresAt": expires_at.isoformat()},
        )
        return RenewExpirationResponse.model_validate(data)

    @intercept_errors
    async def update_resource_limits(
        self,
        *,
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
    ) -> UpdateResourceLimitsResponse:
        """Update CPU / memory / storage limits while the sandbox is running."""
        limits: Dict[str, str] = {}
        if cpu:
            limits["cpu"] = cpu
        if memory:
            limits["memory"] = memory
        if storage:
            limits["storage"] = storage
        data = await self._http.patch(
            f"/sandboxes/{self.id}", json={"resourceLimits": limits}
        )
        return UpdateResourceLimitsResponse.model_validate(data)

    @intercept_errors
    async def update_env(self, env: Dict[str, Optional[str]]) -> UpdateEnvResponse:
        """Replace all user-defined environment variables.

        Pass ``None`` as a value to delete a variable.
        Internal variables (e.g. ``EXECD_TOKEN``) are preserved automatically.
        """
        data = await self._http.put(f"/sandboxes/{self.id}/env", json={"env": env})
        return UpdateEnvResponse.model_validate(data)

    # ── Observability ─────────────────────────────────────────────────────────

    @intercept_errors
    async def get_endpoint(
        self, port: int, *, use_server_proxy: bool = False
    ) -> Endpoint:
        """Get the public endpoint for a port exposed by the sandbox.

        Args:
            port:             Port number inside the sandbox.
            use_server_proxy: Route through the server-side HTTP proxy.
        """
        params: Dict[str, Any] = {}
        if use_server_proxy:
            params["use_server_proxy"] = "true"
        data = await self._http.get(
            f"/sandboxes/{self.id}/endpoints/{port}", params=params or None
        )
        return Endpoint.model_validate(data)

    @intercept_errors
    async def get_logs(self, *, tail: int = 100) -> str:
        """Return the last ``tail`` lines of container logs as a string."""
        params: Dict[str, Any] = {"tail": tail, "follow": False}
        return await self._http.get(f"/sandboxes/{self.id}/logs", params=params)

    async def stream_logs(self, *, tail: int = 100) -> AsyncIterator[str]:
        """Async generator that streams container log lines in real time."""
        params: Dict[str, Any] = {"tail": tail, "follow": True}
        async for line in self._http.stream_get(f"/sandboxes/{self.id}/logs", params=params):
            yield line

    def __repr__(self) -> str:
        return f"Sandbox(id={self.id!r}, state={self.status.state!r})"
