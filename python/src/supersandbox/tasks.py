"""Task execution sub-resource for a running sandbox."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ._http import AsyncHTTPClient
from ._utils.errors import intercept_errors
from .models import Task, TaskLogsResponse


class Tasks:
    """Run and manage background shell commands on a sandbox via the execd sidecar.

    Obtain an instance via ``sandbox.tasks``.

    Usage::

        task = await sandbox.tasks.submit("python train.py", cwd="/workspace")

        # Poll until done
        while True:
            task = await sandbox.tasks.get(task.id)
            if task.status in ("completed", "failed"):
                break

        # Stream logs with cursor-based pagination
        cursor = None
        while True:
            result = await sandbox.tasks.logs(task.id, cursor=cursor)
            print(result.logs, end="")
            if result.next_cursor is None:
                break
            cursor = result.next_cursor
    """

    def __init__(self, http: AsyncHTTPClient, sandbox_id: str) -> None:
        self._http = http
        self._sandbox_id = sandbox_id
        self._base = f"/sandboxes/{sandbox_id}/tasks"

    @intercept_errors
    async def submit(
        self,
        command: str,
        *,
        cwd: str = "/workspace",
        timeout_ms: Optional[int] = None,
        envs: Optional[Dict[str, str]] = None,
    ) -> Task:
        """Submit a background shell command.

        Args:
            command:    Shell command to run.
            cwd:        Working directory inside the sandbox (default: /workspace).
            timeout_ms: Kill the task after this many milliseconds.
            envs:       Additional environment variables for this task.

        Returns:
            Task object with ``id`` and initial ``status``.
        """
        body: Dict[str, Any] = {"command": command, "cwd": cwd}
        if timeout_ms is not None:
            body["timeout"] = timeout_ms
        if envs:
            body["envs"] = envs
        data = await self._http.post(self._base, json=body)
        return Task.model_validate(data)

    @intercept_errors
    async def get(self, task_id: str) -> Task:
        """Get the current status of a task."""
        data = await self._http.get(f"{self._base}/{task_id}")
        return Task.model_validate(data)

    @intercept_errors
    async def logs(self, task_id: str, *, cursor: Optional[int] = None) -> TaskLogsResponse:
        """Fetch task stdout/stderr logs.

        Args:
            task_id: Task identifier.
            cursor:  Pagination cursor from a previous call's ``next_cursor``.
                     Pass ``None`` to start from the beginning.

        Returns:
            TaskLogsResponse with ``logs`` text and ``next_cursor`` for the next page.
            ``next_cursor`` is ``None`` when the task has finished and all logs are read.
        """
        params: Dict[str, Any] = {}
        if cursor is not None:
            params["cursor"] = cursor
        body, headers = await self._http.request_with_headers(
            "GET", f"{self._base}/{task_id}/logs", params=params or None
        )
        raw_cursor = headers.get("x-task-log-cursor")
        next_cursor = int(raw_cursor) if raw_cursor is not None else None
        return TaskLogsResponse(logs=body or "", next_cursor=next_cursor)

    @intercept_errors
    async def kill(self, task_id: str) -> None:
        """Kill a running task."""
        await self._http.delete(f"{self._base}/{task_id}")
