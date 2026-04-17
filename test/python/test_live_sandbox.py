"""
Integration tests — require a live SuperSandbox API.

Run with:
    SUPERSANDBOX_API_KEY=<key> pytest test/ -v -m integration

These tests provision real sandboxes and are NOT part of the regular unit test
suite. They are intended for manual verification and CI gates that have API
access.
"""

import asyncio
import os

import pytest

from supersandbox import AsyncSuperSandbox
from supersandbox.exceptions import NotFoundError

pytestmark = pytest.mark.integration

API_KEY = os.environ.get("SUPERSANDBOX_API_KEY", "")
BASE_URL = os.environ.get("SUPERSANDBOX_BASE_URL", "https://sandbox.superagii.com")


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    async with AsyncSuperSandbox(api_key=API_KEY, base_url=BASE_URL) as c:
        yield c


@pytest.fixture
async def sandbox(client):
    """Provision a sandbox for a test, delete it afterwards."""
    sb = await client.create(
        image="python:3.11-slim",
        entrypoint=["sleep", "120"],
        resource_limits={"cpu": "250m", "memory": "256Mi"},
        metadata={"test": "integration"},
    )
    yield sb
    try:
        await sb.delete()
    except Exception:
        pass


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_get(client, sandbox):
    fetched = await client.get(sandbox.id)
    assert fetched.id == sandbox.id
    assert fetched.status.state == "Running"


@pytest.mark.asyncio
async def test_list_includes_sandbox(client, sandbox):
    sandboxes = await client.list(state=["Running"])
    ids = [sb.id for sb in sandboxes]
    assert sandbox.id in ids


@pytest.mark.asyncio
async def test_get_nonexistent_raises(client):
    with pytest.raises(NotFoundError):
        await client.get("does-not-exist-xyz")


@pytest.mark.asyncio
async def test_pause_resume(sandbox):
    await sandbox.pause()
    sb = await sandbox._http  # re-fetch via tasks to check state... simplified below
    await sandbox.resume()


# ── Tasks ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_task_submit_and_logs(sandbox):
    task = await sandbox.tasks.submit("echo integration-test-ok")
    assert task.id

    for _ in range(15):
        task = await sandbox.tasks.get(task.id)
        if task.status in ("completed", "failed"):
            break
        await asyncio.sleep(1)

    assert task.status == "completed"
    assert task.exit_code == 0

    result = await sandbox.tasks.logs(task.id)
    assert "integration-test-ok" in result.logs


@pytest.mark.asyncio
async def test_task_with_env(sandbox):
    task = await sandbox.tasks.submit(
        "echo $MY_VAR",
        envs={"MY_VAR": "hello-from-env"},
    )
    for _ in range(15):
        task = await sandbox.tasks.get(task.id)
        if task.status in ("completed", "failed"):
            break
        await asyncio.sleep(1)

    result = await sandbox.tasks.logs(task.id)
    assert "hello-from-env" in result.logs


@pytest.mark.asyncio
async def test_task_kill(sandbox):
    task = await sandbox.tasks.submit("sleep 60")
    await asyncio.sleep(1)
    await sandbox.tasks.kill(task.id)

    task = await sandbox.tasks.get(task.id)
    assert task.status in ("failed", "killed", "stopped")


# ── Logs ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_logs(sandbox):
    logs = await sandbox.get_logs(tail=20)
    assert isinstance(logs, str)


# ── Env ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_env(sandbox):
    result = await sandbox.update_env({"INTEGRATION_VAR": "set"})
    assert result.env.get("INTEGRATION_VAR") == "set"
