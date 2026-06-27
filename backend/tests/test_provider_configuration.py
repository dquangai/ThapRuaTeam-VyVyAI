from __future__ import annotations

import asyncio
import socket
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import MissingConfigurationError, Settings
from app.evidence import EvidenceSearchAdapter, EvidenceSearchMode
from app.graph import InvestigationGraphDependencies, build_investigation_graph
from app.graph.builder import JudgeModelReview, ReportModelNarrative
from app.main import app
from app.models import InvestigationRequest, Locale
from app.nodes.experts import ExpertRole, run_expert_group
from app.nodes.intake_classifier import (
    IntakeOutput,
    ScamPatternClassification,
    classify_scam_patterns,
    run_intake,
)
from app.scoring import score_verification
from app.services.fast_check import analyze_fast_check
from app.services.mock_llm import MockInvestigationLLMProvider
from app.services.model_router import ModelRole, get_model_for_role
from app.services.openai_provider import OpenAIProvider
from app.services.provider_errors import ProviderAuthenticationError
from app.services.provider_factory import build_provider_bundle
from app.services.tavily_provider import TavilySearchProvider


class TinySchema(BaseModel):
    value: str


class RecordingStructuredClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, type[BaseModel]]] = []

    async def structured(
        self,
        *,
        model: str,
        prompt: str,
        schema: type[BaseModel],
    ) -> dict[str, Any]:
        self.calls.append((model, schema))
        if schema is IntakeOutput:
            return valid_intake_payload()
        if schema is ScamPatternClassification:
            return valid_classification_payload()
        if schema.__name__ == "ExpertAssessment":
            return expert_payload(prompt)
        if schema is JudgeModelReview:
            return {
                "reasoning_summary": "Judge model reviewed deterministic findings safely.",
                "disagreement_notes": [],
                "unsupported_finding_notes": [],
            }
        if schema is ReportModelNarrative:
            return {"markdown_addendum": "Tóm tắt bổ sung không thay đổi điểm số hoặc bằng chứng."}
        return {"value": "ok"}


class AuthenticationError(Exception):
    pass


class AuthenticationFailingClient:
    def __init__(self) -> None:
        self.calls = 0

    async def structured(self, *, model: str, prompt: str, schema: type[BaseModel]) -> Any:
        self.calls += 1
        raise AuthenticationError("do-not-leak-secret")


class InvalidTwiceProvider:
    def __init__(self) -> None:
        self.calls = 0

    async def structured(self, prompt: str, schema: type[BaseModel]) -> dict[str, Any]:
        self.calls += 1
        return {"not": "valid"}


class TimeoutClient:
    async def post(self, *args: Any, **kwargs: Any) -> Any:
        raise httpx.ReadTimeout("timeout")

    async def aclose(self) -> None:
        return None


class TavilyPayloadResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "results": [
                {
                    "title": "Cảnh báo thủ đoạn yêu cầu mã OTP",
                    "url": "https://www.example.org/canh-bao-otp",
                    "content": "Không cung cấp mã OTP cho người lạ hoặc đường link không xác minh.",
                }
            ]
        }


class TavilyPayloadClient:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    async def post(self, *args: Any, **kwargs: Any) -> TavilyPayloadResponse:
        self.requests.append(kwargs)
        return TavilyPayloadResponse()

    async def aclose(self) -> None:
        return None


class FailingVirusTotalProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def lookup(self, target: str, target_type: str) -> None:
        self.calls.append((target, target_type))
        raise RuntimeError("virustotal unavailable")


