"""Async httpx client for Australia's Federal Register of Legislation with cache.

legislation.gov.au is a keyless Angular (server-side rendered) site - the initial HTML
response already contains the real legislative text and search results, no separate API
needed. ``robots.txt`` allows crawling (only ``/assets/`` is disallowed) but asks for a
10-second crawl delay; this connector relies on aggressive caching (`cache.py`) to avoid
repeat hits rather than enforcing an in-process sleep, the same approach already used for
``sg-eli-mcp``'s robots.txt compliance.
"""

from __future__ import annotations

from urllib.parse import quote

import anyio
import httpx

from .cache import HttpCache

DEFAULT_BASE_URL = "https://www.legislation.gov.au"
DEFAULT_TIMEOUT = httpx.Timeout(40.0, connect=10.0)
USER_AGENT = "au-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/au-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3


class FrliClient:
    """Async client. Use as ``async with FrliClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        )

    async def __aenter__(self) -> FrliClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def _get_html(self, path: str, *, category: str) -> str:
        url = f"{self.base_url}{path}"
        cached = self._cache.get(url)
        if cached is not None and isinstance(cached, str):
            return cached
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await self._http.get(url)
                resp.raise_for_status()
                self._cache.set(url, resp.text, ttl=HttpCache.ttl_for(category))
                return resp.text
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def search_by_title(self, title: str, collection: str = "act") -> str:
        path = f"/search/title({quote(title)})/collection({quote(collection)})"
        return await self._get_html(path, category="search")

    async def get_text(self, act_id: str, version: str = "latest") -> str:
        path = f"/{quote(act_id)}/{quote(version)}/text"
        return await self._get_html(path, category="act")
