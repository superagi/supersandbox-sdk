# Integration Tests

These tests run against a **live SuperSandbox API** and provision real sandboxes.
They are separate from the unit tests in each SDK's own `tests/` folder.

## Requirements

- A valid `SUPERSANDBOX_API_KEY`
- Network access to `https://sandbox.superagii.com`
- SDK installed: `pip install -e python/`

## Run

```bash
export SUPERSANDBOX_API_KEY=your-api-key

# All integration tests
pytest test/ -v -m integration

# Python only
pytest test/python/ -v -m integration
```

## Structure

```
test/
├── python/
│   └── test_live_sandbox.py   # Lifecycle, tasks, logs, env
└── README.md
```

> Unit tests live in each SDK package (`python/tests/`, `go/tests/`, etc.)
> and run without any API key via mocks.
