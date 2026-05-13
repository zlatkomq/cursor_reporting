"""Pydantic request/response schemas for the metrics API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IngestPayload(BaseModel):
    """Telemetry payload sent by Cursor IDE hooks via POST /api/v1/ingest."""

    event_type: Literal["stop", "session_end"]
    conversation_id: str = "unknown"
    generation_id: str = "unknown"
    model: str = "unknown"
    user_email: str = "unknown"
    status: Literal["completed", "aborted", "error"] = "completed"
    duration_ms: int | None = None
    loop_count: int | None = None
    cursor_version: str | None = None
    timestamp: datetime | None = None


class HealthCheckResponse(BaseModel):
    """Response schema for GET / health-check endpoint."""

    status: str
    version: str
    database: str
