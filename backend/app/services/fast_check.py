from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["medium", "high", "critical"]


class FastCheckRiskBand(StrEnum):
    LOW = "low"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class FastCheckFlag(BaseModel):
    code: str
    label: str
    severity: Severity
    evidence_span: str


class FastCheckResponse(BaseModel):
    request_id: str
    risk_band: FastCheckRiskBand
    score: int = Field(ge=0, le=100)
    triggered_flags: list[FastCheckFlag]
    message: str
    immediate_actions: list[str]
    latency_ms: int = Field(ge=0)


@dataclass(frozen=True)
class Rule:
    code: str
    label: str
    severity: Severity
    score: int
    patterns: tuple[re.Pattern[str], ...]


SHORTENED_DOMAINS = frozenset(
    {
        "bit.ly",
        "bitly.com",
        "bom.so",
        "cutt.ly",
        "goo.gl",
        "is.gd",
        "ow.ly",
        "rebrand.ly",
        "s.id",
        "shorturl.at",
        "t.co",
        "tiny.cc",
        "tinyurl.com",
    }
)

URL_PATTERN = re.compile(
    r"(?P<url>https?://[^\s<>()]+|www\.[^\s<>()]+)",
    re.IGNORECASE,
)


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)


RULES = (
    Rule(
        code="OTP_REQUEST",
        label="Yêu cầu cung cấp OTP, mật khẩu hoặc PIN",
        severity="critical",
        score=45,
        patterns=(
            _compile(
                r"\b(?:cung cap|gui|nhap|xac nhan|chia se|doc|cho biet|tiet lo|dien|cap nhat)"
                r"\b.{0,40}\b(?:otp|mat khau|password|ma pin|pin|ma xac thuc|"
                r"ma dang nhap|ma bao mat)\b"
            ),
            _compile(
                r"\b(?:otp|mat khau|password|ma pin|pin|ma xac thuc|ma dang nhap|ma bao mat)"
                r"\b.{0,40}\b(?:gui lai|cung cap|de xac minh|de xac nhan|cho chung toi|cho toi)\b"
            ),
        ),
    ),
    Rule(
        code="URGENT_MONEY_TRANSFER",
        label="Yêu cầu chuyển tiền gấp",
        severity="high",
        score=35,
        patterns=(
            _compile(
                r"\b(?:chuyen tien|chuyen khoan|ck|nap tien|gui tien|thanh toan)"
                r"\b.{0,80}\b(?:gap|ngay|lap tuc|trong \d+ phut|truoc \d+h|neu khong|khong se)\b"
            ),
            _compile(
                r"\b(?:gap|ngay|lap tuc|trong \d+ phut|truoc \d+h)"
                r"\b.{0,80}\b(?:chuyen tien|chuyen khoan|ck|nap tien|gui tien|thanh toan)\b"
            ),
            _compile(r"\bcan tien gap\b"),
        ),
    ),
    Rule(
        code="ACCOUNT_LOCK_OR_ARREST_THREAT",
        label="Đe dọa khóa tài khoản hoặc bắt giữ",
        severity="high",
        score=35,
        patterns=(
            _compile(
                r"\b(?:tai khoan|the|vi|sim)"
                r"\b.{0,50}\b(?:bi khoa|se bi khoa|tam khoa|dong bang|vo hieu hoa)\b"
            ),
            _compile(
                r"\b(?:bi khoa|se bi khoa|tam khoa|dong bang|vo hieu hoa)"
                r"\b.{0,50}\b(?:tai khoan|the|vi|sim)\b"
            ),
            _compile(
                r"\b(?:cong an|toa an|vien kiem sat|co quan dieu tra)"
                r"\b.{0,80}\b(?:bat|bat giu|truy na|khoi to|tam giam|lenh bat)\b"
            ),
            _compile(r"\b(?:se bi|sap bi)\b.{0,30}\b(?:bat|khoi to|tam giam)\b"),
        ),
    ),
    Rule(
        code="REMOTE_CONTROL_APP_REQUEST",
        label="Yêu cầu cài ứng dụng điều khiển từ xa",
        severity="critical",
        score=45,
        patterns=(
            _compile(
                r"\b(?:cai|tai|mo|cho phep|cap quyen|ket noi)"
                r"\b.{0,60}\b(?:anydesk|teamviewer|ultraviewer|rustdesk|quicksupport|"
                r"dieu khien tu xa|chia se man hinh)\b"
            ),
            _compile(
                r"\b(?:anydesk|teamviewer|ultraviewer|rustdesk|quicksupport)"
                r"\b.{0,60}\b(?:ho tro|cap quyen|ket noi|dieu khien|chia se man hinh)\b"
            ),
        ),
    ),
    Rule(
        code="UPFRONT_FEE",
        label="Yêu cầu nộp phí trước cho tuyển dụng hoặc nhận thưởng",
        severity="high",
        score=35,
        patterns=(
            _compile(
                r"\b(?:tuyen dung|viec lam|cong tac vien|ctv|don hang|lam online|"
                r"trung thuong|nhan qua|giai thuong|qua tang)"
                r"\b.{0,120}\b(?:phi|dat coc|nop tien|chuyen khoan|ung tien|thue|"
                r"phi ho so|phi van chuyen|xac minh tai khoan)\b"
            ),
            _compile(
                r"\b(?:phi|dat coc|nop tien|chuyen khoan|ung tien|thue|phi ho so|"
                r"phi van chuyen|xac minh tai khoan)"
                r"\b.{0,120}\b(?:tuyen dung|viec lam|cong tac vien|ctv|don hang|"
                r"lam online|trung thuong|nhan qua|giai thuong|qua tang)\b"
            ),
        ),
    ),
    Rule(
        code="GUARANTEED_INVESTMENT_RETURN",
        label="Cam kết lợi nhuận đầu tư chắc chắn",
        severity="high",
        score=30,
        patterns=(
            _compile(
                r"\b(?:dau tu|chung khoan|crypto|forex|tien ao|coin|co phieu)"
                r"\b.{0,120}\b(?:cam ket|dam bao|bao dam|chac chan|khong lo)"
                r"\b.{0,80}\b(?:loi nhuan|lai|lai suat|thu nhap|\d+%)\b"
            ),
            _compile(
                r"\b(?:cam ket|dam bao|bao dam|chac chan|khong lo)"
                r"\b.{0,80}\b(?:loi nhuan|lai|lai suat|thu nhap|\d+%)"
                r"\b.{0,120}\b(?:dau tu|chung khoan|crypto|forex|tien ao|coin|co phieu)\b"
            ),
        ),
    ),
    Rule(
        code="SECRECY_REQUEST",
        label="Yêu cầu giữ bí mật hoặc không báo cho người khác",
        severity="medium",
        score=20,
        patterns=(
            _compile(r"\bgiu bi mat\b"),
            _compile(r"\bkhong noi voi ai\b"),
            _compile(r"\bdung ke\b"),
            _compile(r"\bkhong bao cong an\b"),
            _compile(r"\bdung bao ngan hang\b"),
            _compile(r"\bchi minh ban biet\b"),
            _compile(r"\bbao mat tuyet doi\b"),
        ),
    ),
)

