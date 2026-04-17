export class APIError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly code: string,
    message: string,
  ) {
    super(`[${statusCode}] ${code}: ${message}`);
    this.name = "APIError";
  }
}

export class NotFoundError extends APIError {
  constructor(code: string, message: string) {
    super(404, code, message);
    this.name = "NotFoundError";
  }
}

export class UnauthorizedError extends APIError {
  constructor(code: string, message: string) {
    super(401, code, message);
    this.name = "UnauthorizedError";
  }
}

export class ConflictError extends APIError {
  constructor(code: string, message: string) {
    super(409, code, message);
    this.name = "ConflictError";
  }
}

export class SandboxNotRunningError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SandboxNotRunningError";
  }
}

export class TerminalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TerminalError";
  }
}

export function makeAPIError(status: number, code: string, message: string): APIError {
  switch (status) {
    case 404: return new NotFoundError(code, message);
    case 401: return new UnauthorizedError(code, message);
    case 409: return new ConflictError(code, message);
    default:  return new APIError(status, code, message);
  }
}
