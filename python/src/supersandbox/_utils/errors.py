"""Error interception decorator — converts unexpected exceptions to OpenSandboxError."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, TypeVar

from ..exceptions import OpenSandboxError

F = TypeVar("F", bound=Callable[..., Any])


def intercept_errors(func: F) -> F:
    """Wrap a method so unexpected exceptions are raised as OpenSandboxError.

    Exceptions that are already OpenSandboxError subclasses pass through unchanged.
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except OpenSandboxError:
                raise
            except Exception as exc:
                raise OpenSandboxError(str(exc)) from exc
        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except OpenSandboxError:
            raise
        except Exception as exc:
            raise OpenSandboxError(str(exc)) from exc
    return sync_wrapper  # type: ignore[return-value]
