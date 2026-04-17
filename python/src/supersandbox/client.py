"""Main SuperSandbox clients — async and sync."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._http import AsyncHTTPClient
from ._utils.errors import intercept_errors
from .config import SandboxConfig
from .models import (
    CreateSandboxResponse,
    ImageSpec,
    ListSandboxesResponse,
    NetworkPolicy,
    Sandbox as _SandboxData,
    Volume,
)
from .sandbox import Sandbox


class AsyncSuperSandbox:
    """Async client for the SuperSandbox API.

    Reads ``api_key`` and ``base_url`` from a :class:`SandboxConfig` object,
    or directly from constructor arguments, or from environment variables
    ``SUPERSANDBOX_API_KEY`` and ``SUPERSANDBOX_BASE_URL``.

    Usage::

        async with AsyncSuperSandbox(api_key="...") as client:
            sb = await client.create(
                image="python:3.11",
                entrypoint=["sleep", "3600"],
                resource_limits={"cpu": "500m", "memory": "512Mi"},
            )
            task = await sb.tasks.submit("echo hello")
            async with sb.terminal() as term:
                await term.send("ls /\\n")
                print(await term.receive())
            await sb.delete()
    """

    def __init__(
        self,
        *,
        config: Optional[SandboxConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        cfg = config or SandboxConfig()
        self._api_key = api_key or cfg.api_key
        self._base_url = (base_url or cfg.base_url).rstrip("/")
        self._timeout = timeout if timeout is not None else cfg.timeout
        self._http = AsyncHTTPClient(self._base_url, self._api_key, timeout=self._timeout)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_sandbox(self, data: Any) -> Sandbox:
        return Sandbox(data, self._http, self._base_url, self._api_key)

    # ── Sandbox lifecycle ─────────────────────────────────────────────────────

    @intercept_errors
    async def create(
        self,
        *,
        image: str | ImageSpec,
        entrypoint: List[str],
        resource_limits: Dict[str, str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None,
        network_policy: Optional[NetworkPolicy] = None,
        volumes: Optional[List[Volume]] = None,
        extensions: Optional[Dict[str, str]] = None,
        wait: bool = True,
    ) -> Sandbox:
        """Create and start a new sandbox.

        Args:
            image:           Docker image URI, or an :class:`ImageSpec` with auth.
            entrypoint:      Container entrypoint command.
            resource_limits: Resource limits dict, e.g. ``{"cpu": "500m", "memory": "512Mi"}``.
            timeout:         Sandbox TTL in seconds.
            env:             Environment variables to inject.
            metadata:        Arbitrary key-value labels.
            network_policy:  Egress network rules.
            volumes:         Storage mounts.
            extensions:      Runtime-specific extension options.
            wait:            If ``False``, return immediately without waiting for
                             the sandbox to reach ``Running`` state.

        Returns:
            A :class:`Sandbox` instance.
        """
        if isinstance(image, str):
            image = ImageSpec(uri=image)

        body: Dict[str, Any] = {
            "image": image.model_dump(exclude_none=True),
            "entrypoint": entrypoint,
            "resourceLimits": resource_limits,
        }
        if timeout is not None:
            body["timeout"] = timeout
        if env:
            body["env"] = env
        if metadata:
            body["metadata"] = metadata
        if network_policy:
            body["networkPolicy"] = network_policy.model_dump(exclude_none=True, by_alias=True)
        if volumes:
            body["volumes"] = [v.model_dump(exclude_none=True, by_alias=True) for v in volumes]
        if extensions:
            body["extensions"] = extensions

        params = None if wait else {"wait": "false"}
        data = await self._http.post("/sandboxes", json=body, params=params)
        return self._make_sandbox(CreateSandboxResponse.model_validate(data))

    @intercept_errors
    async def get(self, sandbox_id: str) -> Sandbox:
        """Fetch a sandbox by ID."""
        data = await self._http.get(f"/sandboxes/{sandbox_id}")
        return self._make_sandbox(_SandboxData.model_validate(data))

    @intercept_errors
    async def list(
        self,
        *,
        state: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Sandbox]:
        """List sandboxes, optionally filtered by state and metadata labels.

        Args:
            state:     Filter by one or more states, e.g. ``["Running", "Paused"]``.
            metadata:  Filter by metadata labels, e.g. ``{"team": "ml"}``.
            page:      Page number (1-based).
            page_size: Number of items per page.
        """
        params: Dict[str, Any] = {"page": page, "pageSize": page_size}
        if state:
            params["state"] = state
        if metadata:
            params["metadata"] = [f"{k}={v}" for k, v in metadata.items()]
        data = await self._http.get("/sandboxes", params=params)
        response = ListSandboxesResponse.model_validate(data)
        return [self._make_sandbox(item) for item in response.items]

    @intercept_errors
    async def delete(self, sandbox_id: str) -> None:
        """Delete a sandbox by ID (shortcut — you can also call ``sandbox.delete()``)."""
        await self._http.delete(f"/sandboxes/{sandbox_id}")

    # ── Connection management ──────────────────────────────────────────────────

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncSuperSandbox":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()


class SuperSandbox:
    """Synchronous client for the SuperSandbox API.

    Wraps :class:`AsyncSuperSandbox` on a dedicated background thread so it can
    be used in scripts and notebooks without an active event loop.

    Usage::

        with SuperSandbox(api_key="...") as client:
            sb = client.create(
                image="python:3.11",
                entrypoint=["sleep", "3600"],
                resource_limits={"cpu": "500m", "memory": "512Mi"},
            )
            task = sb.tasks.submit("echo hello")
            with sb.terminal() as term:
                term.send("ls /\\n")
                print(term.receive())
            sb.delete()
    """

    def __init__(
        self,
        *,
        config: Optional[SandboxConfig] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        from ._sync import _EventLoopThread, SyncSandbox

        self._runner = _EventLoopThread()
        self._async = AsyncSuperSandbox(
            config=config, api_key=api_key, base_url=base_url, timeout=timeout
        )
        self._SyncSandbox = SyncSandbox

    def _wrap(self, async_sandbox: Sandbox) -> Any:
        return self._SyncSandbox(async_sandbox, self._runner)

    def create(self, **kwargs: Any) -> Any:
        return self._wrap(self._runner.run(self._async.create(**kwargs)))

    def get(self, sandbox_id: str) -> Any:
        return self._wrap(self._runner.run(self._async.get(sandbox_id)))

    def list(self, **kwargs: Any) -> List[Any]:
        return [self._wrap(sb) for sb in self._runner.run(self._async.list(**kwargs))]

    def delete(self, sandbox_id: str) -> None:
        self._runner.run(self._async.delete(sandbox_id))

    def close(self) -> None:
        self._runner.run(self._async.aclose())
        self._runner.stop()

    def __enter__(self) -> "SuperSandbox":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
