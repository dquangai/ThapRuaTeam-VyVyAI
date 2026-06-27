from __future__ import annotations

import base64
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import MissingConfigurationError, Settings


class VirusTotalReputation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str
    target_type: str
    reputation: int | None = None
    harmless: int = Field(ge=0, default=0)
    malicious: int = Field(ge=0, default=0)
    suspicious: int = Field(ge=0, default=0)
    undetected: int = Field(ge=0, default=0)


class VirusTotalProvider:
    provider_name = "virustotal"

    def __init__(self, *, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client

    async def lookup(self, target: str, target_type: str) -> VirusTotalReputation | None:
        api_key = self.settings.virustotal_api_key
        if api_key is None:
            raise MissingConfigurationError(
                "VIRUSTOTAL_API_KEY is required for VirusTotal enrichment.",
                variable_name="VIRUSTOTAL_API_KEY",
            )
        if target_type not in {"url", "domain"}:
            return None

        close_client = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=self.settings.provider_timeout_float())
            close_client = True

        try:
            endpoint = _endpoint_for_target(target=target, target_type=target_type)
            response = await client.get(
                endpoint,
                headers={"x-apikey": api_key.get_secret_value()},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return _normalize_reputation(
                target=target,
                target_type=target_type,
                payload=response.json(),
            )
        finally:
            if close_client:
                await client.aclose()


def _endpoint_for_target(*, target: str, target_type: str) -> str:
    if target_type == "domain":
        return f"https://www.virustotal.com/api/v3/domains/{target}"
    encoded = base64.urlsafe_b64encode(target.encode("utf-8")).decode("ascii").rstrip("=")
    return f"https://www.virustotal.com/api/v3/urls/{encoded}"


def _normalize_reputation(
    *,
    target: str,
    target_type: str,
    payload: dict[str, Any],
) -> VirusTotalReputation:
    attributes = (
        payload.get("data", {}).get("attributes", {})
        if isinstance(payload.get("data"), dict)
        else {}
    )
    stats = attributes.get("last_analysis_stats", {})
    if not isinstance(stats, dict):
        stats = {}
    reputation = attributes.get("reputation")
    return VirusTotalReputation(
        target=target,
        target_type=target_type,
        reputation=reputation if isinstance(reputation, int) else None,
        harmless=_non_negative_int(stats.get("harmless")),
        malicious=_non_negative_int(stats.get("malicious")),
        suspicious=_non_negative_int(stats.get("suspicious")),
        undetected=_non_negative_int(stats.get("undetected")),
    )


def _non_negative_int(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0
