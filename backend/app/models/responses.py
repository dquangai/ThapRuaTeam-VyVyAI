from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Score = Annotated[float, Field(ge=0, le=100)]
NonNegativeMilliseconds = Annotated[int, Field(ge=0)]
NonEmptyString = Annotated[str, StringConstraints(min_length=1)]


class InvestigationStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class RiskLabel(StrEnum):
    LOW = "low"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_id: str
    title: str
    url: str
    source_name: str
    published_at: str | None = None
    snippet: str
    retrieved_at: str
    credibility_score: Score
    relevance_score: Score


class ExpertAssessment(BaseModel):
    """Stable citation fields; task T06 may add typed assessment details."""

    model_config = ConfigDict(extra="allow")

    expert: NonEmptyString
    cited_evidence_ids: list[str]


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    risk_score: Score
    risk_label: RiskLabel
    confidence_score: Score


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    investigation_id: str
    status: InvestigationStatus
    evidence: list[EvidenceItem] = Field(default_factory=list)
    experts: list[ExpertAssessment] = Field(default_factory=list)
    verification: VerificationResult
    report: dict[str, Any]
    warnings: list[str]
    timings_ms: dict[str, NonNegativeMilliseconds]
