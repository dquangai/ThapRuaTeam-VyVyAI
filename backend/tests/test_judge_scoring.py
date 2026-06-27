from app.evidence import (
    EvidenceOperationStatus,
    EvidenceSearchMode,
    EvidenceSearchStatus,
)
from app.models import EvidenceItem, RiskLabel
from app.nodes.behavioral import BehavioralAnalysis, BehavioralFlagType, BehavioralRedFlag
from app.nodes.experts import (
    ExpertAssessment,
    ExpertReason,
    ExpertRole,
    ExpertVerdict,
    ReasonBasis,
)
from app.nodes.judge import ConsensusLabel, FindingBasis, judge_findings
from app.scoring import (
    ConfidenceComponents,
    RiskComponents,
    calculate_confidence_score,
    calculate_risk_score,
    score_verification,
)


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


def expert(
    role: ExpertRole,
    *,
    score: float,
    verdict: ExpertVerdict,
    confidence: float = 80,
    reasons: list[ExpertReason] | None = None,
    missing: list[str] | None = None,
    warnings: list[str] | None = None,
) -> ExpertAssessment:
    return ExpertAssessment(
        expert=role,
        score=score,
        verdict=verdict,
        reasons=reasons
        or [
            ExpertReason(
                text=f"{role.value} supported by evidence.",
                basis=ReasonBasis.EVIDENCE,
                evidence_ids=["ev_bank_001"],
                input_text_span=None,
            )
        ],
        cited_evidence_ids=["ev_bank_001"],
        missing_information=missing or [],
        confidence=confidence,
        warnings=warnings or [],
    )


def behavioral(score: int = 70) -> BehavioralAnalysis:
    return BehavioralAnalysis(
        red_flags=[
            BehavioralRedFlag(
                type=BehavioralFlagType.URGENCY,
                severity="high",
                evidence_span="gấp",
                explanation="Tạo áp lực thời gian.",
            )
        ],
        behavioral_risk_score=score,
        summary="Có dấu hiệu thao túng hành vi.",
    )


def completed_evidence_status() -> EvidenceSearchStatus:
    return EvidenceSearchStatus(
        provider="mock",
        mode=EvidenceSearchMode.MOCK,
        operation_status=EvidenceOperationStatus.COMPLETED,
        success=True,
        queries_attempted=2,
        results_returned=2,
        errors=[],
    )


def partial_evidence_status() -> EvidenceSearchStatus:
    return EvidenceSearchStatus(
        provider="mock",
        mode=EvidenceSearchMode.FAILED,
        operation_status=EvidenceOperationStatus.PARTIAL,
        success=False,
        queries_attempted=1,
        results_returned=0,
        errors=["Search timeout"],
    )


def test_judge_validates_references_rejects_unsupported_and_preserves_disagreements() -> None:
    text = "Tài khoản sẽ bị khóa nếu không cung cấp OTP."
    assessments = [
        expert(ExpertRole.CYBER, score=85, verdict=ExpertVerdict.HIGH_RISK),
        expert(
            ExpertRole.LEGAL_RISK,
            score=20,
            verdict=ExpertVerdict.LOW_RISK,
            reasons=[
                ExpertReason(
                    text="Legal finding cites missing evidence.",
                    basis=ReasonBasis.EVIDENCE,
                    evidence_ids=["ev_missing"],
                    input_text_span=None,
                )
            ],
            missing=["Cần nguồn chính thức về thủ tục khóa tài khoản."],
        ),
        expert(
            ExpertRole.FINANCIAL,
            score=65,
            verdict=ExpertVerdict.SUSPICIOUS,
            reasons=[
                ExpertReason(
                    text="Nội dung yêu cầu hành động với tài khoản.",
                    basis=ReasonBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span="cung cấp OTP",
                )
            ],
        ),
    ]

    result = judge_findings(text=text, evidence=evidence_items(), expert_assessments=assessments)

    assert len(result.supported_findings) == 2
    assert {finding.basis for finding in result.supported_findings} == {
        FindingBasis.EVIDENCE,
        FindingBasis.INPUT_TEXT,
    }
    assert len(result.rejected_findings) == 1
    assert result.rejected_findings[0].invalid_evidence_ids == ["ev_missing"]
    assert result.disagreements
    assert "ev_missing" in " ".join(result.missing_evidence)
    assert result.consensus_label is ConsensusLabel.HIGH_RISK


def test_risk_score_boundary_formula_clamps_and_rounds() -> None:
    assert calculate_risk_score(
        RiskComponents(
            evidence_risk=0,
            source_risk=0,
            consensus_risk=0,
            context_risk=0,
            behavioral_risk=0,
        )
    ) == 0
    assert calculate_risk_score(
        RiskComponents(
            evidence_risk=100,
            source_risk=100,
            consensus_risk=100,
            context_risk=100,
            behavioral_risk=100,
        )
    ) == 100
    assert calculate_risk_score(
        RiskComponents(
            evidence_risk=33.3,
            source_risk=66.6,
            consensus_risk=55.5,
            context_risk=44.4,
            behavioral_risk=77.7,
        )
    ) == 51.6


