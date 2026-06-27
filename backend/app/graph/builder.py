from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from inspect import isawaitable
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import ConfigurationError
from app.evidence import (
    EvidenceCollectionResult,
    EvidenceOperationStatus,
    EvidenceSearchAdapter,
    EvidenceSearchMode,
    EvidenceSearchStatus,
)
from app.models import InvestigationRequest, InvestigationStatus, Locale
from app.nodes.behavioral import BehavioralAnalysis, analyze_behavioral_patterns
from app.nodes.experts import (
    ExpertAssessment,
    ExpertGroupResult,
    ExpertLLMProvider,
    ExpertReason,
    ExpertRole,
    ExpertVerdict,
    ReasonBasis,
    run_expert_group,
)
from app.nodes.intake_classifier import (
    EntityType,
    IntakeDomain,
    IntakeIntent,
    IntakeOutput,
    ScamPattern,
    ScamPatternClassification,
    ScamPatternLabel,
    StructuredLLMProvider,
    classify_scam_patterns,
    run_intake,
)
from app.nodes.judge import judge_findings
from app.nodes.safety import generate_safety_advice
from app.reporting import ReportInput, generate_report
from app.scoring import score_verification
from app.services.provider_errors import ProviderError

from .state import InvestigationState

BehavioralAnalyzer = Callable[[str], BehavioralAnalysis | Awaitable[BehavioralAnalysis]]
IdFactory = Callable[[], str]


class JudgeModelReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reasoning_summary: str = Field(min_length=1)
    disagreement_notes: list[str] = Field(default_factory=list)
    unsupported_finding_notes: list[str] = Field(default_factory=list)


class ReportModelNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown_addendum: str = Field(min_length=1, max_length=1200)


class VirusTotalLookupProvider(Protocol):
    async def lookup(self, target: str, target_type: str) -> object | None: ...


@dataclass(frozen=True)
class InvestigationGraphDependencies:
    llm_provider: StructuredLLMProvider
    evidence_adapter: EvidenceSearchAdapter | None = None
    expert_provider: ExpertLLMProvider | None = None
    judge_provider: StructuredLLMProvider | None = None
    report_provider: StructuredLLMProvider | None = None
    virustotal_provider: VirusTotalLookupProvider | None = None
    behavioral_analyzer: BehavioralAnalyzer = analyze_behavioral_patterns
    id_factory: IdFactory = field(default_factory=lambda: lambda: str(uuid4()))


