export interface ImageAuth {
  username: string;
  password: string;
}

export interface ImageSpec {
  uri: string;
  auth?: ImageAuth;
}

export type ResourceLimits = Record<string, string>;

export interface NetworkRule {
  action: string;
  target: string;
}

export interface NetworkPolicy {
  defaultAction?: string;
  egress?: NetworkRule[];
}

export interface PVC {
  claimName: string;
}

export interface HostPath {
  path: string;
}

export interface OSSFS {
  bucket: string;
  endpoint: string;
  version?: "1.0" | "2.0";
  options?: string[];
  accessKeyId?: string;
  accessKeySecret?: string;
}

export interface Volume {
  name: string;
  host?: HostPath;
  pvc?: PVC;
  ossfs?: OSSFS;
  mountPath: string;
  readOnly?: boolean;
  subPath?: string;
}

export interface SandboxStatus {
  state: string;
  reason?: string;
  message?: string;
  lastTransitionAt?: string;
}

export interface SandboxInfo {
  id: string;
  image: ImageSpec;
  status: SandboxStatus;
  metadata?: Record<string, string>;
  entrypoint: string[];
  expiresAt?: string;
  createdAt: string;
  lastActivityAt?: string;
}

export interface CreateSandboxParams {
  image: string | ImageSpec;
  entrypoint: string[];
  resourceLimits?: ResourceLimits;
  timeout?: number;
  env?: Record<string, string>;
  metadata?: Record<string, string>;
  volumes?: Volume[];
  networkPolicy?: NetworkPolicy;
}

export interface CreateSandboxResponse {
  id: string;
  status: SandboxStatus;
  metadata?: Record<string, string>;
  expiresAt?: string;
  createdAt: string;
  entrypoint: string[];
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNextPage: boolean;
}

export interface ListSandboxesResponse {
  items: SandboxInfo[];
  pagination: PaginationInfo;
}

export interface Task {
  id?: string;
  taskId?: string;
  status?: string;
  exitCode?: number;
  startedAt?: string;
  finishedAt?: string;
}

export interface TaskLogsResponse {
  logs: string;
  nextCursor?: number;
}

export interface SubmitTaskParams {
  command: string;
  envs?: Record<string, string>;
  timeout?: number;
}

export interface Endpoint {
  endpoint: string;
  headers?: Record<string, string>;
}

export interface UpdateEnvResponse {
  id: string;
  env: Record<string, string>;
}

export interface UpdateResourceLimitsResponse {
  id: string;
  status: SandboxStatus;
  resourceLimits: ResourceLimits;
}

export interface RenewExpirationResponse {
  expiresAt: string;
}

export interface ListParams {
  state?: string[];
  page?: number;
  pageSize?: number;
}
