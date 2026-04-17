import type { HttpClient } from "./http.js";
import type { Task, TaskLogsResponse, SubmitTaskParams } from "./models.js";

export class Tasks {
  constructor(
    private readonly sandboxId: string,
    private readonly http: HttpClient,
  ) {}

  private base(): string {
    return `/sandboxes/${this.sandboxId}/tasks`;
  }

  async submit(
    command: string,
    opts: Omit<SubmitTaskParams, "command"> = {},
  ): Promise<Task> {
    return this.http.post<Task>(this.base(), { command, ...opts });
  }

  async get(taskId: string): Promise<Task> {
    return this.http.get<Task>(`${this.base()}/${taskId}`);
  }

  async logs(taskId: string, cursor?: number): Promise<TaskLogsResponse> {
    const params: Record<string, string> = {};
    if (cursor !== undefined) params["cursor"] = String(cursor);

    const { body, returned } = await this.http.getWithHeaders<string>(
      `${this.base()}/${taskId}/logs`,
      params,
    );

    const rawCursor = returned.get("x-task-log-cursor");
    return {
      logs: body,
      nextCursor: rawCursor !== null ? Number(rawCursor) : undefined,
    };
  }

  async kill(taskId: string): Promise<void> {
    return this.http.delete(`${this.base()}/${taskId}`);
  }
}
