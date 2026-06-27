from fastapi.testclient import TestClient

from app.main import app
from app.services.fast_check import analyze_fast_check

client = TestClient(app)


def flag_codes(text: str) -> list[str]:
    response = analyze_fast_check(text, request_id="test")
    return [flag.code for flag in response.triggered_flags]


def test_fast_check_detects_required_red_flags_with_vietnamese_spans() -> None:
    text = (
        "Tài khoản của bạn sẽ bị khóa. Vui lòng cung cấp OTP tại https://bit.ly/xacminh. "
        "Chuyển khoản gấp phí xác minh trong 10 phút. Tải AnyDesk để được hỗ trợ. "
        "Bạn trúng thưởng iPhone, hãy nộp phí vận chuyển. Đầu tư crypto cam kết lợi nhuận "
        "30% mỗi tháng. Giữ bí mật chuyện này, không nói với ai."
    )

    response = analyze_fast_check(text, request_id="test")
    codes = [flag.code for flag in response.triggered_flags]

    assert codes == [
        "OTP_REQUEST",
        "URGENT_MONEY_TRANSFER",
        "ACCOUNT_LOCK_OR_ARREST_THREAT",
        "REMOTE_CONTROL_APP_REQUEST",
        "UPFRONT_FEE",
        "GUARANTEED_INVESTMENT_RETURN",
        "SECRECY_REQUEST",
        "SUSPICIOUS_LINK",
    ]
    assert response.score == 100
    assert response.risk_band == "critical"
    assert all(flag.evidence_span in text for flag in response.triggered_flags)


def test_fast_check_detects_otp_password_pin_request() -> None:
    text = "Vui lòng cung cấp OTP để xác minh tài khoản ngay hôm nay."

    response = analyze_fast_check(text, request_id="test")

    assert flag_codes(text) == ["OTP_REQUEST"]
    assert response.triggered_flags[0].evidence_span == "cung cấp OTP"


def test_fast_check_detects_urgent_money_transfer() -> None:
    text = "Hãy chuyển khoản gấp 5 triệu trong 10 phút để xử lý hồ sơ."

    assert flag_codes(text) == ["URGENT_MONEY_TRANSFER"]


def test_fast_check_detects_account_lock_or_arrest_threat() -> None:
    text = "Tài khoản ngân hàng của bạn sẽ bị khóa nếu không xác minh ngay."

    assert flag_codes(text) == ["ACCOUNT_LOCK_OR_ARREST_THREAT"]


def test_fast_check_detects_remote_control_app_request() -> None:
    text = "Tải AnyDesk và cấp quyền điều khiển từ xa để nhân viên hỗ trợ."

    assert flag_codes(text) == ["REMOTE_CONTROL_APP_REQUEST"]


def test_fast_check_detects_suspicious_shortened_link() -> None:
    text = "Bấm vào https://bit.ly/nhan-qua để cập nhật thông tin nhận thưởng."

    response = analyze_fast_check(text, request_id="test")

    assert flag_codes(text) == ["SUSPICIOUS_LINK"]
    assert response.triggered_flags[0].evidence_span == "https://bit.ly/nhan-qua"


def test_fast_check_detects_recruitment_or_prize_upfront_fee() -> None:
    text = "Bạn trúng thưởng xe máy, cần nộp phí vận chuyển trước khi nhận quà."

    assert flag_codes(text) == ["UPFRONT_FEE"]


def test_fast_check_detects_guaranteed_investment_return() -> None:
    text = "Đầu tư crypto hôm nay, cam kết lợi nhuận 30% mỗi tháng và không lỗ."

    assert flag_codes(text) == ["GUARANTEED_INVESTMENT_RETURN"]


def test_fast_check_detects_secrecy_request() -> None:
    text = "Giữ bí mật chuyện này và không nói với ai để tránh ảnh hưởng hồ sơ."

    assert flag_codes(text) == ["SECRECY_REQUEST"]


def test_fast_check_deduplicates_flags() -> None:
    text = "Hãy cung cấp OTP ngay, sau đó cung cấp mật khẩu để xác minh tài khoản."

    response = analyze_fast_check(text, request_id="test")

    assert [flag.code for flag in response.triggered_flags] == ["OTP_REQUEST"]


def test_benign_message_avoids_high_risk() -> None:
    text = "Mai mình chuyển khoản tiền cà phê, khi nào rảnh thì xác nhận giúp nhé."

    response = analyze_fast_check(text, request_id="test")

    assert response.triggered_flags == []
    assert response.score < 25
    assert response.risk_band == "low"


def test_fast_check_returns_clear_immediate_actions() -> None:
    text = "Vui lòng cung cấp OTP và bấm vào https://bit.ly/xacminh để cập nhật."

    response = analyze_fast_check(text, request_id="test")

    assert "Không cung cấp OTP, mật khẩu, PIN hoặc mã xác thực." in response.immediate_actions
    assert (
        "Không bấm vào đường dẫn lạ; hãy tự nhập địa chỉ website chính thức."
        in response.immediate_actions
    )


def test_fast_check_api_returns_contract_shape() -> None:
    response = client.post(
        "/api/v1/fast-check",
        json={
            "text": (
                "Tài khoản của bạn sẽ bị khóa. Vui lòng cung cấp OTP tại "
                "https://bit.ly/xacminh."
            ),
            "locale": "vi",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "request_id",
        "risk_band",
        "score",
        "triggered_flags",
        "message",
        "immediate_actions",
        "latency_ms",
    }
    assert payload["risk_band"] == "critical"
    assert payload["score"] == 100
    assert [flag["code"] for flag in payload["triggered_flags"]] == [
        "OTP_REQUEST",
        "ACCOUNT_LOCK_OR_ARREST_THREAT",
        "SUSPICIOUS_LINK",
    ]
    assert isinstance(payload["request_id"], str)
    assert payload["latency_ms"] >= 0


def test_fast_check_api_validates_input_length() -> None:
    response = client.post("/api/v1/fast-check", json={"text": "ngắn"})

    assert response.status_code == 422
