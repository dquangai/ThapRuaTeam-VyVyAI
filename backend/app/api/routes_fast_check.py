from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter

from app.models import InvestigationRequest
from app.services.fast_check import FastCheckResponse, analyze_fast_check

router = APIRouter(prefix="/api/v1", tags=["fast-check"])


@router.post("/fast-check", response_model=FastCheckResponse)
async def fast_check(request: InvestigationRequest) -> FastCheckResponse:
    start = perf_counter()
    request_id = str(uuid4())
    response = analyze_fast_check(
        text=request.text,
        request_id=request_id,
    )
    latency_ms = round((perf_counter() - start) * 1000)
    return response.model_copy(update={"latency_ms": latency_ms})
