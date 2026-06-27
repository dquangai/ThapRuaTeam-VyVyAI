from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel, ConfigDict, Field

from app.evidence import EvidenceOperationStatus, EvidenceSearchStatus
from app.models import EvidenceItem, RiskLabel, VerificationResult
from app.nodes.behavioral import BehavioralAnalysis
from app.nodes.experts import ExpertAssessment
from app.nodes.judge import FindingBasis, JudgeResult


class RiskComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_risk: float = Field(ge=0, le=100)
    source_risk: float = Field(ge=0, le=100)
    consensus_risk: float = Field(ge=0, le=100)
    context_risk: float = Field(ge=0, le=100)
    behavioral_risk: float = Field(ge=0, le=100)


class ConfidenceComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_coverage: float = Field(ge=0, le=100)
    source_quality: float = Field(ge=0, le=100)
    expert_agreement: float = Field(ge=0, le=100)
    data_completeness: float = Field(ge=0, le=100)


class VerificationScoringResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification: VerificationResult
    risk_components: RiskComponents
    confidence_components: ConfidenceComponents
    confidence_penalties: list[str] = Field(default_factory=list)


def score_verification(
    *,
    judge: JudgeResult,
    evidence: list[EvidenceItem],
    expert_assessments: list[ExpertAssessment],
    behavioral_analysis: BehavioralAnalysis | None,
    evidence_status: EvidenceSearchStatus | None = None,
    text: str | None = None,
) -> VerificationScoringResult:
    risk_components = RiskComponents(
        evidence_risk=_evidence_risk(judge),
        source_risk=_source_risk(judge, evidence),
        consensus_risk=judge.consensus_score,
        context_risk=_context_risk(judge, text=text),
        behavioral_risk=behavioral_analysis.behavioral_risk_score
        if behavioral_analysis is not None
        else 0,
    )
    confidence_components = ConfidenceComponents(
        evidence_coverage=_evidence_coverage(judge, evidence),
        source_quality=_source_quality(judge, evidence),
        expert_agreement=_expert_agreement(expert_assessments),
        data_completeness=_data_completeness(
            judge=judge,
            evidence=evidence,
            expert_assessments=expert_assessments,
            behavioral_analysis=behavioral_analysis,
        ),
    )
    confidence_score, penalties = calculate_confidence_score(
        confidence_components=confidence_components,
        evidence=evidence,
        expert_assessments=expert_assessments,
        judge=judge,
        evidence_status=evidence_status,
    )
    risk_score = calculate_risk_score(risk_components)

    return VerificationScoringResult(
        verification=VerificationResult(
            risk_score=risk_score,
            risk_label=_risk_label(risk_score),
            confidence_score=confidence_score,
        ),
        risk_components=risk_components,
        confidence_components=confidence_components,
        confidence_penalties=penalties,
    )


def calculate_risk_score(components: RiskComponents) -> float:
    score = (
        0.35 * components.evidence_risk
        + 0.25 * components.source_risk
        + 0.20 * components.consensus_risk
        + 0.10 * components.context_risk
        + 0.10 * components.behavioral_risk
    )
    score = max(score, _context_safety_floor(components))
    return round(_clamp(score, 0, 100), 1)


def calculate_confidence_score(
    *,
    confidence_components: ConfidenceComponents,
    evidence: list[EvidenceItem],
    expert_assessments: list[ExpertAssessment],
    judge: JudgeResult,
    evidence_status: EvidenceSearchStatus | None = None,
) -> tuple[float, list[str]]:
    score = (
        0.30 * confidence_components.evidence_coverage
        + 0.25 * confidence_components.source_quality
        + 0.25 * confidence_components.expert_agreement
        + 0.20 * confidence_components.data_completeness
    )
    penalties: list[str] = []

    if evidence_status is not None and (
        not evidence_status.success
        or evidence_status.operation_status
        in {EvidenceOperationStatus.PARTIAL, EvidenceOperationStatus.DISABLED}
    ):
        score -= 20
        penalties.append("Search unavailable or partial: -20")

    failed_experts = [
        assessment
        for assessment in expert_assessments
        if assessment.confidence == 0 or assessment.warnings
    ]
    if len(failed_experts) > 1:
        score -= 15
        penalties.append("More than one expert failed: -15")

    if not any(item.credibility_score >= 80 for item in evidence):
        score -= 10
        penalties.append("No official or high-quality source: -10")

    if not judge.supported_findings:
        score -= 10
        penalties.append("Input too vague or no supported findings: -10")

    return round(_clamp(score, 0, 100), 1), penalties


def _evidence_risk(judge: JudgeResult) -> float:
    scores = [
        finding.risk_score
        for finding in judge.supported_findings
        if finding.basis is FindingBasis.EVIDENCE
    ]
    return _average(scores)


def _source_risk(judge: JudgeResult, evidence: list[EvidenceItem]) -> float:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    cited_items = [
        evidence_by_id[evidence_id]
        for finding in judge.supported_findings
        for evidence_id in finding.evidence_ids
        if evidence_id in evidence_by_id
    ]
    if not cited_items:
        return 0
    return round(
        _average(
            [
                (item.credibility_score * item.relevance_score) / 100
                for item in cited_items
            ]
        ),
        1,
    )


