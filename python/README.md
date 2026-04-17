# SuperSandbox Python SDK

Python SDK for the [SuperSandbox](https://sandbox.superagii.com) API — provision and manage isolated sandbox environments programmatically.

- **Async-first** with `AsyncSuperSandbox`
- **Sync client** with `SuperSandbox` (no event loop required)
- Sub-resources on the `Sandbox` object — `sandbox.tasks`, `sandbox.terminal()`
- Fully typed, Pydantic v2 models, Python 3.10–3.13

## Installation

```bash
pip install supersandbox
```

## Quick start

### Async

```python
import asyncio
from supersandbox import AsyncSuperSandbox

async def main():
    async with AsyncSuperSandbox(api_key="your-api-key") as client:
        sb = await client.create(
            image="python:3.11",
            entrypoint=["sleep", "3600"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        print(sb)  # Sandbox(id='...', state='Running')

        task = await sb.tasks.submit("echo hello from sandbox")
        print(task.id, task.status)

        await sb.delete()

asyncio.run(main())
```

### Sync

```python
from supersandbox import SuperSandbox

with SuperSandbox(api_key="your-api-key") as client:
    sb = client.create(
        image="python:3.11",
        entrypoint=["sleep", "3600"],
        resource_limits={"cpu": "500m", "memory": "512Mi"},
    )
    task = sb.tasks.submit("echo hello")
    print(task.id, task.status)
    sb.delete()
```

## Configuration

```python
from supersandbox import AsyncSuperSandbox, SandboxConfig

# Option 1 — explicit kwargs
client = AsyncSuperSandbox(api_key="...", base_url="https://sandbox.superagii.com", timeout=60.0)

# Option 2 — config object
cfg = SandboxConfig(api_key="...", base_url="...", timeout=30.0)
client = AsyncSuperSandbox(config=cfg)

# Option 3 — environment variables (no code changes needed)
# export SUPERSANDBOX_API_KEY=...
# export SUPERSANDBOX_BASE_URL=...   (optional)
client = AsyncSuperSandbox()
```

---

## Client methods

| Method | Description |
|---|---|
| `client.create(...)` | Create a new sandbox → `Sandbox` |
| `client.get(id)` | Fetch a sandbox by ID → `Sandbox` |
| `client.list(...)` | List sandboxes → `list[Sandbox]` |
| `client.delete(id)` | Delete by ID (or call `sandbox.delete()`) |

---

## Sandbox

All lifecycle operations and sub-resources live directly on the `Sandbox` object.

### Create

```python
from supersandbox import ImageSpec, ImageAuth, NetworkPolicy, NetworkRule, Volume, PVC

sb = await client.create(
    image="python:3.11",                           # or ImageSpec(uri=..., auth=ImageAuth(...))
    entrypoint=["sleep", "3600"],
    resource_limits={"cpu": "500m", "memory": "512Mi", "storage": "10Gi"},
    env={"DEBUG": "1", "MY_VAR": "value"},
    metadata={"team": "ml", "env": "prod"},
    timeout=3600,                                  # sandbox TTL in seconds
    wait=True,                                     # wait for Running state (default)
    network_policy=NetworkPolicy(
        default_action="deny",
        egress=[NetworkRule(action="allow", target="0.0.0.0/0")],
    ),
    volumes=[Volume(name="data", pvc=PVC(claim_name="my-pvc"), mount_path="/data")],
)
```

**`wait=False`** returns as soon as the API accepts the request, without waiting for `Running` state.

### Lifecycle

```python
await sb.pause()
await sb.resume()
await sb.delete()

from datetime import datetime, timezone, timedelta
await sb.renew_expiration(datetime.now(timezone.utc) + timedelta(hours=2))
```

### Update

```python
# Replace all user-defined env vars (None removes a variable)
result = await sb.update_env({"FOO": "bar", "OLD_VAR": None})
print(result.env)

# Change resource limits on a running sandbox
await sb.update_resource_limits(cpu="1000m", memory="2Gi")
```

### Observability

```python
# Buffered logs (last N lines)
logs = await sb.get_logs(tail=200)

# Streaming logs (async generator)
async for line in sb.stream_logs(tail=50):
    print(line)

# Public endpoint for an in-sandbox service
ep = await sb.get_endpoint(port=8080)
ep = await sb.get_endpoint(port=8080, use_server_proxy=True)
print(ep.endpoint)
```

---

## Tasks

Run background shell commands on the sandbox via the `execd` sidecar.

```python
# Submit
task = await sb.tasks.submit(
    "python train.py",
    cwd="/workspace",
    timeout_ms=300_000,
    envs={"EPOCHS": "10"},
)

# Poll until done
import asyncio
while True:
    task = await sb.tasks.get(task.id)
    if task.status in ("completed", "failed"):
        break
    await asyncio.sleep(1)

# Stream logs with cursor-based pagination
cursor = None
while True:
    result = await sb.tasks.logs(task.id, cursor=cursor)
    if result.logs:
        print(result.logs, end="")
    if result.next_cursor is None:
        break
    cursor = result.next_cursor

# Kill
await sb.tasks.kill(task.id)
```

---

## Terminal

Opens an interactive WebSocket PTY. Raises `SandboxNotRunningError` if the sandbox isn't `Running`.

```python
async with sb.terminal() as term:
    await term.send("ls /workspace\n")
    print(await term.receive(timeout=2.0))

    # Stream all output until connection closes
    async for chunk in term.stream():
        print(chunk, end="", flush=True)
```

**Sync equivalent:**

```python
with sb.terminal() as term:
    term.send("ls /workspace\n")
    print(term.receive(timeout=2.0))
```

---

## Volumes

```python
from supersandbox import Volume, Host, PVC, OSSFS

# Kubernetes PVC
Volume(name="workspace", pvc=PVC(claim_name="my-pvc"), mount_path="/workspace")

# Host path
Volume(name="data", host=Host(path="/mnt/data"), mount_path="/data", read_only=True)

# Alibaba Cloud OSS
Volume(
    name="oss-data",
    ossfs=OSSFS(
        bucket="my-bucket",
        endpoint="oss-cn-hangzhou.aliyuncs.com",
        access_key_id="...",
        access_key_secret="...",
    ),
    mount_path="/data",
    sub_path="datasets/",
)
```

---

## Error handling

```python
from supersandbox import (
    OpenSandboxError,        # base — all SDK errors
    APIError,                # non-2xx HTTP (.status_code, .code, .message)
    NotFoundError,           # 404
    UnauthorizedError,       # 401
    ConflictError,           # 409
    SandboxNotRunningError,  # terminal/task on non-Running sandbox
    TerminalError,           # WebSocket failure
)

try:
    sb = await client.get("missing-id")
except NotFoundError as e:
    print(e.status_code, e.code, e.message)
except SandboxNotRunningError as e:
    print("Not ready:", e)
```

---

## Models reference

| Model | Key fields |
|---|---|
| `Sandbox` | `id`, `image`, `status`, `metadata`, `entrypoint`, `expires_at`, `created_at` |
| `SandboxStatus` | `state`, `reason`, `message`, `last_transition_at` |
| `Task` | `id`, `status`, `exit_code`, `started_at`, `finished_at` |
| `TaskLogsResponse` | `logs: str`, `next_cursor: Optional[int]` |
| `Endpoint` | `endpoint: str`, `headers: Optional[Dict[str, str]]` |
| `UpdateEnvResponse` | `id`, `env: Dict[str, str]` |
| `ImageSpec` | `uri`, `auth: Optional[ImageAuth]` |
| `NetworkPolicy` | `default_action`, `egress: List[NetworkRule]` |
| `Volume` | `name`, `host`, `pvc`, `ossfs`, `mount_path`, `read_only`, `sub_path` |
| `SandboxConfig` | `api_key`, `base_url`, `timeout` |

Sandbox `state` values: `Pending` · `Running` · `Pausing` · `Paused` · `Stopping` · `Terminated` · `Failed`

---

## Development

```bash
git clone git@github.com:superagi/supersandbox-sdk.git
cd supersandbox-sdk/python

pip install -e ".[dev]"
pytest tests/ -v
```
