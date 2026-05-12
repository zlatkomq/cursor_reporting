"""Stub ingest router — accepts telemetry payloads and returns 202 Accepted."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from cursor_metrics.models.metrics import IngestPayload

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(payload: IngestPayload) -> JSONResponse:
    """Accept a telemetry payload for later processing."""
    return JSONResponse(content={"status": "accepted"}, status_code=status.HTTP_202_ACCEPTED)
