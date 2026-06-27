from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from app.nodes.experts import ExpertAssessment, ExpertRole
from app.nodes.intake_classifier import IntakeOutput, ScamPatternClassification


class MockInvestigationLLMProvider:
    provider_name = "mock_llm"

    async def structured(self, prompt: str, schema: type[BaseModel]) -> dict[str, Any]:
        if schema is IntakeOutput:
            return _mock_intake_payload(_extract_user_text(prompt))
        if schema is ScamPatternClassification:
            return _mock_classification_payload(_extract_user_text(prompt))
        if schema is ExpertAssessment:
            return _mock_expert_payload(prompt)
        raise ValueError("Unsupported structured schema.")


def _mock_intake_payload(text: str) -> dict[str, Any]:
    organization = _first_present(
        text,
        (
            "Ngân hàng VYBank Demo",
            "VYBank Demo",
            "JobBee Demo",
            "DemoMarket",
        ),
    )
    url = _first_url(text)
    has_otp = _contains(text, "otp")
    has_lock = _contains(text, "bị khóa", "bi khoa", "khóa tài khoản", "khoa tai khoan")

    entities: list[dict[str, str]] = []
    if organization is not None:
        entities.append({"text": organization, "type": "organization"})
    if url is not None:
        entities.append({"text": url, "type": "url"})

    claims: list[str] = []
    if organization is not None and has_otp:
        claims.append(f"{organization} yêu cầu cung cấp OTP.")
    elif has_otp:
        claims.append("Nội dung yêu cầu cung cấp OTP.")
    if has_lock:
        claims.append("Tài khoản sẽ bị khóa.")
    if url is not None:
        claims.append(f"Có đường dẫn {url}.")

    query_subject = organization or url or "OTP"
    queries = [f"{query_subject} OTP khóa tài khoản cảnh báo"] if has_otp or has_lock else []

    return {
        "summary": "Nội dung có dấu hiệu yêu cầu xác minh thông tin nhạy cảm.",
        "language": "vi",
        "domain": "banking" if organization or has_otp else "other",
        "intent": "credential_request" if has_otp else "other",
        "entities": entities,
        "claims": claims[:5],
        "search_queries": queries[:3],
        "is_ready": True,
        "clarification_question": None,
    }


def _mock_classification_payload(text: str) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    otp_span = _present_span(text, r"cung cấp OTP|OTP|mật khẩu|PIN")
    lock_span = _present_span(text, r"tài khoản sẽ bị khóa|bị khóa|khóa tài khoản")
    link_span = _first_url(text)

    if otp_span is not None:
        patterns.append(
            {
                "label": "otp_password_request",
                "probability": 0.9,
                "evidence_spans": [otp_span],
            }
        )
    if lock_span is not None:
        patterns.append(
            {
                "label": "account_lock_threat",
                "probability": 0.8,
                "evidence_spans": [lock_span],
            }
        )
    if link_span is not None:
        patterns.append(
            {
                "label": "phishing_link",
                "probability": 0.7,
                "evidence_spans": [link_span],
            }
        )
    if not patterns:
        patterns.append({"label": "unknown", "probability": 0, "evidence_spans": []})

    return {
        "patterns": patterns,
        "primary_pattern": patterns[0]["label"],
        "requires_immediate_warning": patterns[0]["label"] != "unknown",
    }


def _mock_expert_payload(prompt: str) -> dict[str, Any]:
    role = _role_from_prompt(prompt)
    evidence_id = _first_evidence_id(prompt)
    input_span = _present_span(_extract_user_text(prompt), r"cung cấp OTP|OTP")

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
                    "input_text_span": input_span,
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
                "input_text_span": input_span,
            },
        ],
        "cited_evidence_ids": [evidence_id],
        "missing_information": ["Chưa xác minh danh tính người gửi."],
        "confidence": 78,
        "warnings": [],
    }


def _extract_user_text(prompt: str) -> str:
    marker = "User text:\n"
    if marker not in prompt:
        return ""
    text = prompt.split(marker, maxsplit=1)[1]
    return text.split("\n\nEvidence items available", maxsplit=1)[0].strip()


def _first_present(text: str, candidates: tuple[str, ...]) -> str | None:
    normalized_text = text.casefold()
    for candidate in candidates:
        if candidate.casefold() in normalized_text:
            return candidate
    return None


def _contains(text: str, *needles: str) -> bool:
    normalized_text = text.casefold()
    return any(needle.casefold() in normalized_text for needle in needles)


def _first_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s<>()]+|www\.[^\s<>()]+", text, re.IGNORECASE)
    return match.group(0) if match else None


def _present_span(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def _role_from_prompt(prompt: str) -> ExpertRole:
    for role in ExpertRole:
        if f"Role: {role.value}" in prompt:
            return role
    raise ValueError("Expert role marker missing.")


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
