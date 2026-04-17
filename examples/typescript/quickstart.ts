/**
 * Quickstart example for the SuperSandbox TypeScript SDK.
 *
 * Run:
 *   cd examples/typescript
 *   npm install
 *   SUPERSANDBOX_API_KEY=<key> npx tsx quickstart.ts
 */

import { SuperSandbox } from "supersandbox";

async function sleep(ms: number): Promise<void> {
  return new Promise((res) => setTimeout(res, ms));
}

async function main(): Promise<void> {
  const apiKey = process.env["SUPERSANDBOX_API_KEY"];
  if (!apiKey) {
    console.error("SUPERSANDBOX_API_KEY is not set");
    process.exit(1);
  }

  const client = new SuperSandbox({ apiKey });

  // ── Create ──────────────────────────────────────────────────────────────────
  console.log("Creating sandbox...");
  const sb = await client.create({
    image: "python:3.11-slim",
    entrypoint: ["sleep", "120"],
    resourceLimits: { cpu: "250m", memory: "256Mi" },
    metadata: { example: "quickstart" },
  });
  console.log(" ", sb.toString());

  try {
    // ── Run a task ─────────────────────────────────────────────────────────────
    console.log("Running task...");
    let task = await sb.tasks.submit(`python3 -c "print('hello from sandbox')"`);
    const taskId = task.taskId ?? task.id ?? "";
    console.log(`  task id=${taskId}`);

    for (let i = 0; i < 30; i++) {
      await sleep(1000);
      task = await sb.tasks.get(taskId);
      if (task.status === "completed" || task.status === "failed") break;
    }
    console.log(`  status=${task.status} exit_code=${task.exitCode ?? "n/a"}`);

    const result = await sb.tasks.logs(taskId);
    console.log(`  output: ${JSON.stringify(result.logs)}`);

    // ── Container logs ──────────────────────────────────────────────────────────
    console.log("Fetching container logs...");
    const logs = await sb.getLogs(20);
    console.log(" ", JSON.stringify(logs.slice(0, 120)));
  } finally {
    console.log("Deleting sandbox...");
    await sb.delete();
    console.log("  Done.");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
