"""Pydantic request/response schemas for the metrics API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class IngestPayload(BaseModel):
    """Telemetry payload sent by Cursor IDE hooks via POST /api/v1/ingest."""

    event_type: Literal["stop", "session_end", "subagent_stop"]
    conversation_id: str = "unknown"
    generation_id: str = "unknown"
    model: str = "unknown"
    user_email: str = "unknown"
    status: Literal["completed", "aborted", "error"] = "completed"
    duration_ms: int | None = None
    loop_count: int | None = None
    cursor_version: str | None = None
    timestamp: datetime | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    session_id: str | None = None
    workspace: str | None = None
    command_name: str | None = None
    skill_name: str | None = None
    subagent_type: str | None = None


class HealthCheckResponse(BaseModel):
    """Response schema for GET / health-check endpoint."""

    status: str
    version: str
    database: str
