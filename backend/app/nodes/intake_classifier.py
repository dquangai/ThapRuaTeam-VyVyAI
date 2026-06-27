from __future__ import annotations

import logging
import re
import unicodedata
from enum import StrEnum
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.models import Locale
from app.prompts.intake_classifier import (
    build_classifier_prompt,
    build_intake_prompt,
    build_repair_prompt,
)

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class StructuredLLMProvider(Protocol):
    async def structured(self, prompt: str, schema: type[SchemaT]) -> Any: ...


class IntakeDomain(StrEnum):
    BANKING = "banking"
    RECRUITMENT = "recruitment"
    ECOMMERCE = "ecommerce"
    GOVERNMENT = "government"
    INVESTMENT = "investment"
    OTHER = "other"


class IntakeIntent(StrEnum):
    PAYMENT_REQUEST = "payment_request"
    CREDENTIAL_REQUEST = "credential_request"
    ACCOUNT_THREAT = "account_threat"
    OFFER = "offer"
    OTHER = "other"


class EntityType(StrEnum):
    ORGANIZATION = "organization"
    PERSON = "person"
    PHONE = "phone"
    BANK_ACCOUNT = "bank_account"
    DOMAIN = "domain"
    URL = "url"
    AMOUNT = "amount"
    DATE = "date"
    OTHER = "other"


class ScamPatternLabel(StrEnum):
    URGENT_MONEY_TRANSFER = "urgent_money_transfer"
    ACCOUNT_LOCK_THREAT = "account_lock_threat"
    OTP_PASSWORD_REQUEST = "otp_password_request"
    GOVERNMENT_IMPERSONATION = "government_impersonation"
    BANK_IMPERSONATION = "bank_impersonation"
    RECRUITMENT_FEE = "recruitment_fee"
    PRIZE_OR_GIVEAWAY = "prize_or_giveaway"
    INVESTMENT_RETURN_PROMISE = "investment_return_promise"
    FAKE_MARKETPLACE_PAYMENT = "fake_marketplace_payment"
    PHISHING_LINK = "phishing_link"
    REMOTE_CONTROL_APP_REQUEST = "remote_control_app_request"
    ROMANCE_SOCIAL_ENGINEERING = "romance_social_engineering"
    UNKNOWN = "unknown"


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    type: EntityType


class IntakeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    language: Locale
    domain: IntakeDomain
    intent: IntakeIntent
    entities: list[ExtractedEntity]
    claims: list[str]
    search_queries: list[str] = Field(default_factory=list)
    is_ready: bool
    clarification_question: str | None = None


class ScamPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: ScamPatternLabel
    probability: float = Field(ge=0, le=1)
    evidence_spans: list[str]


class ScamPatternClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patterns: list[ScamPattern]
    primary_pattern: ScamPatternLabel
    requires_immediate_warning: bool


async def run_intake(
    text: str,
    locale: Locale,
    provider: StructuredLLMProvider,
) -> IntakeOutput:
    prompt = build_intake_prompt(text=text, locale=locale)
    output = await _call_with_retry(
        provider=provider,
        prompt=prompt,
        schema=IntakeOutput,
        fallback=_fallback_intake(locale),
        node_name="intake",
    )
    return _sanitize_intake(output, text=text, locale=locale)


async def classify_scam_patterns(
    text: str,
    locale: Locale,
    intake: IntakeOutput,
    provider: StructuredLLMProvider,
) -> ScamPatternClassification:
    prompt = build_classifier_prompt(
        text=text,
        intake_summary=intake.summary,
        locale=locale,
    )
    output = await _call_with_retry(
        provider=provider,
        prompt=prompt,
        schema=ScamPatternClassification,
        fallback=_fallback_classification(),
        node_name="classifier",
    )
    return _sanitize_classification(output, text=text)


