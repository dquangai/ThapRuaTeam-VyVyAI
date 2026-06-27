from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.evidence import EvidenceSearchAdapter, EvidenceSearchMode  # noqa: E402
from app.services.model_router import ModelRole, get_model_for_role  # noqa: E402
from app.services.openai_provider import OpenAIProvider  # noqa: E402
from app.services.provider_errors import ProviderError  # noqa: E402
from app.services.tavily_provider import TavilySearchProvider  # noqa: E402
from app.services.virustotal_provider import VirusTotalProvider  # noqa: E402


class SmokeStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=240)


async def main() -> int:
    settings = get_settings()
    if not settings.run_live_provider_tests:
        print("live_provider_smoke skipped: RUN_LIVE_PROVIDER_TESTS is not true")
        return 0

    for role in ModelRole:
        await _smoke_openai(settings, role)

    if settings.enable_web_search:
        await _smoke_tavily(settings)
    else:
        print("provider=tavily enabled=false status=skipped")

    if settings.enable_virustotal:
        await _smoke_virustotal(settings)
    else:
        print("provider=virustotal enabled=false status=skipped")

    return 0


async def _smoke_openai(settings, role: ModelRole) -> None:
    model_name = _safe_model_name(settings, role)
    provider = OpenAIProvider(settings=settings, model_role=role)
    started = perf_counter()
    try:
        await provider.structured(
            "Return a short harmless Vietnamese summary for provider smoke testing.",
            SmokeStructuredOutput,
        )
        _print_result(
            provider="openai",
            role=role.value,
            model=model_name,
            ok=True,
            latency_ms=_elapsed_ms(started),
        )
    except Exception as exc:
        _print_result(
            provider="openai",
            role=role.value,
            model=model_name,
            ok=False,
            latency_ms=_elapsed_ms(started),
            error_type=_safe_error_type(exc),
        )


async def _smoke_tavily(settings) -> None:
    adapter = EvidenceSearchAdapter(
        provider=TavilySearchProvider(settings=settings),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=settings.provider_timeout_float(),
        max_queries=1,
        max_results=1,
    )
    started = perf_counter()
    try:
        result = await adapter.collect(["Vietnam online scam warning OTP"])
        _print_result(
            provider="tavily",
            role="search",
            model=None,
            ok=result.evidence_status.success,
            latency_ms=_elapsed_ms(started),
            result_count=result.evidence_status.results_returned,
            error_type=";".join(result.evidence_status.errors) or None,
        )
    except Exception as exc:
        _print_result(
            provider="tavily",
            role="search",
            model=None,
            ok=False,
            latency_ms=_elapsed_ms(started),
            error_type=_safe_error_type(exc),
        )


async def _smoke_virustotal(settings) -> None:
    domain = "example.com"
    provider = VirusTotalProvider(settings=settings)
    started = perf_counter()
    try:
        result = await provider.lookup(domain, "domain")
        _print_result(
            provider="virustotal",
            role="domain",
            model=None,
            ok=True,
            latency_ms=_elapsed_ms(started),
            result_count=0 if result is None else 1,
        )
    except Exception as exc:
        _print_result(
            provider="virustotal",
            role="domain",
            model=None,
            ok=False,
            latency_ms=_elapsed_ms(started),
            error_type=_safe_error_type(exc),
        )


def _safe_model_name(settings, role: ModelRole) -> str:
    try:
        return get_model_for_role(role, settings)
    except Exception:
        return "unconfigured"


def _print_result(
    *,
    provider: str,
    role: str,
    model: str | None,
    ok: bool,
    latency_ms: int,
    result_count: int | None = None,
    error_type: str | None = None,
) -> None:
    parts = [
        f"provider={provider}",
        f"role={role}",
        f"model={model or 'n/a'}",
        f"status={'success' if ok else 'failure'}",
        f"latency_ms={latency_ms}",
    ]
    if result_count is not None:
        parts.append(f"result_count={result_count}")
    if error_type:
        parts.append(f"error_type={error_type}")
    print(" ".join(parts))


def _safe_error_type(exc: Exception) -> str:
    if isinstance(exc, ProviderError):
        return exc.error_type or exc.__class__.__name__
    return exc.__class__.__name__


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
