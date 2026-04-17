"""Run a background task and stream its logs with cursor-based pagination."""

import asyncio
import os
from supersandbox import AsyncSuperSandbox

API_KEY = os.environ["SUPERSANDBOX_API_KEY"]


async def main() -> None:
    async with AsyncSuperSandbox(api_key=API_KEY) as client:
        sb = await client.create(
            image="python:3.11-slim",
            entrypoint=["sleep", "300"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        print(f"Sandbox: {sb}")

        # Submit a long-running task
        task = await sb.tasks.submit(
            "for i in $(seq 1 5); do echo \"step $i\"; sleep 0.5; done",
            cwd="/workspace",
        )
        print(f"Task submitted: {task.id}")

        # Stream logs with cursor until task finishes
        cursor = None
        while True:
            task = await sb.tasks.get(task.id)
            result = await sb.tasks.logs(task.id, cursor=cursor)

            if result.logs:
                print(result.logs, end="", flush=True)

            cursor = result.next_cursor

            if task.status in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

        print(f"\nFinished — exit code: {task.exit_code}")
        await sb.delete()


if __name__ == "__main__":
    asyncio.run(main())
