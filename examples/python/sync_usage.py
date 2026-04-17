"""Synchronous client — no asyncio required."""

import os
from supersandbox import SuperSandbox

API_KEY = os.environ["SUPERSANDBOX_API_KEY"]


def main() -> None:
    with SuperSandbox(api_key=API_KEY) as client:
        print("Creating sandbox (sync)...")
        sb = client.create(
            image="python:3.11-slim",
            entrypoint=["sleep", "300"],
            resource_limits={"cpu": "500m", "memory": "512Mi"},
        )
        print(f"  {sb}")

        task = sb.tasks.submit("echo 'sync task works'")
        print(f"  task: {task.id}")

        import time
        for _ in range(10):
            task = sb.tasks.get(task.id)
            if task.status in ("completed", "failed"):
                break
            time.sleep(1)

        result = sb.tasks.logs(task.id)
        print(f"  output: {result.logs.strip()!r}")

        sb.delete()
        print("Done.")


if __name__ == "__main__":
    main()
