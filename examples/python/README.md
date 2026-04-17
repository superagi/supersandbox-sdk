# Python Examples

Set your API key first:

```bash
export SUPERSANDBOX_API_KEY=your-api-key
```

Install the SDK:

```bash
pip install -e ../../python
```

| Script | What it shows |
|---|---|
| `quickstart.py` | Create → run task → get logs → delete |
| `run_task.py` | Task submission with cursor-based log streaming |
| `terminal.py` | Interactive WebSocket PTY session |
| `sync_usage.py` | Synchronous `SuperSandbox` client (no asyncio) |

Run any example:

```bash
python quickstart.py
```
