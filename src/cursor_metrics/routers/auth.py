"""Auth router — dashboard login and session management."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
