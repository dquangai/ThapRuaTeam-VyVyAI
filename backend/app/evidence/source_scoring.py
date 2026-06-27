from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

OFFICIAL_SOURCE_TERMS = (
    "bo cong an",
    "cong an",
    "chinh phu",
    "ngan hang nha nuoc",
    "state bank",
    "gov",
)

BANK_SOURCE_TERMS = (
    "bank",
    "ngan hang",
    "vietcombank",
    "vpbank",
    "techcombank",
    "bidv",
    "mbbank",
    "acb",
)

NEWS_SOURCE_TERMS = (
    "vnexpress",
    "tuoi tre",
    "thanh nien",
    "vietnamnet",
    "dan tri",
)

SHORTENER_HOSTS = frozenset(
    {
        "bit.ly",
        "bom.so",
        "cutt.ly",
        "goo.gl",
        "s.id",
        "t.co",
        "tinyurl.com",
    }
)

STOPWORDS = {
    "ban",
    "bao",
    "can",
    "canh",
    "cho",
    "cua",
    "duoc",
    "hay",
    "khong",
    "lua",
    "nay",
    "nguoi",
    "nguon",
    "phai",
    "thuc",
    "tin",
    "tra",
    "trong",
    "voi",
}


def score_source_credibility(source_name: str, url: str) -> float:
    host = _host(url)
    normalized_source = _normalize(source_name)

    if host.endswith(".gov.vn") or host.endswith(".gov"):
        return 95
    if any(term in normalized_source for term in OFFICIAL_SOURCE_TERMS):
        return 90
    if _is_bank_like(host, normalized_source):
        return 82
    if any(term in normalized_source or term in host for term in NEWS_SOURCE_TERMS):
        return 72
    if host in SHORTENER_HOSTS or host.count(".") >= 3:
        return 35
    return 55


def score_source_relevance(query: str, title: str, snippet: str, url: str) -> float:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return 0

    searchable_text = f"{title} {snippet} {url}"
    searchable_tokens = set(_tokens(searchable_text))
    if not searchable_tokens:
        return 0

    overlap = query_tokens & searchable_tokens
    score = (len(overlap) / len(query_tokens)) * 100
    if _contains_phrase(query, title) or _contains_phrase(query, snippet):
        score += 15
    return _clamp(round(score, 1), 0, 100)


def _is_bank_like(host: str, normalized_source: str) -> bool:
    if host.endswith(".com.vn") and any(term in normalized_source for term in BANK_SOURCE_TERMS):
        return True
    return any(term in host for term in ("bank", "vietcombank", "vpbank", "mbbank"))


def _contains_phrase(query: str, text: str) -> bool:
    normalized_query = _normalize(query)
    normalized_text = _normalize(text)
    if len(normalized_query) < 8:
        return False
    return normalized_query in normalized_text


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]{3,}", _normalize(text))
        if token not in STOPWORDS
    ]


def _host(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.casefold().removeprefix("www.")


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


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
