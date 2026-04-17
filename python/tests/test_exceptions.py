"""Tests for exception hierarchy."""

import pytest

from supersandbox.exceptions import (
    APIError,
    ConflictError,
    NotFoundError,
    OpenSandboxError,
    SandboxNotRunningError,
    TerminalError,
    UnauthorizedError,
)


def test_api_error_is_opensandbox_error():
    err = APIError(500, "internal", "boom")
    assert isinstance(err, OpenSandboxError)


def test_not_found_is_api_error():
    err = NotFoundError(404, "not_found", "missing")
    assert isinstance(err, APIError)
    assert err.status_code == 404
    assert err.code == "not_found"
    assert err.message == "missing"


def test_unauthorized_is_api_error():
    err = UnauthorizedError(401, "unauthorized", "bad key")
    assert isinstance(err, APIError)
    assert err.status_code == 401


def test_conflict_is_api_error():
    err = ConflictError(409, "conflict", "already exists")
    assert isinstance(err, APIError)
    assert err.status_code == 409


def test_sandbox_not_running_is_opensandbox_error():
    err = SandboxNotRunningError("not running")
    assert isinstance(err, OpenSandboxError)
    assert not isinstance(err, APIError)


def test_terminal_error_is_opensandbox_error():
    err = TerminalError("ws failed")
    assert isinstance(err, OpenSandboxError)


def test_api_error_str_format():
    err = APIError(503, "unavailable", "service down")
    assert "503" in str(err)
    assert "unavailable" in str(err)
    assert "service down" in str(err)
