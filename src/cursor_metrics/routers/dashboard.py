"""Dashboard router — HTML views rendered via Jinja2 + HTMX."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["dashboard"])
