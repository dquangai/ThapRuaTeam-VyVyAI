from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_fast_check import router as fast_check_router
from app.api.routes_health import router as health_router
from app.api.routes_investigation import router as investigation_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="VYVY API",
    description="Text-only investigation and verification MVP.",
    version=settings.app_version,
)

if settings.cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Không thể xử lý yêu cầu lúc này.",
                "details": {},
                "request_id": request_id,
            }
        },
    )


app.include_router(health_router)
app.include_router(fast_check_router)
app.include_router(investigation_router)
