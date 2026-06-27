from app.evidence import EvidenceOperationStatus, EvidenceSearchMode, EvidenceSearchStatus
from app.models import EvidenceItem, InvestigationStatus, RiskLabel, VerificationResult
from app.nodes.behavioral import BehavioralAnalysis, BehavioralFlagType, BehavioralRedFlag
from app.nodes.experts import ExpertAssessment, ExpertReason, ExpertRole, ExpertVerdict, ReasonBasis
from app.nodes.judge import judge_findings
from app.nodes.safety import generate_safety_advice
from app.reporting import ReportInput, generate_report
from app.scoring import ConfidenceComponents, RiskComponents, VerificationScoringResult


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
        )
    ]


def expert_assessments() -> list[ExpertAssessment]:
    return [
        ExpertAssessment(
            expert=ExpertRole.CYBER,
            score=88,
            verdict=ExpertVerdict.HIGH_RISK,
            reasons=[
                ExpertReason(
                    text="Bằng chứng chính thức cảnh báo không cung cấp OTP.",
                    basis=ReasonBasis.EVIDENCE,
                    evidence_ids=["ev_bank_001"],
                    input_text_span=None,
                ),
                ExpertReason(
                    text="Nội dung đầu vào yêu cầu cung cấp OTP.",
                    basis=ReasonBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span="cung cấp OTP",
                ),
            ],
            cited_evidence_ids=["ev_bank_001"],
            missing_information=["Chưa xác minh danh tính người gửi."],
            confidence=82,
            warnings=[],
        )
    ]


def behavioral() -> BehavioralAnalysis:
    return BehavioralAnalysis(
        red_flags=[
            BehavioralRedFlag(
                type=BehavioralFlagType.URGENCY,
                severity="high",
                evidence_span="gấp",
                explanation="Tạo áp lực thời gian để giảm xác minh.",
            )
        ],
        behavioral_risk_score=70,
        summary="Có áp lực thời gian.",
    )


def scoring_result(
    risk_score: float = 82.4,
    confidence_score: float = 76.5,
    penalties: list[str] | None = None,
) -> VerificationScoringResult:
    return VerificationScoringResult(
        verification=VerificationResult(
            risk_score=risk_score,
            risk_label=RiskLabel.HIGH_RISK,
            confidence_score=confidence_score,
        ),
        risk_components=RiskComponents(
            evidence_risk=85,
            source_risk=90,
            consensus_risk=88,
            context_risk=75,
            behavioral_risk=70,
        ),
        confidence_components=ConfidenceComponents(
            evidence_coverage=100,
            source_quality=95,
            expert_agreement=80,
            data_completeness=100,
        ),
        confidence_penalties=penalties or [],
    )


def completed_status() -> EvidenceSearchStatus:
    return EvidenceSearchStatus(
        provider="mock",
        mode=EvidenceSearchMode.MOCK,
        operation_status=EvidenceOperationStatus.COMPLETED,
        success=True,
        queries_attempted=1,
        results_returned=1,
        errors=[],
    )


def partial_status() -> EvidenceSearchStatus:
    return EvidenceSearchStatus(
        provider="mock",
        mode=EvidenceSearchMode.FAILED,
        operation_status=EvidenceOperationStatus.PARTIAL,
        success=False,
        queries_attempted=1,
        results_returned=0,
        errors=["Search timeout"],
    )


def test_completed_investigation_report_preserves_scores_and_markdown_sections() -> None:
    text = "Tài khoản sẽ bị khóa nếu không cung cấp OTP gấp."
    judge = judge_findings(
        text=text,
        evidence=evidence_items(),
        expert_assessments=expert_assessments(),
    )
    scoring = scoring_result()
    safety = generate_safety_advice(
        verification=scoring.verification,
        judge=judge,
        behavioral_analysis=behavioral(),
    )

    report = generate_report(
        ReportInput(
            status=InvestigationStatus.COMPLETED,
            verification_scoring=scoring,
            judge=judge,
            evidence=evidence_items(),
            expert_assessments=expert_assessments(),
            behavioral_analysis=behavioral(),
            safety_advice=safety,
            evidence_status=completed_status(),
        )
    )

    assert report.risk_score == 82.4
    assert report.confidence_score == 76.5
    assert "chắc chắn là lừa đảo" not in report.markdown.lower()
    assert "tư vấn pháp lý" in " ".join(report.limitations)
    for heading in [
        "## Kết luận",
        "## Vì sao",
        "## Bằng chứng",
        "## Đồng thuận chuyên gia",
        "## Dấu hiệu hành vi",
        "## Hành động khuyến nghị",
        "## Giới hạn",
    ]:
        assert heading in report.markdown
    assert "Không cung cấp OTP" in " ".join(report.actions)


def test_partial_investigation_report_includes_limitations_and_no_pdf_output() -> None:
    text = "Tin nhắn yêu cầu xác minh tài khoản."
    judge = judge_findings(text=text, evidence=[], expert_assessments=[])
    scoring = scoring_result(
        risk_score=35,
        confidence_score=28,
        penalties=["Search unavailable: -20"],
    )
    safety = generate_safety_advice(
        verification=scoring.verification,
        judge=judge,
        behavioral_analysis=None,
    )

    report = generate_report(
        ReportInput(
            status=InvestigationStatus.PARTIAL,
            verification_scoring=scoring,
            judge=judge,
            evidence=[],
            expert_assessments=[],
            behavioral_analysis=None,
            safety_advice=safety,
            evidence_status=partial_status(),
        )
    )

    assert report.status is InvestigationStatus.PARTIAL
    assert report.risk_score == 35
    assert report.confidence_score == 28
    assert "Kết quả một phần" in report.conclusion
    assert "Tìm kiếm bằng chứng bị thiếu hoặc lỗi" in " ".join(report.limitations)
    assert "pdf" not in report.model_dump_json().lower()
    assert "Chưa có bằng chứng ngoài được chuẩn hóa." in report.markdown
