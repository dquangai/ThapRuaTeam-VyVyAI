from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models import RiskLabel, VerificationResult
from app.nodes.behavioral import BehavioralAnalysis
from app.nodes.judge import JudgeResult


class SafetyAdvice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    note: str


def generate_safety_advice(
    *,
    verification: VerificationResult,
    judge: JudgeResult,
    behavioral_analysis: BehavioralAnalysis | None = None,
) -> SafetyAdvice:
    actions: list[str] = []
    warnings: list[str] = []

    if verification.risk_label in {RiskLabel.CRITICAL, RiskLabel.HIGH_RISK}:
        actions.append("Tạm dừng mọi chuyển tiền, nộp phí hoặc cung cấp thông tin nhạy cảm.")
        actions.append("Không cung cấp OTP, mật khẩu, PIN hoặc mã xác thực cho bất kỳ ai.")
    elif verification.risk_label is RiskLabel.SUSPICIOUS:
        actions.append("Chưa thực hiện giao dịch; hãy xác minh độc lập trước khi phản hồi.")
    else:
        actions.append("Vẫn nên xác minh qua kênh chính thức nếu nội dung liên quan đến tiền.")

    if _mentions_link_or_credentials(judge):
        actions.append("Không bấm đường dẫn lạ; hãy tự nhập địa chỉ website chính thức nếu cần.")

    if behavioral_analysis is not None and behavioral_analysis.red_flags:
        actions.append(
            "Trao đổi với người thân hoặc người đáng tin cậy trước khi làm theo yêu cầu."
        )

    actions.extend(
        [
            (
                "Liên hệ tổ chức liên quan qua số điện thoại hoặc ứng dụng chính thức, "
                "không dùng liên hệ trong tin nhắn."
            ),
            (
                "Lưu lại tin nhắn, số điện thoại, tài khoản nhận tiền và thời điểm "
                "liên hệ để đối chiếu."
            ),
            (
                "Nếu đã chuyển tiền hoặc lộ mã, liên hệ ngân hàng/nhà mạng ngay "
                "để khóa giao dịch hoặc tài khoản."
            ),
        ]
    )

    if verification.confidence_score < 50:
        warnings.append("Độ tin cậy còn hạn chế vì dữ liệu xác minh chưa đầy đủ.")
    if judge.missing_evidence:
        warnings.append("Còn thiếu bằng chứng để xác nhận đầy đủ bối cảnh.")

    return SafetyAdvice(
        actions=_dedupe(actions),
        warnings=_dedupe(warnings),
        note="Đây không phải tư vấn pháp lý; hãy xác minh qua kênh chính thức trước khi hành động.",
    )


def _mentions_link_or_credentials(judge: JudgeResult) -> bool:
    combined_text = " ".join(finding.statement for finding in judge.supported_findings).casefold()
    keywords = ("otp", "mật khẩu", "mat khau", "pin", "đường dẫn", "duong dan", "link")
    return any(keyword in combined_text for keyword in keywords)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
