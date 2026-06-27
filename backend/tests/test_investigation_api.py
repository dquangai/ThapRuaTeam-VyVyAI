from typing import Any

from fastapi.testclient import TestClient

from app.api import routes_investigation
from app.graph import InvestigationState
from app.main import app
from app.models import InvestigationResponse, InvestigationStatus

client = TestClient(app)


def valid_payload(use_web_search: bool = True) -> dict[str, object]:
    return {
        "text": (
            "VPBank thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại "
            "https://vpbank.example/login để xác minh gấp trong 10 phút."
        ),
        "locale": "vi",
        "use_web_search": use_web_search,
    }


def test_investigate_api_returns_completed_mock_mode_contract_response() -> None:
    response = client.post("/api/v1/investigate", json=valid_payload())

    assert response.status_code == 200
    payload = response.json()
    contract = InvestigationResponse.model_validate(payload)

    assert contract.status is InvestigationStatus.COMPLETED
    assert isinstance(contract.investigation_id, str)
    assert contract.evidence
    assert len(contract.experts) == 4
    assert contract.verification.risk_score == payload["report"]["risk_score"]
    assert contract.verification.confidence_score == payload["report"]["confidence_score"]
    assert payload["input"]["text_length"] == len(valid_payload()["text"])
    assert payload["evidence_status"]["mode"] == "mock"
    assert payload["behavioral_analysis"]["red_flags"]
    assert payload["judge"]["supported_findings"]
    assert payload["safety_advice"]["actions"]
    assert "## Kết luận" in payload["report"]["markdown"]
    assert all(isinstance(value, int) and value >= 0 for value in payload["timings_ms"].values())


def test_investigate_api_returns_partial_when_web_search_is_disabled() -> None:
    response = client.post("/api/v1/investigate", json=valid_payload(use_web_search=False))

    assert response.status_code == 200
    payload = response.json()
    contract = InvestigationResponse.model_validate(payload)

    assert contract.status is InvestigationStatus.PARTIAL
    assert payload["evidence_status"]["operation_status"] == "disabled"
    assert payload["evidence"] == []
    assert any("evidence_search" in warning for warning in payload["warnings"])
    assert "Search unavailable or partial: -20" in payload["report"]["limitations"]


def test_investigate_api_serializes_failed_graph_state(monkeypatch: Any) -> None:
    class FailedGraph:
        async def ainvoke(self, request: Any) -> InvestigationState:
            return InvestigationState(
                investigation_id="failed-test",
                input_text=request.text,
                locale=request.locale,
                use_web_search=request.use_web_search,
                status=InvestigationStatus.FAILED,
                warnings=["Graph stopped safely."],
                timings_ms={"total": 1},
            )

    monkeypatch.setattr(routes_investigation, "build_graph_for_request", lambda: FailedGraph())

    response = client.post("/api/v1/investigate", json=valid_payload())

    assert response.status_code == 200
    payload = response.json()
    contract = InvestigationResponse.model_validate(payload)

    assert contract.status is InvestigationStatus.FAILED
    assert contract.investigation_id == "failed-test"
    assert contract.verification.risk_score == 0
    assert payload["report"]["conclusion"] == "Không tạo được báo cáo điều tra đầy đủ."
    assert payload["warnings"] == ["Graph stopped safely."]


def test_investigate_api_validates_input_length() -> None:
    response = client.post("/api/v1/investigate", json={"text": "ngắn"})

    assert response.status_code == 422


def test_investigate_api_rejects_extra_request_fields() -> None:
    payload = valid_payload()
    payload["file"] = "image.png"

    response = client.post("/api/v1/investigate", json=payload)

    assert response.status_code == 422


def test_investigate_cors_uses_configured_origin_allowlist() -> None:
    response = client.options(
        "/api/v1/investigate",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_global_exception_handler_does_not_leak_raw_exception(monkeypatch: Any) -> None:
    def explode() -> Any:
        raise RuntimeError("secret-provider-token")

    monkeypatch.setattr(routes_investigation, "build_graph_for_request", explode)
    safe_client = TestClient(app, raise_server_exceptions=False)

    response = safe_client.post(
        "/api/v1/investigate",
        json=valid_payload(),
        headers={"x-request-id": "request-test-001"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Không thể xử lý yêu cầu lúc này.",
            "details": {},
            "request_id": "request-test-001",
        }
    }
    assert "secret-provider-token" not in response.text
