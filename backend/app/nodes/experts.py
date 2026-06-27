from __future__ import annotations

import asyncio
import logging
import re
from enum import StrEnum
from typing import Annotated, Any, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import ConfigurationError
from app.models import EvidenceItem
from app.prompts.experts import build_expert_prompt, build_expert_repair_prompt
from app.services.provider_errors import ProviderError

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)
Score = Annotated[float, Field(ge=0, le=100)]


class ExpertLLMProvider(Protocol):
    async def structured(self, prompt: str, schema: type[SchemaT]) -> Any: ...


class ExpertRole(StrEnum):
    FINANCIAL = "financial"
    LEGAL_RISK = "legal_risk"
    CYBER = "cyber"
    OSINT = "osint"


class ExpertVerdict(StrEnum):
    LOW_RISK = "low_risk"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"


class ReasonBasis(StrEnum):
    EVIDENCE = "evidence"
    INPUT_TEXT = "input_text"


class ExpertReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    basis: ReasonBasis
    evidence_ids: list[str] = Field(default_factory=list)
    input_text_span: str | None = None


class ExpertAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expert: ExpertRole
    score: Score
    verdict: ExpertVerdict
    reasons: list[ExpertReason]
    cited_evidence_ids: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: Score
    warnings: list[str] = Field(default_factory=list)


class ExpertGroupResult(BaseModel):
    assessments: list[ExpertAssessment]
    warnings: list[str] = Field(default_factory=list)


async def run_expert_agent(
    role: ExpertRole,
    text: str,
    evidence: list[EvidenceItem],
    provider: ExpertLLMProvider,
) -> ExpertAssessment:
    evidence_ids = _evidence_id_set(evidence)
    prompt = build_expert_prompt(role=role, text=text, evidence=evidence)
    fallback = _fallback_assessment(role, warning="Expert provider returned no usable output.")
    assessment = await _call_with_retry(
        provider=provider,
        prompt=prompt,
        schema=ExpertAssessment,
        fallback=fallback,
        node_name=f"{role.value}_expert",
    )
    return _sanitize_assessment(assessment, role=role, text=text, evidence_ids=evidence_ids)


async def run_expert_group(
    text: str,
    evidence: list[EvidenceItem],
    provider: ExpertLLMProvider,
) -> ExpertGroupResult:
    tasks = [
        _safe_run_expert(role=role, text=text, evidence=evidence, provider=provider)
        for role in ExpertRole
    ]
    assessments = list(await asyncio.gather(*tasks))
    warnings = [
        warning
        for assessment in assessments
        for warning in assessment.warnings
        if warning
    ]
    return ExpertGroupResult(assessments=assessments, warnings=warnings)


async def _safe_run_expert(
    role: ExpertRole,
    text: str,
    evidence: list[EvidenceItem],
    provider: ExpertLLMProvider,
) -> ExpertAssessment:
    try:
        return await run_expert_agent(
            role=role,
            text=text,
            evidence=evidence,
            provider=provider,
        )
    except Exception as exc:
        safe_error = _safe_error_message(exc)
        logger.warning("%s expert failed: %s", role.value, safe_error)
        return _fallback_assessment(
            role,
            warning=f"{role.value} expert failed: {safe_error}.",
        )


async def _call_with_retry[ModelT: BaseModel](
    provider: ExpertLLMProvider,
    prompt: str,
    schema: type[ModelT],
    fallback: ModelT,
    node_name: str,
) -> ModelT:
    current_prompt = prompt
    for attempt in range(2):
        try:
            raw = await provider.structured(current_prompt, schema)
            return schema.model_validate(raw)
        except (TypeError, ValueError, ValidationError) as exc:
            logger.warning(
                "%s structured output invalid on attempt %s: %s",
                node_name,
                attempt + 1,
                exc.__class__.__name__,
            )
            if attempt == 0:
                current_prompt = build_expert_repair_prompt(prompt)

    return fallback


def _sanitize_assessment(
    assessment: ExpertAssessment,
    role: ExpertRole,
    text: str,
    evidence_ids: set[str],
) -> ExpertAssessment:
    sanitized_reasons = [
        _sanitize_reason(reason, text=text, evidence_ids=evidence_ids)
        for reason in assessment.reasons
    ]
    sanitized_reasons = [reason for reason in sanitized_reasons if reason.text.strip()]
    if not sanitized_reasons:
        sanitized_reasons = [
            ExpertReason(
                text="Chưa đủ dữ liệu để đưa ra lý do có cấu trúc; dựa trên nội dung đầu vào.",
                basis=ReasonBasis.INPUT_TEXT,
                evidence_ids=[],
                input_text_span=None,
            )
        ]

    cited_ids = _dedupe_ids(
        [
            evidence_id
            for evidence_id in assessment.cited_evidence_ids
            if evidence_id in evidence_ids
        ]
        + [
            evidence_id
            for reason in sanitized_reasons
            for evidence_id in reason.evidence_ids
            if evidence_id in evidence_ids
        ]
    )
    warnings = [_strip_urls(warning) for warning in assessment.warnings]

    return assessment.model_copy(
        update={
            "expert": role,
            "reasons": sanitized_reasons,
            "cited_evidence_ids": cited_ids,
            "missing_information": [
                _strip_urls(item)
                for item in assessment.missing_information
                if _strip_urls(item)
            ],
            "warnings": [warning for warning in warnings if warning],
        }
    )


def _sanitize_reason(reason: ExpertReason, text: str, evidence_ids: set[str]) -> ExpertReason:
    valid_ids = [evidence_id for evidence_id in reason.evidence_ids if evidence_id in evidence_ids]
    reason_text = _strip_urls(reason.text)
    input_span = _ground_input_span(reason.input_text_span, text)

    if reason.basis is ReasonBasis.EVIDENCE and valid_ids:
        return reason.model_copy(
            update={
                "text": reason_text,
                "basis": ReasonBasis.EVIDENCE,
                "evidence_ids": _dedupe_ids(valid_ids),
                "input_text_span": None,
            }
        )

    return reason.model_copy(
        update={
            "text": reason_text,
            "basis": ReasonBasis.INPUT_TEXT,
            "evidence_ids": [],
            "input_text_span": input_span,
        }
    )


def _fallback_assessment(role: ExpertRole, warning: str) -> ExpertAssessment:
    return ExpertAssessment(
        expert=role,
        score=0,
        verdict=ExpertVerdict.UNCERTAIN,
        reasons=[
            ExpertReason(
                text="Không tạo được đánh giá chuyên gia có cấu trúc; cần kiểm tra thủ công.",
                basis=ReasonBasis.INPUT_TEXT,
                evidence_ids=[],
                input_text_span=None,
            )
        ],
        cited_evidence_ids=[],
        missing_information=[f"Đánh giá {role.value} không khả dụng."],
        confidence=0,
        warnings=[warning],
    )


def _evidence_id_set(evidence: list[EvidenceItem]) -> set[str]:
    return {item.evidence_id for item in evidence}


def _dedupe_ids(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for evidence_id in ids:
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        deduped.append(evidence_id)
    return deduped


def _ground_input_span(span: str | None, text: str) -> str | None:
    if span is None:
        return None
    cleaned = _strip_urls(span).strip()
    if not cleaned:
        return None
    return cleaned if cleaned in text else None


def _strip_urls(value: str) -> str:
    return URL_PATTERN.sub("[đường dẫn đã được ẩn]", value).strip()


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, ProviderError | ConfigurationError):
        return str(exc)
    return exc.__class__.__name__


URL_PATTERN = re.compile(r"https?://[^\s<>()]+|www\.[^\s<>()]+", re.IGNORECASE)
