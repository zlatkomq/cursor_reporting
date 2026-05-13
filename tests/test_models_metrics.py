"""Tests for Pydantic request/response schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    yield
    get_settings.cache_clear()


class TestIngestPayload:
    """Validate IngestPayload accepts correct data and rejects invalid data."""

    @pytest.fixture()
    def valid_payload(self) -> dict[str, object]:
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

    def test_accepts_valid_stop_payload(self, valid_payload: dict[str, object]) -> None:
        from datetime import datetime

        from cursor_metrics.models.metrics import IngestPayload

        payload = IngestPayload(**valid_payload)
        assert payload.event_type == "stop"
        assert payload.conversation_id == "conv-abc-123"
        assert payload.generation_id == "gen-xyz-789"
        assert payload.model == "claude-4-opus"
        assert payload.user_email == "dev@company.com"
        assert payload.status == "completed"
        assert payload.duration_ms == 45000
        assert payload.loop_count == 3
        assert payload.cursor_version == "1.2.0"
        assert isinstance(payload.timestamp, datetime)

    def test_accepts_valid_session_end_payload(self, valid_payload: dict[str, object]) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["event_type"] = "session_end"
        valid_payload["status"] = "aborted"
        payload = IngestPayload(**valid_payload)
        assert payload.event_type == "session_end"
        assert payload.status == "aborted"

    def test_accepts_error_status(self, valid_payload: dict[str, object]) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["status"] = "error"
        payload = IngestPayload(**valid_payload)
        assert payload.status == "error"

    def test_optional_fields_default_to_none(self, valid_payload: dict[str, object]) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        del valid_payload["duration_ms"]
        del valid_payload["loop_count"]
        del valid_payload["cursor_version"]
        payload = IngestPayload(**valid_payload)
        assert payload.duration_ms is None
        assert payload.loop_count is None
        assert payload.cursor_version is None

    def test_rejects_invalid_event_type(self, valid_payload: dict[str, object]) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["event_type"] = "invalid_type"
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)

    def test_rejects_invalid_status(self, valid_payload: dict[str, object]) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["status"] = "unknown"
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)

    def test_rejects_missing_event_type(self, valid_payload: dict[str, object]) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        del valid_payload["event_type"]
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)

    def test_defaults_for_optional_fields(self) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        payload = IngestPayload(event_type="stop")
        assert payload.conversation_id == "unknown"
        assert payload.generation_id == "unknown"
        assert payload.model == "unknown"
        assert payload.user_email == "unknown"
        assert payload.status == "completed"
        assert payload.timestamp is None
        assert payload.input_tokens is None
        assert payload.output_tokens is None
        assert payload.cache_read_tokens is None
        assert payload.cache_write_tokens is None
        assert payload.session_id is None
        assert payload.workspace is None
        assert payload.command_name is None
        assert payload.skill_name is None

    def test_timestamp_parsed_as_datetime(self, valid_payload: dict[str, object]) -> None:
        from datetime import datetime

        from cursor_metrics.models.metrics import IngestPayload

        payload = IngestPayload(**valid_payload)
        assert isinstance(payload.timestamp, datetime)
        assert payload.timestamp.tzinfo is not None

    def test_accepts_datetime_object_directly(self, valid_payload: dict[str, object]) -> None:
        import datetime as dt

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["timestamp"] = dt.datetime(2026, 5, 12, 10, 0, 0, tzinfo=dt.UTC)
        payload = IngestPayload(**valid_payload)
        assert isinstance(payload.timestamp, dt.datetime)

    def test_has_all_expected_fields(self) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        expected_fields = {
            "event_type",
            "conversation_id",
            "generation_id",
            "model",
            "user_email",
            "status",
            "duration_ms",
            "loop_count",
            "cursor_version",
            "timestamp",
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "session_id",
            "workspace",
            "command_name",
            "skill_name",
        }
        assert set(IngestPayload.model_fields.keys()) == expected_fields

    def test_duration_ms_rejects_non_integer(self, valid_payload: dict[str, object]) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["duration_ms"] = "not_a_number"
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)

    def test_loop_count_rejects_non_integer(self, valid_payload: dict[str, object]) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload["loop_count"] = "not_a_number"
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)

    def test_accepts_all_new_fields(self, valid_payload: dict[str, object]) -> None:
        from cursor_metrics.models.metrics import IngestPayload

        valid_payload.update(
            {
                "input_tokens": 1500,
                "output_tokens": 3200,
                "cache_read_tokens": 800,
                "cache_write_tokens": 200,
                "session_id": "sess-abc-123",
                "workspace": "/home/dev/project",
                "command_name": "composer",
                "skill_name": "create-rule",
            }
        )
        payload = IngestPayload(**valid_payload)
        assert payload.input_tokens == 1500
        assert payload.output_tokens == 3200
        assert payload.cache_read_tokens == 800
        assert payload.cache_write_tokens == 200
        assert payload.session_id == "sess-abc-123"
        assert payload.workspace == "/home/dev/project"
        assert payload.command_name == "composer"
        assert payload.skill_name == "create-rule"

    @pytest.mark.parametrize(
        "field",
        ["input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"],
    )
    def test_token_fields_reject_non_integer(self, valid_payload: dict[str, object], field: str) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import IngestPayload

        valid_payload[field] = "not_a_number"
        with pytest.raises(ValidationError):
            IngestPayload(**valid_payload)


class TestHealthCheckResponse:
    """Validate HealthCheckResponse schema."""

    def test_accepts_valid_response(self) -> None:
        from cursor_metrics.models.metrics import HealthCheckResponse

        resp = HealthCheckResponse(status="ok", version="0.1.0", database="connected")
        assert resp.status == "ok"
        assert resp.version == "0.1.0"
        assert resp.database == "connected"

    def test_accepts_disconnected_database(self) -> None:
        from cursor_metrics.models.metrics import HealthCheckResponse

        resp = HealthCheckResponse(status="ok", version="0.1.0", database="disconnected")
        assert resp.database == "disconnected"

    def test_has_all_expected_fields(self) -> None:
        from cursor_metrics.models.metrics import HealthCheckResponse

        expected_fields = {"status", "version", "database"}
        assert set(HealthCheckResponse.model_fields.keys()) == expected_fields

    def test_rejects_missing_status(self) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import HealthCheckResponse

        with pytest.raises(ValidationError):
            HealthCheckResponse(version="0.1.0", database="connected")  # type: ignore[call-arg]

    def test_rejects_missing_version(self) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import HealthCheckResponse

        with pytest.raises(ValidationError):
            HealthCheckResponse(status="ok", database="connected")  # type: ignore[call-arg]

    def test_rejects_missing_database(self) -> None:
        from pydantic import ValidationError

        from cursor_metrics.models.metrics import HealthCheckResponse

        with pytest.raises(ValidationError):
            HealthCheckResponse(status="ok", version="0.1.0")  # type: ignore[call-arg]

    def test_serializes_to_dict(self) -> None:
        from cursor_metrics.models.metrics import HealthCheckResponse

        resp = HealthCheckResponse(status="ok", version="0.1.0", database="connected")
        data = resp.model_dump()
        assert data == {"status": "ok", "version": "0.1.0", "database": "connected"}

    def test_re_exported_from_init(self) -> None:
        from cursor_metrics.models import HealthCheckResponse, IngestPayload

        assert HealthCheckResponse is not None
        assert IngestPayload is not None
