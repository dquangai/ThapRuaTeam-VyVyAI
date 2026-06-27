import asyncio
from typing import Any

from pydantic import BaseModel

from app.models import Locale
from app.nodes import (
    EntityType,
    IntakeDomain,
    IntakeIntent,
    ScamPatternLabel,
    classify_scam_patterns,
    run_intake,
)
from app.nodes.intake_classifier import IntakeOutput, ScamPatternClassification


class FakeLLMProvider:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, type[BaseModel]]] = []

    async def structured(self, prompt: str, schema: type[BaseModel]) -> Any:
        self.calls.append((prompt, schema))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def valid_intake_payload() -> dict[str, Any]:
    return {
        "summary": "Tin nhắn tự xưng ngân hàng yêu cầu OTP và đe dọa khóa tài khoản.",
        "language": "vi",
        "domain": "banking",
        "intent": "credential_request",
        "entities": [
            {"text": "VPBank", "type": "organization"},
            {"text": "https://vpbank.example/login", "type": "url"},
            {"text": "Vietcombank", "type": "organization"},
        ],
        "claims": [
            "Tin nhắn tự xưng VPBank.",
            "Người gửi yêu cầu cung cấp OTP.",
            "Tài khoản bị dọa khóa.",
            "Có đường dẫn https://vpbank.example/login.",
            "Người nhận phải xác minh ngay.",
            "Claim thứ sáu sẽ bị cắt bớt.",
        ],
        "search_queries": [
            "VPBank OTP khóa tài khoản cảnh báo",
            "https://vpbank.example/login lừa đảo",
            "Vietcombank cảnh báo giả mạo",
            "query thứ tư bị cắt",
        ],
        "is_ready": True,
        "clarification_question": None,
    }


def test_intake_agent_returns_structured_grounded_output() -> None:
    text = (
        "VPBank thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại "
        "https://vpbank.example/login để xác minh ngay."
    )
    provider = FakeLLMProvider([valid_intake_payload()])

    output = run(run_intake(text=text, locale=Locale.VI, provider=provider))

    assert provider.calls[0][1] is IntakeOutput
    assert output.language == Locale.VI
    assert output.domain == IntakeDomain.BANKING
    assert output.intent == IntakeIntent.CREDENTIAL_REQUEST
    assert [(entity.text, entity.type) for entity in output.entities] == [
        ("VPBank", EntityType.ORGANIZATION),
        ("https://vpbank.example/login", EntityType.URL),
    ]
    assert len(output.claims) == 5
    assert len(output.search_queries) == 3
    assert all("Vietcombank" not in query for query in output.search_queries)


def test_intake_retries_invalid_structured_output_once() -> None:
    text = "VPBank yêu cầu cung cấp OTP để xác minh tài khoản."
    provider = FakeLLMProvider(
        [
            {"summary": "missing required fields"},
            {
                "summary": "Tin nhắn yêu cầu OTP.",
                "language": "vi",
                "domain": "banking",
                "intent": "credential_request",
                "entities": [{"text": "VPBank", "type": "organization"}],
                "claims": ["VPBank yêu cầu cung cấp OTP."],
                "search_queries": ["VPBank cung cấp OTP cảnh báo"],
                "is_ready": True,
                "clarification_question": None,
            },
        ]
    )

    output = run(run_intake(text=text, locale=Locale.VI, provider=provider))

    assert len(provider.calls) == 2
    assert "previous structured output was invalid" in provider.calls[1][0]
    assert output.entities[0].text == "VPBank"
    assert output.is_ready is True


def test_intake_returns_typed_fallback_after_second_invalid_output() -> None:
    provider = FakeLLMProvider(
        [
            {"summary": "missing required fields"},
            {"domain": "not-a-valid-domain"},
        ]
    )

    output = run(
        run_intake(
            text="Tin nhắn mơ hồ yêu cầu xác minh tài khoản.",
            locale=Locale.VI,
            provider=provider,
        )
    )

    assert len(provider.calls) == 2
    assert output.domain == IntakeDomain.OTHER
    assert output.intent == IntakeIntent.OTHER
    assert output.entities == []
    assert output.claims == []
    assert output.search_queries == []
    assert output.is_ready is False
    assert output.clarification_question is not None


def test_classifier_returns_grounded_patterns_and_preserves_uncertainty() -> None:
    text = "Tài khoản sẽ bị khóa nếu không cung cấp OTP ngay."
    intake = IntakeOutput(
        summary="Tin nhắn đe dọa khóa tài khoản và yêu cầu OTP.",
        language=Locale.VI,
        domain=IntakeDomain.BANKING,
        intent=IntakeIntent.CREDENTIAL_REQUEST,
        entities=[],
        claims=["Tài khoản sẽ bị khóa.", "Người gửi yêu cầu cung cấp OTP."],
        search_queries=[],
        is_ready=True,
        clarification_question=None,
    )
    provider = FakeLLMProvider(
        [
            {
                "patterns": [
                    {
                        "label": "otp_password_request",
                        "probability": 0.88,
                        "evidence_spans": ["cung cấp OTP", "mật khẩu ngân hàng"],
                    },
                    {
                        "label": "bank_impersonation",
                        "probability": 0.5,
                        "evidence_spans": ["ngân hàng ABC"],
                    },
                    {
                        "label": "unknown",
                        "probability": 0.1,
                        "evidence_spans": [],
                    },
                ],
                "primary_pattern": "otp_password_request",
                "requires_immediate_warning": True,
            }
        ]
    )

    output = run(
        classify_scam_patterns(
            text=text,
            locale=Locale.VI,
            intake=intake,
            provider=provider,
        )
    )

    assert provider.calls[0][1] is ScamPatternClassification
    assert [pattern.label for pattern in output.patterns] == [
        ScamPatternLabel.OTP_PASSWORD_REQUEST,
        ScamPatternLabel.UNKNOWN,
    ]
    assert output.patterns[0].evidence_spans == ["cung cấp OTP"]
    assert output.primary_pattern == ScamPatternLabel.OTP_PASSWORD_REQUEST
    assert output.requires_immediate_warning is True


def test_classifier_returns_typed_fallback_after_provider_errors() -> None:
    intake = IntakeOutput(
        summary="Không đủ dữ liệu.",
        language=Locale.VI,
        domain=IntakeDomain.OTHER,
        intent=IntakeIntent.OTHER,
        entities=[],
        claims=[],
        search_queries=[],
        is_ready=False,
        clarification_question="Nguồn nội dung là gì?",
    )
    provider = FakeLLMProvider([ValueError("bad json"), ValueError("bad json again")])

    output = run(
        classify_scam_patterns(
            text="Nội dung chưa rõ ràng cần kiểm tra thêm.",
            locale=Locale.VI,
            intake=intake,
            provider=provider,
        )
    )

    assert len(provider.calls) == 2
    assert output.primary_pattern == ScamPatternLabel.UNKNOWN
    assert output.patterns[0].label == ScamPatternLabel.UNKNOWN
    assert output.requires_immediate_warning is False