def test_verification_scoring_uses_code_calculated_risk_and_confidence() -> None:
    text = "Tài khoản sẽ bị khóa nếu không cung cấp OTP."
    assessments = [
        expert(ExpertRole.CYBER, score=90, verdict=ExpertVerdict.HIGH_RISK),
        expert(ExpertRole.FINANCIAL, score=80, verdict=ExpertVerdict.HIGH_RISK),
        expert(ExpertRole.OSINT, score=85, verdict=ExpertVerdict.HIGH_RISK),
        expert(ExpertRole.LEGAL_RISK, score=70, verdict=ExpertVerdict.SUSPICIOUS),
    ]
    judge = judge_findings(text=text, evidence=evidence_items(), expert_assessments=assessments)

    result = score_verification(
        judge=judge,
        evidence=evidence_items(),
        expert_assessments=assessments,
        behavioral_analysis=behavioral(score=70),
        evidence_status=completed_evidence_status(),
    )

    assert result.verification.risk_score == 73.2
    assert result.verification.risk_label is RiskLabel.SUSPICIOUS
    assert result.verification.confidence_score == 78.8
    assert result.confidence_penalties == []


def test_partial_result_search_failure_lowers_confidence_but_keeps_scoring() -> None:
    text = "Tin nhắn mơ hồ cần kiểm tra thêm."
    assessments = [
        expert(
            ExpertRole.CYBER,
            score=0,
            verdict=ExpertVerdict.UNCERTAIN,
            confidence=0,
            warnings=["cyber failed"],
        ),
        expert(
            ExpertRole.FINANCIAL,
            score=0,
            verdict=ExpertVerdict.UNCERTAIN,
            confidence=0,
            warnings=["financial failed"],
        ),
        expert(
            ExpertRole.OSINT,
            score=30,
            verdict=ExpertVerdict.UNCERTAIN,
            confidence=40,
            reasons=[
                ExpertReason(
                    text="Chỉ có dấu hiệu từ nội dung đầu vào.",
                    basis=ReasonBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span=None,
                )
            ],
        ),
    ]
    judge = judge_findings(text=text, evidence=[], expert_assessments=assessments)

    result = score_verification(
        judge=judge,
        evidence=[],
        expert_assessments=assessments,
        behavioral_analysis=None,
        evidence_status=partial_evidence_status(),
    )

    assert result.verification.risk_score >= 0
    assert result.verification.confidence_score == 0
    assert "Search unavailable or partial: -20" in result.confidence_penalties
    assert "More than one expert failed: -15" in result.confidence_penalties
    assert "No official or high-quality source: -10" in result.confidence_penalties


def test_text_only_investment_promise_raises_risk_floor_without_external_evidence() -> None:
    text = (
        "Một người bạn giới thiệu em đầu tư vào dự án coin mới. "
        "Họ cam kết lợi nhuận 3% mỗi ngày. Nếu giới thiệu thêm người tham gia "
        "em sẽ được hoa hồng."
    )
    assessments = [
        expert(
            ExpertRole.FINANCIAL,
            score=20,
            verdict=ExpertVerdict.UNCERTAIN,
            confidence=45,
            reasons=[
                ExpertReason(
                    text="Nội dung có cam kết lợi nhuận cố định mỗi ngày.",
                    basis=ReasonBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span="cam kết lợi nhuận 3% mỗi ngày",
                )
            ],
            missing=["Thiếu bằng chứng ngoài về dự án."],
        ),
        expert(
            ExpertRole.OSINT,
            score=20,
            verdict=ExpertVerdict.UNCERTAIN,
            confidence=45,
            reasons=[
                ExpertReason(
                    text="Có dấu hiệu hoa hồng giới thiệu người tham gia.",
                    basis=ReasonBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span="giới thiệu thêm người tham gia",
                )
            ],
            missing=["Thiếu đăng ký pháp lý hoặc nguồn chính thức."],
        ),
    ]
    judge = judge_findings(text=text, evidence=[], expert_assessments=assessments)

    result = score_verification(
        judge=judge,
        evidence=[],
        expert_assessments=assessments,
        behavioral_analysis=behavioral(score=35),
        evidence_status=partial_evidence_status(),
        text=text,
    )

    assert result.risk_components.context_risk >= 82
    assert result.verification.risk_score >= 55
    assert result.verification.risk_label is RiskLabel.SUSPICIOUS
    assert result.verification.confidence_score < 50
    assert "Search unavailable or partial: -20" in result.confidence_penalties


def test_no_supported_findings_returns_low_risk_and_vague_input_penalty() -> None:
    judge = judge_findings(
        text="Không rõ nội dung.",
        evidence=[],
        expert_assessments=[
            expert(
                ExpertRole.CYBER,
                score=50,
                verdict=ExpertVerdict.UNCERTAIN,
                reasons=[
                    ExpertReason(
                        text="Evidence finding without citation.",
                        basis=ReasonBasis.EVIDENCE,
                        evidence_ids=[],
                        input_text_span=None,
                    )
                ],
            )
        ],
    )

    confidence, penalties = calculate_confidence_score(
        confidence_components=ConfidenceComponents(
            evidence_coverage=0,
            source_quality=0,
            expert_agreement=50,
            data_completeness=25,
        ),
        evidence=[],
        expert_assessments=[],
        judge=judge,
        evidence_status=None,
    )

    assert judge.supported_findings == []
    assert judge.rejected_findings
    assert judge.consensus_score == 0
    assert confidence == 0
    assert "Input too vague or no supported findings: -10" in penalties
