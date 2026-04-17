"""Low-level async HTTP transport for the SuperSandbox API."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional, Tuple

import httpx

from .exceptions import APIError, ConflictError, NotFoundError, UnauthorizedError


def _raise_for(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    try:
        body = resp.json()
        code = body.get("code", "unknown")
        message = body.get("message", resp.text)
    except Exception:
        code = "unknown"
        message = resp.text

    status = resp.status_code
    if status == 404:
        raise NotFoundError(status, code, message)
    if status == 401:
        raise UnauthorizedError(status, code, message)
    if status == 409:
        raise ConflictError(status, code, message)
    raise APIError(status, code, message)


class AsyncHTTPClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={
                "OPEN-SANDBOX-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        resp = await self._client.request(method, path, json=json, params=params)
        _raise_for(resp)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    async def request_with_headers(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Dict[str, str]]:
        resp = await self._client.request(method, path, json=json, params=params)
        _raise_for(resp)
        body = resp.json() if resp.content else None
        return body, dict(resp.headers)

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(
        self, path: str, *, json: Optional[Any] = None, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        return await self.request("POST", path, json=json, params=params)

    async def put(
        self, path: str, *, json: Optional[Any] = None, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        return await self.request("PUT", path, json=json, params=params)

    async def patch(
        self, path: str, *, json: Optional[Any] = None, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        return await self.request("PATCH", path, json=json, params=params)

    async def delete(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("DELETE", path, params=params)

    async def stream_get(
        self, path: str, *, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        async with self._client.stream("GET", path, params=params) as resp:
            _raise_for(resp)
            async for line in resp.aiter_lines():
                if line:
                    yield line

    async def aclose(self) -> None:
        await self._client.aclose()
