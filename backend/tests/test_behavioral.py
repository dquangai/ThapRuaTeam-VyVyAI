from app.nodes.behavioral import (
    BehavioralFlagType,
    analyze_behavioral_patterns,
)


def test_behavioral_analyzer_detects_suspicious_vietnamese_manipulation_patterns() -> None:
    text = (
        "Anh là cán bộ công an, tài khoản của bạn sẽ bị khóa và có thể bị bắt giữ. "
        "Phải chuyển khoản gấp trong 10 phút. Cơ hội duy nhất chỉ hôm nay, "
        "chỉ còn 2 suất, hàng nghìn người đã nhận lãi. Giữ bí mật, "
        "không báo gia đình và không hỏi ai. Tôi đã hỗ trợ miễn phí cho bạn nên "
        "bạn chỉ cần đặt cọc nhỏ. Hãy nạp thử 500 nghìn cho nhiệm vụ đầu tiên, "
        "bước tiếp theo sẽ mở lợi nhuận."
    )

    result = analyze_behavioral_patterns(text)
    flag_types = {flag.type for flag in result.red_flags}

    assert flag_types == {
        BehavioralFlagType.URGENCY,
        BehavioralFlagType.FEAR,
        BehavioralFlagType.AUTHORITY_PRESSURE,
        BehavioralFlagType.FOMO,
        BehavioralFlagType.SCARCITY,
        BehavioralFlagType.SECRECY,
        BehavioralFlagType.ISOLATION,
        BehavioralFlagType.SOCIAL_PROOF_MANIPULATION,
        BehavioralFlagType.RECIPROCITY,
        BehavioralFlagType.GRADUAL_COMMITMENT,
    }
    assert result.behavioral_risk_score == 100
    assert all(flag.evidence_span in text for flag in result.red_flags)
    assert all(flag.explanation for flag in result.red_flags)


def test_behavioral_analyzer_preserves_vietnamese_evidence_spans() -> None:
    text = "Giữ bí mật chuyện này, không nói với ai và chuyển khoản gấp trong 10 phút."

    result = analyze_behavioral_patterns(text)
    spans = {flag.type: flag.evidence_span for flag in result.red_flags}

    assert spans[BehavioralFlagType.SECRECY] == "Giữ bí mật"
    assert spans[BehavioralFlagType.URGENCY] == "gấp"


def test_behavioral_analyzer_keeps_benign_vietnamese_message_low_risk() -> None:
    text = (
        "Chiều mai cả nhà mình họp bàn kế hoạch du lịch. Ai rảnh thì góp ý, "
        "không cần quyết định ngay và không liên quan đến chuyển tiền."
    )

    result = analyze_behavioral_patterns(text)

    assert result.red_flags == []
    assert result.behavioral_risk_score == 0
    assert "Chưa thấy" in result.summary
