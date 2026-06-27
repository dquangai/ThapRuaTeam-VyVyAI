from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.models import EvidenceItem
from app.nodes.experts import ExpertAssessment, ExpertRole, ReasonBasis


class ConsensusLabel(StrEnum):
    SAFE = "safe"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"


class FindingBasis(StrEnum):
    EVIDENCE = "evidence"
    INPUT_TEXT = "input_text"


class SupportedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    expert: ExpertRole
    statement: str
    basis: FindingBasis
    evidence_ids: list[str] = Field(default_factory=list)
    input_text_span: str | None = None
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)


class RejectedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expert: ExpertRole
    statement: str
    reason: str
    invalid_evidence_ids: list[str] = Field(default_factory=list)


class ExpertDisagreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    summary: str
    experts: dict[str, str]


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consensus_score: float = Field(ge=0, le=100)
    consensus_label: ConsensusLabel
    supported_findings: list[SupportedFinding]
    rejected_findings: list[RejectedFinding]
    disagreements: list[ExpertDisagreement]
    missing_evidence: list[str]
    reasoning_summary: str


EXPERT_WEIGHTS = {
    ExpertRole.CYBER: 0.30,
    ExpertRole.FINANCIAL: 0.25,
    ExpertRole.OSINT: 0.25,
    ExpertRole.LEGAL_RISK: 0.20,
}


def judge_findings(
    *,
    text: str,
    evidence: list[EvidenceItem],
    expert_assessments: list[ExpertAssessment],
) -> JudgeResult:
    evidence_ids = {item.evidence_id for item in evidence}
    supported: list[SupportedFinding] = []
    rejected: list[RejectedFinding] = []
    missing_evidence: list[str] = []

    for assessment in expert_assessments:
        missing_evidence.extend(assessment.missing_information)
        for reason_index, reason in enumerate(assessment.reasons, start=1):
            finding_id = f"{assessment.expert.value}_{reason_index}"
            invalid_ids = [
                evidence_id
                for evidence_id in reason.evidence_ids
                if evidence_id not in evidence_ids
            ]

            if reason.basis is ReasonBasis.EVIDENCE:
                if invalid_ids:
                    rejected.append(
                        RejectedFinding(
                            expert=assessment.expert,
                            statement=reason.text,
                            reason="Finding cites evidence IDs that are not present.",
                            invalid_evidence_ids=invalid_ids,
                        )
                    )
                    missing_evidence.extend(
                        f"Referenced evidence ID is unavailable: {evidence_id}"
                        for evidence_id in invalid_ids
                    )
                    continue
                if not reason.evidence_ids:
                    rejected.append(
                        RejectedFinding(
                            expert=assessment.expert,
                            statement=reason.text,
                            reason="Evidence-based finding does not cite evidence IDs.",
                            invalid_evidence_ids=[],
                        )
                    )
                    continue
                supported.append(
                    SupportedFinding(
                        finding_id=finding_id,
                        expert=assessment.expert,
                        statement=reason.text,
                        basis=FindingBasis.EVIDENCE,
                        evidence_ids=reason.evidence_ids,
                        input_text_span=None,
                        risk_score=assessment.score,
                        confidence=assessment.confidence,
                    )
                )
                continue

            if reason.input_text_span is not None and reason.input_text_span not in text:
                rejected.append(
                    RejectedFinding(
                        expert=assessment.expert,
                        statement=reason.text,
                        reason="Input-text finding span is not present in the original text.",
                        invalid_evidence_ids=[],
                    )
                )
                continue

            supported.append(
                SupportedFinding(
                    finding_id=finding_id,
                    expert=assessment.expert,
                    statement=reason.text,
                    basis=FindingBasis.INPUT_TEXT,
                    evidence_ids=[],
                    input_text_span=reason.input_text_span,
                    risk_score=assessment.score,
                    confidence=assessment.confidence,
                )
            )

    missing_evidence = _dedupe_text(missing_evidence)
    disagreements = _detect_disagreements(expert_assessments)
    consensus_score = _consensus_score(expert_assessments, supported)

    return JudgeResult(
        consensus_score=consensus_score,
        consensus_label=_consensus_label(consensus_score),
        supported_findings=supported,
        rejected_findings=rejected,
        disagreements=disagreements,
        missing_evidence=missing_evidence,
        reasoning_summary=_reasoning_summary(supported, rejected, disagreements),
    )


def _consensus_score(
    assessments: list[ExpertAssessment],
    supported_findings: list[SupportedFinding],
) -> float:
    supported_roles = {finding.expert for finding in supported_findings}
    weighted_scores = [
        (assessment.score, EXPERT_WEIGHTS[assessment.expert])
        for assessment in assessments
        if assessment.expert in supported_roles and assessment.confidence > 0
    ]
    weight_total = sum(weight for _, weight in weighted_scores)
    if weight_total <= 0:
        return 0
    score = sum(score * weight for score, weight in weighted_scores) / weight_total
    return round(_clamp(score, 0, 100), 1)


def _consensus_label(score: float) -> ConsensusLabel:
    if score >= 75:
        return ConsensusLabel.HIGH_RISK
    if score >= 50:
        return ConsensusLabel.SUSPICIOUS
    if score >= 25:
        return ConsensusLabel.UNCERTAIN
    return ConsensusLabel.SAFE


def _detect_disagreements(assessments: list[ExpertAssessment]) -> list[ExpertDisagreement]:
    verdicts = {assessment.expert.value: assessment.verdict.value for assessment in assessments}
    if len(set(verdicts.values())) <= 1:
        return []

    scores = {
        assessment.expert.value: str(round(assessment.score, 1))
        for assessment in assessments
    }
    return [
        ExpertDisagreement(
            type="expert_verdict",
            summary="Expert verdicts are not fully aligned and should be preserved for review.",
            experts=verdicts,
        ),
        ExpertDisagreement(
            type="expert_score_range",
            summary="Expert risk scores differ across roles.",
            experts=scores,
        ),
    ]


def _reasoning_summary(
    supported: list[SupportedFinding],
    rejected: list[RejectedFinding],
    disagreements: list[ExpertDisagreement],
) -> str:
    return (
        f"Judge accepted {len(supported)} supported findings, rejected {len(rejected)} "
        f"unsupported findings, and preserved {len(disagreements)} disagreement records."
    )


def _dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        cleaned = " ".join(item.strip().split())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
