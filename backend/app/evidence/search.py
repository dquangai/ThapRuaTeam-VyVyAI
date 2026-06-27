from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.evidence.source_scoring import score_source_credibility, score_source_relevance
from app.models import EvidenceItem

MAX_QUERY_COUNT = 3
MAX_NORMALIZED_RESULTS = 8
DEFAULT_TIMEOUT_SECONDS = 5.0


class EvidenceSearchMode(StrEnum):
    LIVE = "live"
    MOCK = "mock"
    DISABLED = "disabled"
    FAILED = "failed"


class EvidenceOperationStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    DISABLED = "disabled"


class RawSearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    url: str | None = None
    source_name: str | None = None
    published_at: str | None = None
    snippet: str | None = None


class EvidenceSearchStatus(BaseModel):
    provider: str
    mode: EvidenceSearchMode
    operation_status: EvidenceOperationStatus
    success: bool
    queries_attempted: int = Field(ge=0)
    results_returned: int = Field(ge=0)
    errors: list[str]


class EvidenceCollectionResult(BaseModel):
    evidence_status: EvidenceSearchStatus
    evidence: list[EvidenceItem]


class SearchProvider(Protocol):
    provider_name: str

    async def search(self, query: str, limit: int) -> list[RawSearchResult]: ...


class EvidenceSearchAdapter:
    def __init__(
        self,
        provider: SearchProvider | None,
        *,
        mode: EvidenceSearchMode,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_queries: int = MAX_QUERY_COUNT,
        max_results: int = MAX_NORMALIZED_RESULTS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.provider = provider
        self.mode = mode
        self.timeout_seconds = timeout_seconds
        self.max_queries = max_queries
        self.max_results = max_results
        self.clock = clock or _utc_now

    async def collect(self, queries: list[str]) -> EvidenceCollectionResult:
        selected_queries = _dedupe_queries(queries)[: self.max_queries]
        provider_name = self.provider.provider_name if self.provider is not None else "none"

        if self.mode is EvidenceSearchMode.DISABLED:
            return self._empty_result(
                provider=provider_name,
                status=EvidenceOperationStatus.DISABLED,
                errors=["Evidence search is disabled."],
                queries_attempted=0,
            )

        if self.mode is EvidenceSearchMode.FAILED:
            return self._empty_result(
                provider=provider_name,
                status=EvidenceOperationStatus.PARTIAL,
                errors=["Evidence search provider is in failed mode."],
                queries_attempted=0,
            )

        if self.provider is None:
            return self._empty_result(
                provider="none",
                status=EvidenceOperationStatus.PARTIAL,
                errors=["Evidence search provider is not configured."],
                queries_attempted=0,
            )

        evidence: list[EvidenceItem] = []
        seen_urls: set[str] = set()
        errors: list[str] = []
        queries_attempted = 0

        for query in selected_queries:
            if len(evidence) >= self.max_results:
                break
            queries_attempted += 1
            try:
                raw_results = await asyncio.wait_for(
                    self.provider.search(query=query, limit=self.max_results),
                    timeout=self.timeout_seconds,
                )
            except TimeoutError:
                errors.append(f"Search timeout for query: {query}")
                continue
            except Exception as exc:
                errors.append(f"Search failed for query '{query}': {exc.__class__.__name__}")
                continue

            for raw_result in raw_results:
                if len(evidence) >= self.max_results:
                    break
                normalized = normalize_search_result(
                    raw_result=raw_result,
                    query=query,
                    retrieved_at=self.clock(),
                )
                if normalized is None:
                    continue
                url_key = normalized.url.casefold()
                if url_key in seen_urls:
                    continue
                seen_urls.add(url_key)
                evidence.append(normalized)

        if (
            self.mode is EvidenceSearchMode.LIVE
            and queries_attempted > 0
            and not evidence
            and not errors
        ):
            errors.append("Search returned no normalized results.")

        operation_status = (
            EvidenceOperationStatus.COMPLETED if not errors else EvidenceOperationStatus.PARTIAL
        )
        return EvidenceCollectionResult(
            evidence_status=EvidenceSearchStatus(
                provider=provider_name,
                mode=self.mode,
                operation_status=operation_status,
                success=not errors,
                queries_attempted=queries_attempted,
                results_returned=len(evidence),
                errors=errors,
            ),
            evidence=evidence,
        )

    def _empty_result(
        self,
        provider: str,
        status: EvidenceOperationStatus,
        errors: list[str],
        queries_attempted: int,
    ) -> EvidenceCollectionResult:
        return EvidenceCollectionResult(
            evidence_status=EvidenceSearchStatus(
                provider=provider,
                mode=self.mode,
                operation_status=status,
                success=False,
                queries_attempted=queries_attempted,
                results_returned=0,
                errors=errors,
            ),
            evidence=[],
        )


class MockSearchProvider:
    provider_name = "mock"

    def __init__(self, fixtures: list[dict[str, object]]) -> None:
        self.fixtures = fixtures

    @classmethod
    def from_default_fixture(cls) -> MockSearchProvider:
        fixture_path = Path(__file__).with_name("mock_fixtures.json")
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        return cls(fixtures=fixtures)

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        normalized_query = _normalize_query(query)
        results: list[RawSearchResult] = []

        for fixture in self.fixtures:
            keywords = fixture.get("query_keywords", [])
            if not isinstance(keywords, list):
                continue
            if not _matches_keywords(normalized_query, keywords):
                continue

            raw_results = fixture.get("results", [])
            if not isinstance(raw_results, list):
                continue
            for raw_result in raw_results:
                if not isinstance(raw_result, dict):
                    continue
                results.append(RawSearchResult.model_validate(raw_result))
                if len(results) >= limit:
                    return results

        return results


class FailedSearchProvider:
    provider_name = "failed"

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        raise RuntimeError("configured provider failure")


def normalize_search_result(
    raw_result: RawSearchResult,
    query: str,
    retrieved_at: datetime,
) -> EvidenceItem | None:
    if not raw_result.title or not raw_result.url or not raw_result.source_name:
        return None
    if not raw_result.snippet:
        return None

    title = raw_result.title.strip()
    url = raw_result.url.strip()
    source_name = raw_result.source_name.strip()
    snippet = raw_result.snippet.strip()
    if not title or not url or not source_name or not snippet:
        return None

    return EvidenceItem(
        evidence_id=stable_evidence_id(title=title, url=url, source_name=source_name),
        title=title,
        url=url,
        source_name=source_name,
        published_at=raw_result.published_at,
        snippet=snippet,
        retrieved_at=retrieved_at.astimezone(UTC).isoformat(),
        credibility_score=score_source_credibility(source_name=source_name, url=url),
        relevance_score=score_source_relevance(
            query=query,
            title=title,
            snippet=snippet,
            url=url,
        ),
    )


def stable_evidence_id(title: str, url: str, source_name: str) -> str:
    seed = "|".join(
        [
            url.strip().casefold(),
            source_name.strip().casefold(),
            title.strip().casefold(),
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"ev_{digest}"


def _dedupe_queries(queries: list[str]) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for query in queries:
        cleaned = " ".join(query.strip().split())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        selected.append(cleaned)
    return selected


def _matches_keywords(normalized_query: str, keywords: list[object]) -> bool:
    return any(
        isinstance(keyword, str) and _normalize_query(keyword) in normalized_query
        for keyword in keywords
    )


def _normalize_query(query: str) -> str:
    return query.strip().casefold()


def _utc_now() -> datetime:
    return datetime.now(UTC)
