"""Reports router — GET endpoints for querying aggregated metrics."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["reports"])
