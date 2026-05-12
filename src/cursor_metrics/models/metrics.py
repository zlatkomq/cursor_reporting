"""Pydantic request/response schemas for the metrics API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IngestPayload(BaseModel):
    """Telemetry payload sent by Cursor IDE hooks via POST /api/v1/ingest."""

    event_type: Literal["stop", "session_end"]
    conversation_id: str
    generation_id: str
    model: str
    user_email: str
    status: Literal["completed", "aborted", "error"]
    duration_ms: int | None = None
    loop_count: int | None = None
    cursor_version: str | None = None
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """Response schema for GET / health-check endpoint."""

    status: str
    version: str
    database: str
