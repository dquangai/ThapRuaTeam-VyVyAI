import asyncio
import re
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from app.evidence import (
    EvidenceOperationStatus,
    EvidenceSearchAdapter,
    EvidenceSearchMode,
    FailedSearchProvider,
    MockSearchProvider,
    RawSearchResult,
)
from app.graph import InvestigationGraphDependencies, build_investigation_graph
from app.models import InvestigationRequest, InvestigationStatus, Locale
from app.nodes.behavioral import analyze_behavioral_patterns
from app.nodes.experts import ExpertAssessment, ExpertRole
from app.nodes.intake_classifier import IntakeOutput, ScamPatternClassification


class ConcurrencyProbe:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self.active = 0
        self.max_active = 0

    async def pause(self) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(self.delay_seconds)
        finally:
            self.active -= 1


class DelayedSearchProvider:
    provider_name = "mock"

    def __init__(self, delegate: MockSearchProvider, probe: ConcurrencyProbe) -> None:
        self.delegate = delegate
        self.probe = probe

    async def search(self, query: str, limit: int) -> Any:
        await self.probe.pause()
        return await self.delegate.search(query=query, limit=limit)


class RecordingSearchProvider:
    provider_name = "fake-live"

    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def search(self, query: str, limit: int) -> list[RawSearchResult]:
        self.calls.append((query, limit))
        return [
            RawSearchResult(
                title="Cảnh báo không cung cấp mã OTP",
                url="https://example.org/canh-bao-otp",
                source_name="Nguồn kiểm thử",
                published_at="2026-01-01",
                snippet="Cơ quan chức năng khuyến cáo không cung cấp mã OTP cho người lạ.",
            )
        ]


class FakeInvestigationLLMProvider:
    def __init__(self, expert_delay_seconds: float = 0) -> None:
        self.expert_delay_seconds = expert_delay_seconds
        self.calls: list[tuple[str, type[BaseModel]]] = []
        self.active_experts = 0
        self.max_active_experts = 0

    async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
        self.calls.append((prompt, schema))
        if schema is IntakeOutput:
            return _intake_payload()
        if schema is ScamPatternClassification:
            return _classification_payload()
        if schema is ExpertAssessment:
            self.active_experts += 1
            self.max_active_experts = max(self.max_active_experts, self.active_experts)
            try:
                if self.expert_delay_seconds:
                    await asyncio.sleep(self.expert_delay_seconds)
                return _expert_payload(prompt)
            finally:
                self.active_experts -= 1
        raise AssertionError(f"Unexpected schema: {schema}")


class FailingContextLLMProvider:
    async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
        raise RuntimeError("provider unavailable")


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_full_investigation_graph_mock_mode_completes_with_concurrency_and_timings() -> None:
    parallel_probe = ConcurrencyProbe(delay_seconds=0.05)
    llm_provider = FakeInvestigationLLMProvider(expert_delay_seconds=0.05)
    search_provider = DelayedSearchProvider(
        delegate=MockSearchProvider.from_default_fixture(),
        probe=parallel_probe,
    )
    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=llm_provider,
            evidence_adapter=EvidenceSearchAdapter(
                provider=search_provider,
                mode=EvidenceSearchMode.MOCK,
                timeout_seconds=1,
            ),
            behavioral_analyzer=_delayed_behavioral(parallel_probe),
            id_factory=lambda: "investigation_test_001",
        )
    )

    started_at = perf_counter()
    state = run(
        graph.ainvoke(
            InvestigationRequest(
                text=(
                    "VPBank thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại "
                    "https://vpbank.example/login để xác minh gấp trong 10 phút."
                ),
                locale=Locale.VI,
                use_web_search=True,
            )
        )
    )
    elapsed_ms = (perf_counter() - started_at) * 1000

    assert state.investigation_id == "investigation_test_001"
    assert state.status is InvestigationStatus.COMPLETED
    assert state.stage_sequence == [
        "intake",
        "classification",
        "evidence_search",
        "behavioral_analysis",
        "experts",
        "judge",
        "scoring",
        "safety",
        "report",
    ]
    assert state.evidence_status is not None
    assert state.evidence_status.mode is EvidenceSearchMode.MOCK
    assert state.evidence_status.operation_status is EvidenceOperationStatus.COMPLETED
    assert len(state.evidence) == 2
    assert len(state.expert_assessments) == 4
    assert state.judge_result is not None
    assert state.verification is not None
    assert state.verification_scoring is not None
    assert state.safety_advice is not None
    assert state.report is not None
    assert state.report.risk_score == state.verification_scoring.verification.risk_score
    assert "## Kết luận" in state.report.markdown
    assert set(state.timings_ms) == {
        "intake",
        "classification",
        "evidence_search",
        "behavioral_analysis",
        "experts",
        "judge",
        "scoring",
        "safety",
        "report",
        "total",
    }
    assert all(value >= 0 for value in state.timings_ms.values())
    assert parallel_probe.max_active == 2
    assert llm_provider.max_active_experts == 4
    assert elapsed_ms < 350


