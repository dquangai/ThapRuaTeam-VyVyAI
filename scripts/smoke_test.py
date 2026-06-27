from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)
    text = (
        "Ngân hàng VYBank Demo thông báo tài khoản sẽ bị khóa. Vui lòng cung cấp OTP tại "
        "https://vybank-demo.example/login để xác minh gấp trong 10 phút."
    )

    health = client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "ok"

    fast_check = client.post(
        "/api/v1/fast-check",
        json={"text": text, "locale": "vi", "use_web_search": True},
    )
    assert fast_check.status_code == 200, fast_check.text
    fast_payload = fast_check.json()
    assert fast_payload["score"] >= 0
    assert fast_payload["triggered_flags"]

    investigation = client.post(
        "/api/v1/investigate",
        json={"text": text, "locale": "vi", "use_web_search": True},
    )
    assert investigation.status_code == 200, investigation.text
    investigation_payload = investigation.json()
    assert investigation_payload["status"] in {"completed", "partial"}
    assert investigation_payload["verification"]["risk_score"] >= 0
    assert "markdown" in investigation_payload["report"]

    print(
        "smoke ok: "
        f"fast_score={fast_payload['score']} "
        f"investigation_status={investigation_payload['status']} "
        f"risk_score={investigation_payload['verification']['risk_score']}"
    )


if __name__ == "__main__":
    main()
