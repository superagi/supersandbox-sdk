import { HttpClient, type HttpClientOptions } from "./http.js";
import { SandboxHandle } from "./sandbox.js";
import type {
  CreateSandboxParams,
  CreateSandboxResponse,
  SandboxInfo,
  ListParams,
  ImageSpec,
} from "./models.js";

export class SuperSandbox {
  private readonly http: HttpClient;

  constructor(opts: HttpClientOptions | string) {
    if (typeof opts === "string") {
      this.http = new HttpClient({ apiKey: opts });
    } else {
      this.http = new HttpClient(opts);
    }
  }

  async create(params: CreateSandboxParams): Promise<SandboxHandle> {
    const image: ImageSpec =
      typeof params.image === "string" ? { uri: params.image } : params.image;

    const body = {
      image,
      entrypoint: params.entrypoint,
      resourceLimits: params.resourceLimits ?? {},
      ...(params.timeout !== undefined && { timeout: params.timeout }),
      ...(params.env && { env: params.env }),
      ...(params.metadata && { metadata: params.metadata }),
      ...(params.volumes && { volumes: params.volumes }),
      ...(params.networkPolicy && { networkPolicy: params.networkPolicy }),
    };

    const data = await this.http.post<CreateSandboxResponse>("/sandboxes", body);
    return new SandboxHandle(data, this.http);
  }

  async get(id: string): Promise<SandboxHandle> {
    const data = await this.http.get<SandboxInfo>(`/sandboxes/${id}`);
    return new SandboxHandle(data, this.http);
  }

  async list(params: ListParams = {}): Promise<SandboxInfo[]> {
    const qs: Record<string, string> = {};
    if (params.state?.length) qs["state"] = params.state.join(",");
    if (params.page !== undefined) qs["page"] = String(params.page);
    if (params.pageSize !== undefined) qs["pageSize"] = String(params.pageSize);

    const data = await this.http.get<{ items: SandboxInfo[] }>("/sandboxes", qs);
    return data.items;
  }

  async delete(id: string): Promise<void> {
    return this.http.delete(`/sandboxes/${id}`);
  }
}
