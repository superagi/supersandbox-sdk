import { makeAPIError } from "./errors.js";

const DEFAULT_BASE_URL = "https://sandbox.superagii.com";

export interface HttpClientOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export class HttpClient {
  readonly baseUrl: string;
  readonly apiKey: string;
  private readonly timeout: number;

  constructor(opts: HttpClientOptions) {
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.timeout = opts.timeout ?? 60_000;
  }

  private headers(extra?: Record<string, string>): Record<string, string> {
    return {
      "OPEN-SANDBOX-API-KEY": this.apiKey,
      "Content-Type": "application/json",
      ...extra,
    };
  }

  async request<T = unknown>(
    method: string,
    path: string,
    options: { body?: unknown; params?: Record<string, string> } = {},
  ): Promise<T> {
    const { body: data, returned } = await this.requestWithHeaders<T>(method, path, options);
    void returned;
    return data;
  }

  async requestWithHeaders<T = unknown>(
    method: string,
    path: string,
    options: { body?: unknown; params?: Record<string, string> } = {},
  ): Promise<{ body: T; returned: Headers }> {
    let url = this.baseUrl + path;
    if (options.params) {
      const qs = new URLSearchParams(options.params).toString();
      if (qs) url += "?" + qs;
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.timeout);

    let resp: Response;
    try {
      resp = await fetch(url, {
        method,
        headers: this.headers(),
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: ctrl.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if (!resp.ok) {
      let code = "unknown";
      let message = `HTTP ${resp.status}`;
      try {
        const err = await resp.json() as { code?: string; message?: string };
        if (err.code) code = err.code;
        if (err.message) message = err.message;
      } catch { /* ignore */ }
      throw makeAPIError(resp.status, code, message);
    }

    if (resp.status === 204) return { body: undefined as T, returned: resp.headers };

    const ct = resp.headers.get("content-type") ?? "";
    let body: T;
    if (ct.includes("json")) {
      body = await resp.json() as T;
    } else {
      body = await resp.text() as unknown as T;
    }
    return { body, returned: resp.headers };
  }

  async get<T = unknown>(path: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>("GET", path, { params });
  }

  async getWithHeaders<T = unknown>(
    path: string,
    params?: Record<string, string>,
  ): Promise<{ body: T; returned: Headers }> {
    return this.requestWithHeaders<T>("GET", path, { params });
  }

  async post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, { body });
  }

  async put<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("PUT", path, { body });
  }

  async patch<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("PATCH", path, { body });
  }

  async delete(path: string): Promise<void> {
    await this.request("DELETE", path);
  }

  async *stream(path: string, params?: Record<string, string>): AsyncGenerator<string> {
    let url = this.baseUrl + path;
    if (params) {
      const qs = new URLSearchParams(params).toString();
      if (qs) url += "?" + qs;
    }
    const resp = await fetch(url, {
      headers: this.headers(),
    });
    if (!resp.ok || !resp.body) {
      throw makeAPIError(resp.status, "stream_error", `HTTP ${resp.status}`);
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        if (line) yield line;
      }
    }
    if (buf) yield buf;
  }
}