NEGATED_UPFRONT_FEE_PATTERNS = (
    _compile(r"\bkhong thu phi\b"),
    _compile(r"\bmien phi\b"),
    _compile(r"\bkhong mat phi\b"),
    _compile(r"\bkhong can dat coc\b"),
)

SUSPICIOUS_LINK_CONTEXT = _compile(
    r"\b(?:bam vao|nhan vao|truy cap|mo link|vao link|xac minh|cap nhat|dang nhap|"
    r"nhan qua|nhan thuong)\b"
)


def analyze_fast_check(text: str, request_id: str, latency_ms: int = 0) -> FastCheckResponse:
    normalized_text, index_map = _normalize_with_index(text)
    triggered_flags = _detect_rule_flags(text, normalized_text, index_map)
    link_flag = _detect_suspicious_link(text, normalized_text, index_map)
    if link_flag is not None:
        triggered_flags.append(link_flag)

    triggered_flags = _deduplicate_flags(triggered_flags)
    score = _score(triggered_flags)

    return FastCheckResponse(
        request_id=request_id,
        risk_band=_risk_band(score),
        score=score,
        triggered_flags=triggered_flags,
        message=_message_for_score(score),
        immediate_actions=_immediate_actions(triggered_flags),
        latency_ms=max(0, latency_ms),
    )


def _detect_rule_flags(
    text: str,
    normalized_text: str,
    index_map: list[int],
) -> list[FastCheckFlag]:
    flags: list[FastCheckFlag] = []
    for rule in RULES:
        if rule.code == "UPFRONT_FEE" and _has_negated_upfront_fee(normalized_text):
            continue
        span = _first_span(text, normalized_text, index_map, rule.patterns)
        if span is not None:
            flags.append(
                FastCheckFlag(
                    code=rule.code,
                    label=rule.label,
                    severity=rule.severity,
                    evidence_span=span,
                )
            )
    return flags


def _detect_suspicious_link(
    text: str,
    normalized_text: str,
    index_map: list[int],
) -> FastCheckFlag | None:
    for match in URL_PATTERN.finditer(text):
        url = match.group("url").rstrip(".,;:!?)]}")
        if _is_suspicious_url(url) or _has_suspicious_link_context(
            normalized_text,
            index_map,
            match.start(),
            match.end(),
        ):
            return FastCheckFlag(
                code="SUSPICIOUS_LINK",
                label="Đường dẫn đáng ngờ hoặc rút gọn",
                severity="high",
                evidence_span=url,
            )
    return None


def _deduplicate_flags(flags: list[FastCheckFlag]) -> list[FastCheckFlag]:
    seen: set[str] = set()
    deduplicated: list[FastCheckFlag] = []
    for flag in flags:
        if flag.code in seen:
            continue
        seen.add(flag.code)
        deduplicated.append(flag)
    return deduplicated


def _score(flags: list[FastCheckFlag]) -> int:
    weights = {rule.code: rule.score for rule in RULES}
    weights["SUSPICIOUS_LINK"] = 25

    score = sum(weights[flag.code] for flag in flags)
    if len(flags) >= 2:
        score += 10
    if len(flags) >= 3:
        score += 10
    return _clamp(score, minimum=0, maximum=100)