class DomainLLMProvider:
    async def structured(self, prompt: str, schema: type[BaseModel]) -> dict[str, Any]:
        if schema is IntakeOutput:
            return {
                "summary": "Nội dung có domain cần enrichment.",
                "language": "vi",
                "domain": "other",
                "intent": "other",
                "entities": [{"text": "example.com", "type": "domain"}],
                "claims": ["example.com xuất hiện trong nội dung."],
                "search_queries": [],
                "is_ready": True,
                "clarification_question": None,
            }
        if schema is ScamPatternClassification:
            return valid_classification_payload()
        if schema.__name__ == "ExpertAssessment":
            return expert_payload(prompt)
        raise ValueError("unsupported schema")


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def live_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "_env_file": None,
        "MOCK_MODE": False,
        "ENABLE_WEB_SEARCH": True,
        "ENABLE_VIRUSTOTAL": False,
        "OPENAI_API_KEY": "test-openai-secret",
        "OPENAI_MODEL_FAST": "fast-model",
        "OPENAI_MODEL_EXPERT": "expert-model",
        "OPENAI_MODEL_JUDGE": "judge-model",
        "OPENAI_MODEL_REPORT": "report-model",
        "TAVILY_API_KEY": "test-tavily-secret",
        "VIRUSTOTAL_API_KEY": "test-vt-secret",
    }
    values.update(overrides)
    return Settings(**values)


def valid_intake_payload() -> dict[str, Any]:
    return {
        "summary": "Tin nhắn yêu cầu OTP.",
        "language": "vi",
        "domain": "banking",
        "intent": "credential_request",
        "entities": [],
        "claims": ["Nội dung yêu cầu OTP."],
        "search_queries": ["OTP khóa tài khoản cảnh báo"],
        "is_ready": True,
        "clarification_question": None,
    }


def valid_classification_payload() -> dict[str, Any]:
    return {
        "patterns": [
            {
                "label": "otp_password_request",
                "probability": 0.9,
                "evidence_spans": ["OTP"],
            }
        ],
        "primary_pattern": "otp_password_request",
        "requires_immediate_warning": True,
    }


def expert_payload(prompt: str) -> dict[str, Any]:
    role = next(role for role in ExpertRole if f"Role: {role.value}" in prompt)
    return {
        "expert": role.value,
        "score": 40,
        "verdict": "uncertain",
        "reasons": [
            {
                "text": "Chỉ có dữ liệu từ nội dung đầu vào.",
                "basis": "input_text",
                "evidence_ids": [],
                "input_text_span": None,
            }
        ],
        "cited_evidence_ids": [],
        "missing_information": ["Thiếu bằng chứng ngoài."],
        "confidence": 40,
        "warnings": [],
    }


