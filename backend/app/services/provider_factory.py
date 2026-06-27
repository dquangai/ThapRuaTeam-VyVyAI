from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.evidence import EvidenceSearchAdapter, EvidenceSearchMode, MockSearchProvider
from app.nodes.experts import ExpertLLMProvider
from app.nodes.intake_classifier import StructuredLLMProvider
from app.services.mock_llm import MockInvestigationLLMProvider
from app.services.model_router import ModelRole
from app.services.openai_provider import OpenAIProvider
from app.services.tavily_provider import TavilySearchProvider
from app.services.virustotal_provider import VirusTotalProvider

ProviderMode = Literal["mock", "live", "disabled"]


class SafeProviderStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_name: str
    configured: bool
    enabled: bool
    mode: ProviderMode
    configured_model_name: str | None = None


@dataclass(frozen=True)
class ProviderBundle:
    llm_provider: StructuredLLMProvider
    expert_provider: ExpertLLMProvider | None
    judge_provider: StructuredLLMProvider | None
    report_provider: StructuredLLMProvider | None
    evidence_adapter: EvidenceSearchAdapter | None
    virustotal_provider: VirusTotalProvider | None
    provider_statuses: tuple[SafeProviderStatus, ...]


def build_provider_bundle(settings: Settings) -> ProviderBundle:
    statuses = safe_provider_statuses(settings)

    if settings.mock_mode:
        mock_llm = MockInvestigationLLMProvider()
        return ProviderBundle(
            llm_provider=mock_llm,
            expert_provider=mock_llm,
            judge_provider=None,
            report_provider=None,
            evidence_adapter=EvidenceSearchAdapter(
                provider=MockSearchProvider.from_default_fixture(),
                mode=EvidenceSearchMode.MOCK,
                timeout_seconds=settings.provider_timeout_float(),
                max_queries=settings.max_search_queries,
                max_results=settings.max_evidence_items,
            ),
            virustotal_provider=None,
            provider_statuses=statuses,
        )

    evidence_adapter = _live_evidence_adapter(settings)
    return ProviderBundle(
        llm_provider=OpenAIProvider(settings=settings, model_role=ModelRole.FAST),
        expert_provider=OpenAIProvider(settings=settings, model_role=ModelRole.EXPERT),
        judge_provider=OpenAIProvider(settings=settings, model_role=ModelRole.JUDGE),
        report_provider=OpenAIProvider(settings=settings, model_role=ModelRole.REPORT),
        evidence_adapter=evidence_adapter,
        virustotal_provider=(
            VirusTotalProvider(settings=settings) if settings.enable_virustotal else None
        ),
        provider_statuses=statuses,
    )


def safe_provider_statuses(settings: Settings) -> tuple[SafeProviderStatus, ...]:
    provider_mode: ProviderMode = "mock" if settings.mock_mode else "live"
    openai_configured = settings.openai_api_key is not None
    openai_enabled = not settings.mock_mode

    statuses = [
        _openai_status(
            role=ModelRole.FAST,
            configured=openai_configured,
            enabled=openai_enabled,
            mode=provider_mode,
            model_name=settings.openai_model_fast,
        ),
        _openai_status(
            role=ModelRole.EXPERT,
            configured=openai_configured,
            enabled=openai_enabled,
            mode=provider_mode,
            model_name=settings.openai_model_expert,
        ),
        _openai_status(
            role=ModelRole.JUDGE,
            configured=openai_configured,
            enabled=openai_enabled,
            mode=provider_mode,
            model_name=settings.openai_model_judge,
        ),
        _openai_status(
            role=ModelRole.REPORT,
            configured=openai_configured,
            enabled=openai_enabled,
            mode=provider_mode,
            model_name=settings.openai_model_report,
        ),
        SafeProviderStatus(
            provider_name="tavily",
            configured=settings.tavily_api_key is not None,
            enabled=(not settings.mock_mode and settings.enable_web_search),
            mode=_search_mode(settings),
        ),
        SafeProviderStatus(
            provider_name="virustotal",
            configured=settings.virustotal_api_key is not None,
            enabled=(not settings.mock_mode and settings.enable_virustotal),
            mode=_virustotal_mode(settings),
        ),
    ]
    return tuple(statuses)


def _live_evidence_adapter(settings: Settings) -> EvidenceSearchAdapter:
    if not settings.enable_web_search:
        return EvidenceSearchAdapter(
            provider=None,
            mode=EvidenceSearchMode.DISABLED,
            timeout_seconds=settings.provider_timeout_float(),
            max_queries=settings.max_search_queries,
            max_results=settings.max_evidence_items,
        )

    return EvidenceSearchAdapter(
        provider=TavilySearchProvider(settings=settings),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=settings.provider_timeout_float(),
        max_queries=settings.max_search_queries,
        max_results=settings.max_evidence_items,
    )


def _openai_status(
    *,
    role: ModelRole,
    configured: bool,
    enabled: bool,
    mode: ProviderMode,
    model_name: str | None,
) -> SafeProviderStatus:
    return SafeProviderStatus(
        provider_name=f"openai:{role.value}",
        configured=configured and bool(model_name),
        enabled=enabled,
        mode=mode,
        configured_model_name=model_name,
    )


def _search_mode(settings: Settings) -> ProviderMode:
    if settings.mock_mode:
        return "mock"
    return "live" if settings.enable_web_search else "disabled"


def _virustotal_mode(settings: Settings) -> ProviderMode:
    if settings.mock_mode:
        return "mock"
    return "live" if settings.enable_virustotal else "disabled"
