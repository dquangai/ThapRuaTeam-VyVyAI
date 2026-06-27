from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import MissingConfigurationError, Settings
from app.evidence import RawSearchResult
from app.services.provider_errors import ProviderAuthenticationError, ProviderInvocationError


class TavilySearchProvider:
    provider_name = "tavily"

    def __init__(self, *, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        api_key = self.settings.tavily_api_key
        if api_key is None:
            raise MissingConfigurationError(
                "TAVILY_API_KEY is required for live web search.",
                variable_name="TAVILY_API_KEY",
            )

        close_client = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self.settings.provider_timeout_float())
            close_client = True

        try:
            try:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key.get_secret_value(),
                        "query": query,
                        "max_results": limit,
                        "search_depth": "basic",
                        "include_answer": False,
                        "include_raw_content": False,
                    },
                )
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise TimeoutError("Tavily search timed out.") from exc
            except httpx.HTTPStatusError as exc:
                raise _safe_http_error(exc) from exc
            payload = response.json()
            return [_raw_result_from_tavily(item) for item in _result_items(payload)]
        finally:
            if close_client:
                await client.aclose()


def _result_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    results = payload.get("results", [])
    return [item for item in results if isinstance(item, dict)]


def _raw_result_from_tavily(item: dict[str, Any]) -> RawSearchResult:
    url = _optional_text(item.get("url"))
    return RawSearchResult(
        title=_optional_text(item.get("title")),
        url=url,
        source_name=_optional_text(item.get("source_name") or item.get("source"))
        or _source_name_from_url(url),
        published_at=_optional_text(item.get("published_date") or item.get("published_at")),
        snippet=_optional_text(item.get("content") or item.get("snippet")),
    )


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _source_name_from_url(url: str | None) -> str | None:
    if url is None:
        return None
    host = urlparse(url).netloc.strip().casefold()
    if not host:
        return None
    return host.removeprefix("www.")


def _safe_http_error(exc: httpx.HTTPStatusError) -> ProviderInvocationError:
    status_code = exc.response.status_code
    if status_code in {401, 403}:
        return ProviderAuthenticationError(
            f"Tavily authentication failed with HTTP {status_code}.",
            provider_name="tavily",
            error_type=f"http_{status_code}",
        )
    return ProviderInvocationError(
        f"Tavily search failed with HTTP {status_code}.",
        provider_name="tavily",
        error_type=f"http_{status_code}",
    )