def test_mock_mode_works_without_api_keys_and_makes_zero_external_requests(
    monkeypatch: Any,
) -> None:
    settings = Settings(_env_file=None, MOCK_MODE=True)
    bundle = build_provider_bundle(settings)

    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=bundle.llm_provider,
            expert_provider=bundle.expert_provider,
            evidence_adapter=bundle.evidence_adapter,
            id_factory=lambda: "mock-provider-test",
        )
    )

    async def invoke_with_socket_guard() -> Any:
        def fail_socket(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("Mock Mode must not open network sockets")

        monkeypatch.setattr(socket, "socket", fail_socket)
        return await graph.ainvoke(
            InvestigationRequest(
                text="Ngân hàng VYBank Demo yêu cầu cung cấp OTP để tránh bị khóa tài khoản.",
                locale=Locale.VI,
                use_web_search=True,
            )
        )

    state = run(invoke_with_socket_guard())

    assert state.investigation_id == "mock-provider-test"
    assert state.evidence_status is not None
    assert state.evidence_status.mode is EvidenceSearchMode.MOCK


def test_live_mode_selects_openai_and_tavily_providers() -> None:
    bundle = build_provider_bundle(live_settings())

    assert isinstance(bundle.llm_provider, OpenAIProvider)
    assert isinstance(bundle.expert_provider, OpenAIProvider)
    assert bundle.evidence_adapter is not None
    assert isinstance(bundle.evidence_adapter.provider, TavilySearchProvider)
    assert bundle.evidence_adapter.mode is EvidenceSearchMode.LIVE


def test_model_roles_resolve_expected_variables() -> None:
    settings = live_settings()

    assert get_model_for_role(ModelRole.FAST, settings) == "fast-model"
    assert get_model_for_role(ModelRole.EXPERT, settings) == "expert-model"
    assert get_model_for_role(ModelRole.JUDGE, settings) == "judge-model"
    assert get_model_for_role(ModelRole.REPORT, settings) == "report-model"


def test_fast_intake_and_classifier_use_fast_model() -> None:
    client = RecordingStructuredClient()
    provider = OpenAIProvider(
        settings=live_settings(),
        model_role=ModelRole.FAST,
        client=client,
    )

    intake = run(run_intake(text="Vui lòng cung cấp OTP.", locale=Locale.VI, provider=provider))
    run(
        classify_scam_patterns(
            text="Vui lòng cung cấp OTP.",
            locale=Locale.VI,
            intake=intake,
            provider=provider,
        )
    )

    assert [model for model, _ in client.calls] == ["fast-model", "fast-model"]


def test_four_experts_use_expert_model() -> None:
    client = RecordingStructuredClient()
    provider = OpenAIProvider(
        settings=live_settings(),
        model_role=ModelRole.EXPERT,
        client=client,
    )

    result = run(run_expert_group(text="Vui lòng cung cấp OTP.", evidence=[], provider=provider))

    assert len(result.assessments) == 4
    assert [model for model, _ in client.calls] == ["expert-model"] * 4


def test_graph_judge_and_report_use_configured_models() -> None:
    settings = live_settings()
    judge_client = RecordingStructuredClient()
    report_client = RecordingStructuredClient()
    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=MockInvestigationLLMProvider(),
            expert_provider=MockInvestigationLLMProvider(),
            judge_provider=OpenAIProvider(
                settings=settings,
                model_role=ModelRole.JUDGE,
                client=judge_client,
            ),
            report_provider=OpenAIProvider(
                settings=settings,
                model_role=ModelRole.REPORT,
                client=report_client,
            ),
            evidence_adapter=None,
            id_factory=lambda: "judge-report-model-test",
        )
    )

    state = run(
        graph.ainvoke(
            InvestigationRequest(
                text="Vui lòng cung cấp OTP trong 10 phút để không bị khóa tài khoản.",
                locale=Locale.VI,
                use_web_search=False,
            )
        )
    )

    assert state.status.value in {"completed", "partial"}
    assert [model for model, _ in judge_client.calls] == ["judge-model"]
    assert [model for model, _ in report_client.calls] == ["report-model"]


def test_fast_check_and_final_scoring_make_no_openai_call() -> None:
    class ExplodingProvider:
        async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
            raise AssertionError("OpenAI should not be called")

    fast = analyze_fast_check("Hãy gửi OTP trong vòng 10 phút.", request_id="fast-test")
    judge = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=MockInvestigationLLMProvider(),
            expert_provider=ExplodingProvider(),
            evidence_adapter=None,
            id_factory=lambda: "scoring-test",
        )
    )

    assert fast.score >= 0
    assert score_verification(
        judge=run(
            judge.ainvoke(
                InvestigationRequest(
                    text="Nội dung bình thường không yêu cầu gì.",
                    locale=Locale.VI,
                    use_web_search=False,
                )
            )
        ).judge_result,
        evidence=[],
        expert_assessments=[],
        behavioral_analysis=None,
        evidence_status=None,
    ).verification.risk_score >= 0


def test_missing_openai_key_is_lazy_and_typed_when_invoked() -> None:
    settings = live_settings(OPENAI_API_KEY=None)
    bundle = build_provider_bundle(settings)
    provider = bundle.llm_provider

    assert isinstance(provider, OpenAIProvider)
    with pytest.raises(MissingConfigurationError):
        run(provider.structured("Return value.", TinySchema))


