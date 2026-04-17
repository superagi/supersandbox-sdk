# SuperSandbox SDK Documentation

SDK documentation for the SuperSandbox API — provision and manage isolated sandbox environments.

## SDKs

| Language | Status | Install |
|---|---|---|
| [Python](python/README.md) | ✅ Stable | `pip install supersandbox` |
| Go | 🚧 In progress | — |
| TypeScript | 🚧 Planned | — |

## API Reference

Base URL: `https://sandbox.superagii.com`

Auth header: `Open-Sandbox-Api-Key: <your-api-key>`

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/sandboxes` | Create sandbox |
| `GET` | `/sandboxes` | List sandboxes |
| `GET` | `/sandboxes/{id}` | Get sandbox |
| `DELETE` | `/sandboxes/{id}` | Delete sandbox |
| `PATCH` | `/sandboxes/{id}` | Update resource limits |
| `PUT` | `/sandboxes/{id}/env` | Replace env vars |
| `POST` | `/sandboxes/{id}/pause` | Pause sandbox |
| `POST` | `/sandboxes/{id}/resume` | Resume sandbox |
| `POST` | `/sandboxes/{id}/renew-expiration` | Extend TTL |
| `GET` | `/sandboxes/{id}/endpoints/{port}` | Get public endpoint |
| `GET` | `/sandboxes/{id}/logs` | Get container logs |
| `POST` | `/sandboxes/{id}/terminal/token` | Get terminal JWT |
| `WS` | `/sandboxes/{id}/terminal` | Interactive terminal |
| `POST` | `/sandboxes/{id}/tasks` | Submit task |
| `GET` | `/sandboxes/{id}/tasks/{task_id}` | Get task |
| `GET` | `/sandboxes/{id}/tasks/{task_id}/logs` | Get task logs |
| `DELETE` | `/sandboxes/{id}/tasks/{task_id}` | Kill task |
| `GET` | `/health` | Health check |

## Quick links

- [Python SDK README](../python/README.md)
- [Examples](../examples/)
- [Integration tests](../test/)
