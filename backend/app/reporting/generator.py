from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.evidence import EvidenceOperationStatus, EvidenceSearchStatus
from app.models import EvidenceItem, InvestigationStatus, VerificationResult
from app.nodes.behavioral import BehavioralAnalysis, BehavioralRedFlag
from app.nodes.experts import ExpertAssessment
from app.nodes.judge import JudgeResult, SupportedFinding
from app.nodes.safety import SafetyAdvice
from app.scoring import VerificationScoringResult


class EvidenceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    title: str
    url: str
    source_name: str
    published_at: str | None = None
    snippet: str
    credibility_score: float = Field(ge=0, le=100)
    relevance_score: float = Field(ge=0, le=100)


class ExpertConsensusReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consensus_score: float = Field(ge=0, le=100)
    consensus_label: str
    supported_findings: list[str]
    disagreements: list[str]
    missing_evidence: list[str]


class InvestigationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InvestigationStatus
    conclusion: str
    risk_score: float = Field(ge=0, le=100)
    risk_label: str
    confidence_score: float = Field(ge=0, le=100)
    why: list[str]
    evidence: list[EvidenceSummary]
    expert_consensus: ExpertConsensusReport
    behavioral_red_flags: list[BehavioralRedFlag]
    actions: list[str]
    limitations: list[str]
    markdown: str


class ReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InvestigationStatus
    verification_scoring: VerificationScoringResult
    judge: JudgeResult
    evidence: list[EvidenceItem]
    expert_assessments: list[ExpertAssessment]
    behavioral_analysis: BehavioralAnalysis | None = None
    safety_advice: SafetyAdvice
    evidence_status: EvidenceSearchStatus | None = None


def generate_report(report_input: ReportInput) -> InvestigationReport:
    verification = report_input.verification_scoring.verification
    report = InvestigationReport(
        status=report_input.status,
        conclusion=_conclusion(verification, report_input.status),
        risk_score=verification.risk_score,
        risk_label=verification.risk_label.value,
        confidence_score=verification.confidence_score,
        why=_top_reasons(report_input.judge.supported_findings),
        evidence=[_evidence_summary(item) for item in report_input.evidence],
        expert_consensus=_expert_consensus(report_input.judge),
        behavioral_red_flags=report_input.behavioral_analysis.red_flags
        if report_input.behavioral_analysis is not None
        else [],
        actions=report_input.safety_advice.actions,
        limitations=_limitations(report_input),
        markdown="",
    )
    return report.model_copy(update={"markdown": _to_markdown(report)})


def _conclusion(verification: VerificationResult, status: InvestigationStatus) -> str:
    prefix = "Kết quả một phần: " if status is InvestigationStatus.PARTIAL else ""
    if verification.risk_score >= 75:
        return (
            f"{prefix}Nội dung có nhiều dấu hiệu nguy cơ cao. "
            "Chưa đủ cơ sở để kết luận chắc chắn, nên cần xác minh độc lập."
        )
    if verification.risk_score >= 50:
        return (
            f"{prefix}Nội dung có một số dấu hiệu đáng nghi. "
            "Không nên hành động trước khi kiểm tra qua kênh chính thức."
        )
    if verification.risk_score >= 25:
        return (
            f"{prefix}Nội dung chưa đủ rõ ràng; có vài dấu hiệu cần thận trọng."
        )
    return f"{prefix}Chưa thấy dấu hiệu nguy cơ cao trong dữ liệu hiện có."


def _top_reasons(findings: list[SupportedFinding]) -> list[str]:
    if not findings:
        return ["Chưa có phát hiện được hỗ trợ đủ mạnh từ dữ liệu hiện có."]
    return [finding.statement for finding in findings[:5]]


