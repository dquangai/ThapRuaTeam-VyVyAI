import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import InvestigationRequest, InvestigationResponse, Locale

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPOSITORY_ROOT / "contracts"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def minimal_response_payload() -> dict[str, object]:
    return {
        "investigation_id": "test-001",
        "status": "partial",
        "verification": {
            "risk_score": 72,
            "risk_label": "suspicious",
            "confidence_score": 41,
        },
        "report": {"summary": "Chưa đủ bằng chứng từ nguồn ngoài."},
        "warnings": ["Không lấy được dữ liệu ngoài."],
        "timings_ms": {"total": 15},
    }


def test_committed_contracts_are_valid_json_schema_documents() -> None:
    request_schema = load_json(CONTRACTS_DIR / "investigation_request.schema.json")
    response_schema = load_json(CONTRACTS_DIR / "investigation_response.schema.json")

    assert request_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert response_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert request_schema["type"] == "object"
    assert response_schema["type"] == "object"
    assert InvestigationRequest.model_json_schema()["type"] == "object"
    assert InvestigationResponse.model_json_schema()["type"] == "object"


def test_request_contract_defaults_and_limits() -> None:
    request = InvestigationRequest(text="Nội dung hợp lệ")

    assert request.locale is Locale.VI
    assert request.use_web_search is True

    with pytest.raises(ValidationError):
        InvestigationRequest(text="quá ngắn")

    with pytest.raises(ValidationError):
        InvestigationRequest(text="x" * 12_001)


def test_request_contract_rejects_invalid_enum_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        InvestigationRequest.model_validate({"text": "Nội dung hợp lệ", "locale": "fr"})

    with pytest.raises(ValidationError):
        InvestigationRequest.model_validate({"text": "Nội dung hợp lệ", "file": "image.png"})


def test_partial_response_omits_optional_collections_safely() -> None:
    response = InvestigationResponse.model_validate(minimal_response_payload())

    assert response.status.value == "partial"
    assert response.evidence == []
    assert response.experts == []
    assert response.verification.risk_score == 72
    assert response.verification.confidence_score == 41


def test_evidence_ids_and_expert_citations_are_explicit() -> None:
    payload = minimal_response_payload()
    payload["evidence"] = [
        {
            "evidence_id": "ev-001",
            "title": "Cảnh báo chính thức",
            "url": "https://example.gov.vn/warning",
            "source_name": "Example Authority",
            "published_at": None,
            "snippet": "Cảnh báo về thủ đoạn yêu cầu OTP.",
            "retrieved_at": "2026-06-27T10:00:00+07:00",
            "credibility_score": 95,
            "relevance_score": 90,
        }
    ]
    payload["experts"] = [
        {"expert": "cyber", "cited_evidence_ids": ["ev-001"]}
    ]

    response = InvestigationResponse.model_validate(payload)

    assert response.evidence[0].evidence_id == "ev-001"
    assert response.experts[0].cited_evidence_ids == ["ev-001"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("risk_label", "medium"),
        ("risk_score", 101),
        ("confidence_score", -1),
    ],
)
def test_verification_rejects_invalid_enums_and_score_bounds(field: str, value: object) -> None:
    payload = minimal_response_payload()
    verification = payload["verification"]
    assert isinstance(verification, dict)
    verification[field] = value

    with pytest.raises(ValidationError):
        InvestigationResponse.model_validate(payload)


def test_response_schema_declares_expert_citation_ids() -> None:
    response_schema = load_json(CONTRACTS_DIR / "investigation_response.schema.json")
    properties = response_schema["properties"]
    assert isinstance(properties, dict)
    experts = properties["experts"]
    assert isinstance(experts, dict)
    items = experts["items"]
    assert isinstance(items, dict)

    assert "cited_evidence_ids" in items["required"]
