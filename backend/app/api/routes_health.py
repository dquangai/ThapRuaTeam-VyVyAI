from fastapi import APIRouter

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "service": "vyvy-backend",
        "status": "ok",
        "version": settings.app_version,
        "mock_mode": settings.mock_mode,
        "providers": _safe_provider_health(settings),
        "models": {
            "fast": settings.openai_model_fast,
            "expert": settings.openai_model_expert,
            "judge": settings.openai_model_judge,
            "report": settings.openai_model_report,
        },
    }


def _safe_provider_health(settings: Settings) -> dict[str, dict[str, object]]:
    mock_mode = settings.mock_mode
    openai_enabled = not mock_mode
    search_enabled = settings.enable_web_search and not mock_mode
    virustotal_enabled = settings.enable_virustotal and not mock_mode
    return {
        "openai": {
            "configured": settings.openai_api_key is not None,
            "enabled": openai_enabled,
            "mode": "mock" if mock_mode else "live",
        },
        "tavily": {
            "configured": settings.tavily_api_key is not None,
            "enabled": search_enabled,
            "mode": "mock" if mock_mode else ("live" if search_enabled else "disabled"),
        },
        "virustotal": {
            "configured": settings.virustotal_api_key is not None,
            "enabled": virustotal_enabled,
            "mode": "mock" if mock_mode else ("live" if virustotal_enabled else "disabled"),
        },
    }
