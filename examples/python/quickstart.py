"""Quickstart — create a sandbox, run a command, delete it."""

import asyncio
import os
from supersandbox import AsyncSuperSandbox

API_KEY = os.environ["SUPERSANDBOX_API_KEY"]


async def main() -> None:
    async with AsyncSuperSandbox(api_key=API_KEY) as client:
        print("Creating sandbox...")
        sb = await client.create(
            image="python:3.11-slim",
            entrypoint=["sleep", "300"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
            metadata={"example": "quickstart"},
        )
        print(f"  {sb}")

        print("Running task...")
        task = await sb.tasks.submit("python3 -c \"print('hello from sandbox')\"")
        print(f"  task id={task.id} status={task.status}")

        # Poll until done
        import asyncio as _a
        for _ in range(10):
            task = await sb.tasks.get(task.id)
            if task.status in ("completed", "failed"):
                break
            await _a.sleep(1)

        result = await sb.tasks.logs(task.id)
        print(f"  output: {result.logs.strip()!r}")
        print(f"  exit code: {task.exit_code}")

        print("Fetching logs...")
        logs = await sb.get_logs(tail=10)
        print(f"  {logs.strip()!r}")

        print("Deleting sandbox...")
        await sb.delete()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
