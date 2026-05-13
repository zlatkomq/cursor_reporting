"""Tests for POST /api/v1/ingest endpoint with DB persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Iterator

    from httpx import Response


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key")
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
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=mock_conn)
    return engine


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    return session


async def _mock_get_db() -> AsyncGenerator[AsyncMock]:
    yield _mock_session()


async def _post_ingest(payload: dict[str, object] | None = None) -> Response:
    from cursor_metrics.database import get_db
    from cursor_metrics.main import app

    app.dependency_overrides[get_db] = _mock_get_db
    try:
        with patch("cursor_metrics.main.async_engine", _mock_engine()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post("/api/v1/ingest", json=payload)
    finally:
        app.dependency_overrides.pop(get_db, None)


FULL_PAYLOAD: dict[str, object] = {
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
    "input_tokens": 1200,
    "output_tokens": 800,
    "cache_read_tokens": 500,
    "cache_write_tokens": 300,
    "session_id": "sess-001",
    "workspace": "/home/dev/project",
    "command_name": "composer",
    "skill_name": "create-rule",
}


async def _post_ingest_with_session(
    payload: dict[str, object],
) -> tuple[Response, AsyncMock]:
    """Post to /ingest and return (response, mock_session) for assertions."""
    from cursor_metrics.database import get_db
    from cursor_metrics.main import app

    session = _mock_session()

    async def _get_db_override() -> AsyncGenerator[AsyncMock]:
        yield session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        with patch("cursor_metrics.main.async_engine", _mock_engine()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/ingest", json=payload)
                return resp, session
    finally:
        app.dependency_overrides.pop(get_db, None)


class TestIngestEndpointValidPayload:
    """POST /api/v1/ingest with valid payloads returns 202 Accepted."""

    async def test_valid_payload_returns_202(self, valid_payload: dict[str, object]) -> None:
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 202

    async def test_valid_payload_returns_json_body(self, valid_payload: dict[str, object]) -> None:
        resp = await _post_ingest(valid_payload)
        body = resp.json()
        assert body["status"] == "accepted"
        assert "id" in body

    async def test_session_end_event_returns_202(self, valid_payload: dict[str, object]) -> None:
        valid_payload["event_type"] = "session_end"
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 202

    async def test_minimal_payload_returns_202(self) -> None:
        resp = await _post_ingest({"event_type": "stop"})
        assert resp.status_code == 202

    async def test_full_payload_with_all_fields_returns_202(self) -> None:
        resp = await _post_ingest(FULL_PAYLOAD)
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "accepted"

    async def test_old_payload_without_new_fields_returns_202(self, valid_payload: dict[str, object]) -> None:
        resp = await _post_ingest(valid_payload)
        assert resp.status_code == 202

    async def test_session_add_called_with_metrics_event(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        resp, session = await _post_ingest_with_session(FULL_PAYLOAD)
        assert resp.status_code == 202
        session.add.assert_called_once()
        event = session.add.call_args[0][0]
        assert isinstance(event, MetricsEvent)
        assert event.input_tokens == 1200
        assert event.output_tokens == 800
        assert event.cache_read_tokens == 500
        assert event.cache_write_tokens == 300
        assert event.session_id == "sess-001"
        assert event.workspace == "/home/dev/project"
        assert event.command_name == "composer"
        assert event.skill_name == "create-rule"


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

    async def test_missing_event_type_returns_422(self) -> None:
        resp = await _post_ingest({"conversation_id": "x"})
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self) -> None:
        resp = await _post_ingest({})
        assert resp.status_code == 422

    async def test_null_body_returns_422(self) -> None:
        resp = await _post_ingest(None)
        assert resp.status_code == 422