def test_full_investigation_graph_returns_partial_when_evidence_stage_fails() -> None:
    llm_provider = FakeInvestigationLLMProvider()
    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=llm_provider,
            evidence_adapter=EvidenceSearchAdapter(
                provider=FailedSearchProvider(),
                mode=EvidenceSearchMode.FAILED,
                timeout_seconds=1,
            ),
            id_factory=lambda: "investigation_test_partial",
        )
    )

    state = run(
        graph.ainvoke(
            InvestigationRequest(
                text="VPBank yêu cầu cung cấp OTP để tránh khóa tài khoản trong hôm nay.",
                locale=Locale.VI,
                use_web_search=True,
            )
        )
    )

    assert state.status is InvestigationStatus.PARTIAL
    assert state.evidence_status is not None
    assert state.evidence_status.operation_status is EvidenceOperationStatus.PARTIAL
    assert state.report is not None
    assert state.verification_scoring is not None
    assert "Search unavailable or partial: -20" in state.verification_scoring.confidence_penalties
    assert any("evidence_search" in warning for warning in state.warnings)


def test_graph_uses_deterministic_search_queries_when_context_llm_fails() -> None:
    search_provider = RecordingSearchProvider()
    graph = build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=FailingContextLLMProvider(),
            evidence_adapter=EvidenceSearchAdapter(
                provider=search_provider,
                mode=EvidenceSearchMode.LIVE,
                timeout_seconds=1,
            ),
            id_factory=lambda: "fallback-query-test",
        )
    )

    state = run(
        graph.ainvoke(
            InvestigationRequest(
                text=(
                    "Bộ phận hỗ trợ thông báo tài khoản sắp bị khóa. "
                    "Hãy gửi mã OTP trong vòng 10 phút để tiếp tục sử dụng."
                ),
                locale=Locale.VI,
                use_web_search=True,
            )
        )
    )

    assert search_provider.calls
    assert len(search_provider.calls) <= 3
    assert any("OTP" in query for query, _ in search_provider.calls)
    assert state.evidence_status is not None
    assert state.evidence_status.mode is EvidenceSearchMode.LIVE
    assert state.evidence_status.queries_attempted >= 1
    assert state.evidence
    assert not any(item.title.startswith("[MOCK]") for item in state.evidence)


def _delayed_behavioral(probe: ConcurrencyProbe) -> Any:
    async def analyzer(text: str) -> Any:
        await probe.pause()
        return analyze_behavioral_patterns(text)

    return analyzer


def _intake_payload() -> dict[str, Any]:
    return {
        "summary": "Tin nhắn tự xưng VPBank yêu cầu OTP và đe dọa khóa tài khoản.",
        "language": "vi",
        "domain": "banking",
        "intent": "credential_request",
        "entities": [
            {"text": "VPBank", "type": "organization"},
            {"text": "https://vpbank.example/login", "type": "url"},
        ],
        "claims": [
            "VPBank yêu cầu cung cấp OTP.",
            "Tài khoản sẽ bị khóa.",
        ],
        "search_queries": ["VPBank OTP khóa tài khoản cảnh báo"],
        "is_ready": True,
        "clarification_question": None,
    }


def _classification_payload() -> dict[str, Any]:
    return {
        "patterns": [
            {
                "label": "otp_password_request",
                "probability": 0.92,
                "evidence_spans": ["cung cấp OTP"],
            },
            {
                "label": "account_lock_threat",
                "probability": 0.84,
                "evidence_spans": ["tài khoản sẽ bị khóa"],
            },
        ],
        "primary_pattern": "otp_password_request",
        "requires_immediate_warning": True,
    }


def _expert_payload(prompt: str) -> dict[str, Any]:
    role = _role_from_prompt(prompt)
    evidence_id = _first_evidence_id(prompt)
    if evidence_id is None:
        return {
            "expert": role.value,
            "score": 45,
            "verdict": "uncertain",
            "reasons": [
                {
                    "text": f"{role.value} chỉ có dữ liệu từ nội dung đầu vào.",
                    "basis": "input_text",
                    "evidence_ids": [],
                    "input_text_span": "cung cấp OTP",
                }
            ],
            "cited_evidence_ids": [],
            "missing_information": ["Chưa có bằng chứng ngoài."],
            "confidence": 45,
            "warnings": [],
        }

    return {
        "expert": role.value,
        "score": _score_for_role(role),
        "verdict": "high_risk",
        "reasons": [
            {
                "text": f"{role.value} nhận thấy dấu hiệu nguy cơ được hỗ trợ bởi bằng chứng.",
                "basis": "evidence",
                "evidence_ids": [evidence_id],
                "input_text_span": None,
            },
            {
                "text": "Nội dung đầu vào có yêu cầu cung cấp OTP.",
                "basis": "input_text",
                "evidence_ids": [],
                "input_text_span": "cung cấp OTP",
            },
        ],
        "cited_evidence_ids": [evidence_id],
        "missing_information": ["Chưa xác minh danh tính người gửi."],
        "confidence": 78,
        "warnings": [],
    }


def _role_from_prompt(prompt: str) -> ExpertRole:
    for role in ExpertRole:
        if f"Role: {role.value}" in prompt:
            return role
    raise AssertionError("role marker missing from prompt")


def _first_evidence_id(prompt: str) -> str | None:
    match = re.search(r"evidence_id: (ev_[a-f0-9]+)", prompt)
    return match.group(1) if match else None


def _score_for_role(role: ExpertRole) -> int:
    return {
        ExpertRole.CYBER: 88,
        ExpertRole.FINANCIAL: 82,
        ExpertRole.LEGAL_RISK: 76,
        ExpertRole.OSINT: 84,
    }[role]
