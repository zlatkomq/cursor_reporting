"""Ingest router — accepts telemetry payloads and persists to database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from cursor_metrics.database import get_db
from cursor_metrics.models.db import MetricsEvent
from cursor_metrics.models.metrics import IngestPayload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    payload: IngestPayload,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Accept a telemetry payload, persist it, and return 202 Accepted."""
    event = MetricsEvent(
        event_type=payload.event_type,
        conversation_id=payload.conversation_id,
        generation_id=payload.generation_id,
        model=payload.model,
        user_email=payload.user_email,
        status=payload.status,
        duration_ms=payload.duration_ms,
        loop_count=payload.loop_count,
        cursor_version=payload.cursor_version,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    return JSONResponse(
        content={"status": "accepted", "id": event.id},
        status_code=status.HTTP_202_ACCEPTED,
    )