class FullInvestigationGraph:
    def __init__(self, dependencies: InvestigationGraphDependencies) -> None:
        self.dependencies = dependencies

    async def ainvoke(
        self,
        graph_input: InvestigationRequest | InvestigationState | dict[str, object],
    ) -> InvestigationState:
        state = self._initial_state(graph_input)
        total_started_at = perf_counter()
        try:
            await self._run_required_context_stages(state)
            await self._run_optional_enrichment_stage(state)
            await self._run_parallel_context_stages(state)
            await self._run_expert_stage(state)
            await self._run_judge_scoring_safety_report(state)
        except Exception as exc:
            _add_warning(state, f"full_investigation failed: {_safe_error_message(exc)}.")
            state.status = InvestigationStatus.FAILED
        finally:
            state.timings_ms["total"] = _elapsed_ms(total_started_at)

        return state

    def _initial_state(
        self,
        graph_input: InvestigationRequest | InvestigationState | dict[str, object],
    ) -> InvestigationState:
        if isinstance(graph_input, InvestigationState):
            return graph_input

        request = (
            graph_input
            if isinstance(graph_input, InvestigationRequest)
            else InvestigationRequest.model_validate(graph_input)
        )
        return InvestigationState(
            investigation_id=self.dependencies.id_factory(),
            input_text=request.text,
            locale=request.locale,
            use_web_search=request.use_web_search,
        )

    async def _run_required_context_stages(self, state: InvestigationState) -> None:
        try:
            state.intake = await self._time_stage(
                state,
                "intake",
                lambda: run_intake(
                    text=state.input_text,
                    locale=state.locale,
                    provider=self.dependencies.llm_provider,
                ),
            )
        except Exception as exc:
            _add_warning(state, f"intake failed: {_safe_error_message(exc)}; using fallback.")
            state.intake = _fallback_intake(state.locale)

        state.search_queries = state.intake.search_queries

        try:
            state.classification = await self._time_stage(
                state,
                "classification",
                lambda: classify_scam_patterns(
                    text=state.input_text,
                    locale=state.locale,
                    intake=state.intake,
                    provider=self.dependencies.llm_provider,
                ),
            )
        except Exception as exc:
            _add_warning(
                state,
                f"classification failed: {_safe_error_message(exc)}; using fallback.",
            )
            state.classification = _fallback_classification()

    async def _run_optional_enrichment_stage(self, state: InvestigationState) -> None:
        provider = self.dependencies.virustotal_provider
        if provider is None or state.intake is None:
            return

        domain = _first_valid_domain(state.intake)
        if domain is None:
            return

        await self._time_stage(
            state,
            "virustotal_enrichment",
            lambda: self._safe_lookup_virustotal(state, domain),
        )

    async def _run_parallel_context_stages(self, state: InvestigationState) -> None:
        evidence_result, behavioral_analysis = await asyncio.gather(
            self._time_stage(state, "evidence_search", lambda: self._safe_collect_evidence(state)),
            self._time_stage(
                state,
                "behavioral_analysis",
                lambda: self._safe_analyze_behavioral(state),
            ),
        )
        state.evidence_status = evidence_result.evidence_status
        state.evidence = evidence_result.evidence
        state.behavioral_analysis = behavioral_analysis

        if evidence_result.evidence_status.errors:
            for error in evidence_result.evidence_status.errors:
                _add_warning(state, f"evidence_search: {error}")
        if not evidence_result.evidence_status.success:
            _add_warning(state, "evidence_search did not complete successfully.")

    async def _run_expert_stage(self, state: InvestigationState) -> None:
        expert_group = await self._time_stage(
            state,
            "experts",
            lambda: self._safe_run_experts(state),
        )
        state.expert_assessments = expert_group.assessments
        for warning in expert_group.warnings:
            _add_warning(state, f"experts: {warning}")

    async def _run_judge_scoring_safety_report(self, state: InvestigationState) -> None:
        state.judge_result = await self._time_stage(
            state,
            "judge",
            lambda: self._run_judge_stage(state),
        )
        state.verification_scoring = await self._time_stage(
            state,
            "scoring",
            lambda: _as_async(
                score_verification(
                    judge=state.judge_result,
                    evidence=state.evidence,
                    expert_assessments=state.expert_assessments,
                    behavioral_analysis=state.behavioral_analysis,
                    evidence_status=state.evidence_status,
                )
            ),
        )
        state.verification = state.verification_scoring.verification
        state.status = _status_for_report(state)
        state.safety_advice = await self._time_stage(
            state,
            "safety",
            lambda: _as_async(
                generate_safety_advice(
                    verification=state.verification_scoring.verification,
                    judge=state.judge_result,
                    behavioral_analysis=state.behavioral_analysis,
                )
            ),
        )
        state.report = await self._time_stage(
            state,
            "report",
            lambda: self._run_report_stage(state),
        )

    async def _run_judge_stage(self, state: InvestigationState):
        deterministic_judge = judge_findings(
            text=state.input_text,
            evidence=state.evidence,
            expert_assessments=state.expert_assessments,
        )
        provider = self.dependencies.judge_provider
        if provider is None:
            return deterministic_judge

        try:
            review = await provider.structured(
                _judge_review_prompt(state, deterministic_judge.reasoning_summary),
                JudgeModelReview,
            )
            review = JudgeModelReview.model_validate(review)
        except Exception as exc:
            _add_warning(state, f"judge model review failed: {_safe_error_message(exc)}.")
            return deterministic_judge

        return deterministic_judge.model_copy(
            update={"reasoning_summary": review.reasoning_summary}
        )

    async def _run_report_stage(self, state: InvestigationState):
        report = generate_report(
            ReportInput(
                status=state.status,
                verification_scoring=state.verification_scoring,
                judge=state.judge_result,
                evidence=state.evidence,
                expert_assessments=state.expert_assessments,
                behavioral_analysis=state.behavioral_analysis,
                safety_advice=state.safety_advice,
                evidence_status=state.evidence_status,
            )
        )
        provider = self.dependencies.report_provider
        if provider is None:
            return report

        try:
            narrative = await provider.structured(
                _report_narrative_prompt(state),
                ReportModelNarrative,
            )
            narrative = ReportModelNarrative.model_validate(narrative)
        except Exception as exc:
            _add_warning(state, f"report model narrative failed: {_safe_error_message(exc)}.")
            return report

        markdown = (
            report.markdown.rstrip()
            + "\n\n## Tóm tắt bổ sung\n"
            + narrative.markdown_addendum.strip()
            + "\n"
        )
        return report.model_copy(update={"markdown": markdown})

    async def _safe_collect_evidence(self, state: InvestigationState) -> EvidenceCollectionResult:
        if not state.use_web_search:
            return _empty_evidence_result(
                provider="none",
                mode=EvidenceSearchMode.DISABLED,
                status=EvidenceOperationStatus.DISABLED,
                errors=["Evidence search disabled by request."],
            )

        adapter = self.dependencies.evidence_adapter
        if adapter is None:
            return _empty_evidence_result(
                provider="none",
                mode=EvidenceSearchMode.FAILED,
                status=EvidenceOperationStatus.PARTIAL,
                errors=["Evidence search adapter is not configured."],
            )

        try:
            return await adapter.collect(state.search_queries)
        except Exception as exc:
            return _empty_evidence_result(
                provider="unknown",
                mode=EvidenceSearchMode.FAILED,
                status=EvidenceOperationStatus.PARTIAL,
                errors=[f"Evidence search failed: {_safe_error_message(exc)}."],
            )

    async def _safe_lookup_virustotal(self, state: InvestigationState, domain: str) -> None:
        provider = self.dependencies.virustotal_provider
        if provider is None:
            return
        try:
            await provider.lookup(domain, "domain")
        except Exception as exc:
            _add_warning(state, f"virustotal enrichment failed: {_safe_error_message(exc)}.")

    async def _safe_analyze_behavioral(
        self,
        state: InvestigationState,
    ) -> BehavioralAnalysis | None:
        try:
            result = self.dependencies.behavioral_analyzer(state.input_text)
            if isawaitable(result):
                return await result
            return result
        except Exception as exc:
            _add_warning(
                state,
                f"behavioral_analysis failed: {_safe_error_message(exc)}; continuing.",
            )
            return None

    async def _safe_run_experts(self, state: InvestigationState) -> ExpertGroupResult:
        provider = self.dependencies.expert_provider or self.dependencies.llm_provider
        try:
            return await run_expert_group(
                text=state.input_text,
                evidence=state.evidence,
                provider=provider,
            )
        except Exception as exc:
            warning = f"expert group failed: {_safe_error_message(exc)}."
            return ExpertGroupResult(
                assessments=[
                    _fallback_expert_assessment(role=role, warning=warning)
                    for role in ExpertRole
                ],
                warnings=[warning],
            )

    async def _time_stage[ResultT](
        self,
        state: InvestigationState,
        stage_name: str,
        factory: Callable[[], Awaitable[ResultT]],
    ) -> ResultT:
        state.stage_sequence.append(stage_name)
        started_at = perf_counter()
        try:
            return await factory()
        finally:
            state.timings_ms[stage_name] = _elapsed_ms(started_at)


