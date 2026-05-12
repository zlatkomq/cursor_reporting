"""Tests for POST /api/v1/ingest stub endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import Iterator

    from httpx import Response


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    yield
    get_settings.cache_clear()


@pytest.fixture()
def valid_payload() -> dict[str, object]:
    return {
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


def _mock_engine() -> MagicMock:
    """Return a mock async_engine so module import doesn't fail."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=mock_conn)
    return engine


async def _post_ingest(payload: dict[str, object] | None = None) -> Response:
    """POST to /api/v1/ingest with the given payload."""
    from cursor_metrics.main import app

    with patch("cursor_metrics.main.async_engine", _mock_engine()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/v1/ingest", json=payload)


class TestIngestEndpointValidPayload:
    """POST /api/v1/ingest with valid payloads returns 202 Accepted."""

    async def test_valid_payload_returns_202(self, valid_payload: dict[str, object]) -> None:
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 202

    async def test_valid_payload_returns_json_body(self, valid_payload: dict[str, object]) -> None:
        resp = await _post_ingest(valid_payload)
        body = resp.json()
        assert "status" in body
        assert body["status"] == "accepted"

    async def test_session_end_event_returns_202(self, valid_payload: dict[str, object]) -> None:
        valid_payload["event_type"] = "session_end"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 202

    async def test_minimal_payload_without_optionals_returns_202(self) -> None:
        payload = {
            "event_type": "stop",
            "conversation_id": "conv-abc-123",
            "generation_id": "gen-xyz-789",
            "model": "claude-4-opus",
            "user_email": "dev@company.com",
            "status": "completed",
            "timestamp": "2026-05-12T10:00:00Z",
        }
        resp = await _post_ingest(payload)
        assert resp.status_code == 202


class TestIngestEndpointInvalidPayload:
    """POST /api/v1/ingest with invalid payloads returns 422 Unprocessable Entity."""

    async def test_invalid_event_type_returns_422(self, valid_payload: dict[str, object]) -> None:
        valid_payload["event_type"] = "invalid_type"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_invalid_status_returns_422(self, valid_payload: dict[str, object]) -> None:
        valid_payload["status"] = "unknown"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_invalid_timestamp_returns_422(self, valid_payload: dict[str, object]) -> None:
        valid_payload["timestamp"] = "not-a-date"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_duration_ms_non_integer_returns_422(self, valid_payload: dict[str, object]) -> None:
        valid_payload["duration_ms"] = "not_a_number"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422


class TestIngestEndpointMissingFields:
    """POST /api/v1/ingest with missing required fields returns 422."""

    async def test_missing_event_type_returns_422(self, valid_payload: dict[str, object]) -> None:
        del valid_payload["event_type"]
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_missing_conversation_id_returns_422(self, valid_payload: dict[str, object]) -> None:
        del valid_payload["conversation_id"]
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_missing_timestamp_returns_422(self, valid_payload: dict[str, object]) -> None:
        del valid_payload["timestamp"]
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self) -> None:
        resp = await _post_ingest({})
        assert resp.status_code == 422

    async def test_null_body_returns_422(self) -> None:
        resp = await _post_ingest(None)
        assert resp.status_code == 422
