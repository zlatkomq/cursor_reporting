"""Unit tests for POST /api/v1/ingest stub endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

VALID_PAYLOAD: dict[str, object] = {
    "event_type": "stop",
    "conversation_id": "conv-abc-123",
    "generation_id": "gen-xyz-789",
    "model": "claude-4-opus",
    "user_email": "dev@company.com",
    "status": "completed",
    "duration_ms": 45000,
    "loop_count": 3,
    "cursor_version": "1.2.0",
    "timestamp": "2026-05-12T10:00:00Z",
}


@pytest.fixture()
def payload() -> dict[str, object]:
    return {**VALID_PAYLOAD}


class TestIngestValidPayload:
    """POST /api/v1/ingest with a well-formed payload."""

    async def test_valid_payload_returns_202(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 202

    async def test_valid_payload_response_body(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.json() == {"status": "accepted"}

    async def test_session_end_event_returns_202(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        payload["event_type"] = "session_end"
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 202

    async def test_minimal_payload_without_optionals_returns_202(self, async_client: AsyncClient) -> None:
        minimal = {k: v for k, v in VALID_PAYLOAD.items() if k not in {"duration_ms", "loop_count", "cursor_version"}}
        resp = await async_client.post("/api/v1/ingest", json=minimal)
        assert resp.status_code == 202


class TestIngestInvalidPayload:
    """POST /api/v1/ingest with invalid field values."""

    async def test_invalid_event_type_returns_422(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        payload["event_type"] = "invalid_type"
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422

    async def test_invalid_status_returns_422(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        payload["status"] = "unknown"
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422

    async def test_invalid_timestamp_returns_422(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        payload["timestamp"] = "not-a-date"
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422

    async def test_duration_ms_non_integer_returns_422(
        self, async_client: AsyncClient, payload: dict[str, object]
    ) -> None:
        payload["duration_ms"] = "not_a_number"
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422


class TestIngestMissingFields:
    """POST /api/v1/ingest with missing required fields."""

    async def test_missing_required_field_returns_422(
        self, async_client: AsyncClient, payload: dict[str, object]
    ) -> None:
        del payload["event_type"]
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422

    async def test_missing_timestamp_returns_422(self, async_client: AsyncClient, payload: dict[str, object]) -> None:
        del payload["timestamp"]
        resp = await async_client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/v1/ingest", json={})
        assert resp.status_code == 422

    async def test_null_body_returns_422(self, async_client: AsyncClient) -> None:
        resp = await async_client.post("/api/v1/ingest", json=None)
        assert resp.status_code == 422
