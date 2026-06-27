from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high"]


class BehavioralFlagType(StrEnum):
    URGENCY = "urgency"
    FEAR = "fear"
    AUTHORITY_PRESSURE = "authority_pressure"
    FOMO = "fomo"
    SCARCITY = "scarcity"
    SECRECY = "secrecy"
    ISOLATION = "isolation"
    SOCIAL_PROOF_MANIPULATION = "social_proof_manipulation"
    RECIPROCITY = "reciprocity"
    GRADUAL_COMMITMENT = "gradual_commitment"


class BehavioralRedFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: BehavioralFlagType
    severity: Severity
    evidence_span: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class BehavioralAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    red_flags: list[BehavioralRedFlag]
    behavioral_risk_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)


@dataclass(frozen=True)
class BehavioralRule:
    flag_type: BehavioralFlagType
    severity: Severity
    score: int
    explanation: str
    patterns: tuple[re.Pattern[str], ...]


def analyze_behavioral_patterns(text: str) -> BehavioralAnalysis:
    normalized_text, index_map = _normalize_with_index(text)
    red_flags = _dedupe_flags(
        [
            flag
            for rule in BEHAVIORAL_RULES
            if (flag := _match_rule(rule, text, normalized_text, index_map)) is not None
        ]
    )
    score = _score(red_flags)

    return BehavioralAnalysis(
        red_flags=red_flags,
        behavioral_risk_score=score,
        summary=_summary(red_flags, score),
    )


def _match_rule(
    rule: BehavioralRule,
    text: str,
    normalized_text: str,
    index_map: list[int],
) -> BehavioralRedFlag | None:
    best_match: re.Match[str] | None = None
    for pattern in rule.patterns:
        match = pattern.search(normalized_text)
        if match is None:
            continue
        if best_match is None or match.start() < best_match.start():
            best_match = match

    if best_match is None:
        return None

    return BehavioralRedFlag(
        type=rule.flag_type,
        severity=rule.severity,
        evidence_span=_span_from_normalized_match(text, index_map, best_match),
        explanation=rule.explanation,
    )


def _dedupe_flags(flags: list[BehavioralRedFlag]) -> list[BehavioralRedFlag]:
    seen: set[BehavioralFlagType] = set()
    deduped: list[BehavioralRedFlag] = []
    for flag in flags:
        if flag.type in seen:
            continue
        seen.add(flag.type)
        deduped.append(flag)
    return deduped


def _score(flags: list[BehavioralRedFlag]) -> int:
    score_by_severity = {"low": 8, "medium": 13, "high": 18}
    score = sum(score_by_severity[flag.severity] for flag in flags)
    if len(flags) >= 3:
        score += 10
    if len(flags) >= 5:
        score += 10
    return _clamp(score, minimum=0, maximum=100)


def _summary(flags: list[BehavioralRedFlag], score: int) -> str:
    if not flags:
        return "Chưa thấy dấu hiệu thao túng hành vi rõ ràng trong nội dung."
    return (
        f"Phát hiện {len(flags)} dấu hiệu thao túng hành vi; "
        f"điểm rủi ro hành vi là {score}/100."
    )


def _span_from_normalized_match(
    text: str,
    index_map: list[int],
    match: re.Match[str],
) -> str:
    start = index_map[match.start()]
    end = index_map[match.end() - 1] + 1
    return text[start:end].strip()


def _normalize_with_index(text: str) -> tuple[str, list[int]]:
    normalized_chars: list[str] = []
    index_map: list[int] = []

    for index, char in enumerate(text):
        if char in {"đ", "Đ"}:
            normalized_chars.append("d")
            index_map.append(index)
            continue

        decomposed = unicodedata.normalize("NFD", char)
        for part in decomposed:
            if unicodedata.category(part) == "Mn":
                continue
            normalized_chars.append(part.casefold())
            index_map.append(index)

    return "".join(normalized_chars), index_map


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


BEHAVIORAL_RULES = (
    BehavioralRule(
        flag_type=BehavioralFlagType.URGENCY,
        severity="high",
        score=18,
        explanation="Tạo áp lực thời gian để người nhận hành động trước khi kịp xác minh.",
        patterns=(
            _compile(r"\b(?:gap|lap tuc|ngay lap tuc|trong \d+ phut|truoc \d+h)\b"),
            _compile(r"\b(?:phai|can|hay)\b.{0,30}\b(?:lam|xac minh|chuyen|gui)\b.{0,20}\bngay\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.FEAR,
        severity="high",
        score=18,
        explanation="Dùng nỗi sợ mất tài khoản, bị phạt hoặc bị xử lý để thúc ép hành động.",
        patterns=(
            _compile(
                r"\b(?:bi khoa|se bi khoa|dong bang|vo hieu hoa)"
                r"\b.{0,40}\b(?:tai khoan|the|vi|sim)\b"
            ),
            _compile(
                r"\b(?:tai khoan|the|vi|sim)"
                r"\b.{0,40}\b(?:bi khoa|se bi khoa|dong bang|vo hieu hoa)\b"
            ),
            _compile(r"\b(?:bi bat|bat giu|khoi to|tam giam|truy na|bi phat|mat tien)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.AUTHORITY_PRESSURE,
        severity="high",
        score=18,
        explanation="Dựa vào danh nghĩa cơ quan hoặc chức danh để gây áp lực phục tùng.",
        patterns=(
            _compile(r"\b(?:cong an|bo cong an|toa an|vien kiem sat|co quan dieu tra)\b"),
            _compile(r"\b(?:can bo|luat su|nhan vien ngan hang|ngan hang nha nuoc)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.FOMO,
        severity="medium",
        score=13,
        explanation="Gợi cảm giác sợ bỏ lỡ cơ hội để giảm khả năng cân nhắc.",
        patterns=(
            _compile(r"\b(?:co hoi duy nhat|chi hom nay|bo lo|lo mat co hoi)\b"),
            _compile(r"\b(?:uu dai doc quyen|nhanh tay|sap het slot)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.SCARCITY,
        severity="medium",
        score=13,
        explanation="Nhấn mạnh sự khan hiếm hoặc giới hạn giả tạo để thúc ép quyết định.",
        patterns=(
            _compile(r"\b(?:chi con \d+|chi con vai|so luong co han|slot cuoi)\b"),
            _compile(r"\b(?:sap het|het han|gioi han suat|con lai rat it)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.SECRECY,
        severity="high",
        score=18,
        explanation="Yêu cầu giữ bí mật làm giảm khả năng người nhận nhờ người khác kiểm tra.",
        patterns=(
            _compile(r"\b(?:giu bi mat|bao mat tuyet doi|khong noi voi ai|dung ke)\b"),
            _compile(r"\b(?:khong bao cong an|dung bao ngan hang)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.ISOLATION,
        severity="medium",
        score=13,
        explanation="Cô lập người nhận khỏi gia đình, ngân hàng hoặc nguồn tư vấn đáng tin cậy.",
        patterns=(
            _compile(r"\b(?:khong hoi ai|khong bao gia dinh|khong bao nguoi than)\b"),
            _compile(r"\b(?:khong lien he ngan hang|dung goi tong dai|tu minh xu ly)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.SOCIAL_PROOF_MANIPULATION,
        severity="medium",
        score=13,
        explanation="Dùng đám đông hoặc câu chuyện người khác thành công để tạo niềm tin nhanh.",
        patterns=(
            _compile(r"\b(?:nhieu nguoi da|hang nghin nguoi|ai cung|nguoi khac da nhan)\b"),
            _compile(r"\b(?:review|feedback|anh chi trong nhom|nhom dau tu)\b"),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.RECIPROCITY,
        severity="medium",
        score=13,
        explanation="Tạo cảm giác mắc nợ hoặc đã nhận lợi ích nên phải đáp lại.",
        patterns=(
            _compile(r"\b(?:da ho tro mien phi|ho tro mien phi cho ban|da ung cho ban)\b"),
            _compile(
                r"\b(?:qua tang rieng|toi giup ban|minh da giup)"
                r"\b.{0,40}\b(?:nen|hay|chi can)\b"
            ),
        ),
    ),
    BehavioralRule(
        flag_type=BehavioralFlagType.GRADUAL_COMMITMENT,
        severity="medium",
        score=13,
        explanation="Dẫn dắt từ bước nhỏ sang cam kết lớn hơn để người nhận khó dừng lại.",
        patterns=(
            _compile(r"\b(?:nap thu|chuyen truoc|dat coc nho|so tien nho)\b"),
            _compile(r"\b(?:nhiem vu dau tien|buoc tiep theo|lam thu buoc dau|mo khoa nhiem vu)\b"),
        ),
    ),
)