def _risk_band(score: int) -> FastCheckRiskBand:
    if score >= 90:
        return FastCheckRiskBand.CRITICAL
    if score >= 75:
        return FastCheckRiskBand.HIGH_RISK
    if score >= 50:
        return FastCheckRiskBand.SUSPICIOUS
    if score >= 25:
        return FastCheckRiskBand.UNCERTAIN
    return FastCheckRiskBand.LOW


def _message_for_score(score: int) -> str:
    band = _risk_band(score)
    if band is FastCheckRiskBand.CRITICAL:
        return (
            "Nội dung có nguy cơ lừa đảo rất cao. Không cung cấp mã, tiền hoặc quyền "
            "truy cập trước khi xác minh qua kênh chính thức."
        )
    if band is FastCheckRiskBand.HIGH_RISK:
        return (
            "Nội dung có nhiều dấu hiệu nguy cơ cao. Hãy dừng thao tác và xác minh độc lập."
        )
    if band is FastCheckRiskBand.SUSPICIOUS:
        return "Nội dung có dấu hiệu đáng nghi. Cần kiểm tra thêm trước khi hành động."
    if band is FastCheckRiskBand.UNCERTAIN:
        return "Nội dung có một số dấu hiệu cần thận trọng. Hãy xác minh qua kênh chính thức."
    return "Chưa thấy dấu hiệu nguy cơ cao trong phần kiểm tra nhanh."


def _immediate_actions(flags: list[FastCheckFlag]) -> list[str]:
    if not flags:
        return [
            "Vẫn xác minh người gửi qua kênh chính thức nếu nội dung liên quan đến "
            "tiền hoặc tài khoản.",
            "Không chia sẻ thông tin nhạy cảm nếu chưa chắc chắn về danh tính người liên hệ.",
        ]

    actions: list[str] = []
    codes = {flag.code for flag in flags}
    if "OTP_REQUEST" in codes:
        actions.append("Không cung cấp OTP, mật khẩu, PIN hoặc mã xác thực.")
    if "URGENT_MONEY_TRANSFER" in codes or "UPFRONT_FEE" in codes:
        actions.append("Không chuyển tiền hoặc nộp phí trước khi xác minh độc lập.")
    if "ACCOUNT_LOCK_OR_ARREST_THREAT" in codes:
        actions.append(
            "Không làm theo lời đe dọa; liên hệ tổ chức hoặc cơ quan qua kênh chính thức."
        )
    if "REMOTE_CONTROL_APP_REQUEST" in codes:
        actions.append("Không cài ứng dụng điều khiển từ xa hoặc chia sẻ màn hình.")
    if "SUSPICIOUS_LINK" in codes:
        actions.append("Không bấm vào đường dẫn lạ; hãy tự nhập địa chỉ website chính thức.")
    if "GUARANTEED_INVESTMENT_RETURN" in codes:
        actions.append("Không đầu tư chỉ dựa trên cam kết lợi nhuận chắc chắn.")
    if "SECRECY_REQUEST" in codes:
        actions.append(
            "Không giữ bí mật một mình; hãy hỏi người thân hoặc kênh hỗ trợ đáng tin cậy."
        )

    actions.append("Lưu lại nội dung tin nhắn để đối chiếu khi cần báo cáo hoặc nhờ hỗ trợ.")
    return actions


def _first_span(
    text: str,
    normalized_text: str,
    index_map: list[int],
    patterns: tuple[re.Pattern[str], ...],
) -> str | None:
    best_match: re.Match[str] | None = None
    for pattern in patterns:
        match = pattern.search(normalized_text)
        if match is None:
            continue
        if best_match is None or match.start() < best_match.start():
            best_match = match

    if best_match is None:
        return None
    return _span_from_normalized_match(text, index_map, best_match)


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


def _has_negated_upfront_fee(normalized_text: str) -> bool:
    return any(pattern.search(normalized_text) for pattern in NEGATED_UPFRONT_FEE_PATTERNS)


def _is_suspicious_url(url: str) -> bool:
    host = _extract_host(url)
    if host in SHORTENED_DOMAINS:
        return True
    if host.startswith("xn--"):
        return True
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        return True
    return host.count(".") >= 3


def _extract_host(url: str) -> str:
    without_scheme = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    without_www = re.sub(r"^www\.", "", without_scheme, flags=re.IGNORECASE)
    return without_www.split("/", maxsplit=1)[0].split(":", maxsplit=1)[0].casefold()


def _has_suspicious_link_context(
    normalized_text: str,
    index_map: list[int],
    original_start: int,
    original_end: int,
) -> bool:
    if not index_map:
        return False

    normalized_positions = [
        position
        for position, original_position in enumerate(index_map)
        if original_start <= original_position < original_end
    ]
    if not normalized_positions:
        return False

    start = max(0, min(normalized_positions) - 80)
    end = min(len(normalized_text), max(normalized_positions) + 81)
    return SUSPICIOUS_LINK_CONTEXT.search(normalized_text[start:end]) is not None


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