def test_missing_tavily_key_returns_partial_search_status() -> None:
    settings = live_settings(TAVILY_API_KEY=None)
    adapter = EvidenceSearchAdapter(
        provider=TavilySearchProvider(settings=settings),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
    )

    result = run(adapter.collect(["OTP khóa tài khoản cảnh báo"]))

    assert result.evidence_status.mode is EvidenceSearchMode.LIVE
    assert result.evidence_status.success is False
    assert result.evidence_status.errors


def test_openai_authentication_error_is_not_retried() -> None:
    client = AuthenticationFailingClient()
    provider = OpenAIProvider(
        settings=live_settings(),
        model_role=ModelRole.FAST,
        client=client,
    )

    with pytest.raises(ProviderAuthenticationError):
        run(run_intake(text="Vui lòng cung cấp OTP.", locale=Locale.VI, provider=provider))

    assert client.calls == 1


def test_malformed_structured_output_is_retried_at_most_once() -> None:
    provider = InvalidTwiceProvider()

    result = run(run_intake(text="Vui lòng cung cấp OTP.", locale=Locale.VI, provider=provider))

    assert provider.calls == 2
    assert result.is_ready is False


def test_tavily_timeout_returns_partial_status() -> None:
    settings = live_settings()
    adapter = EvidenceSearchAdapter(
        provider=TavilySearchProvider(settings=settings, client=TimeoutClient()),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
    )

    result = run(adapter.collect(["OTP khóa tài khoản cảnh báo"]))

    assert result.evidence_status.operation_status.value == "partial"
    assert result.evidence_status.success is False
    assert "timeout" in " ".join(result.evidence_status.errors).casefold()


def test_tavily_source_name_falls_back_to_url_hostname() -> None:
    client = TavilyPayloadClient()
    provider = TavilySearchProvider(settings=live_settings(), client=client)

    results = run(provider.search(query="cảnh báo OTP", limit=1))

    assert len(results) == 1
    assert results[0].title == "Cảnh báo thủ đoạn yêu cầu mã OTP"
    assert results[0].url == "https://www.example.org/canh-bao-otp"
    assert results[0].source_name == "example.org"
    assert results[0].snippet == (
        "Không cung cấp mã OTP cho người lạ hoặc đường link không xác minh."
    )


def test_virustotal_failure_adds_warning_without_failing_investigation() -> None:
    vt_provider = FailingVirusTotalProvider()
    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=DomainLLMProvider(),
            expert_provider=DomainLLMProvider(),
            virustotal_provider=vt_provider,
            evidence_adapter=None,
            id_factory=lambda: "vt-failure-test",
        )
    )

    state = run(
        graph.ainvoke(
            InvestigationRequest(
                text="Kiểm tra domain example.com trước khi phản hồi.",
                locale=Locale.VI,
                use_web_search=False,
            )
        )
    )

    assert vt_provider.calls == [("example.com", "domain")]
    assert state.status.value != "failed"
    assert any("virustotal enrichment failed" in warning for warning in state.warnings)


def test_health_makes_no_paid_calls_and_exposes_no_secrets() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["providers"]) == {"openai", "tavily", "virustotal"}
    assert "test-openai-secret" not in response.text
    assert "authorization" not in response.text.casefold()


def test_secret_values_are_excluded_from_settings_serialization() -> None:
    settings = live_settings()

    dumped = settings.model_dump_json()

    assert "test-openai-secret" not in dumped
    assert "test-tavily-secret" not in dumped
    assert "test-vt-secret" not in dumped


def test_real_env_files_are_ignored_and_deprecated_openai_model_is_absent() -> None:
    root = Path(__file__).resolve().parents[2]

    check_env = subprocess.run(
        ["git", "check-ignore", ".env"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    check_backend_env = subprocess.run(
        ["git", "check-ignore", "backend/.env"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    tracked_env = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    deprecated = subprocess.run(
        ["git", "grep", "OPENAI_" + "MODEL="],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert check_env.returncode == 0
    assert check_backend_env.returncode == 0
    assert not any(line.endswith(".env") for line in tracked_env.stdout.splitlines())
    assert deprecated.returncode == 1