def _evidence_summary(item: EvidenceItem) -> EvidenceSummary:
    return EvidenceSummary(
        evidence_id=item.evidence_id,
        title=item.title,
        url=item.url,
        source_name=item.source_name,
        published_at=item.published_at,
        snippet=item.snippet,
        credibility_score=item.credibility_score,
        relevance_score=item.relevance_score,
    )


def _expert_consensus(judge: JudgeResult) -> ExpertConsensusReport:
    return ExpertConsensusReport(
        consensus_score=judge.consensus_score,
        consensus_label=judge.consensus_label.value,
        supported_findings=[finding.statement for finding in judge.supported_findings],
        disagreements=[disagreement.summary for disagreement in judge.disagreements],
        missing_evidence=judge.missing_evidence,
    )


def _limitations(report_input: ReportInput) -> list[str]:
    limitations = [
        "Báo cáo này không phải tư vấn pháp lý và không kết luận cá nhân/tổ chức là tội phạm.",
        "Kết quả phản ánh dữ liệu đầu vào và bằng chứng đã thu thập tại thời điểm kiểm tra.",
    ]
    if report_input.status is InvestigationStatus.PARTIAL:
        limitations.append(
            "Một số bước xác minh chưa hoàn tất nên kết quả cần được xem là một phần."
        )
    if report_input.evidence_status is not None and (
        not report_input.evidence_status.success
        or report_input.evidence_status.operation_status
        in {EvidenceOperationStatus.PARTIAL, EvidenceOperationStatus.DISABLED}
    ):
        limitations.append("Tìm kiếm bằng chứng bị thiếu hoặc lỗi, làm giảm độ tin cậy.")
    if report_input.verification_scoring.confidence_penalties:
        limitations.extend(report_input.verification_scoring.confidence_penalties)
    if report_input.safety_advice.warnings:
        limitations.extend(report_input.safety_advice.warnings)
    return _dedupe(limitations)


def _to_markdown(report: InvestigationReport) -> str:
    lines = [
        "# Báo cáo xác minh VYVY",
        "",
        "## Kết luận",
        report.conclusion,
        "",
        "## Điểm đánh giá",
        f"- Risk score: {report.risk_score}",
        f"- Risk label: {report.risk_label}",
        f"- Confidence score: {report.confidence_score}",
        "",
        "## Vì sao",
        *_bullet_lines(report.why),
        "",
        "## Bằng chứng",
        *_evidence_lines(report.evidence),
        "",
        "## Đồng thuận chuyên gia",
        f"- Consensus score: {report.expert_consensus.consensus_score}",
        f"- Consensus label: {report.expert_consensus.consensus_label}",
        *_optional_section("Supported findings", report.expert_consensus.supported_findings),
        *_optional_section("Disagreements", report.expert_consensus.disagreements),
        *_optional_section("Missing evidence", report.expert_consensus.missing_evidence),
        "",
        "## Dấu hiệu hành vi",
        *_behavioral_lines(report.behavioral_red_flags),
        "",
        "## Hành động khuyến nghị",
        *_bullet_lines(report.actions),
        "",
        "## Giới hạn",
        *_bullet_lines(report.limitations),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- Không có dữ liệu."]


def _evidence_lines(evidence: list[EvidenceSummary]) -> list[str]:
    if not evidence:
        return ["- Chưa có bằng chứng ngoài được chuẩn hóa."]
    return [
        (
            f"- [{item.evidence_id}] {item.title} — {item.source_name}; "
            f"credibility={item.credibility_score}, relevance={item.relevance_score}. "
            f"URL: {item.url}"
        )
        for item in evidence
    ]


def _behavioral_lines(flags: list[BehavioralRedFlag]) -> list[str]:
    if not flags:
        return ["- Chưa thấy dấu hiệu thao túng hành vi rõ ràng."]
    return [
        f"- {flag.type.value} ({flag.severity}): “{flag.evidence_span}” — {flag.explanation}"
        for flag in flags
    ]


def _optional_section(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"- {title}:"] + [f"  - {item}" for item in items]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped
