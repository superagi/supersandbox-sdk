import type { HttpClient } from "./http.js";
import type {
  SandboxStatus,
  ResourceLimits,
  Endpoint,
  UpdateEnvResponse,
  UpdateResourceLimitsResponse,
  RenewExpirationResponse,
} from "./models.js";
import { SandboxNotRunningError } from "./errors.js";
import { Tasks } from "./tasks.js";
import { TerminalSession, type TerminalOptions } from "./terminal.js";

export class SandboxHandle {
  readonly id: string;
  readonly status: SandboxStatus;
  readonly metadata?: Record<string, string>;
  readonly entrypoint: string[];
  readonly expiresAt?: string;
  readonly createdAt: string;
  readonly lastActivityAt?: string;

  private readonly http: HttpClient;

  constructor(data: {
    id: string;
    status: SandboxStatus;
    metadata?: Record<string, string>;
    entrypoint: string[];
    expiresAt?: string;
    createdAt: string;
    lastActivityAt?: string;
  }, http: HttpClient) {
    this.id = data.id;
    this.status = data.status;
    this.metadata = data.metadata;
    this.entrypoint = data.entrypoint;
    this.expiresAt = data.expiresAt;
    this.createdAt = data.createdAt;
    this.lastActivityAt = data.lastActivityAt;
    this.http = http;
  }

  get tasks(): Tasks {
    return new Tasks(this.id, this.http);
  }

  async delete(): Promise<void> {
    return this.http.delete(`/sandboxes/${this.id}`);
  }

  async pause(): Promise<void> {
    await this.http.post(`/sandboxes/${this.id}/pause`);
  }

  async resume(): Promise<void> {
    await this.http.post(`/sandboxes/${this.id}/resume`);
  }

  async renewExpiration(ttlSeconds: number): Promise<RenewExpirationResponse> {
    return this.http.put<RenewExpirationResponse>(
      `/sandboxes/${this.id}/expiration`,
      { timeout: ttlSeconds },
    );
  }

  async updateResourceLimits(limits: ResourceLimits): Promise<UpdateResourceLimitsResponse> {
    return this.http.put<UpdateResourceLimitsResponse>(
      `/sandboxes/${this.id}/resources`,
      { resourceLimits: limits },
    );
  }

  async updateEnv(env: Record<string, string>): Promise<UpdateEnvResponse> {
    return this.http.put<UpdateEnvResponse>(
      `/sandboxes/${this.id}/env`,
      { env },
    );
  }

  async getEndpoint(port: number, options: { public?: boolean } = {}): Promise<Endpoint> {
    const params: Record<string, string> = {};
    if (options.public) params["public"] = "true";
    return this.http.get<Endpoint>(`/sandboxes/${this.id}/endpoints/${port}`, params);
  }

  async getLogs(tail = 100): Promise<string> {
    return this.http.get<string>(`/sandboxes/${this.id}/logs`, {
      tail: String(tail),
      follow: "false",
    });
  }

  async *streamLogs(tail = 100): AsyncGenerator<string> {
    yield* this.http.stream(`/sandboxes/${this.id}/logs`, {
      tail: String(tail),
      follow: "true",
    });
  }

  async terminal(opts: TerminalOptions = {}): Promise<TerminalSession> {
    if (this.status.state !== "Running") {
      throw new SandboxNotRunningError(
        `Sandbox ${this.id} is not running (state: ${this.status.state})`,
      );
    }
    return TerminalSession.connect(this.http.baseUrl, this.http.apiKey, this.id, opts);
  }

  toString(): string {
    return `SandboxHandle(id=${this.id}, state=${this.status.state})`;
  }
}
