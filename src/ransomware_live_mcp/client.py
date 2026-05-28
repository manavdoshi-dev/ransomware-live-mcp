"""HTTP client for the ransomware.live v2 API.

The public v2 API is rate-limited to roughly one request per minute per
endpoint. We add a small in-process TTL cache so repeated tool calls from the
same Claude session don't immediately trip the limit, and we surface clean
errors when we do.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

BASE_URL = "https://api.ransomware.live"
DEFAULT_TIMEOUT = 30.0
DEFAULT_TTL = 60.0  # seconds — matches upstream rate-limit window
USER_AGENT = "ransomware-live-mcp/0.1 (+https://github.com/)"


class RansomwareLiveError(RuntimeError):
    """Raised when the upstream API returns an error or unparseable body."""


class _TTLCache:
    def __init__(self, ttl: float = DEFAULT_TTL) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)


class RansomwareLiveClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        cache_ttl: float = DEFAULT_TTL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )
        self._cache = _TTLCache(ttl=cache_ttl)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "RansomwareLiveClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    async def get(self, path: str) -> Any:
        path = "/" + path.lstrip("/")
        cached = await self._cache.get(path)
        if cached is not None:
            return cached

        url = f"{self._base_url}{path}"
        try:
            resp = await self._client.get(url)
        except httpx.HTTPError as exc:
            raise RansomwareLiveError(f"network error calling {path}: {exc}") from exc

        # Upstream returns 200 with {"message": "1 per 1 minute"} on rate-limit.
        if resp.status_code == 429:
            raise RansomwareLiveError(f"rate limited on {path} (HTTP 429)")
        if resp.status_code >= 400:
            raise RansomwareLiveError(
                f"{path} returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise RansomwareLiveError(
                f"{path} returned non-JSON body: {resp.text[:200]}"
            ) from exc

        if isinstance(data, dict) and set(data.keys()) == {"message"} and "minute" in str(data["message"]):
            raise RansomwareLiveError(
                f"rate limited on {path}: {data['message']} — retry shortly"
            )

        await self._cache.set(path, data)
        return data
