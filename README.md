# SuperSandbox SDK

Multi-language SDK for the [SuperSandbox](https://sandbox.superagii.com) API — provision and manage isolated sandbox environments programmatically.

## SDKs

| Language | Status | Docs |
|---|---|---|
| [Python](python/) | ✅ Stable | [README](python/README.md) |
| [Go](go/) | 🚧 In progress | [README](go/README.md) |
| TypeScript | 🚧 Planned | — |

## Quick start (Python)

```bash
pip install supersandbox
```

```python
from supersandbox import AsyncSuperSandbox
import asyncio

async def main():
    async with AsyncSuperSandbox(api_key="your-api-key") as client:
        sb = await client.create(
            image="python:3.11-slim",
            entrypoint=["sleep", "300"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        task = await sb.tasks.submit("echo hello")
        print(task.id, task.status)
        await sb.delete()

asyncio.run(main())
```

## Repo structure

```
supersandbox-sdk/
├── python/          # Python SDK (stable)
├── go/              # Go SDK (in progress)
├── typescript/      # TypeScript SDK (planned)
├── examples/        # Runnable usage examples
│   └── python/
├── test/            # Integration tests (require live API)
│   └── python/
├── docs/            # API reference & SDK docs
├── .devcontainer/   # VS Code dev container
└── .github/
    └── workflows/   # CI pipelines
```

## Development

```bash
git clone git@github.com:superagi/supersandbox-sdk.git
cd supersandbox-sdk

# Python
pip install -e "python[dev]"
pytest python/tests/ -v

# Integration tests (needs API key)
export SUPERSANDBOX_API_KEY=your-key
pytest test/python/ -v -m integration
```

## License

MIT