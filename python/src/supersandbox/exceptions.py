"""OpenSandbox SDK exceptions."""


class OpenSandboxError(Exception):
    """Base exception for all SDK errors."""


class APIError(OpenSandboxError):
    """Raised when the API returns a non-2xx response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[{status_code}] {code}: {message}")


class NotFoundError(APIError):
    """404 — resource does not exist."""


class UnauthorizedError(APIError):
    """401 — missing or invalid API key."""


class ConflictError(APIError):
    """409 — operation conflicts with current state."""


class SandboxNotRunningError(OpenSandboxError):
    """Raised when a terminal/exec operation is attempted on a non-running sandbox."""


class TerminalError(OpenSandboxError):
    """Raised on WebSocket terminal connection failures."""