def build_investigation_graph(
    dependencies: InvestigationGraphDependencies,
) -> FullInvestigationGraph:
    return FullInvestigationGraph(dependencies=dependencies)


async def _as_async[ResultT](value: ResultT) -> ResultT:
    return value


def _fallback_intake(locale: Locale) -> IntakeOutput:
    return IntakeOutput(
        summary="Chưa đủ dữ liệu có cấu trúc; tiếp tục kiểm tra ở chế độ một phần.",
        language=locale,
        domain=IntakeDomain.OTHER,
        intent=IntakeIntent.OTHER,
        entities=[],
        claims=[],
        search_queries=[],
        is_ready=False,
        clarification_question="Bạn có thể cung cấp thêm ngữ cảnh hoặc nguồn của nội dung không?",
    )


def _fallback_classification() -> ScamPatternClassification:
    return ScamPatternClassification(
        patterns=[
            ScamPattern(
                label=ScamPatternLabel.UNKNOWN,
                probability=0,
                evidence_spans=[],
            )
        ],
        primary_pattern=ScamPatternLabel.UNKNOWN,
        requires_immediate_warning=False,
    )


def _fallback_expert_assessment(role: ExpertRole, warning: str) -> ExpertAssessment:
    return ExpertAssessment(
        expert=role,
        score=0,
        verdict=ExpertVerdict.UNCERTAIN,
        reasons=[
            ExpertReason(
                text="Không tạo được đánh giá chuyên gia; cần kiểm tra thủ công.",
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


def _empty_evidence_result(
    *,
    provider: str,
    mode: EvidenceSearchMode,
    status: EvidenceOperationStatus,
    errors: list[str],
) -> EvidenceCollectionResult:
    return EvidenceCollectionResult(
        evidence_status=EvidenceSearchStatus(
            provider=provider,
            mode=mode,
            operation_status=status,
            success=False,
            queries_attempted=0,
            results_returned=0,
            errors=errors,
        ),
        evidence=[],
    )


def _status_for_report(state: InvestigationState) -> InvestigationStatus:
    if state.judge_result is None or state.verification_scoring is None:
        return InvestigationStatus.FAILED
    if state.warnings:
        return InvestigationStatus.PARTIAL
    if state.evidence_status is not None and (
        not state.evidence_status.success
        or state.evidence_status.operation_status
        in {EvidenceOperationStatus.PARTIAL, EvidenceOperationStatus.DISABLED}
    ):
        return InvestigationStatus.PARTIAL
    if any(assessment.warnings for assessment in state.expert_assessments):
        return InvestigationStatus.PARTIAL
    return InvestigationStatus.COMPLETED


def _add_warning(state: InvestigationState, warning: str) -> None:
    if warning not in state.warnings:
        state.warnings.append(warning)


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, ProviderError | ConfigurationError):
        return str(exc)
    return exc.__class__.__name__


def _first_valid_domain(intake: IntakeOutput) -> str | None:
    for entity in intake.entities:
        if entity.type is not EntityType.DOMAIN:
            continue
        candidate = entity.text.strip().lower()
        if _DOMAIN_RE.fullmatch(candidate):
            return candidate
    return None


def _judge_review_prompt(state: InvestigationState, deterministic_summary: str) -> str:
    expert_lines = [
        f"- {assessment.expert.value}: verdict={assessment.verdict.value}, "
        f"score={assessment.score}, confidence={assessment.confidence}"
        for assessment in state.expert_assessments
    ]
    return "\n".join(
        [
            "Review the deterministic judge result for concise explanation only.",
            "Do not change numeric scores, evidence IDs, or supported/rejected decisions.",
            "Return only reasoning_summary, disagreement_notes, and unsupported_finding_notes.",
            "",
            f"Deterministic summary: {deterministic_summary}",
            "Expert assessments:",
            *expert_lines,
        ]
    )


def _report_narrative_prompt(state: InvestigationState) -> str:
    verification = state.verification
    risk_score = verification.risk_score if verification is not None else 0
    confidence_score = verification.confidence_score if verification is not None else 0
    risk_label = verification.risk_label.value if verification is not None else "unknown"
    supported_findings = (
        [finding.statement for finding in state.judge_result.supported_findings[:5]]
        if state.judge_result is not None
        else []
    )
    return "\n".join(
        [
            "Write one concise Vietnamese markdown paragraph for a scam-risk report.",
            "Do not change risk_score, confidence_score, evidence IDs, or judge decisions.",
            (
                "Do not accuse anyone definitively. "
                "Use wording like nguy cơ/dấu hiệu/chưa đủ bằng chứng."
            ),
            "",
            f"risk_score={risk_score}",
            f"risk_label={risk_label}",
            f"confidence_score={confidence_score}",
            "Supported findings:",
            *[f"- {finding}" for finding in supported_findings],
        ]
    )


_DOMAIN_RE = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
