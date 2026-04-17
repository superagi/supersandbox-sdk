"""Interactive terminal — open a PTY session and send commands."""

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

        async with sb.terminal() as term:
            commands = [
                "echo 'hello from terminal'\n",
                "ls /\n",
                "python3 --version\n",
            ]
            for cmd in commands:
                print(f">>> {cmd.strip()}")
                await term.send(cmd)
                await asyncio.sleep(0.3)
                output = await term.receive(timeout=2.0)
                if output:
                    print(output.strip())

        await sb.delete()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
