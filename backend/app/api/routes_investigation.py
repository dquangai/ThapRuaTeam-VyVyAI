from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.graph import InvestigationGraphDependencies, InvestigationState, build_investigation_graph
from app.models import (
    InvestigationRequest,
    InvestigationResponse,
    InvestigationStatus,
    VerificationResult,
)
from app.services.provider_factory import build_provider_bundle

router = APIRouter(prefix="/api/v1", tags=["investigation"])


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest) -> InvestigationResponse:
    graph = build_graph_for_request()
    state = await graph.ainvoke(request)
    return response_from_state(state)


def build_graph_for_request() -> Any:
    settings = get_settings()
    provider_bundle = build_provider_bundle(settings)

    return build_investigation_graph(
        InvestigationGraphDependencies(
            llm_provider=provider_bundle.llm_provider,
            evidence_adapter=provider_bundle.evidence_adapter,
            expert_provider=provider_bundle.expert_provider,
            judge_provider=provider_bundle.judge_provider,
            report_provider=provider_bundle.report_provider,
            virustotal_provider=provider_bundle.virustotal_provider,
            id_factory=lambda: str(uuid4()),
        )
    )


def response_from_state(state: InvestigationState) -> InvestigationResponse:
    verification = _verification_from_state(state)
    report = (
        state.report.model_dump(mode="json")
        if state.report is not None
        else _failed_report(state)
    )
    warnings = _warnings_from_state(state)

    return InvestigationResponse.model_validate(
        {
            "investigation_id": state.investigation_id,
            "status": state.status,
            "input": {
                "locale": state.locale.value,
                "use_web_search": state.use_web_search,
                "text_length": len(state.input_text),
            },
            "intake": _dump_optional(state.intake),
            "classification": _dump_optional(state.classification),
            "evidence_status": _dump_optional(state.evidence_status),
            "evidence": [item.model_dump(mode="json") for item in state.evidence],
            "experts": [
                assessment.model_dump(mode="json")
                for assessment in state.expert_assessments
            ],
            "behavioral_analysis": _dump_optional(state.behavioral_analysis),
            "judge": _dump_optional(state.judge_result),
            "verification": verification.model_dump(mode="json"),
            "safety_advice": _dump_optional(state.safety_advice),
            "report": report,
            "warnings": warnings,
            "timings_ms": state.timings_ms,
        }
    )


def _verification_from_state(state: InvestigationState) -> VerificationResult:
    if state.verification is not None:
        return state.verification
    return VerificationResult(risk_score=0, risk_label="low", confidence_score=0)


def _failed_report(state: InvestigationState) -> dict[str, object]:
    return {
        "status": state.status.value,
        "conclusion": "Không tạo được báo cáo điều tra đầy đủ.",
        "markdown": (
            "# Báo cáo xác minh VYVY\n\n"
            "## Kết luận\n"
            "Không tạo được báo cáo điều tra đầy đủ.\n"
        ),
        "limitations": [
            "Báo cáo này không phải tư vấn pháp lý.",
            "Không đủ dữ liệu để tạo kết quả xác minh đáng tin cậy.",
        ],
    }


def _warnings_from_state(state: InvestigationState) -> list[str]:
    warnings = list(state.warnings)
    if state.status is InvestigationStatus.FAILED and not warnings:
        warnings.append("Full investigation failed before a complete report could be generated.")
    return warnings


def _dump_optional(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value
