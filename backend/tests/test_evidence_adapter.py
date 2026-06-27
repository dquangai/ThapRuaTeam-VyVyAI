import asyncio
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.evidence import (
    EvidenceOperationStatus,
    EvidenceSearchAdapter,
    EvidenceSearchMode,
    FailedSearchProvider,
    MockSearchProvider,
    RawSearchResult,
    score_source_credibility,
    score_source_relevance,
)
from app.models import Locale
from app.nodes import run_intake

FIXED_NOW = datetime(2026, 6, 27, 10, 0, tzinfo=UTC)


class FakeSearchProvider:
    provider_name = "fake"

    def __init__(self, results: list[RawSearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        self.calls.append((query, limit))
        return self.results[:limit]


class PerQuerySearchProvider:
    provider_name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        self.calls.append((query, limit))
        query_index = len(self.calls) - 1
        return [raw_result(query_index * 3 + offset) for offset in range(3)][:limit]


class ErrorSearchProvider:
    provider_name = "error"

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        raise RuntimeError("provider exploded")


class SlowSearchProvider:
    provider_name = "slow"

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        await asyncio.sleep(0.05)
        return []


class FakeLLMProvider:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses

    async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
        return self.responses.pop(0)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def fixed_clock() -> datetime:
    return FIXED_NOW


def raw_result(index: int) -> RawSearchResult:
    return RawSearchResult(
        title=f"Cảnh báo OTP giả mạo số {index}",
        url=f"https://evidence-unit.example/warning-{index}",
        source_name="Nguồn kiểm thử",
        published_at="2026-01-01",
        snippet="Cảnh báo không cung cấp OTP, mật khẩu hoặc mã xác thực.",
    )


def test_adapter_limits_queries_results_and_assigns_stable_evidence_ids() -> None:
    provider = PerQuerySearchProvider()
    adapter = EvidenceSearchAdapter(
        provider=provider,
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
        clock=fixed_clock,
    )

    result = run(adapter.collect(["q1", "q2", "q3", "q4"]))
    repeated_adapter = EvidenceSearchAdapter(
        provider=PerQuerySearchProvider(),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
        clock=fixed_clock,
    )
    repeated = run(repeated_adapter.collect(["q1"]))

    assert [call[0] for call in provider.calls[:3]] == ["q1", "q2", "q3"]
    assert len(provider.calls[:3]) == 3
    assert result.evidence_status.mode == EvidenceSearchMode.LIVE
    assert result.evidence_status.operation_status == EvidenceOperationStatus.COMPLETED
    assert result.evidence_status.queries_attempted == 3
    assert result.evidence_status.results_returned == 8
    assert len(result.evidence) == 8
    assert result.evidence[0].evidence_id == repeated.evidence[0].evidence_id
    assert result.evidence[0].retrieved_at == "2026-06-27T10:00:00+00:00"


def test_normalization_drops_incomplete_results_without_inventing_fields() -> None:
    provider = FakeSearchProvider(
        results=[
            RawSearchResult(
                title="Thiếu URL",
                source_name="Nguồn có thật",
                snippet="Có snippet nhưng thiếu URL.",
            ),
            RawSearchResult(
                title="Thiếu source",
                url="https://example.com/source-missing",
                snippet="Có snippet nhưng thiếu source_name.",
            ),
            RawSearchResult(
                title="Cảnh báo hợp lệ",
                url="https://evidence-unit.example/valid",
                source_name="Nguồn kiểm thử",
                snippet="Cảnh báo liên quan OTP.",
            ),
        ]
    )
    adapter = EvidenceSearchAdapter(
        provider=provider,
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
        clock=fixed_clock,
    )

    result = run(adapter.collect(["OTP cảnh báo"]))

    assert len(result.evidence) == 1
    assert result.evidence[0].title == "Cảnh báo hợp lệ"
    assert result.evidence[0].url == "https://evidence-unit.example/valid"
    assert result.evidence[0].source_name == "Nguồn kiểm thử"
    assert result.evidence[0].published_at is None


def test_source_scoring_is_deterministic_and_explainable() -> None:
    assert score_source_credibility("Bộ Công an", "https://bocongan.gov.vn/canh-bao") == 95
    assert score_source_credibility("Unknown Blog", "https://bit.ly/abc") == 35
    assert (
        score_source_relevance(
            query="VYBank Demo OTP cảnh báo",
            title="Cảnh báo OTP giả mạo VYBank Demo",
            snippet="Không cung cấp OTP.",
            url="https://evidence-unit.example/vybank-demo",
        )
        >= 60
    )


def test_disabled_and_failed_modes_are_explicit_without_provider_calls() -> None:
    disabled = EvidenceSearchAdapter(provider=None, mode=EvidenceSearchMode.DISABLED)
    failed = EvidenceSearchAdapter(provider=FailedSearchProvider(), mode=EvidenceSearchMode.FAILED)

    disabled_result = run(disabled.collect(["VYBank Demo OTP"]))
    failed_result = run(failed.collect(["VYBank Demo OTP"]))

    assert disabled_result.evidence_status.mode == EvidenceSearchMode.DISABLED
    assert disabled_result.evidence_status.operation_status == EvidenceOperationStatus.DISABLED
    assert disabled_result.evidence_status.provider == "none"
    assert disabled_result.evidence == []
    assert failed_result.evidence_status.mode == EvidenceSearchMode.FAILED
    assert failed_result.evidence_status.operation_status == EvidenceOperationStatus.PARTIAL
    assert failed_result.evidence_status.provider == "failed"
    assert failed_result.evidence == []


def test_provider_error_returns_partial_status() -> None:
    adapter = EvidenceSearchAdapter(
        provider=ErrorSearchProvider(),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=1,
        clock=fixed_clock,
    )

    result = run(adapter.collect(["VYBank Demo OTP"]))

    assert result.evidence_status.operation_status == EvidenceOperationStatus.PARTIAL
    assert result.evidence_status.success is False
    assert result.evidence_status.results_returned == 0
    assert result.evidence_status.errors


def test_provider_timeout_returns_partial_status() -> None:
    adapter = EvidenceSearchAdapter(
        provider=SlowSearchProvider(),
        mode=EvidenceSearchMode.LIVE,
        timeout_seconds=0.001,
        clock=fixed_clock,
    )

    result = run(adapter.collect(["VYBank Demo OTP"]))

    assert result.evidence_status.operation_status == EvidenceOperationStatus.PARTIAL
    assert result.evidence_status.errors == ["Search timeout for query: VYBank Demo OTP"]


def test_mock_integration_uses_intake_queries_and_fixture() -> None:
    text = (
        "Ngân hàng VYBank Demo thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại "
        "https://vybank-demo.example/login để xác minh ngay."
    )
    intake_provider = FakeLLMProvider(
        [
            {
                "summary": "Tin nhắn tự xưng VYBank Demo yêu cầu OTP.",
                "language": "vi",
                "domain": "banking",
                "intent": "credential_request",
                "entities": [
                    {"text": "Ngân hàng VYBank Demo", "type": "organization"},
                    {"text": "https://vybank-demo.example/login", "type": "url"},
                ],
                "claims": ["Ngân hàng VYBank Demo yêu cầu cung cấp OTP."],
                "search_queries": ["VYBank Demo OTP khóa tài khoản cảnh báo"],
                "is_ready": True,
                "clarification_question": None,
            }
        ]
    )
    intake = run(run_intake(text=text, locale=Locale.VI, provider=intake_provider))
    adapter = EvidenceSearchAdapter(
        provider=MockSearchProvider.from_default_fixture(),
        mode=EvidenceSearchMode.MOCK,
        timeout_seconds=1,
        clock=fixed_clock,
    )

    result = run(adapter.collect(intake.search_queries))

    assert result.evidence_status.provider == "mock"
    assert result.evidence_status.mode == EvidenceSearchMode.MOCK
    assert result.evidence_status.operation_status == EvidenceOperationStatus.COMPLETED
    assert result.evidence_status.results_returned == 2
    assert [item.source_name for item in result.evidence] == [
        "VYVY Mock Evidence — Bank Safety Lab",
        "VYVY Mock Evidence — Account Safety Lab",
    ]
    assert all(item.title.startswith("[MOCK]") for item in result.evidence)
    assert all(".example/" in item.url for item in result.evidence)
    assert all(item.evidence_id.startswith("ev_") for item in result.evidence)


def test_mock_mode_fixture_performs_no_network_call(monkeypatch) -> None:
    async def collect_with_socket_guard() -> Any:
        import socket

        def fail_socket(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("Mock Mode must not open network sockets")

        monkeypatch.setattr(socket, "socket", fail_socket)
        adapter = EvidenceSearchAdapter(
            provider=MockSearchProvider.from_default_fixture(),
            mode=EvidenceSearchMode.MOCK,
            timeout_seconds=1,
            clock=fixed_clock,
        )
        return await adapter.collect(["VYBank Demo OTP khóa tài khoản cảnh báo"])

    result = run(collect_with_socket_guard())

    assert result.evidence_status.provider == "mock"
    assert result.evidence_status.mode == EvidenceSearchMode.MOCK
    assert result.evidence_status.operation_status == EvidenceOperationStatus.COMPLETED
    assert result.evidence_status.results_returned == 2
    assert all(item.source_name.startswith("VYVY Mock Evidence") for item in result.evidence)