def _context_risk(judge: JudgeResult, *, text: str | None = None) -> float:
    scores = [
        finding.risk_score
        for finding in judge.supported_findings
        if finding.basis is FindingBasis.INPUT_TEXT
    ]
    context_text = " ".join(
        item
        for finding in judge.supported_findings
        for item in [finding.statement, finding.input_text_span or ""]
        if item
    )
    if text:
        context_text = f"{text} {context_text}"
    return max(_average(scores), _text_context_risk(context_text))


def _evidence_coverage(judge: JudgeResult, evidence: list[EvidenceItem]) -> float:
    if not evidence:
        return 0
    cited_ids = {
        evidence_id
        for finding in judge.supported_findings
        for evidence_id in finding.evidence_ids
    }
    return round(_clamp((len(cited_ids) / min(len(evidence), 3)) * 100, 0, 100), 1)


def _source_quality(judge: JudgeResult, evidence: list[EvidenceItem]) -> float:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    cited_items = [
        evidence_by_id[evidence_id]
        for finding in judge.supported_findings
        for evidence_id in finding.evidence_ids
        if evidence_id in evidence_by_id
    ]
    if not cited_items:
        return 0
    return _average([item.credibility_score for item in cited_items])


def _expert_agreement(expert_assessments: list[ExpertAssessment]) -> float:
    usable_scores = [
        assessment.score
        for assessment in expert_assessments
        if assessment.confidence > 0 and not assessment.warnings
    ]
    if not usable_scores:
        return 0
    if len(usable_scores) == 1:
        return 50
    return round(_clamp(100 - (max(usable_scores) - min(usable_scores)), 0, 100), 1)


def _data_completeness(
    *,
    judge: JudgeResult,
    evidence: list[EvidenceItem],
    expert_assessments: list[ExpertAssessment],
    behavioral_analysis: BehavioralAnalysis | None,
) -> float:
    checks = [
        bool(evidence),
        bool(judge.supported_findings),
        len(expert_assessments) >= 4,
        behavioral_analysis is not None,
    ]
    return round((sum(checks) / len(checks)) * 100, 1)


def _risk_label(score: float) -> RiskLabel:
    if score >= 90:
        return RiskLabel.CRITICAL
    if score >= 75:
        return RiskLabel.HIGH_RISK
    if score >= 50:
        return RiskLabel.SUSPICIOUS
    if score >= 25:
        return RiskLabel.UNCERTAIN
    return RiskLabel.LOW


def _context_safety_floor(components: RiskComponents) -> float:
    """Prevent strong text-only danger signs from being mislabeled as low risk.

    External evidence controls confidence. Risk must still reflect obvious unsafe
    content such as OTP requests, urgent money transfer, or guaranteed returns.
    """

    floor = 0.0
    if components.context_risk >= 85:
        floor = 65
    elif components.context_risk >= 75:
        floor = 55
    elif components.context_risk >= 65:
        floor = 45

    if components.context_risk >= 75 and components.consensus_risk >= 60:
        floor = max(floor, 70)
    if components.context_risk >= 75 and components.behavioral_risk >= 60:
        floor = max(floor, 65)
    if components.context_risk >= 85 and (
        components.consensus_risk >= 75 or components.behavioral_risk >= 75
    ):
        floor = max(floor, 75)
    return floor


def _text_context_risk(text: str) -> float:
    normalized = _normalize_text(text)
    if not normalized:
        return 0

    score = 0.0
    if _has_any(normalized, ["otp", "ma xac thuc", "mat khau", "password", "pin"]):
        score = max(score, 90)
    if _has_any(normalized, ["khoa tai khoan", "dong bang tai khoan", "bi khoa"]):
        score = max(score, 85)
    if _has_any(normalized, ["bat giu", "vu an", "rua tien", "cong an", "toa an"]):
        score = max(score, 90)
    if _has_any(normalized, ["chuyen tien", "chuyen khoan", "nap tien"]) and _has_any(
        normalized,
        ["gap", "ngay", "phut", "hom nay", "trong vong"],
    ):
        score = max(score, 88)
    if _has_any(normalized, ["phi ho so", "dat coc", "phi truoc", "tra phi"]):
        score = max(score, 78)
    if _has_investment_promise(normalized):
        score = max(score, 82)
    if _has_any(normalized, ["hoa hong", "gioi thieu them", "tuyen tuyen duoi"]):
        score = max(score, 72)
    if _has_any(normalized, ["khong duoc noi voi ai", "giu bi mat", "bao mat tuyet doi"]):
        score = max(score, 82)
    if _has_any(normalized, ["anydesk", "teamviewer", "ultraviewer", "dieu khien tu xa"]):
        score = max(score, 86)
    if re.search(r"https?://|bit\.ly|tinyurl|zalo\.me", normalized):
        score = max(score, 62)
    return score


def _has_investment_promise(normalized: str) -> bool:
    return (
        _has_any(normalized, ["loi nhuan", "lai", "cam ket", "bao loi", "dam bao"])
        and _has_any(normalized, ["moi ngay", "%", "phan tram", "coin", "dau tu", "du an"])
    )


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _normalize_text(text: str) -> str:
    chars: list[str] = []
    for char in text:
        if char in {"đ", "Đ"}:
            chars.append("d")
            continue
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.category(part) != "Mn":
                chars.append(part.casefold())
    return " ".join("".join(chars).split())


def _average(values: list[float]) -> float:
    if not values:
        return 0
    return round(sum(values) / len(values), 1)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
