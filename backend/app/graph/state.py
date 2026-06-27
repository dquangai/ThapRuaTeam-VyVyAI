from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.evidence import EvidenceSearchStatus
from app.models import EvidenceItem, InvestigationStatus, Locale, VerificationResult
from app.nodes.behavioral import BehavioralAnalysis
from app.nodes.experts import ExpertAssessment
from app.nodes.intake_classifier import IntakeOutput, ScamPatternClassification
from app.nodes.judge import JudgeResult
from app.nodes.safety import SafetyAdvice
from app.reporting import InvestigationReport
from app.scoring import VerificationScoringResult


class InvestigationState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    investigation_id: str
    input_text: str
    locale: Locale
    use_web_search: bool
    status: InvestigationStatus = InvestigationStatus.PARTIAL
    intake: IntakeOutput | None = None
    classification: ScamPatternClassification | None = None
    search_queries: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_status: EvidenceSearchStatus | None = None
    expert_assessments: list[ExpertAssessment] = Field(default_factory=list)
    behavioral_analysis: BehavioralAnalysis | None = None
    judge_result: JudgeResult | None = None
    verification: VerificationResult | None = None
    verification_scoring: VerificationScoringResult | None = None
    safety_advice: SafetyAdvice | None = None
    report: InvestigationReport | None = None
    warnings: list[str] = Field(default_factory=list)
    timings_ms: dict[str, int] = Field(default_factory=dict)
    stage_sequence: list[str] = Field(default_factory=list)
