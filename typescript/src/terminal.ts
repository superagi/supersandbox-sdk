import WebSocket from "ws";
import { TerminalError } from "./errors.js";

export interface TerminalOptions {
  cols?: number;
  rows?: number;
}

export class TerminalSession {
  private ws: WebSocket;

  constructor(ws: WebSocket) {
    this.ws = ws;
  }

  static connect(
    baseUrl: string,
    apiKey: string,
    sandboxId: string,
    opts: TerminalOptions = {},
  ): Promise<TerminalSession> {
    const wsUrl = baseUrl
      .replace(/^https:\/\//, "wss://")
      .replace(/^http:\/\//, "ws://");
    const cols = opts.cols ?? 80;
    const rows = opts.rows ?? 24;
    const url = `${wsUrl}/sandboxes/${sandboxId}/terminal?cols=${cols}&rows=${rows}`;

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url, { headers: { "OPEN-SANDBOX-API-KEY": apiKey } });
      ws.once("open", () => resolve(new TerminalSession(ws)));
      ws.once("error", (err) => reject(new TerminalError(err.message)));
    });
  }

  send(data: string): void {
    this.ws.send(data);
  }

  receive(): Promise<string> {
    return new Promise((resolve, reject) => {
      this.ws.once("message", (data) => resolve(data.toString()));
      this.ws.once("error", reject);
      this.ws.once("close", () => reject(new TerminalError("connection closed")));
    });
  }

  async *stream(): AsyncGenerator<string> {
    const queue: string[] = [];
    let done = false;
    let err: Error | null = null;
    let notify: (() => void) | null = null;

    const wake = () => { if (notify) { notify(); notify = null; } };

    this.ws.on("message", (data) => { queue.push(data.toString()); wake(); });
    this.ws.once("close", () => { done = true; wake(); });
    this.ws.once("error", (e) => { err = e; done = true; wake(); });

    while (true) {
      while (queue.length > 0) yield queue.shift()!;
      if (done) break;
      await new Promise<void>((res) => { notify = res; });
    }
    if (err) throw err;
  }

  close(): void {
    this.ws.close();
  }
}
