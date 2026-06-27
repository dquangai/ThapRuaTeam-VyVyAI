import asyncio
from time import perf_counter
from typing import Any

from pydantic import BaseModel

from app.models import EvidenceItem
from app.nodes import (
    ExpertAssessment,
    ExpertRole,
    ExpertVerdict,
    ReasonBasis,
    run_expert_agent,
    run_expert_group,
)


class FakeExpertProvider:
    def __init__(self, responses_by_role: dict[str, list[Any]], delay_seconds: float = 0) -> None:
        self.responses_by_role = responses_by_role
        self.delay_seconds = delay_seconds
        self.calls: list[tuple[str, type[BaseModel]]] = []
        self.active = 0
        self.max_active = 0

    async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
        self.calls.append((prompt, schema))
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            if self.delay_seconds:
                await asyncio.sleep(self.delay_seconds)
            role = _role_from_prompt(prompt)
            response = self.responses_by_role[role].pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        finally:
            self.active -= 1


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def evidence_items() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id="ev_bank_001",
            title="Cảnh báo giả mạo ngân hàng yêu cầu OTP",
            url="https://www.sbv.gov.vn/canh-bao-gia-mao-otp",
            source_name="Ngân hàng Nhà nước Việt Nam",
            published_at="2025-11-20",
            snippet="Không cung cấp OTP, mật khẩu hoặc mã xác thực cho bất kỳ ai.",
            retrieved_at="2026-06-27T10:00:00+00:00",
            credibility_score=95,
            relevance_score=90,
        ),
        EvidenceItem(
            evidence_id="ev_police_001",
            title="Khuyến cáo phòng tránh tin nhắn giả mạo ngân hàng",
            url="https://bocongan.gov.vn/canh-bao-tin-nhan-gia-mao-ngan-hang",
            source_name="Bộ Công an",
            published_at="2025-09-14",
            snippet="Đối tượng gửi đường dẫn giả, đe dọa khóa tài khoản và yêu cầu nhập OTP.",
            retrieved_at="2026-06-27T10:00:00+00:00",
            credibility_score=95,
            relevance_score=88,
        ),
    ]


def assessment_payload(role: ExpertRole, evidence_id: str = "ev_bank_001") -> dict[str, Any]:
    return {
        "expert": role.value,
        "score": 82,
        "verdict": "high_risk",
        "reasons": [
            {
                "text": f"{role.value} nhận thấy dấu hiệu cần cảnh giác từ evidence.",
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
        "confidence": 76,
        "warnings": [],
    }


def responses_for_all_roles() -> dict[str, list[Any]]:
    return {role.value: [assessment_payload(role)] for role in ExpertRole}


def test_expert_agent_uses_shared_typed_schema_and_valid_citations() -> None:
    provider = FakeExpertProvider({ExpertRole.CYBER.value: [assessment_payload(ExpertRole.CYBER)]})

    result = run(
        run_expert_agent(
            role=ExpertRole.CYBER,
            text="Vui lòng cung cấp OTP để xác minh tài khoản.",
            evidence=evidence_items(),
            provider=provider,
        )
    )

    assert provider.calls[0][1] is ExpertAssessment
    assert result.expert is ExpertRole.CYBER
    assert result.score == 82
    assert result.verdict is ExpertVerdict.HIGH_RISK
    assert result.cited_evidence_ids == ["ev_bank_001"]
    assert result.reasons[0].basis is ReasonBasis.EVIDENCE
    assert result.reasons[0].evidence_ids == ["ev_bank_001"]
    assert result.reasons[1].basis is ReasonBasis.INPUT_TEXT


def test_expert_sanitizes_invalid_evidence_ids_and_urls() -> None:
    payload = assessment_payload(ExpertRole.OSINT, evidence_id="ev_missing")
    payload["reasons"][0]["text"] = "Xem thêm https://evil.example/report để kết luận."
    payload["cited_evidence_ids"] = ["ev_bank_001", "ev_missing"]
    payload["missing_information"] = ["Không truy cập http://unknown.example để kiểm chứng."]
    provider = FakeExpertProvider({ExpertRole.OSINT.value: [payload]})

    result = run(
        run_expert_agent(
            role=ExpertRole.OSINT,
            text="Tin nhắn yêu cầu cung cấp OTP.",
            evidence=evidence_items(),
            provider=provider,
        )
    )

    assert result.cited_evidence_ids == ["ev_bank_001"]
    assert result.reasons[0].basis is ReasonBasis.INPUT_TEXT
    assert result.reasons[0].evidence_ids == []
    dumped = result.model_dump_json()
    assert "https://" not in dumped
    assert "http://" not in dumped


def test_invalid_structured_output_retries_once_then_succeeds() -> None:
    provider = FakeExpertProvider(
        {
            ExpertRole.FINANCIAL.value: [
                {"expert": "financial", "score": 200},
                assessment_payload(ExpertRole.FINANCIAL),
            ]
        }
    )

    result = run(
        run_expert_agent(
            role=ExpertRole.FINANCIAL,
            text="Chuyển khoản gấp để nhận thưởng.",
            evidence=evidence_items(),
            provider=provider,
        )
    )

    assert len(provider.calls) == 2
    assert "previous structured output was invalid" in provider.calls[1][0]
    assert result.expert is ExpertRole.FINANCIAL
    assert result.confidence == 76


def test_one_expert_failure_does_not_fail_group() -> None:
    responses = responses_for_all_roles()
    responses[ExpertRole.LEGAL_RISK.value] = [
        RuntimeError("provider down"),
        RuntimeError("still down"),
    ]
    provider = FakeExpertProvider(responses)

    result = run(
        run_expert_group(
            text="Tài khoản sẽ bị khóa nếu không cung cấp OTP.",
            evidence=evidence_items(),
            provider=provider,
        )
    )

    assert len(result.assessments) == 4
    by_role = {assessment.expert: assessment for assessment in result.assessments}
    assert by_role[ExpertRole.LEGAL_RISK].verdict is ExpertVerdict.UNCERTAIN
    assert by_role[ExpertRole.LEGAL_RISK].confidence == 0
    assert by_role[ExpertRole.CYBER].score == 82
    assert result.warnings


def test_expert_group_runs_agents_concurrently() -> None:
    provider = FakeExpertProvider(responses_for_all_roles(), delay_seconds=0.08)

    start = perf_counter()
    result = run(
        run_expert_group(
            text="Tài khoản sẽ bị khóa nếu không cung cấp OTP.",
            evidence=evidence_items(),
            provider=provider,
        )
    )
    elapsed_ms = (perf_counter() - start) * 1000

    print(f"CONCURRENCY elapsed_ms={elapsed_ms:.1f} max_active={provider.max_active}")
    assert len(result.assessments) == 4
    assert provider.max_active == 4
    assert elapsed_ms < 240


def _role_from_prompt(prompt: str) -> str:
    for role in ExpertRole:
        marker = f"Role: {role.value}"
        if marker in prompt:
            return role.value
    raise AssertionError("role marker missing from prompt")