async def _call_with_retry[ModelT: BaseModel](
    provider: StructuredLLMProvider,
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
                current_prompt = build_repair_prompt(prompt)

    return fallback


def _fallback_intake(locale: Locale) -> IntakeOutput:
    return IntakeOutput(
        summary="Chưa đủ dữ liệu có cấu trúc; cần kiểm tra thủ công.",
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


def _sanitize_intake(output: IntakeOutput, text: str, locale: Locale) -> IntakeOutput:
    entities = _ground_entities(output.entities, text)
    claims = _select_grounded_items(output.claims, text=text, limit=5, max_length=180)
    queries = _sanitize_queries(output.search_queries, text=text, entities=entities, claims=claims)

    return output.model_copy(
        update={
            "language": locale,
            "entities": entities,
            "claims": claims,
            "search_queries": queries,
            "is_ready": output.is_ready and bool(output.summary.strip()),
        }
    )


def _sanitize_classification(
    output: ScamPatternClassification,
    text: str,
) -> ScamPatternClassification:
    patterns: list[ScamPattern] = []
    seen_labels: set[ScamPatternLabel] = set()

    for pattern in output.patterns:
        if pattern.label in seen_labels:
            continue
        spans = _ground_spans(pattern.evidence_spans, text)
        if pattern.label is not ScamPatternLabel.UNKNOWN and not spans:
            continue
        patterns.append(pattern.model_copy(update={"evidence_spans": spans}))
        seen_labels.add(pattern.label)

    if not patterns:
        return _fallback_classification()

    labels = {pattern.label for pattern in patterns}
    primary = output.primary_pattern if output.primary_pattern in labels else patterns[0].label
    requires_warning = output.requires_immediate_warning and primary is not ScamPatternLabel.UNKNOWN

    return ScamPatternClassification(
        patterns=patterns,
        primary_pattern=primary,
        requires_immediate_warning=requires_warning,
    )


def _ground_entities(entities: list[ExtractedEntity], text: str) -> list[ExtractedEntity]:
    grounded: list[ExtractedEntity] = []
    seen: set[tuple[EntityType, str]] = set()

    for entity in entities:
        span = _find_present_span(entity.text, text)
        if span is None:
            continue
        key = (entity.type, _normalize(span))
        if key in seen:
            continue
        seen.add(key)
        grounded.append(entity.model_copy(update={"text": span}))

    return grounded


def _ground_spans(spans: list[str], text: str) -> list[str]:
    grounded: list[str] = []
    seen: set[str] = set()

    for span in spans:
        present_span = _find_present_span(span, text)
        if present_span is None:
            continue
        key = _normalize(present_span)
        if key in seen:
            continue
        seen.add(key)
        grounded.append(present_span)

    return grounded


def _select_grounded_items(
    items: list[str],
    text: str,
    limit: int,
    max_length: int,
) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned = _clean_text_item(item, max_length=max_length)
        if not cleaned or not _has_meaningful_overlap(cleaned, text):
            continue
        key = _normalize(cleaned)
        if key in seen:
            continue
        seen.add(key)
        selected.append(cleaned)
        if len(selected) == limit:
            break

    return selected


def _sanitize_queries(
    queries: list[str],
    text: str,
    entities: list[ExtractedEntity],
    claims: list[str],
) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()

    for query in queries:
        cleaned = _clean_text_item(query, max_length=140)
        if not cleaned or not _query_is_grounded(cleaned, text, entities, claims):
            continue
        _append_unique(selected, seen, cleaned)
        if len(selected) == 3:
            return selected

    for query in _planned_queries(entities, claims):
        _append_unique(selected, seen, query)
        if len(selected) == 3:
            break

    return selected


def _planned_queries(entities: list[ExtractedEntity], claims: list[str]) -> list[str]:
    queries: list[str] = []
    priority_types = {
        EntityType.URL,
        EntityType.DOMAIN,
        EntityType.PHONE,
        EntityType.BANK_ACCOUNT,
        EntityType.ORGANIZATION,
    }

    for entity in entities:
        if entity.type in priority_types:
            queries.append(f"{entity.text} lừa đảo cảnh báo")
            break

    source_id_types = {
        EntityType.URL,
        EntityType.DOMAIN,
        EntityType.PHONE,
        EntityType.BANK_ACCOUNT,
    }
    for entity in entities:
        if entity.type in source_id_types:
            queries.append(f"{entity.text} cảnh báo lừa đảo")
            break

    if claims:
        queries.append(f"{claims[0]} nguồn chính thức")

    return [_clean_text_item(query, max_length=140) for query in queries]


def _append_unique(items: list[str], seen: set[str], item: str) -> None:
    key = _normalize(item)
    if key in seen:
        return
    seen.add(key)
    items.append(item)


def _query_is_grounded(
    query: str,
    text: str,
    entities: list[ExtractedEntity],
    claims: list[str],
) -> bool:
    normalized_query = _normalize(query)
    if any(_normalize(entity.text) in normalized_query for entity in entities):
        return True
    return any(_has_substantial_overlap(query, claim) for claim in claims)


def _find_present_span(candidate: str, text: str) -> str | None:
    cleaned = candidate.strip()
    if not cleaned:
        return None

    normalized_text, index_map = _normalize_with_index(text)
    normalized_candidate = _normalize(cleaned)
    start = normalized_text.find(normalized_candidate)
    if start == -1:
        return None

    end = start + len(normalized_candidate) - 1
    original_start = index_map[start]
    original_end = index_map[end] + 1
    return text[original_start:original_end]


def _has_meaningful_overlap(candidate: str, text: str) -> bool:
    text_tokens = set(_meaningful_tokens(text))
    return any(token in text_tokens for token in _meaningful_tokens(candidate))


def _has_substantial_overlap(candidate: str, text: str) -> bool:
    text_tokens = set(_meaningful_tokens(text))
    candidate_tokens = set(_meaningful_tokens(candidate))
    return len(candidate_tokens & text_tokens) >= 2


def _meaningful_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]{3,}", _normalize(text))
        if token not in STOPWORDS
    ]


def _clean_text_item(item: str, max_length: int) -> str:
    cleaned = " ".join(item.strip().split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rstrip(" ,.;:")


def _normalize(text: str) -> str:
    chars: list[str] = []
    for char in text:
        if char in {"đ", "Đ"}:
            chars.append("d")
            continue
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.category(part) != "Mn":
                chars.append(part.casefold())
    return "".join(chars)


def _normalize_with_index(text: str) -> tuple[str, list[int]]:
    normalized_chars: list[str] = []
    index_map: list[int] = []

    for index, char in enumerate(text):
        if char in {"đ", "Đ"}:
            normalized_chars.append("d")
            index_map.append(index)
            continue
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.category(part) == "Mn":
                continue
            normalized_chars.append(part.casefold())
            index_map.append(index)

    return "".join(normalized_chars), index_map


STOPWORDS = {
    "ban",
    "bang",
    "cac",
    "can",
    "cho",
    "cua",
    "duoc",
    "hay",
    "khi",
    "khong",
    "mot",
    "nay",
    "nguoi",
    "nhung",
    "qua",
    "tai",
    "thi",
    "toi",
    "trong",
    "voi",
}
